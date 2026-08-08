import uuid
from datetime import datetime
from typing import Optional, Any, TYPE_CHECKING
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, UUID, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base

if TYPE_CHECKING:
    from models.session import AgentSession


class TraceStep(Base):
    __tablename__ = "trace_steps"

    step_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    step_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # llm_call | tool_call | decision
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    input_data: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    output_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    tool_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tool_input: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    tool_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tool_success: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reasoning_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    context_used: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    status: Mapped[str] = mapped_column(
        String(50), default="success", nullable=False
    )  # success | failed | skipped
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    was_recovered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    session: Mapped["AgentSession"] = relationship(
        "AgentSession", back_populates="trace_steps"
    )
