"""Runtime services as graph-event subscribers.

The firewall, recorder, verifier, recovery and replay engines coordinate
**only** by reacting to graph events and reading/writing the shared
:class:`ExecutionContext` — never by calling one another. :func:`register`
wires each engine to the bus topics it cares about.

Event → reactions:

* ``graph.started``  → recovery checkpoints the attempt
* ``node.firewall``  → firewall filters context, emits ``request_started``
* ``node.record``    → recorder builds + records the step
* ``node.verify``    → verifier scores the step (per plan strategy)
* ``node.recover``   → recovery requests a retry or surfaces a plan
* ``node.replay``    → replay materialises the session timeline
* ``graph.completed``→ ``step_recorded`` is emitted for the final step
* ``graph.failed``   → recorder records the failure, recovery is triggered
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List

from ...types import (
    ConflictItem,
    Event,
    EventType,
    RecoveryPolicy,
    StepType,
    VerificationResult,
    VerificationStrategy,
)
from ..verification import VerificationContext, VerificationEngine, VerificationReport
from . import ExecutionContext, GraphBus, GraphEvent, GraphEventType, node_topic, NodeKind

EmitUser = Callable[[Event], None]
DEFAULT_STRICT_MIN_CONFIDENCE = 0.7
DEFAULT_CONFIDENCE_THRESHOLD = 0.2


class RuntimeServices:
    """Binds the runtime engines to the graph bus as event subscribers."""

    def __init__(
        self,
        *,
        recorder: Any,
        firewall: Any,
        engine: VerificationEngine,
        recovery: Any,
        replay: Any,
        emit_user: EmitUser,
        dashboard_url: Callable[[], str],
        extract_response: Callable[[Any], Any],
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
        strict_min_confidence: float = DEFAULT_STRICT_MIN_CONFIDENCE,
    ) -> None:
        self._recorder = recorder
        self._firewall = firewall
        self._engine = engine
        self._recovery = recovery
        self._replay = replay
        self._emit = emit_user
        self._dashboard_url = dashboard_url
        self._extract = extract_response
        self._confidence_threshold = confidence_threshold
        self._strict_min_confidence = strict_min_confidence

    def register(self, bus: GraphBus) -> None:
        """Subscribe every service to its graph topics (order is significant)."""
        bus.subscribe(GraphEventType.GRAPH_STARTED.value, self._on_started)
        bus.subscribe(node_topic(NodeKind.FIREWALL), self._on_firewall)
        bus.subscribe(node_topic(NodeKind.RECORD), self._on_record)
        bus.subscribe(node_topic(NodeKind.VERIFY), self._on_verify)
        bus.subscribe(node_topic(NodeKind.RECOVER), self._on_recover)
        bus.subscribe(node_topic(NodeKind.REPLAY), self._on_replay)
        bus.subscribe(GraphEventType.GRAPH_COMPLETED.value, self._on_completed)
        # graph.failed: recorder records the failure first, then recovery reacts.
        bus.subscribe(GraphEventType.GRAPH_FAILED.value, self._on_failed_record)
        bus.subscribe(GraphEventType.GRAPH_FAILED.value, self._on_failed_recover)

    # -- pre-dispatch -----------------------------------------------------

    def _on_started(self, event: GraphEvent) -> None:
        ctx = event.context
        self._recovery.checkpoint(ctx.session_id, ctx.step_number, {"step": ctx.step_number})

    def _on_firewall(self, event: GraphEvent) -> None:
        ctx = event.context
        _, conflicts = self._firewall.filter(ctx.request.context_sources)
        ctx.conflicts = conflicts
        payload = {"step_number": ctx.step_number, "conflicts": len(conflicts)}
        if ctx.streaming:
            payload["streaming"] = True
        if ctx.is_async:
            payload["async"] = True
        self._emit(Event(type="request_started", session_id=ctx.session_id, payload=payload))

    # -- post-dispatch ----------------------------------------------------

    def _on_record(self, event: GraphEvent) -> None:
        ctx = event.context
        if not ctx.observable:
            ctx.step = self._recorder.record(
                self._recorder.build_step(
                    ctx.session_id,
                    ctx.step_number,
                    name="messages.create (stream)",
                    input_data=ctx.input_summary,
                    output_data={"streamed": True},
                    latency_ms=ctx.latency_ms,
                )
            )
            return
        text, usage, tools, stop_reason, has_thinking = self._extract(ctx.observed)
        model = ctx.request.payload.get("model", "?")
        name = f"messages.stream ({model})" if ctx.streaming else f"messages.create ({model})"
        ctx.step = self._recorder.record(
            self._recorder.build_step(
                ctx.session_id,
                ctx.step_number,
                name=name,
                input_data={
                    **ctx.input_summary,
                    "plan": ctx.plan.to_dict(),
                    "graph": [k.value for k in ctx.graph.kinds()],
                },
                output_text=text,
                output_data={
                    "tools": tools,
                    "stop_reason": stop_reason,
                    "has_thinking": has_thinking,
                },
                token_usage=usage,
                latency_ms=ctx.latency_ms,
            )
        )

    def _on_verify(self, event: GraphEvent) -> None:
        ctx = event.context
        if ctx.step is None:
            return
        report = self._engine.verify(self._build_context(ctx))
        # Confidence is now evidence-derived — overwrite the neutral placeholder.
        ctx.step.confidence_score = report.confidence
        ctx.step.output_data["verification"] = self._evidence(report)
        ctx.verification = self._to_result(report, ctx.plan.verification_strategy)
        if not ctx.verification.is_valid:
            self._emit(
                Event(
                    type=EventType.VERIFICATION_FAILED.value,
                    session_id=ctx.session_id,
                    payload={
                        "step_number": ctx.step_number,
                        "confidence": report.confidence,
                        "explanation": report.explanation,
                        "failed_checks": [c.name for c in report.failed_checks()],
                    },
                )
            )

    def _on_recover(self, event: GraphEvent) -> None:
        ctx = event.context
        verification = ctx.verification
        if verification is None or verification.is_valid:
            return
        policy = ctx.plan.recovery_policy
        if policy is RecoveryPolicy.RETRY_ONCE and not ctx.retried:
            ctx.retry_requested = True
            self._emit_recovery(ctx)
        elif policy is RecoveryPolicy.CHECKPOINT:
            self._emit_recovery(ctx)

    def _on_replay(self, event: GraphEvent) -> None:
        ctx = event.context
        ctx.replay_timeline = self._replay.timeline(ctx.session_id)

    def _on_completed(self, event: GraphEvent) -> None:
        ctx = event.context
        if ctx.retry_requested or ctx.error is not None or ctx.step is None:
            return
        self._emit_recorded(ctx)

    # -- failure path -----------------------------------------------------

    def _on_failed_record(self, event: GraphEvent) -> None:
        ctx = event.context
        ctx.step = self._recorder.record(
            self._recorder.build_step(
                ctx.session_id,
                ctx.step_number,
                step_type=StepType.LLM_CALL,
                name="provider call (failed)",
                input_data=ctx.input_summary,
                error=ctx.error,
                latency_ms=ctx.latency_ms,
            )
        )
        self._emit(
            Event(
                type=EventType.VERIFICATION_FAILED.value,
                session_id=ctx.session_id,
                payload={"step_number": ctx.step_number, "error": ctx.error},
            )
        )

    def _on_failed_recover(self, event: GraphEvent) -> None:
        self._emit_recovery(event.context)

    # -- verification helpers --------------------------------------------

    def _build_context(self, ctx: ExecutionContext) -> VerificationContext:
        """Assemble the provider-independent verification context for the engine."""
        text, usage, _tools, stop_reason, _has_thinking = self._extract(ctx.observed)
        return VerificationContext(
            output_text=text,
            tool_calls=self._extract_tool_calls(ctx.observed),
            stop_reason=stop_reason,
            token_usage=usage,
            raw_output=ctx.observed,
            request_payload=ctx.request.payload,
            plan=ctx.plan,
            metadata={"session_id": ctx.session_id, "step_number": ctx.step_number},
        )

    @staticmethod
    def _extract_tool_calls(observed: Any) -> List[Dict[str, Any]]:
        """Duck-type tool_use blocks into ``[{"name", "input"}]`` (provider-aware)."""
        content = getattr(observed, "content", None)
        if content is None and isinstance(observed, dict):
            content = observed.get("content")
        calls: List[Dict[str, Any]] = []
        if isinstance(content, list):
            for block in content:
                btype = getattr(block, "type", None)
                if btype is None and isinstance(block, dict):
                    btype = block.get("type")
                if btype == "tool_use":
                    if isinstance(block, dict):
                        calls.append({"name": block.get("name"), "input": block.get("input")})
                    else:
                        calls.append(
                            {"name": getattr(block, "name", None), "input": getattr(block, "input", None)}
                        )
        return calls

    def _to_result(
        self, report: VerificationReport, strategy: VerificationStrategy
    ) -> VerificationResult:
        """Fold the report into a VerificationResult, applying the strategy threshold."""
        if strategy is VerificationStrategy.SKIP:
            is_valid = True
        else:
            threshold = (
                self._strict_min_confidence
                if strategy is VerificationStrategy.STRICT
                else self._confidence_threshold
            )
            is_valid = report.passed and report.confidence >= threshold
        conflicts = [
            ConflictItem(
                source_id=c.name,
                conflict_type=c.verifier,
                description=c.explanation,
                confidence_score=c.score,
            )
            for c in report.failed_checks()
        ]
        return VerificationResult(
            is_valid=is_valid,
            conflicts=conflicts,
            firewall_status="pass" if is_valid else "block",
            metadata={
                "confidence": report.confidence,
                "verified": report.verified,
                "explanation": report.explanation,
                "strategy": strategy.value,
            },
        )

    @staticmethod
    def _evidence(report: VerificationReport) -> Dict[str, Any]:
        return {
            "confidence": report.confidence,
            "passed": report.passed,
            "verified": report.verified,
            "explanation": report.explanation,
            "checks": [c.to_dict() for c in report.checks],
        }

    def _emit_recovery(self, ctx: ExecutionContext) -> None:
        plan = self._recovery.plan(ctx.session_id, failed_at_step=ctx.step_number)
        self._emit(
            Event(
                type=EventType.RECOVERY_TRIGGERED.value,
                session_id=ctx.session_id,
                payload={"status": plan.status},
            )
        )

    def _emit_recorded(self, ctx: ExecutionContext) -> None:
        self._emit(
            Event(
                type=EventType.STEP_RECORDED.value,
                session_id=ctx.session_id,
                payload={
                    "step_number": ctx.step.step_number,
                    "confidence": ctx.step.confidence_score,
                    "dashboard_url": self._dashboard_url(),
                },
            )
        )


def register(bus: GraphBus, services: RuntimeServices) -> None:
    """Wire ``services`` to ``bus`` (convenience wrapper)."""
    services.register(bus)


__all__ = ["RuntimeServices", "register", "DEFAULT_STRICT_MIN_CONFIDENCE"]
