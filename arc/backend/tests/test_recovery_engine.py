import pytest
import pytest_asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

try:
    from db.database import Base
    from models.session import AgentSession
    from models.checkpoint import Checkpoint, FailureEvent
    from core.recovery_engine import RecoveryEngine
except ImportError:
    from arc.backend.db.database import Base
    from arc.backend.models.session import AgentSession
    from arc.backend.models.checkpoint import Checkpoint, FailureEvent
    from arc.backend.core.recovery_engine import RecoveryEngine


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
async def test_checkpoint_validation_scores(async_db: AsyncSession):
    engine = RecoveryEngine(db_session=async_db)
    session_id = uuid.uuid4()

    # Need an AgentSession in DB for Foreign Key constraint
    agent_session = AgentSession(
        session_id=session_id,
        agent_name="test_agent",
        task="testing recovery engine",
        status="running",
    )
    async_db.add(agent_session)
    await async_db.commit()

    # 1. Full valid checkpoint -> score = 1.0, is_valid = True
    chk1 = await engine.checkpoint(
        session_id=session_id,
        step_number=1,
        agent_state={"agent_name": "test_agent", "task": "testing"},
        messages_history=[{"role": "user", "content": "hello"}],
        context_snapshot="Active context line 1",
        tool_results={"result": "ok"},
    )
    assert chk1.is_valid is True
    assert chk1.validation_score == 1.0
    assert chk1.was_used_for_recovery is False

    # 2. Empty messages history -> score = 0.0, is_valid = False
    chk2 = await engine.checkpoint(
        session_id=session_id,
        step_number=2,
        agent_state={"agent_name": "test_agent"},
        messages_history=[],
        context_snapshot="Active context line 1",
    )
    assert chk2.is_valid is False
    assert chk2.validation_score == 0.0

    # 3. Missing agent state keys -> subtract 0.2 => score = 0.8, is_valid = True
    chk3 = await engine.checkpoint(
        session_id=session_id,
        step_number=3,
        agent_state={},
        messages_history=[{"role": "user", "content": "hello"}],
        context_snapshot="Active context line 1",
    )
    assert chk3.is_valid is True
    assert chk3.validation_score == 0.8

    # 4. Empty context snapshot -> subtract 0.1 => score = 0.9, is_valid = True
    chk4 = await engine.checkpoint(
        session_id=session_id,
        step_number=4,
        agent_state={"agent_name": "test_agent"},
        messages_history=[{"role": "user", "content": "hello"}],
        context_snapshot="",
    )
    assert chk4.is_valid is True
    assert chk4.validation_score == 0.9

    # 5. Missing agent keys + Empty context snapshot -> subtract 0.3 => score = 0.7
    chk5 = await engine.checkpoint(
        session_id=session_id,
        step_number=5,
        agent_state=None,
        messages_history=[{"role": "user", "content": "hello"}],
        context_snapshot=None,
    )
    assert chk5.is_valid is True
    assert chk5.validation_score == 0.7


@pytest.mark.asyncio
async def test_detect_failure():
    engine = RecoveryEngine()

    # 1. API error
    is_fail, ftype = await engine.detect_failure(error="Internal Server Error")
    assert is_fail is True
    assert ftype == "api_error"

    # 2. Tool error
    is_fail, ftype = await engine.detect_failure(tool_success=False)
    assert is_fail is True
    assert ftype == "tool_error"

    # 3. Empty output (None or len < 5)
    is_fail, ftype = await engine.detect_failure(output_text="hi")
    assert is_fail is True
    assert ftype == "empty_output"

    is_fail, ftype = await engine.detect_failure(output_text=None)
    assert is_fail is True
    assert ftype == "empty_output"

    # 4. Bad output (expected json but invalid json)
    is_fail, ftype = await engine.detect_failure(
        output_text="This is not valid json", expected_type="json"
    )
    assert is_fail is True
    assert ftype == "bad_output"

    # 5. Valid cases
    is_fail, ftype = await engine.detect_failure(
        output_text='{"status": "success", "data": 123}', expected_type="json"
    )
    assert is_fail is False
    assert ftype is None

    is_fail, ftype = await engine.detect_failure(
        output_text="This is a valid long output text response from LLM.",
        tool_success=True,
    )
    assert is_fail is False
    assert ftype is None


@pytest.mark.asyncio
async def test_recovery_workflow(async_db: AsyncSession):
    engine = RecoveryEngine(db_session=async_db)
    session_id = uuid.uuid4()

    agent_session = AgentSession(
        session_id=session_id,
        agent_name="recovery_agent",
        task="Run complex pipeline",
        status="running",
    )
    async_db.add(agent_session)
    await async_db.commit()

    # Step 1: Valid checkpoint
    await engine.checkpoint(
        session_id=session_id,
        step_number=1,
        agent_state={"step": 1, "memory": "a"},
        messages_history=[{"role": "user", "content": "step 1"}],
        context_snapshot="Context step 1",
    )

    # Step 2: Invalid checkpoint (empty messages)
    await engine.checkpoint(
        session_id=session_id,
        step_number=2,
        agent_state={"step": 2},
        messages_history=[],
    )

    # Step 3: Valid checkpoint
    await engine.checkpoint(
        session_id=session_id,
        step_number=3,
        agent_state={"step": 3, "memory": "ab"},
        messages_history=[{"role": "user", "content": "step 3"}],
        context_snapshot="Context step 3",
    )

    # Attempt recovery at step 5 after failure
    recovered_data = await engine.recover(
        session_id=session_id,
        failed_at_step=5,
        failure_type="tool_error",
        error_message="Tool execution failed at step 5",
    )

    assert recovered_data is not None
    assert recovered_data["step_number"] == 3
    assert recovered_data["recovered_from_step"] == 3
    assert recovered_data["steps_lost"] == 2
    assert recovered_data["agent_state"] == {"step": 3, "memory": "ab"}

    # Verify FailureEvent logged in DB
    failures = await engine.get_failures(session_id)
    assert len(failures) == 1
    assert failures[0].step_number == 5
    assert failures[0].failure_type == "tool_error"
    assert failures[0].recovery_success is True
    assert failures[0].steps_replayed == 2

    # Verify Checkpoint updated in DB
    checkpoints = await engine.get_checkpoints(session_id)
    assert len(checkpoints) == 3
    step3_chk = [c for c in checkpoints if c.step_number == 3][0]
    assert step3_chk.was_used_for_recovery is True


@pytest.mark.asyncio
async def test_recovery_no_checkpoint(async_db: AsyncSession):
    engine = RecoveryEngine(db_session=async_db)
    session_id = uuid.uuid4()

    agent_session = AgentSession(
        session_id=session_id,
        agent_name="recovery_agent",
        task="No checkpoint task",
        status="running",
    )
    async_db.add(agent_session)
    await async_db.commit()

    # Attempt recovery with no checkpoints existing
    recovered_data = await engine.recover(
        session_id=session_id,
        failed_at_step=2,
        failure_type="api_error",
        error_message="Timeout on API call",
    )

    assert recovered_data is None

    failures = await engine.get_failures(session_id)
    assert len(failures) == 1
    assert failures[0].recovery_success is False
    assert failures[0].recovery_checkpoint_id is None
