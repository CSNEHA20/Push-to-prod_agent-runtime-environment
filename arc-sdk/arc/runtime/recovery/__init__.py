"""Self-healing rollback & state checkpointing (interface only)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ...types import Checkpoint, RecoveryPlan


@runtime_checkable
class RecoveryEngine(Protocol):
    """Checkpoints agent state and restores it after a failed step."""

    def checkpoint(self, session_id: str, step_number: int) -> Checkpoint:
        """Persist a restorable snapshot of the current session state."""
        ...

    def plan(self, session_id: str) -> RecoveryPlan:
        """Compute the recovery plan for a failed session."""
        ...

    def restore(self, checkpoint: Checkpoint) -> None:
        """Roll session state back to a previous checkpoint."""
        ...


__all__ = ["RecoveryEngine"]
