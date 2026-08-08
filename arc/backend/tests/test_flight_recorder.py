import pytest
import pytest_asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from db.database import Base
from models.session import AgentSession
from models.trace import TraceStep
from core.flight_recorder import FlightRecorder


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


@pytest.mark.asyncio
async def test_confidence_score_heuristic():
    # Base case: text >= 50 chars without negative phrases -> score = 0.8
    normal_text = "This is a detailed and conclusive response from the LLM model that exceeds 50 characters easily."
    assert FlightRecorder.calculate_confidence_score(normal_text) == 0.8

    # Short response (<50 chars) -> -0.2 => 0.6
    short_text = "Yes, sure."
    assert FlightRecorder.calculate_confidence_score(short_text) == 0.6

    # Response with negative phrases: "I think", "probably", "I'm not sure", "might be"
    uncertain_text = "I think this might be correct, but I'm not sure, and it is probably fine. Detailed extra padding text."
    # 4 phrases matched: -0.4 => 0.8 - 0.4 = 0.4
    assert FlightRecorder.calculate_confidence_score(uncertain_text) == 0.4

    # Clamping test: short + 4 phrases -> 0.8 - 0.4 - 0.2 = 0.2
    very_uncertain_short = "I think it might be fine, probably, I'm not sure."
    assert FlightRecorder.calculate_confidence_score(very_uncertain_short) == 0.2

    # Clamping minimum 0.1
    extreme_low = "I think I think I think probably might be I'm not sure"
    assert FlightRecorder.calculate_confidence_score(extreme_low) >= 0.1


@pytest.mark.asyncio
async def test_reasoning_summary():
    text = "  First line of response.\nSecond line with   spaces.  "
    summary = FlightRecorder.generate_reasoning_summary(text)
    assert summary == "First line of response. Second line with spaces."
    assert len(summary) <= 100


@pytest.mark.asyncio
async def test_flight_recorder_workflow(async_db: AsyncSession):
    recorder = FlightRecorder(db_session=async_db)

    # 1. start_session
    session = await recorder.start_session(agent_name="code_agent", task="Fix bug in core")
    assert session is not None
    assert session.session_id is not None
    assert session.agent_name == "code_agent"
    assert session.task == "Fix bug in core"
    assert session.status == "running"
    assert session.total_steps == 0
    session_id = session.session_id

    # 2. record_llm_call
    llm_step = await recorder.record_llm_call(
        session_id=session_id,
        step_number=1,
        messages=[{"role": "user", "content": "Hello"}],
        response_text="I will process your request by searching the codebase for relevant functions.",
        input_tokens=150,
        output_tokens=30,
        duration_ms=450,
    )
    assert llm_step.step_type == "llm_call"
    assert llm_step.step_number == 1
    assert llm_step.confidence_score == 0.8
    assert llm_step.reasoning_summary.startswith("I will process your request")

    # 3. record_tool_call
    tool_step = await recorder.record_tool_call(
        session_id=session_id,
        step_number=2,
        tool_name="search_code",
        tool_input={"query": "def start_session"},
        tool_output="Found 1 result in flight_recorder.py",
        success=True,
        duration_ms=120,
    )
    assert tool_step.step_type == "tool_call"
    assert tool_step.step_number == 2
    assert tool_step.tool_name == "search_code"
    assert tool_step.tool_success is True

    # 4. get_session
    retrieved_session = await recorder.get_session(session_id)
    assert retrieved_session is not None
    assert retrieved_session.total_steps == 2

    # 5. get_trace
    trace = await recorder.get_trace(session_id)
    assert len(trace) == 2
    assert trace[0].step_number == 1
    assert trace[1].step_number == 2

    # 6. end_session
    ended_session = await recorder.end_session(session_id, status="completed")
    assert ended_session.status == "completed"
    assert ended_session.ended_at is not None

    # 7. get_replay
    replay = await recorder.get_replay(session_id)
    assert replay["session"].session_id == session_id
    assert len(replay["steps"]) == 2
    assert replay["failure_point"] is None
    assert replay["recovery_point"] is None
