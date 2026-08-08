import pytest
import pytest_asyncio
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from main import app
from db.database import Base, get_db
from models.session import AgentSession
from models.context import ContextConflict, ContextLog


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
async def client(async_db):
    async def _override_get_db():
        yield async_db

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_context_routes_full_flow(client, async_db):
    # 1. Create a session, logs, and conflicts in DB
    session_id = uuid.uuid4()
    session = AgentSession(
        session_id=session_id,
        agent_name="ContextAgent",
        task="Financial context analysis",
        status="running",
    )
    async_db.add(session)

    log1 = ContextLog(
        log_id=uuid.uuid4(),
        session_id=session_id,
        step_number=1,
        total_received=3,
        passed=2,
        rejected=1,
        final_context="Doc 1\nDoc 2",
        provenance_map={"Doc 1": 0.9, "Doc 2": 0.85},
    )
    async_db.add(log1)

    conflict1 = ContextConflict(
        conflict_id=uuid.uuid4(),
        session_id=session_id,
        step_number=1,
        conflict_type="numerical",
        description="Revenue mismatch between Doc 1 ($10M) and Doc 2 ($12M)",
        severity="high",
        source_a_id="Doc 1",
        source_b_id="Doc 2",
    )
    conflict2 = ContextConflict(
        conflict_id=uuid.uuid4(),
        session_id=session_id,
        step_number=1,
        conflict_type="factual",
        description="Location discrepancy",
        severity="critical",
        source_a_id="Doc 1",
        source_b_id="Doc 2",
    )
    async_db.add(conflict1)
    async_db.add(conflict2)
    await async_db.commit()

    # 2. Test GET /api/context/{session_id}/log
    res_log = await client.get(f"/api/context/{session_id}/log")
    assert res_log.status_code == 200
    logs_data = res_log.json()
    assert len(logs_data) == 1
    assert logs_data[0]["step_number"] == 1
    assert logs_data[0]["passed"] == 2
    assert logs_data[0]["provenance_map"] == {"Doc 1": 0.9, "Doc 2": 0.85}

    # 3. Test GET /api/context/{session_id}/conflicts
    res_conf = await client.get(f"/api/context/{session_id}/conflicts")
    assert res_conf.status_code == 200
    conf_data = res_conf.json()
    assert conf_data["total_conflicts"] == 2
    assert conf_data["by_severity"]["critical"] == 1
    assert conf_data["by_severity"]["high"] == 1
    assert conf_data["by_type"]["numerical"] == 1
    assert conf_data["by_type"]["factual"] == 1
    # Verify critical severity is first
    assert conf_data["conflicts"][0]["severity"] == "critical"
    assert conf_data["conflicts"][1]["severity"] == "high"

    # 4. Test GET /api/context/{session_id}/provenance
    res_prov = await client.get(f"/api/context/{session_id}/provenance")
    assert res_prov.status_code == 200
    prov_data = res_prov.json()
    assert len(prov_data) == 2
    names = [p["source_name"] for p in prov_data]
    assert "Doc 1" in names
    assert "Doc 2" in names

    # 5. Test 404 for non-existent session
    fake_id = uuid.uuid4()
    res_404 = await client.get(f"/api/context/{fake_id}/conflicts")
    assert res_404.status_code == 404
