"""
Tests for ARC SDK (client, agent wrapper, init).
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

try:
    from db.database import Base
except ImportError:
    from arc.backend.db.database import Base

try:
    import arc_sdk
    from arc_sdk.client import ARCClient
    from arc_sdk.agent import ARCAgent
except ImportError:
    from arc.sdk import arc_sdk
    from arc.sdk.arc_sdk.client import ARCClient
    from arc.sdk.arc_sdk.agent import ARCAgent


@pytest_asyncio.fixture
async def async_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )

    async with SessionLocal() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def mock_anthropic_client():
    client = MagicMock()
    res = MagicMock()
    res.content = [MagicMock(text="SDK response output from Claude model.")]
    res.usage = MagicMock(input_tokens=20, output_tokens=30)
    client.messages.create.return_value = res
    return client


def test_arc_sdk_init():
    """Test arc_sdk.init() sets environment and default client."""
    arc_sdk.init(api_key="test_key_123", anthropic_api_key="test_anthropic_456")
    assert arc_sdk._default_client is not None
    assert arc_sdk._default_client.api_key == "test_key_123"


def test_arc_client_methods():
    """Test ARCClient methods with mocked httpx responses."""
    client = ARCClient(server_url="http://localhost:8000")

    with patch("httpx.Client.get") as mock_get:
        mock_get.return_value.json.return_value = [{"session_id": "s1"}]
        mock_get.return_value.raise_for_status = MagicMock()

        sessions = client.get_sessions()
        assert len(sessions) == 1
        assert sessions[0]["session_id"] == "s1"


@pytest.mark.asyncio
async def test_arc_agent_call_claude(async_db, mock_anthropic_client):
    """Test ARCAgent call_claude pipeline."""
    with patch("api.websocket.publish_event", new_callable=AsyncMock), \
         patch("arc.backend.api.websocket.publish_event", new_callable=AsyncMock, create=True):

        agent = ARCAgent(
            name="SDKTestAgent",
            task="Perform SDK analysis",
            anthropic_client=mock_anthropic_client,
            db_session=async_db,
        )

        res = await agent.acall_claude(
            messages=[{"role": "user", "content": "Hello SDK"}]
        )

        assert res == "SDK response output from Claude model."
        assert "http://localhost:3000/sessions/" in agent.dashboard_url
