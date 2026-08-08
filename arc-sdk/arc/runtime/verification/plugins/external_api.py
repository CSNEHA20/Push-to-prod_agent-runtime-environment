"""External / API verification.

Delegates the verdict to a caller-supplied ``checker`` — typically a call to an
external service (a fact-checker, a moderation API, a domain validator). The
checker receives the neutral :class:`VerificationContext` and returns either a
bool or a result mapping ``{"passed", "score"?, "explanation"?, ...evidence}``.
Keeping the checker injected keeps ARC provider- and vendor-independent.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Union

from .. import VerificationCheck, VerificationContext

ExternalChecker = Callable[[VerificationContext], Union[bool, Dict[str, Any]]]


class ExternalAPIVerifier:
    """Runs an external verification callable and structures its result."""

    verifier_type = "external_api"

    def __init__(self, checker: ExternalChecker, *, name: str = "external_api") -> None:
        self._checker = checker
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def applies(self, context: VerificationContext) -> bool:
        return True

    def verify(self, context: VerificationContext) -> VerificationCheck:
        result = self._checker(context)
        if isinstance(result, dict):
            passed = bool(result.get("passed", False))
            score = float(result.get("score", 1.0 if passed else 0.0))
            explanation = result.get(
                "explanation", "External verification "
                + ("passed." if passed else "failed."),
            )
            evidence = {k: v for k, v in result.items()
                        if k not in {"passed", "score", "explanation"}}
            evidence.setdefault("source", self._name)
            return VerificationCheck(
                name=self._name, verifier=self.verifier_type, passed=passed,
                score=max(0.0, min(1.0, score)), evidence=evidence, explanation=explanation,
            )
        passed = bool(result)
        return VerificationCheck(
            name=self._name, verifier=self.verifier_type, passed=passed,
            score=1.0 if passed else 0.0, evidence={"result": passed, "source": self._name},
            explanation="External verification " + ("passed." if passed else "failed."),
        )


__all__ = ["ExternalAPIVerifier", "ExternalChecker"]
