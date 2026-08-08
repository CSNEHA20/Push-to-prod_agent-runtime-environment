import uuid
from datetime import datetime
from typing import Optional, Any, List, TYPE_CHECKING
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, UUID, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base

if TYPE_CHECKING:
    from models.session import AgentSession


class Checkpoint(Base):
    __tablename__ = "checkpoints"

    checkpoint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    agent_state: Mapped[Any] = mapped_column(JSON, nullable=False)
    messages_history: Mapped[Any] = mapped_column(JSON, nullable=False)
    context_snapshot: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tool_results: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    validation_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    was_used_for_recovery: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # Relationships
    session: Mapped["AgentSession"] = relationship(
        "AgentSession", back_populates="checkpoints"
    )
    failure_events: Mapped[List["FailureEvent"]] = relationship(
        "FailureEvent", back_populates="recovery_checkpoint"
    )


class FailureEvent(Base):
    __tablename__ = "failure_events"

    failure_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    failure_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # api_error | bad_output | timeout | logic_error
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    recovery_attempted: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    recovery_checkpoint_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("checkpoints.checkpoint_id", ondelete="SET NULL"),
        nullable=True,
    )
    recovery_success: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    steps_replayed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    session: Mapped["AgentSession"] = relationship(
        "AgentSession", back_populates="failure_events"
    )
    recovery_checkpoint: Mapped[Optional["Checkpoint"]] = relationship(
        "Checkpoint", back_populates="failure_events"
    )
