"""Built-in verification plugins.

Each plugin implements the :class:`arc.runtime.verification.Verifier` interface,
producing a :class:`~arc.runtime.verification.VerificationCheck` with structured
evidence and an explanation.
"""

from __future__ import annotations

from .assertion import AssertionVerifier
from .execution import ExecutionResult, ExecutionVerifier
from .external_api import ExternalAPIVerifier
from .integrity import ResponseIntegrityVerifier
from .json_schema import JSONSchemaVerifier
from .llm_judge import JudgeVerdict, LLMJudgeVerifier
from .pydantic import PydanticVerifier
from .tool_output import ToolOutputVerifier

__all__ = [
    "ResponseIntegrityVerifier",
    "JSONSchemaVerifier",
    "PydanticVerifier",
    "ToolOutputVerifier",
    "ExternalAPIVerifier",
    "LLMJudgeVerifier",
    "JudgeVerdict",
    "AssertionVerifier",
    "ExecutionVerifier",
    "ExecutionResult",
]
