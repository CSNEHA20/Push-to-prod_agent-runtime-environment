import pytest
import pytest_asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from db.database import Base
from core.arc_runtime import ARCRuntime


@pytest_asyncio.fixture
async def async_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )

    async with AsyncSessionLocal() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def mock_anthropic_client():
    client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="This is a valid response from Claude AI model.")]
    mock_response.usage = MagicMock(input_tokens=15, output_tokens=25)
    client.messages.create.return_value = mock_response
    return client


@pytest.mark.asyncio
async def test_arc_runtime_init_properties(async_db, mock_anthropic_client):
    runtime = ARCRuntime(
        anthropic_client=mock_anthropic_client,
        agent_name="TestAgent",
        task="Test task execution",
        db_session=async_db,
    )

    assert isinstance(runtime.session_id, uuid.UUID)
    assert runtime.dashboard_url == f"http://localhost:3000/sessions/{runtime.session_id}"
    assert runtime.step_counter == 0


@pytest.mark.asyncio
async def test_call_claude_pipeline(async_db, mock_anthropic_client):
    runtime = ARCRuntime(
        anthropic_client=mock_anthropic_client,
        agent_name="TestAgent",
        task="Solve math problem",
        db_session=async_db,
    )

    messages = [{"role": "user", "content": "What is 2+2?"}]
    response = await runtime.call_claude(messages=messages)

    assert response == "This is a valid response from Claude AI model."
    assert runtime.step_counter == 1
    mock_anthropic_client.messages.create.assert_called_once()


@pytest.mark.asyncio
async def test_call_claude_with_context_sources(async_db, mock_anthropic_client):
    runtime = ARCRuntime(
        anthropic_client=mock_anthropic_client,
        agent_name="ContextAgent",
        task="Analyze document",
        db_session=async_db,
    )

    # Mock ContextFirewall filter response
    with patch.object(
        runtime.context_firewall,
        "filter",
        new_callable=AsyncMock,
        return_value={
            "final_context": "Doc context chunk 1",
            "conflicts": [],
        },
    ):
        messages = [{"role": "user", "content": "Summarize the document."}]
        context_sources = [{"name": "doc1", "content": "Doc context chunk 1"}]

        response = await runtime.call_claude(messages=messages, context_sources=context_sources)

        assert response == "This is a valid response from Claude AI model."
        assert runtime.step_counter == 1


@pytest.mark.asyncio
async def test_run_tool(async_db, mock_anthropic_client):
    runtime = ARCRuntime(
        anthropic_client=mock_anthropic_client,
        agent_name="ToolAgent",
        task="Perform calculation",
        db_session=async_db,
    )

    def sample_tool(args):
        return args["x"] * 2

    result = await runtime.run_tool(
        tool_name="multiply",
        tool_input={"x": 5},
        tool_fn=sample_tool,
    )

    assert result == 10
    assert runtime.step_counter == 1


@pytest.mark.asyncio
async def test_complete_session(async_db, mock_anthropic_client):
    runtime = ARCRuntime(
        anthropic_client=mock_anthropic_client,
        agent_name="CompleteAgent",
        task="Finish workflow",
        db_session=async_db,
    )

    await runtime._ensure_session()
    session = await runtime.complete(final_output="Task completed successfully.")

    assert session is not None
    assert session.status == "completed"


@pytest.mark.asyncio
async def test_call_claude_low_confidence_recovery(async_db, mock_anthropic_client):
    runtime = ARCRuntime(
        anthropic_client=mock_anthropic_client,
        agent_name="RecoveryAgent",
        task="Uncertain task",
        db_session=async_db,
    )

    # Return a low-confidence response on 1st call, high-confidence on 2nd call
    low_res = MagicMock()
    low_res.content = [MagicMock(text="i think probably i'm not sure might be confusing")]
    low_res.usage = MagicMock(input_tokens=10, output_tokens=10)

    high_res = MagicMock()
    high_res.content = [MagicMock(text="This is a solid, definitive, high-confidence response that is long enough.")]
    high_res.usage = MagicMock(input_tokens=10, output_tokens=20)

    mock_anthropic_client.messages.create.side_effect = [low_res, high_res]

    with patch.object(
        runtime.flight_recorder,
        "calculate_confidence_score",
        side_effect=[0.1, 0.9],
    ):
        with patch.object(
            runtime.recovery_engine,
            "recover",
            new_callable=AsyncMock,
            return_value={
                "messages_history": [{"role": "user", "content": "Retry prompt"}],
            },
        ) as mock_recover:
            messages = [{"role": "user", "content": "Hello"}]
            res = await runtime.call_claude(messages=messages)

            assert res == "This is a solid, definitive, high-confidence response that is long enough."
            mock_recover.assert_called_once()

