"""End-to-end tests for the ARC interception transport (M0.2).

These drive the real transport against a fake Anthropic-shaped client
(see conftest.py) — the transport code under test is genuine, not mocked.
"""

from __future__ import annotations

import pytest

from arc import ARC
from arc.types import Event
from tests.conftest import FakeClient, FakeMessage, FakeTextBlock, FakeToolUseBlock


def test_create_returns_provider_response_unchanged() -> None:
    client = FakeClient()
    arc = ARC(client)
    resp = arc.messages.create(
        model="claude-opus-4-8",
        max_tokens=16000,
        messages=[{"role": "user", "content": "Hello"}],
    )
    # The exact SDK object flows back untouched.
    assert isinstance(resp, FakeMessage)
    assert resp.content[0].text.startswith("This is a confident")


def test_kwargs_forwarded_untouched_including_thinking_and_metadata() -> None:
    client = FakeClient()
    arc = ARC(client)
    arc.messages.create(
        model="claude-opus-4-8",
        max_tokens=16000,
        messages=[{"role": "user", "content": "Hi"}],
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
        tools=[{"name": "get_weather", "description": "x", "input_schema": {"type": "object"}}],
        metadata={"user_id": "u1"},
    )
    sent = client.messages.calls[-1]
    assert sent["thinking"] == {"type": "adaptive"}
    assert sent["output_config"] == {"effort": "high"}
    assert sent["metadata"] == {"user_id": "u1"}
    assert "arc_context_sources" not in sent  # ARC-only kwargs never reach the SDK


def test_arc_context_sources_not_forwarded() -> None:
    client = FakeClient()
    arc = ARC(client)
    arc.messages.create(
        model="claude-opus-4-8",
        max_tokens=100,
        messages=[{"role": "user", "content": "Hi"}],
        arc_context_sources=[{"key": "k", "claim": "a", "relevance": 0.1}],
    )
    assert "arc_context_sources" not in client.messages.calls[-1]


def test_call_is_recorded_and_traceable() -> None:
    arc = ARC(FakeClient())
    arc.messages.create(model="m", max_tokens=100, messages=[{"role": "user", "content": "Q"}])
    steps = arc.trace()
    assert len(steps) == 1
    assert steps[0].step_type.value == "llm_call"
    assert steps[0].token_usage == {"input_tokens": 12, "output_tokens": 34}
    assert steps[0].confidence_score > 0.2


def test_tool_use_blocks_recorded() -> None:
    client = FakeClient()
    client.messages.create = lambda **kw: FakeMessage(  # type: ignore[assignment]
        [FakeTextBlock("Calling a tool now to help."), FakeToolUseBlock("get_weather")]
    )
    arc = ARC(client)
    arc.messages.create(model="m", max_tokens=100, messages=[{"role": "user", "content": "weather?"}])
    step = arc.trace()[0]
    assert step.output_data["tools"] == ["get_weather"]


def test_middleware_runs_in_pipeline() -> None:
    arc = ARC(FakeClient())
    seen = []

    @arc.middleware
    def recording_mw(request, call_next):  # type: ignore[no-untyped-def]
        seen.append(request.payload["model"])
        return call_next(request)

    arc.messages.create(model="claude-opus-4-8", max_tokens=100, messages=[{"role": "user", "content": "x"}])
    assert seen == ["claude-opus-4-8"]


def test_events_dispatched() -> None:
    arc = ARC(FakeClient())
    events: list[Event] = []

    @arc.event("step_recorded")
    def on_step(evt: Event) -> None:
        events.append(evt)

    arc.messages.create(model="m", max_tokens=100, messages=[{"role": "user", "content": "x"}])
    assert len(events) == 1
    assert events[0].payload["confidence"] > 0.2
    assert "dashboard_url" in events[0].payload


def test_streaming_records_final_message() -> None:
    arc = ARC(FakeClient())
    with arc.messages.stream(model="m", max_tokens=100, messages=[{"role": "user", "content": "x"}]) as stream:
        chunks = list(stream.text_stream)
    assert chunks  # streamed text delivered to the caller
    step = arc.trace()[0]
    assert step.name.startswith("messages.stream")
    assert step.confidence_score > 0.2


def test_low_stream_mode_passthrough_iterator() -> None:
    arc = ARC(FakeClient())
    result = arc.messages.create(
        model="m", max_tokens=100, messages=[{"role": "user", "content": "x"}], stream=True
    )
    assert list(result)  # raw event iterator returned unchanged
    assert arc.trace()[0].output_data["streamed"] is True


def test_beta_namespace_intercepts_for_mcp() -> None:
    client = FakeClient()
    arc = ARC(client)
    arc.beta.messages.create(
        model="claude-opus-4-8",
        max_tokens=100,
        messages=[{"role": "user", "content": "x"}],
        mcp_servers=[{"type": "url", "name": "svc", "url": "https://mcp.example/sse"}],
        betas=["mcp-client-2025-11-20"],
    )
    sent = client.beta.messages.calls[-1]
    assert sent["mcp_servers"][0]["name"] == "svc"
    assert sent["betas"] == ["mcp-client-2025-11-20"]
    assert arc.trace()[0].input_data["has_mcp"] is True


def test_passthrough_of_non_intercepted_methods() -> None:
    arc = ARC(FakeClient())
    assert arc.messages.count_tokens(messages=[]).input_tokens == 99


def test_failure_is_recorded_and_reraised() -> None:
    client = FakeClient()

    def boom(**kwargs: object) -> object:
        raise RuntimeError("api down")

    client.messages.create = boom  # type: ignore[assignment]
    arc = ARC(client)
    with pytest.raises(RuntimeError, match="api down"):
        arc.messages.create(model="m", max_tokens=100, messages=[{"role": "user", "content": "x"}])
    step = arc.trace()[0]
    assert step.error == "api down"
    assert step.confidence_score == 0.0
    assert arc.recover().status == "recoverable"


def test_verify_enforces_rules() -> None:
    from arc import AssertionVerifier

    arc = ARC(FakeClient())  # complete reply -> integrity passes
    # A failing assertion drags confidence below 1.0 — derived from evidence.
    arc.verifier(AssertionVerifier({"mentions_spaceship": lambda text: "spaceship" in text}))
    arc.messages.create(model="m", max_tokens=100, messages=[{"role": "user", "content": "x"}])
    step = arc.trace()[0]
    assert 0.0 < step.confidence_score < 1.0  # from verification, not wording
    failing = arc.verify(rules=[{"min_confidence": 0.9}])
    assert not failing.is_valid
    assert any(c.conflict_type == "rule_confidence" for c in failing.conflicts)


def test_missing_client_raises_configuration_error() -> None:
    from arc import ConfigurationError

    arc = ARC()
    with pytest.raises(ConfigurationError):
        _ = arc.messages
