"""Execution step tracing — the Flight Recorder (interface only)."""

from __future__ import annotations

from typing import List, Protocol, runtime_checkable

from ...types import TraceStep


@runtime_checkable
class Recorder(Protocol):
    """Persists every LLM/tool step and reconstructs traces on demand."""

    def record(self, step: TraceStep) -> TraceStep:
        """Persist a single execution step."""
        ...

    def trace(self, session_id: str) -> List[TraceStep]:
        """Return the ordered steps recorded for a session."""
        ...


__all__ = ["Recorder"]
