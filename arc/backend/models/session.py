import uuid
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, Integer, Boolean, DateTime, UUID, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base

if TYPE_CHECKING:
    from models.trace import TraceStep
    from models.context import ContextConflict
    from models.checkpoint import Checkpoint, FailureEvent


class AgentSession(Base):
    __tablename__ = "agent_sessions"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_name: Mapped[str] = mapped_column(String(255), nullable=False)
    task: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="running", nullable=False
    )  # running | completed | failed | recovered
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    total_steps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_at_step: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    recovered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    trace_steps: Mapped[List["TraceStep"]] = relationship(
        "TraceStep", back_populates="session", cascade="all, delete-orphan"
    )
    context_conflicts: Mapped[List["ContextConflict"]] = relationship(
        "ContextConflict", back_populates="session", cascade="all, delete-orphan"
    )
    checkpoints: Mapped[List["Checkpoint"]] = relationship(
        "Checkpoint", back_populates="session", cascade="all, delete-orphan"
    )
    failure_events: Mapped[List["FailureEvent"]] = relationship(
        "FailureEvent", back_populates="session", cascade="all, delete-orphan"
    )
