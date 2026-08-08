"""Response integrity verifier (default, always applicable).

Structural completeness checks grounded in facts about the response, not its
wording: is there content at all, did the model refuse, was the output
truncated. This is what gives an out-of-the-box ``ARC(client)`` a real,
evidence-based confidence signal without any developer configuration.
"""

from __future__ import annotations

from .. import VerificationCheck, VerificationContext

#: stop_reasons that indicate the response is not a clean completion.
_REFUSAL = "refusal"
_TRUNCATED = {"max_tokens", "model_context_window_exceeded"}


class ResponseIntegrityVerifier:
    """Verifies the response is present and cleanly terminated."""

    verifier_type = "integrity"

    @property
    def name(self) -> str:
        return "response_integrity"

    def applies(self, context: VerificationContext) -> bool:
        return True

    def verify(self, context: VerificationContext) -> VerificationCheck:
        text = context.output_text or ""
        has_text = bool(text.strip())
        has_tools = bool(context.tool_calls)
        stop = context.stop_reason
        evidence = {
            "output_length": len(text),
            "has_tool_calls": has_tools,
            "stop_reason": stop,
        }

        if stop == _REFUSAL:
            return VerificationCheck(
                name=self.name, verifier=self.verifier_type,
                passed=False, score=0.0, evidence=evidence,
                explanation="Model refused the request (stop_reason=refusal).",
            )
        if not has_text and not has_tools:
            return VerificationCheck(
                name=self.name, verifier=self.verifier_type,
                passed=False, score=0.0, evidence=evidence,
                explanation="Response is empty (no text and no tool calls).",
            )
        if stop in _TRUNCATED:
            return VerificationCheck(
                name=self.name, verifier=self.verifier_type,
                passed=True, score=0.6, required=False, evidence=evidence,
                explanation=f"Response was truncated (stop_reason={stop}).",
            )
        return VerificationCheck(
            name=self.name, verifier=self.verifier_type,
            passed=True, score=1.0, evidence=evidence,
            explanation="Response present and cleanly terminated.",
        )


__all__ = ["ResponseIntegrityVerifier"]
