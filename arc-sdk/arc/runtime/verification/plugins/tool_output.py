"""Tool-call / tool-output verification.

Verifies the tool calls the model produced: that expected tools were called,
and/or that each call's arguments satisfy a caller-supplied validator. Operates
on the neutral ``context.tool_calls`` (``[{"name", "input"}, ...]``), so it is
provider-independent.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence

from .. import VerificationCheck, VerificationContext

#: A validator: given the list of tool calls, return True/False or an evidence dict.
ToolCallValidator = Callable[[List[Dict[str, Any]]], Any]


class ToolOutputVerifier:
    """Checks tool calls against expected tools and/or a validator."""

    verifier_type = "tool_output"

    def __init__(
        self,
        *,
        expected_tools: Optional[Sequence[str]] = None,
        validator: Optional[ToolCallValidator] = None,
        require_tool_use: bool = True,
        name: str = "tool_output",
    ) -> None:
        self._expected = list(expected_tools) if expected_tools else None
        self._validator = validator
        self._require_tool_use = require_tool_use
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def applies(self, context: VerificationContext) -> bool:
        return True

    def verify(self, context: VerificationContext) -> VerificationCheck:
        calls = context.tool_calls
        called = [c.get("name") for c in calls]
        evidence: Dict[str, Any] = {"called": called}

        if self._require_tool_use and not calls:
            return self._fail("No tool was called.", evidence)

        if self._expected is not None:
            missing = [t for t in self._expected if t not in called]
            evidence.update({"expected": self._expected, "missing": missing})
            if missing:
                return self._fail(f"Expected tool(s) not called: {missing}.", evidence)

        if self._validator is not None:
            result = self._validator(calls)
            if isinstance(result, dict):
                evidence["validator"] = result
                if not result.get("passed", True):
                    return self._fail(
                        result.get("explanation", "Tool-argument validation failed."),
                        evidence,
                    )
            elif not result:
                return self._fail("Tool-argument validation failed.", evidence)

        return VerificationCheck(
            name=self._name, verifier=self.verifier_type, passed=True, score=1.0,
            evidence=evidence, explanation="Tool calls satisfy expectations.",
        )

    def _fail(self, explanation: str, evidence: Dict[str, Any]) -> VerificationCheck:
        return VerificationCheck(
            name=self._name, verifier=self.verifier_type, passed=False, score=0.0,
            evidence=evidence, explanation=explanation,
        )


__all__ = ["ToolOutputVerifier", "ToolCallValidator"]
