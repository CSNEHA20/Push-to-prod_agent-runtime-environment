"""
ARC SDK — ARCAgent wrapper module for Claude agents.
"""

import os
import sys
import uuid
import asyncio
import logging
import inspect
from typing import Optional, List, Dict, Any, Union, Callable

try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass

from .client import ARCClient

logger = logging.getLogger("arc_sdk.agent")


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
    """Fallback mock Anthropic client when API key is missing or offline mode is active."""

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
                f"ARC Managed Claude Response: Successfully processed query '{last_msg[:80]}...'"
                if last_msg
                else "ARC Managed Claude Response"
            )
            return MockAnthropicResponse(resp_text)

    def __init__(self):
        self.messages = self.Messages(self)


def get_default_anthropic_client(api_key: Optional[str] = None) -> Any:
    """Helper to initialize Anthropic client or fallback mock client."""
    key = api_key or os.getenv("ANTHROPIC_API_KEY")
    invalid_keys = ("mock-key", "...", "your-api-key", "sk-ant-...")
    if key and key not in invalid_keys and not key.startswith("sk-ant-..."):
        try:
            import anthropic
            return anthropic.Anthropic(api_key=key)
        except Exception as e:
            logger.warning(f"Failed to initialize Anthropic client: {e}. Falling back to Mock client.")
    return MockAnthropicClient()


# Import backend ARCRuntime if available locally
try:
    from arc.backend.core.arc_runtime import ARCRuntime
except ImportError:
    try:
        from core.arc_runtime import ARCRuntime
    except ImportError:
        try:
            from backend.core.arc_runtime import ARCRuntime
        except ImportError:
            ARCRuntime = None


class ARCAgent:
    """
    ARCAgent wraps any callable agent or execution workflow, providing
    Flight Recorder step tracing, Context Firewall filtering, and Recovery Engine auto-rollback.
    """

    def __init__(
        self,
        name: str,
        task: str,
        arc_client: Optional[ARCClient] = None,
        anthropic_client: Optional[Any] = None,
        server_url: str = "http://localhost:8000",
        dashboard_url: str = "http://localhost:3000",
        session_id: Optional[Union[str, uuid.UUID]] = None,
    ):
        """
        Initialize ARCAgent session wrapper.

        :param name: Human readable name of the agent
        :param task: Description of the agent's task/goal
        :param arc_client: Optional custom ARCClient instance
        :param anthropic_client: Optional custom Anthropic API client
        :param server_url: Base URL of ARC backend server
        :param dashboard_url: Base URL of ARC dashboard frontend
        :param session_id: Optional existing session UUID
        """
        self.name = name
        self.task = task
        self.server_url = server_url.rstrip("/")
        self.dashboard_base_url = dashboard_url.rstrip("/")

        # Check global config fallback
        from . import _global_config
        global_api_key = _global_config.get("api_key")
        global_anthropic_key = _global_config.get("anthropic_api_key")
        if _global_config.get("server_url"):
            self.server_url = _global_config["server_url"].rstrip("/")
        if _global_config.get("dashboard_url"):
            self.dashboard_base_url = _global_config["dashboard_url"].rstrip("/")

        self.arc_client = arc_client or ARCClient(api_key=global_api_key, server_url=self.server_url)
        self.anthropic_client = anthropic_client or get_default_anthropic_client(global_anthropic_key)

        self._session_id = str(session_id) if session_id else str(uuid.uuid4())

        # Initialize local runtime if backend core package is available
        if ARCRuntime is not None:
            self._runtime = ARCRuntime(
                anthropic_client=self.anthropic_client,
                agent_name=self.name,
                task=self.task,
                session_id=self._session_id,
            )
        else:
            self._runtime = None

    @property
    def session_id(self) -> str:
        """Return unique session ID string."""
        return self._session_id

    @property
    def dashboard_url(self) -> str:
        """Return live dashboard URL monitoring this agent session."""
        return f"{self.dashboard_base_url}/sessions/{self.session_id}"

    def _execute(self, coro):
        """Execute async coroutine synchronously or in active loop context."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is not None and loop.is_running():
            try:
                import nest_asyncio
                nest_asyncio.apply(loop)
                return loop.run_until_complete(coro)
            except Exception:
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, coro)
                    return future.result()
        else:
            return asyncio.run(coro)

    def call_claude(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        context_sources: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Calls Claude API via ARC Runtime (with Context Firewall filtering & Flight Recorder tracing).

        :param messages: List of message objects [{"role": "user", "content": "..."}]
        :param tools: Optional list of tool definitions
        :param context_sources: Optional list of context sources for Context Firewall conflict checking
        :return: Response text string from Claude
        """
        if self._runtime:
            try:
                coro = self._runtime.call_claude(
                    messages=messages,
                    tools=tools,
                    context_sources=context_sources,
                )
                return self._execute(coro)
            except Exception as e:
                if "invalid x-api-key" in str(e).lower() or "401" in str(e) or "AuthenticationError" in type(e).__name__:
                    logger.warning(f"Anthropic API key invalid/unauthorized: {e}. Falling back to Mock client.")
                    self.anthropic_client = MockAnthropicClient()
                    self._runtime.anthropic_client = self.anthropic_client
                    self._runtime.context_firewall.client = self.anthropic_client
                    coro = self._runtime.call_claude(
                        messages=messages,
                        tools=tools,
                        context_sources=context_sources,
                    )
                    return self._execute(coro)
                raise e

        # Direct Anthropic client fallback if local runtime core module is absent
        kwargs = {"model": "claude-sonnet-4-6", "max_tokens": 1024, "messages": messages}
        if tools:
            kwargs["tools"] = tools

        try:
            res = self.anthropic_client.messages.create(**kwargs)
        except Exception as e:
            if "invalid x-api-key" in str(e).lower() or "401" in str(e) or "AuthenticationError" in type(e).__name__:
                logger.warning(f"Anthropic API key invalid/unauthorized: {e}. Falling back to Mock client.")
                self.anthropic_client = MockAnthropicClient()
                res = self.anthropic_client.messages.create(**kwargs)
            else:
                raise e

        if hasattr(res, "content") and res.content:
            if isinstance(res.content, list):
                return res.content[0].text if hasattr(res.content[0], "text") else str(res.content[0])
            return str(res.content)
        return str(res)

    def run_tool(
        self,
        tool_name: str,
        tool_input: Any,
        tool_fn: Callable[[Any], Any],
    ) -> Any:
        """
        Runs an agent tool via ARC Runtime with automatic step tracing and state checkpointing.

        :param tool_name: Name of the tool being executed
        :param tool_input: Arguments/inputs passed to the tool
        :param tool_fn: Function or callable executing the tool
        :return: Tool execution result
        """
        if self._runtime:
            coro = self._runtime.run_tool(
                tool_name=tool_name,
                tool_input=tool_input,
                tool_fn=tool_fn,
            )
            return self._execute(coro)

        # Fallback sync tool runner
        if inspect.iscoroutinefunction(tool_fn):
            return self._execute(tool_fn(tool_input))
        res = tool_fn(tool_input)
        if inspect.isawaitable(res):
            return self._execute(res)
        return res

    def complete(self, output: Any = None) -> Any:
        """
        Marks the session as completed in ARC Flight Recorder.

        :param output: Final output or result summary of the agent run
        :return: Session details or completed status dict
        """
        if self._runtime:
            coro = self._runtime.complete(final_output=output)
            return self._execute(coro)

        return {
            "session_id": self.session_id,
            "status": "completed",
            "dashboard_url": self.dashboard_url,
            "final_output": output,
        }
