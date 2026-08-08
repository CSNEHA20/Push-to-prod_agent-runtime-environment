"""Verification Engine — evidence-based confidence.

Confidence in ARC is derived from **verification results**, never from response
wording. A request's response is turned into a provider-independent
:class:`VerificationContext`; a set of pluggable :class:`Verifier`\\ s each
produce a :class:`VerificationCheck` carrying a structured ``evidence`` payload
and a human ``explanation``; the :class:`VerificationEngine` aggregates those
checks into a :class:`VerificationReport` whose ``confidence`` is a weighted
function of the checks that ran.

The interface is provider-independent: verifiers see only the neutral
:class:`VerificationContext` (text, tool calls, stop reason, token usage, the
opaque raw output, and the request payload), never an Anthropic-specific object.
The runtime is responsible for building the context from whatever provider it
wraps.

Built-in plugin types (see :mod:`arc.runtime.verification.plugins`):

* :class:`ResponseIntegrityVerifier` — structural completeness (default)
* :class:`JSONSchemaVerifier` — JSON Schema validation
* :class:`PydanticVerifier` — Pydantic model validation
* :class:`ToolOutputVerifier` — tool-call verification
* :class:`ExternalAPIVerifier` — external/HTTP verification
* :class:`LLMJudgeVerifier` — LLM-as-a-Judge (judge injected; provider-neutral)
* :class:`AssertionVerifier` — assertion/predicate verification
* :class:`ExecutionVerifier` — execution / runtime verification
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

#: Confidence used when a response cannot be verified (e.g. an un-observed
#: streamed iterator). It is recorded alongside ``verified=False`` so consumers
#: can tell "not checked" apart from "checked and passed".
UNVERIFIED_CONFIDENCE = 1.0


@dataclass
class VerificationContext:
    """Provider-independent view of a response to be verified.

    The runtime builds this from the wrapped provider's response; verifiers only
    ever see this neutral shape.
    """

    output_text: str = ""
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    stop_reason: Optional[str] = None
    token_usage: Dict[str, int] = field(default_factory=dict)
    raw_output: Any = None
    request_payload: Dict[str, Any] = field(default_factory=dict)
    plan: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class VerificationCheck(BaseModel):
    """The structured result of a single verifier."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    name: str = Field(..., description="Human-readable check name")
    verifier: str = Field(..., description="Verifier type slug, e.g. 'json_schema'")
    passed: bool = Field(..., description="Whether the check passed")
    score: float = Field(..., ge=0.0, le=1.0, description="Check score in [0,1]")
    weight: float = Field(default=1.0, ge=0.0, description="Aggregation weight")
    required: bool = Field(default=True, description="A failed required check fails the report")
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Structured evidence")
    explanation: str = Field(default="", description="Why the check reached its verdict")
    error: Optional[str] = Field(default=None, description="Verifier error, if any")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class VerificationReport(BaseModel):
    """Aggregate verification outcome for one response."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    checks: List[VerificationCheck] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0, description="Evidence-derived confidence")
    passed: bool = Field(..., description="All required checks passed")
    verified: bool = Field(..., description="At least one verifier actually ran")
    explanation: str = Field(default="", description="Aggregate explanation")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    def failed_checks(self) -> List[VerificationCheck]:
        return [c for c in self.checks if not c.passed]


@runtime_checkable
class Verifier(Protocol):
    """A verification plugin.

    Implementations MUST be provider-independent — they read only the neutral
    :class:`VerificationContext`.
    """

    #: Stable slug identifying the verifier type (e.g. ``"assertion"``).
    verifier_type: str

    @property
    def name(self) -> str:
        """Human-readable name for the check this verifier produces."""
        ...

    def applies(self, context: VerificationContext) -> bool:
        """Whether this verifier should run for ``context``."""
        ...

    def verify(self, context: VerificationContext) -> VerificationCheck:
        """Run the verification and return a structured check."""
        ...


@runtime_checkable
class VerificationEngine(Protocol):
    """Aggregates verifier checks into an evidence-based report."""

    def register(self, verifier: Verifier) -> None:
        """Add a verifier plugin."""
        ...

    def verify(self, context: VerificationContext) -> VerificationReport:
        """Run all applicable verifiers and aggregate the result."""
        ...


__all__ = [
    "UNVERIFIED_CONFIDENCE",
    "VerificationContext",
    "VerificationCheck",
    "VerificationReport",
    "Verifier",
    "VerificationEngine",
]
