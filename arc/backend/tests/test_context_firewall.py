import pytest
import pytest_asyncio
import uuid
from unittest.mock import MagicMock
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from db.database import Base
from models.session import AgentSession
from models.context import ContextConflict, ContextLog
from core.context_firewall import ContextFirewall


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


class MockAnthropicClient:
    """Mock client for Anthropic messages.create API calls."""
    def __init__(self, scores=None, conflicts=None):
        self.scores = scores or []
        self.conflicts = conflicts or []
        self.call_count = 0
        self.score_idx = 0
        self.conflict_idx = 0
        self.messages = MagicMock()
        self.messages.create = self._create

    def _create(self, model, max_tokens, messages):
        prompt = messages[0]["content"]
        res_mock = MagicMock()

        if "Rate how relevant" in prompt:
            score = self.scores[self.score_idx] if self.score_idx < len(self.scores) else "0.8"
            self.score_idx += 1
            res_mock.content = [MagicMock(text=str(score))]
        elif "conflict with each other" in prompt:
            conflict = self.conflicts[self.conflict_idx] if self.conflict_idx < len(self.conflicts) else "NO_CONFLICT"
            self.conflict_idx += 1
            res_mock.content = [MagicMock(text=str(conflict))]
        else:
            res_mock.content = [MagicMock(text="0.5")]

        return res_mock


@pytest.mark.asyncio
async def test_context_firewall_pipeline(async_db):
    # 1. Create a parent session in DB
    session_id = uuid.uuid4()
    agent_session = AgentSession(
        session_id=session_id,
        agent_name="TestAgent",
        task="Analyze company revenue",
        status="running",
    )
    async_db.add(agent_session)
    await async_db.commit()

    # 2. Setup mock client:
    # Source 1 score: 0.9 (passed)
    # Source 2 score: 0.1 (rejected)
    # Source 3 score: 0.85 (passed)
    # Conflict between Source 1 & Source 3: "Yes, numerical conflict on revenue numbers."
    mock_client = MockAnthropicClient(
        scores=["0.9", "0.1", "0.85"],
        conflicts=["Yes, numerical conflict on revenue numbers."]
    )

    firewall = ContextFirewall(client=mock_client, db_session=async_db)

    sources = [
        {"name": "Report A", "content": "Q3 Revenue was $10M.", "source_type": "doc", "confidence": 0.9},
        {"name": "Unrelated Blog", "content": "Favorite food is pizza.", "source_type": "web", "confidence": 0.1},
        {"name": "Report B", "content": "Q3 Revenue was $12M.", "source_type": "doc", "confidence": 0.8},
    ]

    result = await firewall.filter(
        session_id=session_id,
        step_number=1,
        sources=sources,
        task="Analyze company revenue",
    )

    # 3. Assert FilteredContext output structure
    assert result["total_received"] == 3
    assert result["passed"] == 2
    assert result["rejected"] == 1
    assert "Report A" in result["provenance_map"]
    assert "Report B" in result["provenance_map"]
    assert "Unrelated Blog" not in result["provenance_map"]
    assert result["provenance_map"]["Report A"] == 0.9
    assert result["provenance_map"]["Report B"] == 0.85

    assert "[SOURCE: Report A | CONFIDENCE: 0.90]" in result["final_context"]
    assert "[SOURCE: Report B | CONFIDENCE: 0.85]" in result["final_context"]

    assert len(result["conflicts"]) == 1
    conflict = result["conflicts"][0]
    assert conflict["conflict_type"] == "numerical"
    assert "numerical conflict" in conflict["description"].lower()

    # 4. Verify DB records
    logs_res = await async_db.execute(select(ContextLog).where(ContextLog.session_id == session_id))
    db_logs = logs_res.scalars().all()
    assert len(db_logs) == 1
    assert db_logs[0].total_received == 3
    assert db_logs[0].passed == 2
    assert db_logs[0].rejected == 1

    conflicts_res = await async_db.execute(select(ContextConflict).where(ContextConflict.session_id == session_id))
    db_conflicts = conflicts_res.scalars().all()
    assert len(db_conflicts) == 1
    assert db_conflicts[0].conflict_type == "numerical"
    assert db_conflicts[0].source_a_id == "Report A"
    assert db_conflicts[0].source_b_id == "Report B"


@pytest.mark.asyncio
async def test_context_firewall_no_conflicts():
    mock_client = MockAnthropicClient(
        scores=["0.9", "0.8"],
        conflicts=["NO_CONFLICT"]
    )
    firewall = ContextFirewall(client=mock_client)

    sources = [
        {"name": "Doc 1", "content": "Sky is blue."},
        {"name": "Doc 2", "content": "Grass is green."},
    ]

    session_id = uuid.uuid4()
    result = await firewall.filter(
        session_id=session_id,
        step_number=1,
        sources=sources,
        task="Check colors",
    )

    assert result["total_received"] == 2
    assert result["passed"] == 2
    assert result["rejected"] == 0
    assert len(result["conflicts"]) == 0
