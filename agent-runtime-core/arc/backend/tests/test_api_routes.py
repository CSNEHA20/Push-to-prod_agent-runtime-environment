import pytest
import pytest_asyncio
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from main import app
from db.database import Base, get_db
from core.flight_recorder import FlightRecorder
from api.websocket import publish_event


@pytest_asyncio.fixture
async def async_test_db():
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
async def client(async_test_db: AsyncSession):
    async def _get_test_db():
        yield async_test_db

    app.dependency_overrides[get_db] = _get_test_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_session_and_trace_routes(client: AsyncClient, async_test_db: AsyncSession):
    recorder = FlightRecorder(db_session=async_test_db)
    
    # Create test session
    session = await recorder.start_session(agent_name="test_agent", task="Run API tests")
    session_id = session.session_id

    # Record steps
    await recorder.record_llm_call(
        session_id=session_id,
        step_number=1,
        messages=[{"role": "user", "content": "Hi"}],
        response_text="Hello! I am ready to assist you with testing.",
        input_tokens=10,
        output_tokens=15,
        duration_ms=100,
    )
    await recorder.record_tool_call(
        session_id=session_id,
        step_number=2,
        tool_name="read_file",
        tool_input={"path": "test.txt"},
        tool_output="file contents",
        success=True,
        duration_ms=50,
    )

    # 1. GET /api/sessions
    res = await client.get("/api/sessions")
    assert res.status_code == 200
    sessions_list = res.json()
    assert len(sessions_list) >= 1
    assert sessions_list[0]["session_id"] == str(session_id)

    # 2. GET /api/sessions/{session_id}
    res = await client.get(f"/api/sessions/{session_id}")
    assert res.status_code == 200
    session_details = res.json()
    assert session_details["agent_name"] == "test_agent"
    assert session_details["total_steps"] == 2

    # 3. GET /api/sessions/{session_id}/trace
    res = await client.get(f"/api/sessions/{session_id}/trace")
    assert res.status_code == 200
    steps = res.json()
    assert len(steps) == 2
    assert steps[0]["step_number"] == 1
    assert steps[1]["step_number"] == 2

    # 4. GET /api/sessions/{session_id}/replay
    res = await client.get(f"/api/sessions/{session_id}/replay")
    assert res.status_code == 200
    replay = res.json()
    assert replay["session"]["session_id"] == str(session_id)
    assert len(replay["steps"]) == 2

    # 5. GET /api/sessions/{session_id}/trace/step/1
    res = await client.get(f"/api/sessions/{session_id}/trace/step/1")
    assert res.status_code == 200
    step_one = res.json()
    assert step_one["step_number"] == 1
    assert step_one["step_type"] == "llm_call"

    # 6. DELETE /api/sessions/{session_id}
    res = await client.delete(f"/api/sessions/{session_id}")
    assert res.status_code == 200
    del_res = res.json()
    assert del_res["session_id"] == str(session_id)

    # Verify 404 after deletion
    res = await client.get(f"/api/sessions/{session_id}")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_publish_event_helper():
    test_session_id = uuid.uuid4()
    # publish_event should handle absence of running Redis without crashing
    success = await publish_event(test_session_id, "step_started", {"step": 1})
    assert isinstance(success, bool)
