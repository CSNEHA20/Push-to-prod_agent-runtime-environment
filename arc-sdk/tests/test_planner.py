"""Tests for the Adaptive Planner (first middleware + execution plan)."""

from __future__ import annotations

from arc import (
    ARC,
    ExecutionPlan,
    Planner,
    ReasoningStrategy,
    RecoveryPolicy,
    RetrievalStrategy,
    ToolStrategy,
    VerificationStrategy,
)
from arc.runtime.planner.default import AdaptivePlanner
from arc.types import Event, RequestContext
from tests.conftest import FakeClient

SHORT = [{"role": "user", "content": "Hi"}]
BIG = [{"role": "user", "content": "x" * 12000}]
TOOLS = [{"name": f"t{i}", "description": "d", "input_schema": {"type": "object"}} for i in range(3)]


# -- planner heuristics (provider-independent) ---------------------------


def test_trivial_request_plans_direct_and_skips() -> None:
    plan = ARC(offline=True).plan(model="m", max_tokens=100, messages=SHORT)
    assert plan.reasoning_strategy is ReasoningStrategy.DIRECT
    assert plan.thinking_budget == 0
    assert plan.tool_strategy is ToolStrategy.NONE
    assert plan.verification_strategy is VerificationStrategy.SKIP
    assert plan.recovery_policy is RecoveryPolicy.NONE
    assert plan.retrieval_strategy is RetrievalStrategy.NONE


def test_tools_drive_extended_reasoning_and_strict_verification() -> None:
    plan = ARC(offline=True).plan(model="m", max_tokens=16000, messages=SHORT, tools=TOOLS)
    assert plan.reasoning_strategy is ReasoningStrategy.EXTENDED  # tool_count 3 -> score >= 6
    assert plan.tool_strategy is ToolStrategy.PARALLEL
    assert plan.verification_strategy is VerificationStrategy.STRICT
    assert plan.thinking_budget > 0


def test_large_input_raises_reasoning() -> None:
    plan = ARC(offline=True).plan(model="m", max_tokens=16000, messages=BIG)
    assert plan.reasoning_strategy is not ReasoningStrategy.DIRECT
    assert plan.context_budget > 512


def test_thinking_hint_forces_extended() -> None:
    plan = ARC(offline=True).plan(
        model="m", max_tokens=16000, messages=SHORT, thinking={"type": "adaptive"}
    )
    assert plan.reasoning_strategy is ReasoningStrategy.EXTENDED


def test_thinking_budget_capped_below_max_tokens() -> None:
    plan = ARC(offline=True).plan(
        model="m", max_tokens=100, messages=SHORT, thinking={"type": "adaptive"}
    )
    assert plan.thinking_budget <= 99


def test_retrieval_scales_with_context_sources() -> None:
    arc = ARC(offline=True)
    sources = [{"key": f"k{i}", "claim": "c"} for i in range(4)]
    plan = arc.plan(model="m", max_tokens=100, messages=SHORT, arc_context_sources=sources)
    assert plan.retrieval_strategy is RetrievalStrategy.AGGRESSIVE


def test_recovery_retry_only_when_auto_recover_enabled() -> None:
    off = ARC(offline=True).plan(model="m", max_tokens=16000, messages=SHORT, tools=TOOLS)
    assert off.recovery_policy is RecoveryPolicy.CHECKPOINT  # auto_recover default off
    on = ARC(offline=True, auto_recover=True).plan(
        model="m", max_tokens=16000, messages=SHORT, tools=TOOLS
    )
    assert on.recovery_policy is RecoveryPolicy.RETRY_ONCE


def test_planner_is_provider_independent() -> None:
    # A payload with no Anthropic-specific structure still plans fine.
    planner = AdaptivePlanner(ARC(offline=True).config)
    ctx = RequestContext(payload={"messages": SHORT, "tools": TOOLS[:1]})
    plan = planner.plan(ctx)
    assert isinstance(plan, ExecutionPlan)
    assert plan.tool_strategy is ToolStrategy.AUTO


# -- pipeline integration ------------------------------------------------


def test_planner_runs_before_user_middleware() -> None:
    arc = ARC(FakeClient())
    seen_plan = {}

    @arc.middleware
    def inspect_plan(request, call_next):  # type: ignore[no-untyped-def]
        seen_plan["plan"] = request.metadata.get("execution_plan")
        return call_next(request)

    arc.messages.create(model="m", max_tokens=100, messages=SHORT)
    assert isinstance(seen_plan["plan"], ExecutionPlan)


def test_plan_created_event_emitted() -> None:
    arc = ARC(FakeClient())
    events: list[Event] = []

    @arc.event("plan_created")
    def on_plan(evt: Event) -> None:
        events.append(evt)

    arc.messages.create(model="m", max_tokens=100, messages=SHORT, tools=TOOLS)
    assert len(events) == 1
    assert events[0].payload["reasoning_strategy"] == "extended"


def test_plan_recorded_on_step() -> None:
    arc = ARC(FakeClient())
    arc.messages.create(model="m", max_tokens=100, messages=SHORT)
    step = arc.trace()[0]
    assert step.input_data["plan"]["verification_strategy"] == "skip"


def test_plan_drives_retry_on_strict_low_confidence() -> None:
    client = FakeClient(reply="ok.")  # short reply -> confidence 0.6 < strict 0.7
    arc = ARC(client, auto_recover=True)
    arc.messages.create(model="m", max_tokens=16000, messages=SHORT, tools=TOOLS)
    # STRICT verification + RETRY_ONCE -> exactly one retry (two provider calls).
    assert len(client.messages.calls) == 2
    assert len(arc.trace()) == 2


def test_no_retry_when_recovery_checkpoint() -> None:
    client = FakeClient(reply="ok.")
    arc = ARC(client)  # auto_recover off -> CHECKPOINT, no re-call
    arc.messages.create(model="m", max_tokens=16000, messages=SHORT, tools=TOOLS)
    assert len(client.messages.calls) == 1


def test_streaming_is_planned() -> None:
    arc = ARC(FakeClient())
    events: list[Event] = []

    @arc.event("plan_created")
    def on_plan(evt: Event) -> None:
        events.append(evt)

    with arc.messages.stream(model="m", max_tokens=100, messages=SHORT) as stream:
        list(stream.text_stream)
    assert len(events) == 1
    assert arc.trace()[0].input_data["plan"] is not None


def test_custom_planner_is_used() -> None:
    class SkipEverythingPlanner:
        def plan(self, request: RequestContext) -> ExecutionPlan:
            return ExecutionPlan(verification_strategy=VerificationStrategy.SKIP)

    planner: Planner = SkipEverythingPlanner()
    client = FakeClient(reply="ok.")
    arc = ARC(client, auto_recover=True, planner=planner)
    arc.messages.create(model="m", max_tokens=100, messages=SHORT, tools=TOOLS)
    # Custom planner skips verification, so no retry despite low confidence + tools.
    assert len(client.messages.calls) == 1


def test_planner_property_is_swappable() -> None:
    arc = ARC(offline=True)
    assert isinstance(arc.planner, AdaptivePlanner)

    class P:
        def plan(self, request: RequestContext) -> ExecutionPlan:
            return ExecutionPlan()

    arc.planner = P()
    assert arc.plan(model="m", max_tokens=1, messages=SHORT).reasoning_strategy is (
        ReasoningStrategy.DIRECT
    )
