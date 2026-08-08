import uuid
import time
import logging
import inspect
from typing import Optional, List, Dict, Any, Union, Callable

from sqlalchemy.ext.asyncio import AsyncSession

try:
    from core.flight_recorder import FlightRecorder
    from core.context_firewall import ContextFirewall
    from core.recovery_engine import RecoveryEngine
    from api.websocket import publish_event
    from models.session import AgentSession
except ImportError:
    from arc.backend.core.flight_recorder import FlightRecorder
    from arc.backend.core.context_firewall import ContextFirewall
    from arc.backend.core.recovery_engine import RecoveryEngine
    from arc.backend.api.websocket import publish_event
    from arc.backend.models.session import AgentSession

logger = logging.getLogger("arc.runtime")


class ARCRuntime:
    """
    ARC Runtime Core — Wires together Engine 1 (FlightRecorder),
    Engine 2 (ContextFirewall), and Engine 3 (RecoveryEngine).
    Provides resilient execution for Claude AI agents with context filtering,
    full trace recording, checkpointing, and automatic recovery.
    """

    def __init__(
        self,
        anthropic_client: Any,
        agent_name: str,
        task: str,
        db_session: Optional[AsyncSession] = None,
        session_id: Optional[Union[uuid.UUID, str]] = None,
    ):
        """
        Initializes ARCRuntime with required dependencies and engines.
        """
        self.anthropic_client = anthropic_client
        self.agent_name = agent_name
        self.task = task
        self.db_session = db_session
        self.step_counter = 0

        self._session_id: uuid.UUID = (
            uuid.UUID(str(session_id)) if session_id else uuid.uuid4()
        )
        self._session_started: bool = False

        self.flight_recorder = FlightRecorder(db_session=db_session)
        self.context_firewall = ContextFirewall(
            client=anthropic_client, db_session=db_session
        )
        self.recovery_engine = RecoveryEngine(db_session=db_session)

    @property
    def db_session(self) -> Optional[AsyncSession]:
        return self._db_session

    @db_session.setter
    def db_session(self, session: Optional[AsyncSession]) -> None:
        self._db_session = session
        if hasattr(self, "flight_recorder"):
            self.flight_recorder._db_session = session
        if hasattr(self, "context_firewall"):
            self.context_firewall._db_session = session
        if hasattr(self, "recovery_engine"):
            self.recovery_engine._db_session = session

    async def _ensure_session(self) -> None:
        """
        Ensures the agent session is created and tracked in the database.
        """
        if not self._session_started:
            try:
                agent_session = await self.flight_recorder.start_session(
                    agent_name=self.agent_name,
                    task=self.task,
                    session_id=self._session_id,
                    session=self.db_session,
                )
                if agent_session and hasattr(agent_session, "session_id"):
                    self._session_id = agent_session.session_id
                self._session_started = True
            except Exception as e:
                logger.error(f"Failed to start session in ARCRuntime: {e}", exc_info=True)
                # Still mark as started so we don't repeatedly fail on start_session if DB issue
                self._session_started = True

    @property
    def session_id(self) -> uuid.UUID:
        """Returns the current session ID."""
        return self._session_id

    @property
    def dashboard_url(self) -> str:
        """Returns the dashboard URL for monitoring the current session trace."""
        return f"http://localhost:3000/sessions/{self.session_id}"

    async def call_claude(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        context_sources: Optional[List[Dict[str, Any]]] = None,
        _is_retry: bool = False,
    ) -> str:
        """
        Main execution pipeline for calling Claude API:
        1. Increments step_counter
        2. ContextFirewall filtering & conflict detection (if context_sources provided)
        3. Calls Anthropic claude-sonnet-4-6 API
        4. Records LLM call in FlightRecorder
        5. Publishes step_completed websocket event
        6. Checks for low confidence failure (< 0.2)
        7. Saves Checkpoint in RecoveryEngine
        8. Triggers recovery & single retry if failure detected
        9. Returns response text
        """
        await self._ensure_session()
        self.step_counter += 1

        call_messages = list(messages) if isinstance(messages, list) else [messages]
        filtered_context: Optional[str] = None

        # 2. Context Firewall filtering
        if context_sources:
            try:
                firewall_res = await self.context_firewall.filter(
                    session_id=self.session_id,
                    step_number=self.step_counter,
                    sources=context_sources,
                    task=self.task,
                    db_session=self.db_session,
                )
                conflicts_found = len(firewall_res.get("conflicts", []))
                filtered_context = firewall_res.get("final_context", "")

                # Publish context_filtered event
                await publish_event(
                    session_id=self.session_id,
                    event_type="context_filtered",
                    data={
                        "type": "context_filtered",
                        "conflicts_found": conflicts_found,
                    },
                )

                # Inject filtered context as system message
                if filtered_context:
                    has_system = False
                    for idx, msg in enumerate(call_messages):
                        if isinstance(msg, dict) and msg.get("role") == "system":
                            call_messages[idx] = {
                                "role": "system",
                                "content": f"{filtered_context}\n\n{msg.get('content', '')}",
                            }
                            has_system = True
                            break
                    if not has_system:
                        call_messages.insert(
                            0, {"role": "system", "content": filtered_context}
                        )
            except Exception as e:
                logger.error(f"Error during context filtering: {e}", exc_info=True)

        # 3. Call Anthropic claude-sonnet-4-6 API
        kwargs: Dict[str, Any] = {
            "model": "claude-sonnet-4-6",
            "max_tokens": 1024,
            "messages": call_messages,
        }
        if tools:
            kwargs["tools"] = tools
        if filtered_context:
            kwargs["system"] = filtered_context

        start_time = time.time()
        try:
            if self.anthropic_client is None:
                raise ValueError("Anthropic client is not initialized.")

            res = self.anthropic_client.messages.create(**kwargs)
            if inspect.isawaitable(res):
                res = await res
        except Exception as e:
            logger.error(f"Error calling Claude API: {e}", exc_info=True)
            raise e

        duration_ms = int((time.time() - start_time) * 1000)

        # Parse response text and token counts
        response_text = ""
        if hasattr(res, "content") and res.content:
            if isinstance(res.content, list):
                text_parts = []
                for block in res.content:
                    if hasattr(block, "text"):
                        text_parts.append(block.text)
                    elif isinstance(block, dict) and "text" in block:
                        text_parts.append(block["text"])
                    else:
                        text_parts.append(str(block))
                response_text = "".join(text_parts).strip()
            else:
                response_text = str(res.content).strip()
        elif isinstance(res, str):
            response_text = res.strip()
        elif isinstance(res, dict) and "content" in res:
            response_text = str(res["content"]).strip()
        else:
            response_text = str(res).strip()

        input_tokens = 0
        output_tokens = 0
        if hasattr(res, "usage") and res.usage:
            input_tokens = getattr(res.usage, "input_tokens", 0)
            output_tokens = getattr(res.usage, "output_tokens", 0)
        elif isinstance(res, dict) and "usage" in res:
            usage = res.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)

        # 4. Record in FlightRecorder
        trace_step = await self.flight_recorder.record_llm_call(
            session_id=self.session_id,
            step_number=self.step_counter,
            messages=call_messages,
            response_text=response_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_ms=duration_ms,
        )

        confidence = trace_step.confidence_score
        summary = trace_step.reasoning_summary

        # 5. Publish websocket event
        await publish_event(
            session_id=self.session_id,
            event_type="step_completed",
            data={
                "type": "step_completed",
                "step_number": self.step_counter,
                "confidence": confidence,
                "summary": summary,
            },
        )

        # 6. Check for failure (confidence < 0.2)
        is_failure = confidence < 0.2

        # 7. Checkpoint state
        agent_state = {
            "step_counter": self.step_counter,
            "agent_name": self.agent_name,
            "task": self.task,
        }
        await self.recovery_engine.checkpoint(
            session_id=self.session_id,
            step_number=self.step_counter,
            agent_state=agent_state,
            messages_history=messages,
            context_snapshot=filtered_context,
        )

        # 8. If failure detected, recover & retry once
        if is_failure and not _is_retry:
            logger.warning(
                f"Low confidence ({confidence} < 0.2) detected at step {self.step_counter}. Initiating recovery."
            )
            recovery_res = await self.recovery_engine.recover(
                session_id=self.session_id,
                failed_at_step=self.step_counter,
                failure_type="low_confidence",
                error_message=f"Confidence score ({confidence}) is below threshold 0.2",
            )
            if recovery_res:
                restored_messages = recovery_res.get("messages_history") or messages
                logger.info(f"Retrying call_claude step once following recovery.")
                return await self.call_claude(
                    messages=restored_messages,
                    tools=tools,
                    context_sources=context_sources,
                    _is_retry=True,
                )

        # 9. Return response text
        return response_text

    async def run_tool(
        self,
        tool_name: str,
        tool_input: Any,
        tool_fn: Callable[[Any], Any],
    ) -> Any:
        """
        Executes tool_fn, records execution in FlightRecorder, checkpoints state, and returns result.
        """
        await self._ensure_session()
        self.step_counter += 1

        start_time = time.time()
        success = True
        tool_output = None

        try:
            if inspect.iscoroutinefunction(tool_fn):
                tool_output = await tool_fn(tool_input)
            else:
                res = tool_fn(tool_input)
                if inspect.isawaitable(res):
                    tool_output = await res
                else:
                    tool_output = res
        except Exception as e:
            success = False
            tool_output = str(e)
            logger.error(f"Tool execution error for tool '{tool_name}': {e}", exc_info=True)

        duration_ms = int((time.time() - start_time) * 1000)

        # Record in FlightRecorder
        await self.flight_recorder.record_tool_call(
            session_id=self.session_id,
            step_number=self.step_counter,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            success=success,
            duration_ms=duration_ms,
        )

        # Checkpoint state
        agent_state = {
            "step_counter": self.step_counter,
            "agent_name": self.agent_name,
            "task": self.task,
            "last_tool": tool_name,
        }
        await self.recovery_engine.checkpoint(
            session_id=self.session_id,
            step_number=self.step_counter,
            agent_state=agent_state,
            messages_history=[{"role": "tool", "name": tool_name, "content": str(tool_output)}],
            tool_results={tool_name: tool_output},
        )

        return tool_output

    async def complete(self, final_output: Any) -> Optional[AgentSession]:
        """
        Completes session in FlightRecorder and publishes session_complete event.
        """
        await self._ensure_session()
        agent_session = await self.flight_recorder.end_session(
            session_id=self.session_id,
            status="completed",
        )

        await publish_event(
            session_id=self.session_id,
            event_type="session_complete",
            data={
                "type": "session_complete",
                "session_id": str(self.session_id),
                "final_output": str(final_output) if final_output is not None else "",
            },
        )

        return agent_session
