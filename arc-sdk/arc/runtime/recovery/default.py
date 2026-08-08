"""Default in-memory Recovery Engine.

Checkpoints agent state after every step and, on failure, computes a plan that
recommends the latest valid checkpoint before the failed step.
"""

from __future__ import annotations

import threading
import uuid
from typing import Any, Dict, List, Optional

from ...types import Checkpoint, RecoveryPlan


class RecoveryEngine:
    """Thread-safe, in-process checkpoint store and planner.

    Satisfies the :class:`arc.runtime.recovery.RecoveryEngine` interface.
    """

    def __init__(self) -> None:
        self._checkpoints: Dict[str, List[Checkpoint]] = {}
        self._lock = threading.Lock()

    def checkpoint(
        self,
        session_id: str,
        step_number: int,
        state: Optional[Dict[str, Any]] = None,
    ) -> Checkpoint:
        """Persist a snapshot of the session state at ``step_number``."""
        cp = Checkpoint(
            checkpoint_id=str(uuid.uuid4()),
            session_id=session_id,
            step_number=step_number,
            metadata=dict(state or {}),
        )
        with self._lock:
            self._checkpoints.setdefault(session_id, []).append(cp)
        return cp

    def checkpoints(self, session_id: str) -> List[Checkpoint]:
        """Return all checkpoints recorded for ``session_id``."""
        with self._lock:
            return list(self._checkpoints.get(session_id, []))

    def plan(self, session_id: str, failed_at_step: Optional[int] = None) -> RecoveryPlan:
        """Compute a recovery plan, recommending the latest valid checkpoint."""
        available = self.checkpoints(session_id)
        candidates = (
            [c for c in available if c.step_number < failed_at_step]
            if failed_at_step is not None
            else available
        )
        recommended = candidates[-1] if candidates else None
        return RecoveryPlan(
            session_id=session_id,
            status="recoverable" if recommended else "no_checkpoint",
            recommended_checkpoint=recommended,
            available_checkpoints=available,
            recovery_actions=(
                [{"type": "rollback", "checkpoint_id": recommended.checkpoint_id}]
                if recommended
                else []
            ),
        )

    def restore(self, checkpoint: Checkpoint) -> Dict[str, Any]:
        """Return the state captured in ``checkpoint`` (caller re-applies it)."""
        return dict(checkpoint.metadata)


__all__ = ["RecoveryEngine"]
