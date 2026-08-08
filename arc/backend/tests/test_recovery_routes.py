import pytest
import pytest_asyncio
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

try:
    from main import app
    from db.database import Base, get_db
    from models.session import AgentSession
    from core.recovery_engine import RecoveryEngine
except ImportError:
    from arc.backend.main import app
    from arc.backend.db.database import Base, get_db
    from arc.backend.models.session import AgentSession
    from arc.backend.core.recovery_engine import RecoveryEngine


@pytest_asyncio.fixture
async def async_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestingSessionLocal = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )

    async with TestingSessionLocal() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def client(async_db: AsyncSession):
    async def _override_get_db():
        yield async_db

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_recovery_routes_flow(client: AsyncClient, async_db: AsyncSession):
    session_id = uuid.uuid4()

    # Create agent session
    agent_session = AgentSession(
        session_id=session_id,
        agent_name="route_test_agent",
        task="Test recovery routes",
        status="running",
    )
    async_db.add(agent_session)
    await async_db.commit()

    engine = RecoveryEngine(db_session=async_db)

    # 1. Create checkpoints
    await engine.checkpoint(
        session_id=session_id,
        step_number=1,
        agent_state={"step": 1},
        messages_history=[{"role": "user", "content": "step 1"}],
        context_snapshot="Active context step 1",
    )
    await engine.checkpoint(
        session_id=session_id,
        step_number=2,
        agent_state={"step": 2},
        messages_history=[{"role": "user", "content": "step 2"}],
        context_snapshot="Active context step 2",
    )

    # Initially: 0 failures -> healthy status
    res_status_healthy = await client.get(f"/api/recovery/{session_id}/status")
    assert res_status_healthy.status_code == 200
    status_data = res_status_healthy.json()
    assert status_data["total_checkpoints"] == 2
    assert status_data["valid_checkpoints"] == 2
    assert status_data["total_failures"] == 0
    assert status_data["overall_health"] == "healthy"
    assert status_data["last_checkpoint_step"] == 2
    assert status_data["last_failure_step"] is None

    # GET checkpoints
    res_checkpoints = await client.get(f"/api/recovery/{session_id}/checkpoints")
    assert res_checkpoints.status_code == 200
    chk_list = res_checkpoints.json()
    assert len(chk_list) == 2
    assert chk_list[0]["step_number"] == 1
    assert chk_list[0]["is_valid"] is True
    assert chk_list[0]["validation_score"] == 1.0

    # 2. Trigger recovery -> creates FailureEvent
    await engine.recover(
        session_id=session_id,
        failed_at_step=3,
        failure_type="tool_error",
        error_message="Tool call failed",
    )

    # GET failures
    res_failures = await client.get(f"/api/recovery/{session_id}/failures")
    assert res_failures.status_code == 200
    fail_list = res_failures.json()
    assert len(fail_list) == 1
    assert fail_list[0]["failure_type"] == "tool_error"
    assert fail_list[0]["recovery_success"] is True

    # Check status -> should be degraded (failures present but all recovered)
    res_status_degraded = await client.get(f"/api/recovery/{session_id}/status")
    assert res_status_degraded.status_code == 200
    deg_data = res_status_degraded.json()
    assert deg_data["total_failures"] == 1
    assert deg_data["recoveries_successful"] == 1
    assert deg_data["overall_health"] == "degraded"
    assert deg_data["last_failure_step"] == 3


@pytest.mark.asyncio
async def test_recovery_routes_failed_health(client: AsyncClient, async_db: AsyncSession):
    session_id = uuid.uuid4()

    agent_session = AgentSession(
        session_id=session_id,
        agent_name="failed_agent",
        task="Fail recovery test",
        status="running",
    )
    async_db.add(agent_session)
    await async_db.commit()

    engine = RecoveryEngine(db_session=async_db)

    # Attempt recovery with no checkpoints -> recovery fails
    await engine.recover(
        session_id=session_id,
        failed_at_step=1,
        failure_type="api_error",
        error_message="Fatal API error",
    )

    res_status = await client.get(f"/api/recovery/{session_id}/status")
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert status_data["total_failures"] == 1
    assert status_data["recoveries_successful"] == 0
    assert status_data["overall_health"] == "failed"


@pytest.mark.asyncio
async def test_recovery_routes_not_found(client: AsyncClient):
    non_existent_id = uuid.uuid4()
    res1 = await client.get(f"/api/recovery/{non_existent_id}/checkpoints")
    assert res1.status_code == 404

    res2 = await client.get(f"/api/recovery/{non_existent_id}/failures")
    assert res2.status_code == 404

    res3 = await client.get(f"/api/recovery/{non_existent_id}/status")
    assert res3.status_code == 404
