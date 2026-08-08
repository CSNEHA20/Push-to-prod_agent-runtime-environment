"""Default confidence/compliance verifier.

Evaluates a recorded trace: a step fails verification if it errored or scored
below the confidence threshold. Optional rules of the form
``{"max_latency_ms": N}`` or ``{"min_confidence": X}`` add extra checks.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ...types import ConflictItem, TraceStep, VerificationResult


class ConfidenceVerifier:
    """Threshold-based verifier over recorded steps.

    Satisfies the :class:`arc.runtime.verifier.Verifier` interface.
    """

    def __init__(self, confidence_threshold: float = 0.2) -> None:
        self.confidence_threshold = confidence_threshold

    def verify(
        self,
        trace: List[TraceStep],
        rules: Optional[List[Dict[str, Any]]] = None,
    ) -> VerificationResult:
        """Return the verification outcome for ``trace`` under ``rules``."""
        conflicts: List[ConflictItem] = []
        for step in trace:
            conflicts.extend(self._check_step(step, rules or []))
        return VerificationResult(
            is_valid=not conflicts,
            conflicts=conflicts,
            firewall_status="pass" if not conflicts else "block",
            metadata={"steps_checked": len(trace)},
        )

    def _check_step(
        self, step: TraceStep, rules: List[Dict[str, Any]]
    ) -> List[ConflictItem]:
        found: List[ConflictItem] = []
        if step.error:
            found.append(self._conflict(step, "error", step.error))
        elif step.confidence_score < self.confidence_threshold:
            found.append(
                self._conflict(
                    step,
                    "low_confidence",
                    f"confidence {step.confidence_score} < {self.confidence_threshold}",
                )
            )
        for rule in rules:
            found.extend(self._check_rule(step, rule))
        return found

    def _check_rule(self, step: TraceStep, rule: Dict[str, Any]) -> List[ConflictItem]:
        found: List[ConflictItem] = []
        max_latency = rule.get("max_latency_ms")
        if max_latency is not None and step.latency_ms > float(max_latency):
            found.append(
                self._conflict(step, "latency", f"{step.latency_ms}ms > {max_latency}ms")
            )
        min_conf = rule.get("min_confidence")
        if min_conf is not None and step.confidence_score < float(min_conf):
            found.append(
                self._conflict(step, "rule_confidence", f"{step.confidence_score} < {min_conf}")
            )
        return found

    @staticmethod
    def _conflict(step: TraceStep, kind: str, description: str) -> ConflictItem:
        return ConflictItem(
            source_id=step.step_id,
            conflict_type=kind,
            description=description,
            confidence_score=step.confidence_score,
        )


__all__ = ["ConfidenceVerifier"]
