"""Compliance & policy verification (interface only)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from ...types import TraceStep, VerificationResult


@runtime_checkable
class Verifier(Protocol):
    """Checks a session or trace against declarative policy rules."""

    def verify(
        self,
        trace: List[TraceStep],
        rules: Optional[List[Dict[str, Any]]] = None,
    ) -> VerificationResult:
        """Evaluate ``rules`` against ``trace`` and return the outcome."""
        ...


__all__ = ["Verifier"]
