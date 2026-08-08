"""Replay store — assembles a deterministic timeline for a recorded session.

The store does not duplicate storage; it composes the Flight Recorder's steps
with the Recovery Engine's checkpoints into a :class:`ReplayTimeline`, and
derives failure points from recorded step errors / low confidence.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ...types import ReplayTimeline, SessionStatus
from ..recorder.default import FlightRecorder
from ..recovery.default import RecoveryEngine


@runtime_checkable
class ReplayStore(Protocol):
    """Assembles a replayable timeline for a session."""

    def timeline(self, session_id: str) -> ReplayTimeline:
        """Return the ordered, replayable timeline for ``session_id``."""
        ...


class DefaultReplayStore:
    """Composes recorder + recovery into a :class:`ReplayTimeline`."""

    def __init__(
        self,
        recorder: FlightRecorder,
        recovery: RecoveryEngine,
        confidence_threshold: float = 0.2,
    ) -> None:
        self._recorder = recorder
        self._recovery = recovery
        self._threshold = confidence_threshold

    def timeline(self, session_id: str) -> ReplayTimeline:
        """Return the ordered, replayable timeline for ``session_id``."""
        steps = self._recorder.trace(session_id)
        failures = [
            s for s in steps if s.error or s.confidence_score < self._threshold
        ]
        status = SessionStatus.FAILED if failures else SessionStatus.COMPLETED
        if not steps:
            status = SessionStatus.ACTIVE
        return ReplayTimeline(
            session_id=session_id,
            status=status,
            timeline_steps=steps,
            failure_points=failures,
            recovery_checkpoints=self._recovery.checkpoints(session_id),
        )


__all__ = ["ReplayStore", "DefaultReplayStore"]
