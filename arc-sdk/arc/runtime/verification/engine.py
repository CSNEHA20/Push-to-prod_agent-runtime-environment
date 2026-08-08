"""Default verification engine — weighted aggregation of plugin checks.

Confidence is a weight-normalised mean of the per-check scores. A verifier that
raises is captured as a failed check (score 0) with the error recorded, so one
bad plugin degrades confidence rather than crashing the request.
"""

from __future__ import annotations

from typing import List, Optional

from . import (
    UNVERIFIED_CONFIDENCE,
    VerificationCheck,
    VerificationContext,
    VerificationReport,
    Verifier,
)


class DefaultVerificationEngine:
    """Runs applicable verifiers and derives confidence from their results.

    Satisfies the :class:`arc.runtime.verification.VerificationEngine` interface.
    """

    def __init__(self, verifiers: Optional[List[Verifier]] = None) -> None:
        self._verifiers: List[Verifier] = list(verifiers or [])

    @property
    def verifiers(self) -> List[Verifier]:
        return list(self._verifiers)

    def register(self, verifier: Verifier) -> None:
        self._verifiers.append(verifier)

    def verify(self, context: VerificationContext) -> VerificationReport:
        checks: List[VerificationCheck] = []
        for verifier in self._verifiers:
            if not self._applies(verifier, context):
                continue
            checks.append(self._run(verifier, context))

        if not checks:
            return VerificationReport(
                checks=[],
                confidence=UNVERIFIED_CONFIDENCE,
                passed=True,
                verified=False,
                explanation="No verifier applied; response was not verified.",
            )

        confidence = self._aggregate_confidence(checks)
        passed = all(c.passed for c in checks if c.required)
        return VerificationReport(
            checks=checks,
            confidence=confidence,
            passed=passed,
            verified=True,
            explanation=self._summarise(checks, passed, confidence),
        )

    # -- internals --------------------------------------------------------

    @staticmethod
    def _applies(verifier: Verifier, context: VerificationContext) -> bool:
        try:
            return bool(verifier.applies(context))
        except Exception:  # noqa: BLE001 - a broken applies() shouldn't crash dispatch
            return False

    def _run(self, verifier: Verifier, context: VerificationContext) -> VerificationCheck:
        try:
            return verifier.verify(context)
        except Exception as exc:  # noqa: BLE001 - capture, don't crash the request
            return VerificationCheck(
                name=getattr(verifier, "name", verifier.verifier_type),
                verifier=verifier.verifier_type,
                passed=False,
                score=0.0,
                evidence={"exception": repr(exc)},
                explanation=f"Verifier raised an exception: {exc}",
                error=str(exc),
            )

    @staticmethod
    def _aggregate_confidence(checks: List[VerificationCheck]) -> float:
        total_weight = sum(c.weight for c in checks)
        if total_weight <= 0:
            return round(sum(c.score for c in checks) / len(checks), 4)
        weighted = sum(c.score * c.weight for c in checks)
        return round(max(0.0, min(1.0, weighted / total_weight)), 4)

    @staticmethod
    def _summarise(checks: List[VerificationCheck], passed: bool, confidence: float) -> str:
        failed = [c.name for c in checks if not c.passed]
        head = f"{len(checks)} check(s) ran; confidence {confidence:.2f}"
        if passed:
            return f"{head}; all required checks passed."
        return f"{head}; failed: {', '.join(failed)}."


__all__ = ["DefaultVerificationEngine"]
