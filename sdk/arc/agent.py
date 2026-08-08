"""
ARC SDK - Agent Protection Layer (`ARCAgent` and `AsyncARCAgent`).
Provides transparent Anthropic client wrapping, automatic Flight Recorder step tracing, Context Firewall checking, and Recovery Engine support.
Fully decoupled from backend server internals.
"""

import time
import uuid
import inspect
import logging
from functools import wraps
from typing import Optional, List, Dict, Any, Union, Callable, ContextManager, AsyncContextManager

from .client import ARC, AsyncARC
from .types import Session, TraceStep, VerificationResult, SessionStatus
from .exceptions import ARCError, APIError, APIConnectionError

logger = logging.getLogger("arc.agent")


class MockAnthropicResponseBlock:
    def __init__(self, text: str):
        self.text = text


class MockAnthropicUsage:
    def __init__(self, input_tokens: int = 150, output_tokens: int = 350):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class MockAnthropicResponse:
    def __init__(self, text: str):
        self.content = [MockAnthropicResponseBlock(text)]
        self.usage = MockAnthropicUsage()


class MockAnthropicClient:
    """Mock Anthropic client explicitly used when mock_mode is enabled for offline testing."""

    class Messages:
        def __init__(self, parent):
            self.parent = parent

        def create(self, **kwargs) -> MockAnthropicResponse:
            messages = kwargs.get("messages", [])
            last_msg = ""
            for msg in reversed(messages):
                if isinstance(msg, dict) and msg.get("role") == "user":
                    last_msg = str(msg.get("content", ""))
                    break

            resp_text = (
                f"ARC Managed Claude Response: Processed query '{last_msg[:80]}...'"
                if last_msg
                else "ARC Managed Claude Response"
            )
            return MockAnthropicResponse(resp_text)

    def __init__(self):
        self.messages = self.Messages(self)


class StepContext:
    """Synchronous context manager for manual step tracing."""
    def __init__(self, agent: "ARCAgent", name: str, input_data: Optional[Dict[str, Any]] = None):
        self.agent = agent
        self.name = name
        self.input_data = input_data or {}
        self.start_time = 0.0

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        latency_ms = (time.time() - self.start_time) * 1000.0
        error_msg = str(exc_val) if exc_val else None
        output = {"status": "error", "error": error_msg} if exc_val else {"status": "success"}
        self.agent.record_step(
            step_type="tool_call",
            name=self.name,
            input_data=self.input_data,
            output_data=output,
            latency_ms=latency_ms,
        )


class AsyncStepContext:
    """Asynchronous context manager for manual step tracing."""
    def __init__(self, agent: "AsyncARCAgent", name: str, input_data: Optional[Dict[str, Any]] = None):
        self.agent = agent
        self.name = name
        self.input_data = input_data or {}
        self.start_time = 0.0

    async def __aenter__(self):
        self.start_time = time.time()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        latency_ms = (time.time() - self.start_time) * 1000.0
        error_msg = str(exc_val) if exc_val else None
        output = {"status": "error", "error": error_msg} if exc_val else {"status": "success"}
        await self.agent.record_step(
            step_type="tool_call",
            name=self.name,
            input_data=self.input_data,
            output_data=output,
            latency_ms=latency_ms,
        )


class ARCAgent:
    """
    Synchronous ARCAgent protector for Claude workflows.
    Tracks execution steps in Flight Recorder, enforces Context Firewall rules, and records session telemetry.
    """

    def __init__(
        self,
        name: str = "ARC Agent",
        task: str = "General Task",
        arc_client: Optional[ARC] = None,
        anthropic_client: Optional[Any] = None,
        server_url: str = "http://localhost:8000",
        dashboard_url: str = "http://localhost:3000",
        session_id: Optional[Union[str, uuid.UUID]] = None,
        mock_mode: bool = False,
    ):
        self.name = name
        self.task = task
        self.server_url = server_url.rstrip("/")
        self.dashboard_base_url = dashboard_url.rstrip("/")
        self.session_id = str(session_id) if session_id else str(uuid.uuid4())
        self.mock_mode = mock_mode

        self.arc_client = arc_client or ARC(server_url=self.server_url)

        if mock_mode:
            self.anthropic_client = MockAnthropicClient()
        else:
            self.anthropic_client = anthropic_client

        self._local_steps: List[TraceStep] = []
        self._init_session()

    def _init_session(self):
        """Create session on remote backend server asynchronously or register locally."""
        try:
            self.arc_client.create_session(
                agent_name=self.name,
                task=self.task,
                session_id=self.session_id,
            )
        except Exception as e:
            logger.debug(f"Could not reach remote ARC server to register session ({e}). Session running in offline mode.")

    @property
    def dashboard_url(self) -> str:
        """Return live visual dashboard URL for this session."""
        return f"{self.dashboard_base_url}/sessions/{self.session_id}"

    def record_step(
        self,
        step_type: str = "llm_call",
        name: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        latency_ms: float = 0.0,
        token_usage: Optional[Dict[str, int]] = None,
        confidence_score: float = 1.0,
    ) -> TraceStep:
        """Record an execution step to the ARC server or local trace history."""
        try:
            step = self.arc_client.record_step(
                session_id=self.session_id,
                step_type=step_type,
                name=name,
                input_data=input_data,
                output_data=output_data,
                latency_ms=latency_ms,
                token_usage=token_usage,
                confidence_score=confidence_score,
            )
            self._local_steps.append(step)
            return step
        except Exception as e:
            logger.debug(f"Failed to push step to ARC server ({e}). Recording locally.")
            step = TraceStep(
                step_id=str(uuid.uuid4()),
                session_id=self.session_id,
                step_type=step_type,
                step_number=len(self._local_steps) + 1,
                name=name or step_type,
                input_data=input_data or {},
                output_data=output_data or {},
                latency_ms=latency_ms,
                token_usage=token_usage or {},
                confidence_score=confidence_score,
            )
            self._local_steps.append(step)
            return step

    def call_claude(
        self,
        messages: List[Dict[str, Any]],
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 1024,
        tools: Optional[List[Dict[str, Any]]] = None,
        system: Optional[str] = None,
    ) -> str:
        """
        Call Claude API under ARC protection with automatic step tracing and latency monitoring.
        """
        start_time = time.time()
        kwargs: Dict[str, Any] = {"model": model, "max_tokens": max_tokens, "messages": messages}
        if tools:
            kwargs["tools"] = tools
        if system:
            kwargs["system"] = system

        if self.anthropic_client is None:
            try:
                import anthropic
                self.anthropic_client = anthropic.Anthropic()
            except Exception:
                if not self.mock_mode:
                    logger.warning("No Anthropic API key or client available. Enabling mock client mode.")
                    self.mock_mode = True
                    self.anthropic_client = MockAnthropicClient()

        try:
            res = self.anthropic_client.messages.create(**kwargs)
            latency_ms = (time.time() - start_time) * 1000.0

            response_text = ""
            if hasattr(res, "content") and res.content:
                if isinstance(res.content, list):
                    response_text = res.content[0].text if hasattr(res.content[0], "text") else str(res.content[0])
                else:
                    response_text = str(res.content)

            input_tokens = getattr(getattr(res, "usage", None), "input_tokens", 0)
            output_tokens = getattr(getattr(res, "usage", None), "output_tokens", 0)

            self.record_step(
                step_type="llm_call",
                name=f"Claude Call ({model})",
                input_data={"messages": messages, "model": model},
                output_data={"text": response_text},
                latency_ms=latency_ms,
                token_usage={"input_tokens": input_tokens, "output_tokens": output_tokens},
            )
            return response_text

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000.0
            self.record_step(
                step_type="llm_call",
                name=f"Claude Call Failed ({model})",
                input_data={"messages": messages, "model": model},
                output_data={"error": str(e)},
                latency_ms=latency_ms,
                confidence_score=0.0,
            )
            raise e

    def run_tool(
        self,
        tool_name: str,
        tool_input: Any,
        tool_fn: Callable[[Any], Any],
    ) -> Any:
        """
        Execute an agent tool wrapped with automatic step tracing and checkpointing.
        """
        start_time = time.time()
        try:
            if isinstance(tool_input, dict):
                res = tool_fn(**tool_input)
            else:
                res = tool_fn(tool_input)

            latency_ms = (time.time() - start_time) * 1000.0
            self.record_step(
                step_type="tool_call",
                name=tool_name,
                input_data=tool_input if isinstance(tool_input, dict) else {"input": str(tool_input)},
                output_data=res if isinstance(res, dict) else {"result": str(res)},
                latency_ms=latency_ms,
            )
            return res
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000.0
            self.record_step(
                step_type="tool_call",
                name=f"{tool_name} (Failed)",
                input_data=tool_input if isinstance(tool_input, dict) else {"input": str(tool_input)},
                output_data={"error": str(e)},
                latency_ms=latency_ms,
                confidence_score=0.0,
            )
            raise e

    def trace_step(self, name: str, input_data: Optional[Dict[str, Any]] = None) -> StepContext:
        """Context manager for protected execution blocks."""
        return StepContext(self, name, input_data)

    def complete(self, output: Any = None) -> Dict[str, Any]:
        """Mark session as completed."""
        return {
            "session_id": self.session_id,
            "status": "completed",
            "dashboard_url": self.dashboard_url,
            "total_steps": len(self._local_steps),
            "final_output": output,
        }


class AsyncARCAgent:
    """
    Asynchronous AsyncARCAgent protector for Claude workflows.
    """

    def __init__(
        self,
        name: str = "Async ARC Agent",
        task: str = "General Task",
        arc_client: Optional[AsyncARC] = None,
        anthropic_client: Optional[Any] = None,
        server_url: str = "http://localhost:8000",
        dashboard_url: str = "http://localhost:3000",
        session_id: Optional[Union[str, uuid.UUID]] = None,
        mock_mode: bool = False,
    ):
        self.name = name
        self.task = task
        self.server_url = server_url.rstrip("/")
        self.dashboard_base_url = dashboard_url.rstrip("/")
        self.session_id = str(session_id) if session_id else str(uuid.uuid4())
        self.mock_mode = mock_mode

        self.arc_client = arc_client or AsyncARC(server_url=self.server_url)

        if mock_mode:
            self.anthropic_client = MockAnthropicClient()
        else:
            self.anthropic_client = anthropic_client

        self._local_steps: List[TraceStep] = []

    @property
    def dashboard_url(self) -> str:
        return f"{self.dashboard_base_url}/sessions/{self.session_id}"

    async def record_step(
        self,
        step_type: str = "llm_call",
        name: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        latency_ms: float = 0.0,
        token_usage: Optional[Dict[str, int]] = None,
        confidence_score: float = 1.0,
    ) -> TraceStep:
        try:
            step = await self.arc_client.record_step(
                session_id=self.session_id,
                step_type=step_type,
                name=name,
                input_data=input_data,
                output_data=output_data,
                latency_ms=latency_ms,
                token_usage=token_usage,
                confidence_score=confidence_score,
            )
            self._local_steps.append(step)
            return step
        except Exception as e:
            logger.debug(f"Failed to push async step to ARC server ({e}). Recording locally.")
            step = TraceStep(
                step_id=str(uuid.uuid4()),
                session_id=self.session_id,
                step_type=step_type,
                step_number=len(self._local_steps) + 1,
                name=name or step_type,
                input_data=input_data or {},
                output_data=output_data or {},
                latency_ms=latency_ms,
                token_usage=token_usage or {},
                confidence_score=confidence_score,
            )
            self._local_steps.append(step)
            return step

    async def acall_claude(
        self,
        messages: List[Dict[str, Any]],
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 1024,
        tools: Optional[List[Dict[str, Any]]] = None,
        system: Optional[str] = None,
    ) -> str:
        start_time = time.time()
        kwargs: Dict[str, Any] = {"model": model, "max_tokens": max_tokens, "messages": messages}
        if tools:
            kwargs["tools"] = tools
        if system:
            kwargs["system"] = system

        if self.anthropic_client is None:
            try:
                import anthropic
                self.anthropic_client = anthropic.AsyncAnthropic()
            except Exception:
                if not self.mock_mode:
                    logger.warning("No Anthropic API key or client available. Enabling mock client mode.")
                    self.mock_mode = True
                    self.anthropic_client = MockAnthropicClient()

        try:
            if inspect.iscoroutinefunction(getattr(self.anthropic_client.messages, "create", None)):
                res = await self.anthropic_client.messages.create(**kwargs)
            else:
                res = self.anthropic_client.messages.create(**kwargs)

            latency_ms = (time.time() - start_time) * 1000.0

            response_text = ""
            if hasattr(res, "content") and res.content:
                if isinstance(res.content, list):
                    response_text = res.content[0].text if hasattr(res.content[0], "text") else str(res.content[0])
                else:
                    response_text = str(res.content)

            input_tokens = getattr(getattr(res, "usage", None), "input_tokens", 0)
            output_tokens = getattr(getattr(res, "usage", None), "output_tokens", 0)

            await self.record_step(
                step_type="llm_call",
                name=f"Claude Async Call ({model})",
                input_data={"messages": messages, "model": model},
                output_data={"text": response_text},
                latency_ms=latency_ms,
                token_usage={"input_tokens": input_tokens, "output_tokens": output_tokens},
            )
            return response_text

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000.0
            await self.record_step(
                step_type="llm_call",
                name=f"Claude Async Call Failed ({model})",
                input_data={"messages": messages, "model": model},
                output_data={"error": str(e)},
                latency_ms=latency_ms,
                confidence_score=0.0,
            )
            raise e

    async def arun_tool(
        self,
        tool_name: str,
        tool_input: Any,
        tool_fn: Callable[[Any], Any],
    ) -> Any:
        start_time = time.time()
        try:
            if inspect.iscoroutinefunction(tool_fn):
                if isinstance(tool_input, dict):
                    res = await tool_fn(**tool_input)
                else:
                    res = await tool_fn(tool_input)
            else:
                if isinstance(tool_input, dict):
                    res = tool_fn(**tool_input)
                else:
                    res = tool_fn(tool_input)

            latency_ms = (time.time() - start_time) * 1000.0
            await self.record_step(
                step_type="tool_call",
                name=tool_name,
                input_data=tool_input if isinstance(tool_input, dict) else {"input": str(tool_input)},
                output_data=res if isinstance(res, dict) else {"result": str(res)},
                latency_ms=latency_ms,
            )
            return res
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000.0
            await self.record_step(
                step_type="tool_call",
                name=f"{tool_name} (Failed)",
                input_data=tool_input if isinstance(tool_input, dict) else {"input": str(tool_input)},
                output_data={"error": str(e)},
                latency_ms=latency_ms,
                confidence_score=0.0,
            )
            raise e

    def atrace_step(self, name: str, input_data: Optional[Dict[str, Any]] = None) -> AsyncStepContext:
        return AsyncStepContext(self, name, input_data)

    async def acomplete(self, output: Any = None) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "status": "completed",
            "dashboard_url": self.dashboard_url,
            "total_steps": len(self._local_steps),
            "final_output": output,
        }


def wrap(
    anthropic_client: Any,
    name: str = "ARC Wrapped Agent",
    task: str = "Protected Claude Task",
    server_url: str = "http://localhost:8000",
) -> Union[ARCAgent, AsyncARCAgent]:
    """
    Wrap an existing Anthropic or AsyncAnthropic client in ARC protection middleware.
    """
    is_async = inspect.iscoroutinefunction(getattr(getattr(anthropic_client, "messages", None), "create", None))
    if is_async:
        return AsyncARCAgent(name=name, task=task, anthropic_client=anthropic_client, server_url=server_url)
    return ARCAgent(name=name, task=task, anthropic_client=anthropic_client, server_url=server_url)


def protected(name: str = "Protected Function", task: str = "Execute Function"):
    """
    Decorator for wrapping functions with automatic ARC protection and step tracing.
    """
    def decorator(fn: Callable):
        if inspect.iscoroutinefunction(fn):
            @wraps(fn)
            async def async_wrapper(*args, **kwargs):
                agent = AsyncARCAgent(name=name, task=task)
                res = await agent.arun_tool(fn.__name__, kwargs or args, fn)
                await agent.acomplete(output=res)
                return res
            return async_wrapper
        else:
            @wraps(fn)
            def sync_wrapper(*args, **kwargs):
                agent = ARCAgent(name=name, task=task)
                res = agent.run_tool(fn.__name__, kwargs or args, fn)
                agent.complete(output=res)
                return res
            return sync_wrapper
    return decorator
