"""ARC Runtime — the interception orchestrator.

Every intercepted provider call flows through :meth:`ARCRuntime.run_create`
(or :meth:`ARCRuntime.open_stream`), which threads the request through the
full pipeline before and after the real provider call::

    Middleware -> Context Firewall -> Event Bus -> Flight Recorder
      -> Verification -> Recovery -> [provider SDK] -> Replay Store -> Dashboard

The provider's response object is returned to the caller **unchanged** — the
runtime only observes it (text, token usage, tool/stop metadata) for recording.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Callable, Dict, List, Optional, Tuple

from .config import ARCConfig
from .runtime.events.default import DefaultEventBus
from .runtime.firewall.default import ContextFirewall
from .runtime.middleware.default import MiddlewarePipeline
from .runtime.planner import Planner
from .runtime.planner.default import AdaptivePlanner, make_planner_middleware
from .runtime.recorder.default import FlightRecorder
from .runtime.recovery.default import RecoveryEngine
from .runtime.replay import DefaultReplayStore
from .runtime.verifier.default import ConfidenceVerifier
from .types import (
    Event,
    EventHandler,
    EventType,
    ExecutionPlan,
    Middleware,
    RecoveryPolicy,
    RequestContext,
    ResponseContext,
    StepType,
    TraceStep,
    VerificationResult,
    VerificationStrategy,
)

_STRICT_MIN_CONFIDENCE = 0.7

Invoke = Callable[[Dict[str, Any]], Any]


def extract_response(raw: Any) -> Tuple[str, Dict[str, int], List[str], Optional[str]]:
    """Observe a provider response: ``(text, token_usage, tool_names, stop_reason)``.

    Handles the Anthropic ``Message`` shape (a list of typed content blocks),
    plain dicts, and strings, without mutating ``raw``.
    """
    text_parts: List[str] = []
    tool_names: List[str] = []
    content = getattr(raw, "content", None)
    if content is None and isinstance(raw, dict):
        content = raw.get("content")

    if isinstance(content, list):
        for block in content:
            btype = getattr(block, "type", None)
            if btype is None and isinstance(block, dict):
                btype = block.get("type")
            if btype == "text" or (btype is None and hasattr(block, "text")):
                text_parts.append(getattr(block, "text", "") or "")
            elif btype == "text" and isinstance(block, dict):
                text_parts.append(block.get("text", ""))
            elif btype == "tool_use":
                tool_names.append(getattr(block, "name", None) or "tool")
    elif isinstance(content, str):
        text_parts.append(content)
    elif isinstance(raw, str):
        text_parts.append(raw)

    usage_obj = getattr(raw, "usage", None) or (raw.get("usage") if isinstance(raw, dict) else None)
    usage: Dict[str, int] = {}
    if usage_obj is not None:
        usage = {
            "input_tokens": int(getattr(usage_obj, "input_tokens", 0)
                                if not isinstance(usage_obj, dict)
                                else usage_obj.get("input_tokens", 0) or 0),
            "output_tokens": int(getattr(usage_obj, "output_tokens", 0)
                                 if not isinstance(usage_obj, dict)
                                 else usage_obj.get("output_tokens", 0) or 0),
        }

    stop_reason = getattr(raw, "stop_reason", None)
    if stop_reason is None and isinstance(raw, dict):
        stop_reason = raw.get("stop_reason")
    return "".join(text_parts).strip(), usage, tool_names, stop_reason


class ARCRuntime:
    """Composes the runtime engines and drives the interception pipeline."""

    def __init__(
        self,
        config: ARCConfig,
        *,
        get_middleware: Callable[[], List[Middleware]],
        get_handlers: Callable[[str], List[EventHandler]],
        planner: Optional[Planner] = None,
    ) -> None:
        self.config = config
        self.session_id = str(uuid.uuid4())
        self.recorder = FlightRecorder()
        self.firewall = ContextFirewall()
        self.recovery = RecoveryEngine()
        self.verifier = ConfidenceVerifier(config.confidence_threshold)
        self.events = DefaultEventBus(get_handlers)
        self.planner: Planner = planner or AdaptivePlanner(config)
        self._stream_plans: Dict[int, ExecutionPlan] = {}
        # The Adaptive Planner is the first (outermost) middleware; user
        # middleware runs inside it, so everything follows the plan.
        planner_mw = make_planner_middleware(lambda: self.planner, self.events.emit)
        self.pipeline = MiddlewarePipeline(lambda: [planner_mw, *get_middleware()])
        self.replay = DefaultReplayStore(self.recorder, self.recovery, config.confidence_threshold)

    @property
    def dashboard_url(self) -> str:
        """Live dashboard URL for the current session."""
        return f"{self.config.dashboard_url}/sessions/{self.session_id}"

    # -- non-streaming create --------------------------------------------

    def run_create(
        self,
        payload: Dict[str, Any],
        invoke: Invoke,
        context_sources: Optional[List[Dict[str, Any]]] = None,
    ) -> Any:
        """Run one ``messages.create`` through the full pipeline; return the raw response."""
        request = RequestContext(
            session_id=self.session_id,
            provider=self.config.provider,
            payload=payload,
            context_sources=list(context_sources or []),
        )
        streaming = payload.get("stream") is True
        response_ctx = self.pipeline.execute(
            request, lambda req: self._core(req, invoke, streaming)
        )
        return response_ctx.metadata["raw_response"]

    def _core(self, req: RequestContext, invoke: Invoke, streaming: bool) -> ResponseContext:
        step_number = self.recorder.next_step_number(req.session_id)
        _, conflicts = self.firewall.filter(req.context_sources)
        self.events.emit(
            Event(
                type="request_started",
                session_id=req.session_id,
                payload={"step_number": step_number, "conflicts": len(conflicts)},
            )
        )
        self.recovery.checkpoint(req.session_id, step_number, {"step": step_number})
        input_summary = self._input_summary(req.payload)

        start = time.perf_counter()
        try:
            raw = invoke(req.payload)
        except Exception as exc:  # noqa: BLE001 - record then re-raise unchanged
            latency = (time.perf_counter() - start) * 1000.0
            self._record_failure(req.session_id, step_number, input_summary, str(exc), latency)
            raise

        latency = (time.perf_counter() - start) * 1000.0
        if streaming:
            return self._record_streamed_iterator(req, step_number, input_summary, latency, raw)
        return self._record_message(req, step_number, input_summary, latency, raw, invoke)

    def _record_message(
        self,
        req: RequestContext,
        step_number: int,
        input_summary: Dict[str, Any],
        latency: float,
        raw: Any,
        invoke: Invoke,
    ) -> ResponseContext:
        text, usage, tools, stop_reason = extract_response(raw)
        plan: Optional[ExecutionPlan] = req.metadata.get("execution_plan")
        step = self.recorder.record(
            self.recorder.build_step(
                req.session_id,
                step_number,
                name=f"messages.create ({req.payload.get('model', '?')})",
                input_data={**input_summary, "plan": plan.to_dict() if plan else None},
                output_text=text,
                output_data={"tools": tools, "stop_reason": stop_reason},
                token_usage=usage,
                latency_ms=latency,
            )
        )
        result = self._verify_with_plan([step], plan)
        if not result.is_valid:
            self.events.emit(
                Event(
                    type=EventType.VERIFICATION_FAILED.value,
                    session_id=req.session_id,
                    payload={"step_number": step_number, "conflicts": len(result.conflicts)},
                )
            )
            if self._retry_allowed(plan, req):
                self._emit_recovery(req.session_id, step_number)
                retry = req.model_copy(update={"metadata": {**req.metadata, "_arc_retry": True}})
                return self._core(retry, invoke, streaming=False)
            if self._checkpoint_recovery(plan):
                self._emit_recovery(req.session_id, step_number)
        self._emit_recorded(req.session_id, step)
        return ResponseContext(
            session_id=req.session_id,
            output={"text": text},
            step=step,
            metadata={"raw_response": raw},
        )

    def _record_streamed_iterator(
        self,
        req: RequestContext,
        step_number: int,
        input_summary: Dict[str, Any],
        latency: float,
        raw: Any,
    ) -> ResponseContext:
        # Low-level stream=True: consuming the iterator would break the caller,
        # so record request metadata only and pass the iterator through.
        step = self.recorder.record(
            self.recorder.build_step(
                req.session_id,
                step_number,
                name="messages.create (stream)",
                input_data=input_summary,
                output_data={"streamed": True},
                latency_ms=latency,
            )
        )
        self._emit_recorded(req.session_id, step)
        return ResponseContext(
            session_id=req.session_id,
            output={"streamed": True},
            step=step,
            metadata={"raw_response": raw},
        )

    # -- streaming (context-manager) -------------------------------------

    def begin_stream(
        self, payload: Dict[str, Any], context_sources: Optional[List[Dict[str, Any]]]
    ) -> int:
        """Plan the stream and run its pre-dispatch stages; return its step number.

        Streams bypass the middleware onion, so the planner is invoked directly
        here to honour "plan before every request reaches the model".
        """
        step_number = self.recorder.next_step_number(self.session_id)
        request = RequestContext(
            session_id=self.session_id,
            provider=self.config.provider,
            payload=payload,
            context_sources=list(context_sources or []),
        )
        plan = self.planner.plan(request)
        self._stream_plans[step_number] = plan
        self.events.emit(
            Event(
                type=EventType.PLAN_CREATED.value,
                session_id=self.session_id,
                payload=plan.to_dict(),
            )
        )
        _, conflicts = self.firewall.filter(request.context_sources)
        self.events.emit(
            Event(
                type="request_started",
                session_id=self.session_id,
                payload={"step_number": step_number, "streaming": True, "conflicts": len(conflicts)},
            )
        )
        self.recovery.checkpoint(self.session_id, step_number, {"step": step_number})
        return step_number

    def finish_stream(
        self,
        step_number: int,
        payload: Dict[str, Any],
        latency_ms: float,
        final_message: Any,
        error: Optional[str],
    ) -> TraceStep:
        """Run the post-dispatch stages for a stream once it has completed."""
        plan = self._stream_plans.pop(step_number, None)
        input_summary = {**self._input_summary(payload), "plan": plan.to_dict() if plan else None}
        if error is not None:
            return self._record_failure(
                self.session_id, step_number, input_summary, error, latency_ms
            )
        text, usage, tools, stop_reason = extract_response(final_message)
        step = self.recorder.record(
            self.recorder.build_step(
                self.session_id,
                step_number,
                name=f"messages.stream ({payload.get('model', '?')})",
                input_data=input_summary,
                output_text=text,
                output_data={"tools": tools, "stop_reason": stop_reason},
                token_usage=usage,
                latency_ms=latency_ms,
            )
        )
        # Streams can't be re-invoked mid-flight, so recovery here is record-only.
        result = self._verify_with_plan([step], plan)
        if not result.is_valid:
            self.events.emit(
                Event(
                    type=EventType.VERIFICATION_FAILED.value,
                    session_id=self.session_id,
                    payload={"step_number": step_number, "conflicts": len(result.conflicts)},
                )
            )
        self._emit_recorded(self.session_id, step)
        return step

    # -- plan-following helpers ------------------------------------------

    def _verify_with_plan(
        self, trace: List[TraceStep], plan: Optional[ExecutionPlan]
    ) -> VerificationResult:
        strategy = plan.verification_strategy if plan else VerificationStrategy.STANDARD
        if strategy == VerificationStrategy.SKIP:
            return VerificationResult(
                is_valid=True, firewall_status="skipped", metadata={"skipped": True}
            )
        rules = (
            [{"min_confidence": _STRICT_MIN_CONFIDENCE}]
            if strategy == VerificationStrategy.STRICT
            else None
        )
        return self.verifier.verify(trace, rules)

    @staticmethod
    def _retry_allowed(plan: Optional[ExecutionPlan], req: RequestContext) -> bool:
        if req.metadata.get("_arc_retry"):
            return False
        if plan is not None:
            return plan.recovery_policy == RecoveryPolicy.RETRY_ONCE
        return False

    @staticmethod
    def _checkpoint_recovery(plan: Optional[ExecutionPlan]) -> bool:
        return plan is not None and plan.recovery_policy == RecoveryPolicy.CHECKPOINT

    # -- helpers ----------------------------------------------------------

    def _record_failure(
        self,
        session_id: str,
        step_number: int,
        input_summary: Dict[str, Any],
        error: str,
        latency: float,
    ) -> TraceStep:
        step = self.recorder.record(
            self.recorder.build_step(
                session_id,
                step_number,
                step_type=StepType.LLM_CALL,
                name="provider call (failed)",
                input_data=input_summary,
                error=error,
                latency_ms=latency,
            )
        )
        self.events.emit(
            Event(
                type=EventType.VERIFICATION_FAILED.value,
                session_id=session_id,
                payload={"step_number": step_number, "error": error},
            )
        )
        self._emit_recovery(session_id, step_number)
        return step

    def _emit_recovery(self, session_id: str, step_number: int) -> None:
        plan = self.recovery.plan(session_id, failed_at_step=step_number)
        self.events.emit(
            Event(
                type=EventType.RECOVERY_TRIGGERED.value,
                session_id=session_id,
                payload={"status": plan.status},
            )
        )

    def _emit_recorded(self, session_id: str, step: TraceStep) -> None:
        self.events.emit(
            Event(
                type=EventType.STEP_RECORDED.value,
                session_id=session_id,
                payload={
                    "step_number": step.step_number,
                    "confidence": step.confidence_score,
                    "dashboard_url": self.dashboard_url,
                },
            )
        )

    @staticmethod
    def _input_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
        # Capture request metadata without copying large/opaque message content.
        return {
            "model": payload.get("model"),
            "message_count": len(payload.get("messages") or []),
            "max_tokens": payload.get("max_tokens"),
            "streaming": bool(payload.get("stream")),
            "has_tools": bool(payload.get("tools")),
            "has_thinking": bool(payload.get("thinking")),
            "has_mcp": bool(payload.get("mcp_servers")),
            "request_metadata": payload.get("metadata") or {},
        }


    # -- agent wrapping ---------------------------------------------------

    def run_agent_call(
        self,
        invoke: "Invoke",
        args: tuple,
        kwargs: dict,
        *,
        session_id: Optional[str] = None,
        name: str = "agent.call",
        step_type: "StepType" = StepType.TOOL_CALL,
    ) -> Any:
        """Run one wrapped agent call through the full pipeline.

        The agent's return value is returned **unchanged**. ARC only observes
        the call: it checkpoints before, records after, verifies confidence,
        triggers recovery when needed, and emits lifecycle events.

        :param invoke: Zero-argument callable that performs the actual agent call.
        :param args: Positional args forwarded to the agent (for metadata only).
        :param kwargs: Keyword args forwarded to the agent (for metadata only).
        :param session_id: Override the runtime session (defaults to self.session_id).
        :param name: Human-readable step label recorded in the Flight Recorder.
        :param step_type: Step category (defaults to ``TOOL_CALL``).
        :returns: The raw return value of ``invoke()``.
        """
        sid = session_id or self.session_id
        step_number = self.recorder.next_step_number(sid)
        _, conflicts = self.firewall.filter([])
        self.events.emit(
            Event(
                type="request_started",
                session_id=sid,
                payload={"step_number": step_number, "agent_call": name, "conflicts": len(conflicts)},
            )
        )
        self.recovery.checkpoint(sid, step_number, {"step": step_number, "name": name})
        input_summary: Dict[str, Any] = {
            "callable": name,
            "arg_count": len(args),
            "kwarg_keys": sorted(kwargs.keys()),
        }
        start = time.perf_counter()
        try:
            raw = invoke()
            raw = _run_maybe_coroutine(raw)
        except Exception as exc:  # noqa: BLE001 - record then re-raise unchanged
            latency = (time.perf_counter() - start) * 1000.0
            self._record_failure(sid, step_number, input_summary, str(exc), latency)
            raise

        latency = (time.perf_counter() - start) * 1000.0
        output_text = str(raw) if raw is not None else None
        step = self.recorder.record(
            self.recorder.build_step(
                sid,
                step_number,
                step_type=step_type,
                name=name,
                input_data=input_summary,
                output_text=output_text,
                latency_ms=latency,
            )
        )
        self.verifier.verify([step])
        self._emit_recorded(sid, step)
        return raw


def _run_maybe_coroutine(value: Any) -> Any:
    """If *value* is a coroutine or awaitable, drive it to completion synchronously."""
    import asyncio
    import inspect as _inspect

    if not _inspect.isawaitable(value):
        return value
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop is not None and loop.is_running():
        # Best-effort: schedule on the running loop via concurrent.futures
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, value)
            return future.result()
    return asyncio.run(value)


__all__ = ["ARCRuntime", "extract_response", "_run_maybe_coroutine"]
