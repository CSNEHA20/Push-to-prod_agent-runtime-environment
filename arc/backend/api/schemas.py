import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class AgentSessionResponse(BaseModel):
    session_id: uuid.UUID
    agent_name: str
    task: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    total_steps: int = 0
    failed_at_step: Optional[int] = None
    recovered: bool = False

    model_config = ConfigDict(from_attributes=True)


class TraceStepResponse(BaseModel):
    step_id: uuid.UUID
    session_id: uuid.UUID
    step_number: int
    step_type: str
    timestamp: datetime
    duration_ms: Optional[int] = None
    input_data: Optional[Any] = None
    output_data: Optional[str] = None
    tool_name: Optional[str] = None
    tool_input: Optional[Any] = None
    tool_output: Optional[str] = None
    tool_success: Optional[bool] = None
    confidence_score: Optional[float] = None
    reasoning_summary: Optional[str] = None
    context_used: Optional[Any] = None
    status: str
    error: Optional[str] = None
    was_recovered: bool = False

    model_config = ConfigDict(from_attributes=True)


class ReplayResponse(BaseModel):
    session: AgentSessionResponse
    steps: List[TraceStepResponse]
    failure_point: Optional[int] = None
    recovery_point: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class DeleteSessionResponse(BaseModel):
    message: str
    session_id: uuid.UUID
