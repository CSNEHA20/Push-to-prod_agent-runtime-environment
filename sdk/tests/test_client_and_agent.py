import pytest
import asyncio
from unittest.mock import patch, MagicMock

import httpx
from arc import (
    ARC,
    AsyncARC,
    ARCAgent,
    AsyncARCAgent,
    wrap,
    protected,
    Session,
    TraceStep,
    VerificationResult,
    ReplayTimeline,
    RecoveryPlan,
    APIError,
    AuthenticationError,
    NotFoundError,
    ServerError,
    APIConnectionError,
)


def test_models_serialization():
    session = Session(session_id="sess-100", agent_name="ResearchAgent", task="Finance Report")
    data = session.to_dict()
    assert data["session_id"] == "sess-100"
    assert data["agent_name"] == "ResearchAgent"
    assert data["status"] == "active"

    step = TraceStep(step_id="step-1", session_id="sess-100", name="Claude Call")
    assert step.to_dict()["step_id"] == "step-1"

    ver = VerificationResult(is_valid=True)
    assert ver.to_dict()["is_valid"] is True


def test_sync_agent_tracing_and_tools():
    agent = ARCAgent(name="Finance Agent", task="Analyze Data", mock_mode=True)
    assert agent.session_id is not None

    # Step context manager
    with agent.trace_step("data_ingestion", input_data={"source": "SEC"}):
        x = 10 + 20

    assert len(agent._local_steps) >= 1
    last_step = agent._local_steps[-1]
    assert last_step.name == "data_ingestion"

    # Tool runner
    def calc_tax(income):
        return income * 0.2

    res = agent.run_tool("calc_tax", {"income": 100000}, calc_tax)
    assert res == 20000.0


@pytest.mark.asyncio
async def test_async_agent_tracing_and_tools():
    async_agent = AsyncARCAgent(name="Async Agent", task="Process Stream", mock_mode=True)
    assert async_agent.session_id is not None

    # Async step context manager
    async with async_agent.atrace_step("stream_fetch", input_data={"stream_id": 1}):
        await asyncio.sleep(0.01)

    assert len(async_agent._local_steps) >= 1

    # Async tool runner
    async def async_fetch(url):
        return {"content": "ok"}

    res = await async_agent.arun_tool("async_fetch", {"url": "http://example.com"}, async_fetch)
    assert res == {"content": "ok"}


def test_wrap_and_protected():
    class MockClient:
        class Messages:
            def create(self, **kwargs):
                return MagicMock(content=[MagicMock(text="Claude Answer")])
        messages = Messages()

    client = MockClient()
    wrapped_agent = wrap(client, name="Wrapped", task="Task")
    assert isinstance(wrapped_agent, ARCAgent)

    @protected(name="Protected Task", task="Calculate")
    def compute(val):
        return val * 10

    out = compute(5)
    assert out == 50


def test_client_error_mapping():
    client = ARC(server_url="http://localhost:8000")

    resp_401 = httpx.Response(401, json={"detail": "Unauthorized"})
    err_401 = client._request if hasattr(client, "_map_http_error") else None

    from arc.client import _map_http_error
    err = _map_http_error(resp_401)
    assert isinstance(err, AuthenticationError)

    resp_404 = httpx.Response(404, json={"detail": "Not found"})
    assert isinstance(_map_http_error(resp_404), NotFoundError)

    resp_500 = httpx.Response(500, json={"detail": "Internal server error"})
    assert isinstance(_map_http_error(resp_500), ServerError)
