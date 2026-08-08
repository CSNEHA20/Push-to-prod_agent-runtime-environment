"""
ARC SDK - Strongly Typed Domain Models.
Defines production-grade data structures for sessions, traces, firewall verification, replays, and recovery.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SessionStatus(str, Enum):
    ACTIVE = "active"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RECOVERED = "recovered"


class StepType(str, Enum):
    LLM_CALL = "llm_call"
    TOOL_CALL = "tool_call"
    CHECKPOINT = "checkpoint"
    VERIFICATION = "verification"
    RECOVERY_ROLLBACK = "recovery_rollback"


class FirewallAction(str, Enum):
    ALLOW = "allow"
    BLOCK = "block"
    SANITIZE = "sanitize"


class ConflictItem(BaseModel):
    """Represents a conflict detected by the Context Firewall engine."""
    source_id: str = Field(..., description="ID of the conflicting data source")
    conflict_type: str = Field(..., description="Type of conflict detected")
    description: str = Field(..., description="Detailed description of the conflict")
    confidence_score: float = Field(default=1.0, description="Confidence rating of conflict (0.0 to 1.0)")
    mitigation: Optional[str] = Field(default=None, description="Suggested mitigation action")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class VerificationResult(BaseModel):
    """Result returned by Context Firewall verification checks."""
    is_valid: bool = Field(..., description="True if no blocking conflicts detected")
    conflicts: List[ConflictItem] = Field(default_factory=list, description="List of detected conflicts")
    firewall_status: str = Field(default="pass", description="Status code: 'pass', 'warn', 'block'")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional verification metadata")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class FirewallRule(BaseModel):
    """Represents a security rule enforced by Context Firewall."""
    id: str = Field(..., description="Unique rule ID")
    rule_type: str = Field(..., description="Type of security rule (regex, vector, heuristic)")
    action: FirewallAction = Field(default=FirewallAction.BLOCK, description="Enforcement action")
    threshold: float = Field(default=0.8, description="Trigger sensitivity threshold")
    pattern: Optional[str] = Field(default=None, description="Matching pattern or regex expression")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class TraceStep(BaseModel):
    """Represents an executed step recorded in Flight Recorder."""
    step_id: str = Field(..., description="Unique step UUID")
    session_id: str = Field(..., description="Parent session UUID")
    step_type: StepType = Field(default=StepType.LLM_CALL, description="Type of step executed")
    step_number: int = Field(default=1, description="Sequential step index within session")
    name: Optional[str] = Field(default=None, description="Name or title of the step")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Input payload or prompt parameters")
    output_data: Optional[Dict[str, Any]] = Field(default=None, description="Output payload or response")
    latency_ms: float = Field(default=0.0, description="Execution time in milliseconds")
    token_usage: Dict[str, int] = Field(default_factory=dict, description="Tokens used: input_tokens, output_tokens")
    confidence_score: float = Field(default=1.0, description="Heuristic confidence score (0.0 to 1.0)")
    timestamp: str = Field(default_factory=_utcnow_iso, description="ISO timestamp")
    error: Optional[str] = Field(default=None, description="Error message if step failed")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class Session(BaseModel):
    """Represents an agent session in ARC."""
    session_id: str = Field(..., description="Unique session UUID")
    agent_name: str = Field(..., description="Name of the protected agent")
    task: str = Field(..., description="Goal or prompt description")
    status: SessionStatus = Field(default=SessionStatus.ACTIVE, description="Current lifecycle status")
    created_at: str = Field(default_factory=_utcnow_iso, description="Creation ISO timestamp")
    updated_at: Optional[str] = Field(default=None, description="Last update ISO timestamp")
    total_steps: int = Field(default=0, description="Count of recorded steps")
    total_tokens: int = Field(default=0, description="Total tokens consumed across all steps")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary session metadata")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class SessionList(BaseModel):
    """Container for list of agent sessions."""
    sessions: List[Session] = Field(default_factory=list, description="List of sessions")
    total_count: int = Field(default=0, description="Total count")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class Checkpoint(BaseModel):
    """Represents a state rollback checkpoint created by Recovery Engine."""
    checkpoint_id: str = Field(..., description="Unique checkpoint UUID")
    session_id: str = Field(..., description="Parent session UUID")
    step_number: int = Field(..., description="Step index where state was saved")
    state_hash: Optional[str] = Field(default=None, description="Cryptographic state checksum")
    timestamp: str = Field(default_factory=_utcnow_iso, description="ISO timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Checkpoint context data")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class RecoveryDiff(BaseModel):
    """Represents state diff payload computed during failure recovery."""
    id: str = Field(..., description="Unique recovery diff UUID")
    session_id: str = Field(..., description="Parent session UUID")
    failed_step_id: str = Field(..., description="Failed step UUID")
    strategy_used: str = Field(..., description="Recovery strategy name")
    diff_payload: Dict[str, Any] = Field(default_factory=dict, description="JSON state diff payload")
    status: str = Field(default="computed", description="Status of recovery diff calculation")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class ReplayTimeline(BaseModel):
    """Visual replay payload containing ordered trace steps and analysis."""
    session_id: str = Field(..., description="Session UUID")
    status: SessionStatus = Field(default=SessionStatus.ACTIVE, description="Session status")
    timeline_steps: List[TraceStep] = Field(default_factory=list, description="Chronological trace steps")
    failure_points: List[TraceStep] = Field(default_factory=list, description="Steps that encountered failures")
    recovery_checkpoints: List[Checkpoint] = Field(default_factory=list, description="Available rollback checkpoints")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class RecoveryPlan(BaseModel):
    """Recovery strategy details returned by Engine 3 (Recovery Engine)."""
    session_id: str = Field(..., description="Session UUID")
    status: str = Field(default="ready", description="Status of recovery mechanism")
    recommended_checkpoint: Optional[Checkpoint] = Field(default=None, description="Optimal target checkpoint for rollback")
    available_checkpoints: List[Checkpoint] = Field(default_factory=list, description="List of all available checkpoints")
    recovery_actions: List[Dict[str, Any]] = Field(default_factory=list, description="Action items to restore health")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
