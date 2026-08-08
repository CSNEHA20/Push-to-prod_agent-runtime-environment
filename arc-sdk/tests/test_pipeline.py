"""Tests for the Production Runtime Pipeline — the graph-driven execution.

Covers: the graph is derived from the plan (source of truth), the executor
publishes ordered graph events, runtime services coordinate only via those
events, and end-to-end model requests (sync/async/stream) run through the graph.
"""

from __future__ import annotations

import pytest

from arc import ARC, ExecutionGraph, NodeKind
from arc.runtime.graph import ExecutionContext, GraphEvent, GraphEventType, node_topic
from arc.runtime.graph.builder import build_execution_graph
from arc.runtime.graph.bus import InProcessGraphBus
from arc.runtime.graph.executor import EventDrivenGraphExecutor
from arc.types import Event
from tests.conftest import FakeClient

SHORT = [{"role": "user", "content": "Hi"}]
TOOLS = [{"name": f"t{i}", "description": "d", "input_schema": {"type": "object"}} for i in range(3)]


# -- graph is the source of truth (derived from the plan) ----------------


def test_graph_preview_matches_plan_trivial() -> None:
    graph = ARC(offline=True).graph(model="m", max_tokens=100, messages=SHORT)
    kinds = graph.kinds()
    # Verification always runs (confidence is evidence-derived); a trivial
    # request has recovery NONE, so there is a verify node but no recover node.
    assert NodeKind.FIREWALL in kinds
    assert NodeKind.DISPATCH in kinds
    assert NodeKind.RECORD in kinds
    assert NodeKind.REPLAY in kinds
    assert NodeKind.VERIFY in kinds
    assert NodeKind.RECOVER not in kinds


def test_graph_includes_verify_and_recover_for_tools() -> None:
    graph = ARC(offline=True, auto_recover=True).graph(
        model="m", max_tokens=16000, messages=SHORT, tools=TOOLS
    )
    assert NodeKind.VERIFY in graph.kinds()      # STRICT verification
    assert NodeKind.RECOVER in graph.kinds()     # RETRY_ONCE recovery


def test_streaming_graph_has_no_recover_node() -> None:
    graph = ARC(offline=True, auto_recover=True).graph(
        model="m", max_tokens=16000, messages=SHORT, tools=TOOLS, stream=True
    )
    # A stream can't be re-invoked mid-flight -> no recover node even with tools.
    assert NodeKind.RECOVER not in graph.kinds()


def test_graph_is_provider_independent() -> None:
    graph = ARC(offline=True).graph(model="m", max_tokens=100, messages=SHORT)
    # Node configs carry only abstract strategy values, never provider keys.
    blob = graph.model_dump_json()
    assert "messages" not in blob and "anthropic" not in blob.lower()


# -- executor publishes ordered graph events ----------------------------


def test_executor_publishes_events_in_graph_order() -> None:
    bus = InProcessGraphBus()
    topics: list[str] = []
    for topic in (
        GraphEventType.GRAPH_STARTED.value,
        node_topic(NodeKind.FIREWALL),
        node_topic(NodeKind.RECORD),
        node_topic(NodeKind.VERIFY),
        node_topic(NodeKind.REPLAY),
        GraphEventType.GRAPH_COMPLETED.value,
    ):
        bus.subscribe(topic, lambda e, t=topic: topics.append(t))

    arc = ARC(offline=True)
    plan = arc.plan(model="m", max_tokens=16000, messages=SHORT, tools=TOOLS[:1])
    graph = build_execution_graph(plan)
    from arc.types import RequestContext

    ctx = ExecutionContext(
        request=RequestContext(payload={"model": "m", "messages": SHORT}),
        plan=plan,
        graph=graph,
        session_id="s",
        input_summary={},
    )
    counter = {"n": 0}
    ex = EventDrivenGraphExecutor(bus, lambda sid: counter.__setitem__("n", counter["n"] + 1) or counter["n"])
    ex.execute(ctx, lambda payload: FakeClient().messages.create(**payload))

    assert topics[0] == GraphEventType.GRAPH_STARTED.value
    assert topics[-1] == GraphEventType.GRAPH_COMPLETED.value
    assert topics.index(node_topic(NodeKind.FIREWALL)) < topics.index(node_topic(NodeKind.RECORD))
    assert topics.index(node_topic(NodeKind.RECORD)) < topics.index(node_topic(NodeKind.VERIFY))


# -- services coordinate only via events ---------------------------------


def test_services_subscribe_rather_than_call_directly() -> None:
    # The verification engine is invoked only via the verify-node event, never
    # by a direct call from run_create — so graph shape governs whether it runs.
    arc = ARC(FakeClient())
    calls = {"verify": 0}
    original = arc._runtime.verification.verify

    def counting_verify(context):  # type: ignore[no-untyped-def]
        calls["verify"] += 1
        return original(context)

    arc._runtime.verification.verify = counting_verify  # type: ignore[assignment]

    # Observable request -> verify node present -> engine invoked via the event.
    arc.messages.create(model="m", max_tokens=100, messages=SHORT)
    assert calls["verify"] == 1

    # Low-level stream iterator -> not observable -> no verify node -> untouched.
    arc.messages.create(model="m", max_tokens=100, messages=SHORT, stream=True)
    assert calls["verify"] == 1  # unchanged: the graph omitted the verify node


def test_graph_built_event_emitted() -> None:
    arc = ARC(FakeClient())
    events: list[Event] = []

    @arc.event("graph_built")
    def on_graph(evt: Event) -> None:
        events.append(evt)

    arc.messages.create(model="m", max_tokens=100, messages=SHORT)
    assert len(events) == 1
    assert "firewall" in events[0].payload["nodes"]
    assert "dispatch" in events[0].payload["nodes"]


def test_step_records_graph_shape() -> None:
    arc = ARC(FakeClient())
    arc.messages.create(model="m", max_tokens=16000, messages=SHORT, tools=TOOLS[:1])
    step = arc.trace()[0]
    assert "verify" in step.input_data["graph"]
    assert step.input_data["plan"]["reasoning_strategy"]


# -- end-to-end through the graph ----------------------------------------


def test_end_to_end_records_via_graph() -> None:
    arc = ARC(FakeClient())
    resp = arc.messages.create(model="m", max_tokens=100, messages=SHORT)
    assert resp.content[0].text.startswith("This is a confident")
    assert len(arc.trace()) == 1


def test_retry_flows_through_graph() -> None:
    from arc import AssertionVerifier

    client = FakeClient(reply="ok.")
    arc = ARC(client, auto_recover=True)
    arc.verifier(AssertionVerifier({"has_answer": lambda text: "spaceship" in text}))
    arc.messages.create(model="m", max_tokens=16000, messages=SHORT, tools=TOOLS)
    assert len(client.messages.calls) == 2   # RETRY_ONCE fired through recover node
    assert len(arc.trace()) == 2


def test_failure_records_and_reraises_via_graph() -> None:
    client = FakeClient()

    def boom(**kwargs: object) -> object:
        raise RuntimeError("api down")

    client.messages.create = boom  # type: ignore[assignment]
    arc = ARC(client)
    with pytest.raises(RuntimeError, match="api down"):
        arc.messages.create(model="m", max_tokens=100, messages=SHORT)
    step = arc.trace()[0]
    assert step.error == "api down"
    assert arc.recover().status == "recoverable"


def test_streaming_runs_through_graph() -> None:
    arc = ARC(FakeClient())
    with arc.messages.stream(model="m", max_tokens=100, messages=SHORT) as stream:
        list(stream.text_stream)
    step = arc.trace()[0]
    assert step.name.startswith("messages.stream")
    assert "graph" in step.input_data


def test_async_runs_through_graph() -> None:
    import asyncio
    from types import SimpleNamespace

    from tests.conftest import FakeMessage, FakeTextBlock

    class AsyncMessages:
        async def create(self, **kwargs):  # type: ignore[no-untyped-def]
            return FakeMessage([FakeTextBlock("This is a confident async answer.")])

    client = SimpleNamespace(messages=AsyncMessages(), beta=SimpleNamespace(messages=AsyncMessages()))

    async def _run() -> None:
        arc = ARC(client)
        resp = await arc.async_messages.create(model="m", max_tokens=100, messages=SHORT)
        assert resp.content[0].text
        assert len(arc.trace()) == 1
        # async request planned + graph-built even without the middleware onion
        assert NodeKind.DISPATCH in arc.graph(model="m", max_tokens=100, messages=SHORT).kinds()

    asyncio.run(_run())
