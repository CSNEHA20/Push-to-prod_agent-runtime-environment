"""In-memory Flight Recorder implementation.

Records every intercepted step and reconstructs per-session traces.

The recorder does **not** score confidence — confidence is derived by the
Verification Engine from verification evidence and written onto the step at the
verify node. ``build_step`` sets a neutral, unverified confidence
(``UNVERIFIED_CONFIDENCE``), or ``0.0`` for a step that recorded a hard error.
"""

from __future__ import annotations

import threading
import uuid
from typing import Any, Dict, List, Optional

from ...types import StepType, TraceStep
from ..verification import UNVERIFIED_CONFIDENCE


def generate_reasoning_summary(response_text: Optional[str]) -> str:
    """First 100 whitespace-normalised characters of ``response_text`` (a label, not a score)."""
    if not response_text:
        return ""
    return " ".join(response_text.strip().split())[:100]


class FlightRecorder:
    """Thread-safe, in-process recorder keyed by session id.

    Satisfies the :class:`arc.runtime.recorder.Recorder` interface.
    """

    def __init__(self) -> None:
        self._steps: Dict[str, List[TraceStep]] = {}
        self._lock = threading.Lock()

    def next_step_number(self, session_id: str) -> int:
        """Return the 1-based index of the next step in a session."""
        with self._lock:
            return len(self._steps.get(session_id, [])) + 1

    def build_step(
        self,
        session_id: str,
        step_number: int,
        *,
        step_type: StepType = StepType.LLM_CALL,
        name: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        output_text: Optional[str] = None,
        output_data: Optional[Dict[str, Any]] = None,
        latency_ms: float = 0.0,
        token_usage: Optional[Dict[str, int]] = None,
        error: Optional[str] = None,
    ) -> TraceStep:
        """Construct a :class:`TraceStep`.

        Confidence is left at the unverified default (``0.0`` on error); the
        verification engine overwrites it with an evidence-derived score.
        """
        confidence = 0.0 if error else UNVERIFIED_CONFIDENCE
        payload = dict(output_data or {})
        if output_text is not None:
            payload.setdefault("text", output_text)
            payload.setdefault("reasoning_summary", generate_reasoning_summary(output_text))
        return TraceStep(
            step_id=str(uuid.uuid4()),
            session_id=session_id,
            step_type=step_type,
            step_number=step_number,
            name=name or step_type.value,
            input_data=input_data or {},
            output_data=payload,
            latency_ms=latency_ms,
            token_usage=token_usage or {},
            confidence_score=confidence,
            error=error,
        )

    def record(self, step: TraceStep) -> TraceStep:
        """Persist ``step`` and return it."""
        with self._lock:
            self._steps.setdefault(step.session_id, []).append(step)
        return step

    def trace(self, session_id: str) -> List[TraceStep]:
        """Return the ordered steps recorded for ``session_id``."""
        with self._lock:
            return list(self._steps.get(session_id, []))


__all__ = ["FlightRecorder", "generate_reasoning_summary"]
