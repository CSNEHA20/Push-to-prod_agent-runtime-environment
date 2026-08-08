"""Pydantic model verification.

Validates the response body against a Pydantic ``BaseModel`` subclass. Accepts
either a JSON string response or an already-parsed dict (e.g. structured
output). Structured, field-level errors are surfaced as evidence.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Type

from pydantic import BaseModel, ValidationError

from .. import VerificationCheck, VerificationContext


class PydanticVerifier:
    """Validates the response against a Pydantic model."""

    verifier_type = "pydantic"

    def __init__(self, model: Type[BaseModel], *, name: str = "pydantic") -> None:
        self._model = model
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def applies(self, context: VerificationContext) -> bool:
        return bool(context.output_text)

    def verify(self, context: VerificationContext) -> VerificationCheck:
        try:
            data: Any = json.loads(context.output_text)
        except (ValueError, TypeError):
            data = context.output_text  # let pydantic reject a non-JSON string

        try:
            self._model.model_validate(data)
        except ValidationError as exc:
            errors = [
                {"loc": list(e["loc"]), "msg": e["msg"], "type": e["type"]}
                for e in exc.errors()
            ]
            return VerificationCheck(
                name=self._name, verifier=self.verifier_type, passed=False, score=0.0,
                evidence={"errors": errors, "error_count": len(errors)},
                explanation=f"Response failed {self._model.__name__} validation "
                f"({len(errors)} error(s)).",
            )
        return VerificationCheck(
            name=self._name, verifier=self.verifier_type, passed=True, score=1.0,
            evidence={"model": self._model.__name__, "errors": []},
            explanation=f"Response satisfies the {self._model.__name__} model.",
        )


__all__ = ["PydanticVerifier"]
