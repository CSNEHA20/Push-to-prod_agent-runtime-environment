"""Execution / runtime verification.

Verifies a response by *running* something and inspecting the result — the
canonical case being "the model produced code; does it execute / pass tests?".
The actual execution is a caller-supplied ``runner`` (sandboxing and language
are the caller's concern), which receives the neutral context and returns an
:class:`ExecutionResult` or a compatible mapping.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Union

from pydantic import BaseModel, Field

from .. import VerificationCheck, VerificationContext


class ExecutionResult(BaseModel):
    """Structured result of an execution attempt."""

    passed: bool
    return_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    score: Optional[float] = None
    explanation: str = ""
    evidence: Dict[str, Any] = Field(default_factory=dict)


#: A runner: given the context, execute and report a result.
Runner = Callable[[VerificationContext], Union[ExecutionResult, Dict[str, Any], bool]]


class ExecutionVerifier:
    """Runs the response through an executor and verifies the outcome."""

    verifier_type = "execution"

    def __init__(self, runner: Runner, *, name: str = "execution") -> None:
        self._runner = runner
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def applies(self, context: VerificationContext) -> bool:
        return True

    def verify(self, context: VerificationContext) -> VerificationCheck:
        result = self._coerce(self._runner(context))
        score = result.score if result.score is not None else (1.0 if result.passed else 0.0)
        evidence = {
            "return_code": result.return_code,
            "stdout": result.stdout[-2000:],
            "stderr": result.stderr[-2000:],
            **result.evidence,
        }
        return VerificationCheck(
            name=self._name, verifier=self.verifier_type, passed=result.passed,
            score=max(0.0, min(1.0, score)), evidence=evidence,
            explanation=result.explanation
            or ("Execution succeeded." if result.passed else "Execution failed."),
        )

    @staticmethod
    def _coerce(raw: Any) -> ExecutionResult:
        if isinstance(raw, ExecutionResult):
            return raw
        if isinstance(raw, dict):
            return ExecutionResult.model_validate(raw)
        return ExecutionResult(passed=bool(raw))


__all__ = ["ExecutionVerifier", "ExecutionResult", "Runner"]
