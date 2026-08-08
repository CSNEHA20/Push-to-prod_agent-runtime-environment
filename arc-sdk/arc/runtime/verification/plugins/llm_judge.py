"""LLM-as-a-Judge verification.

Grades the response with a language model against a rubric. To stay
provider-independent, the actual model call is a caller-supplied ``judge``
callable — ARC never hardcodes a judge model or vendor. The judge receives the
response text, the rubric, and the neutral context, and returns a
:class:`JudgeVerdict` (or a compatible mapping).

Build a judge from any provider; an Anthropic-backed helper lives in
``arc.integrations.anthropic`` so the core stays neutral.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Union

from pydantic import BaseModel, Field

from .. import VerificationCheck, VerificationContext


class JudgeVerdict(BaseModel):
    """Structured verdict returned by a judge callable."""

    score: float = Field(..., ge=0.0, le=1.0)
    passed: Optional[bool] = None
    explanation: str = ""
    evidence: Dict[str, Any] = Field(default_factory=dict)


#: A judge: (response_text, rubric, context) -> verdict (model or mapping).
Judge = Callable[[str, str, VerificationContext], Union[JudgeVerdict, Dict[str, Any], float]]


class LLMJudgeVerifier:
    """Delegates grading to an injected, provider-independent judge callable."""

    verifier_type = "llm_judge"

    def __init__(
        self,
        judge: Judge,
        *,
        rubric: str = "Is the response correct, relevant, and complete?",
        pass_threshold: float = 0.5,
        name: str = "llm_judge",
    ) -> None:
        self._judge = judge
        self._rubric = rubric
        self._pass_threshold = pass_threshold
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def applies(self, context: VerificationContext) -> bool:
        return bool(context.output_text)

    def verify(self, context: VerificationContext) -> VerificationCheck:
        raw = self._judge(context.output_text, self._rubric, context)
        verdict = self._coerce(raw)
        passed = (
            verdict.passed
            if verdict.passed is not None
            else verdict.score >= self._pass_threshold
        )
        evidence = {"rubric": self._rubric, "score": verdict.score, **verdict.evidence}
        return VerificationCheck(
            name=self._name, verifier=self.verifier_type, passed=passed,
            score=verdict.score, evidence=evidence,
            explanation=verdict.explanation or f"Judge score {verdict.score:.2f}.",
        )

    @staticmethod
    def _coerce(raw: Any) -> JudgeVerdict:
        if isinstance(raw, JudgeVerdict):
            return raw
        if isinstance(raw, dict):
            return JudgeVerdict.model_validate(raw)
        return JudgeVerdict(score=float(raw))


__all__ = ["LLMJudgeVerifier", "JudgeVerdict", "Judge"]
