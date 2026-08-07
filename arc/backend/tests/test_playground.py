"""
Tests for Playground API route, ChaosInjector, and Demo Agent execution.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

try:
    from main import app
    from demo.chaos_injector import ChaosInjector
    from demo.demo_agent import run_demo_agent, search_funding_information
except ImportError:
    from arc.backend.main import app
    from arc.demo.chaos_injector import ChaosInjector
    from arc.demo.demo_agent import run_demo_agent, search_funding_information


@pytest.fixture
def client():
    return TestClient(app)


def test_playground_run_endpoint(client):
    """Test POST /api/playground/run returns 200 with session_id and dashboard_url."""
    payload = {
        "task": "Research Anthropic, find funding, and write investment brief",
        "scenario": "conflicting_sources",
        "inject_chaos": False
    }

    response = client.post("/api/playground/run", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "session_id" in data
    assert "dashboard_url" in data
    assert data["dashboard_url"] == f"http://localhost:3000/sessions/{data['session_id']}"
    assert data["scenario"] == "conflicting_sources"
    assert data["inject_chaos"] is False


def test_chaos_injector_methods():
    """Test ChaosInjector methods: api failure, bad output, and timeout."""
    chaos = ChaosInjector(enabled=True)

    # Test API failure
    with pytest.raises(RuntimeError, match="Simulated Anthropic API failure"):
        chaos.inject_api_failure(force=True)

    # Test bad output corruption
    corrupted = chaos.inject_bad_output("Original good text", force=True)
    assert "i think probably i'm not sure" in corrupted

    # Test timeout
    with pytest.raises(TimeoutError, match="Simulated API Request Timeout"):
        chaos.inject_timeout(seconds=0.01, force=True)


def test_search_funding_information_conflicts():
    """Test search_funding_information returns conflicting $7.3B vs $8.1B funding sources."""
    sources = search_funding_information("funding")
    assert len(sources) == 2
    assert "$7.3 Billion" in sources[0]["content"]
    assert "$8.1 Billion" in sources[1]["content"]


@pytest.mark.asyncio
async def test_run_demo_agent_execution():
    """Test running the demo agent asynchronously end-to-end."""
    with patch("arc.backend.core.arc_runtime.publish_event", new_callable=AsyncMock):
        res = await run_demo_agent(
            task="Research Anthropic and write investment brief",
            inject_chaos=False,
        )

        assert res["status"] == "completed"
        assert "session_id" in res
        assert "dashboard_url" in res
        assert len(res["final_output"]) > 50
