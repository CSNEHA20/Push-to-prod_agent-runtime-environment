"""JSON Schema verification.

Parses the response text as JSON and validates it against a JSON Schema. Uses
the ``jsonschema`` package when installed (full Draft support); otherwise falls
back to a minimal structural validator covering ``type``, ``required`` and
``properties`` — enough for the common object-shape case without a hard
dependency.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from .. import VerificationCheck, VerificationContext


def _minimal_validate(instance: Any, schema: Dict[str, Any], path: str = "$") -> List[str]:
    """Best-effort validator used when ``jsonschema`` is unavailable."""
    errors: List[str] = []
    expected = schema.get("type")
    type_map = {
        "object": dict, "array": list, "string": str,
        "number": (int, float), "integer": int, "boolean": bool, "null": type(None),
    }
    if expected in type_map and not isinstance(instance, type_map[expected]):
        errors.append(f"{path}: expected {expected}, got {type(instance).__name__}")
        return errors
    if expected == "object" and isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                errors.append(f"{path}: missing required property '{key}'")
        for key, subschema in (schema.get("properties") or {}).items():
            if key in instance and isinstance(subschema, dict):
                errors.extend(_minimal_validate(instance[key], subschema, f"{path}.{key}"))
    if expected == "array" and isinstance(instance, list):
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for i, item in enumerate(instance):
                errors.extend(_minimal_validate(item, item_schema, f"{path}[{i}]"))
    return errors


class JSONSchemaVerifier:
    """Validates the JSON response body against a JSON Schema."""

    verifier_type = "json_schema"

    def __init__(self, schema: Dict[str, Any], *, name: str = "json_schema") -> None:
        self._schema = schema
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def applies(self, context: VerificationContext) -> bool:
        return bool(context.output_text)

    def verify(self, context: VerificationContext) -> VerificationCheck:
        try:
            instance = json.loads(context.output_text)
        except (ValueError, TypeError) as exc:
            return self._fail(f"Response is not valid JSON: {exc}", {"parse_error": str(exc)})

        errors = self._validate(instance)
        if errors:
            return self._fail(
                f"JSON does not satisfy the schema ({len(errors)} error(s)).",
                {"errors": errors, "instance_keys": self._keys(instance)},
            )
        return VerificationCheck(
            name=self._name, verifier=self.verifier_type, passed=True, score=1.0,
            evidence={"errors": [], "instance_keys": self._keys(instance)},
            explanation="Response JSON satisfies the schema.",
        )

    # -- internals --------------------------------------------------------

    def _validate(self, instance: Any) -> List[str]:
        try:
            import jsonschema  # type: ignore

            validator = jsonschema.Draft202012Validator(self._schema)
            return [e.message for e in validator.iter_errors(instance)]
        except ImportError:
            return _minimal_validate(instance, self._schema)

    @staticmethod
    def _keys(instance: Any) -> Optional[List[str]]:
        return sorted(instance.keys()) if isinstance(instance, dict) else None

    def _fail(self, explanation: str, evidence: Dict[str, Any]) -> VerificationCheck:
        return VerificationCheck(
            name=self._name, verifier=self.verifier_type, passed=False, score=0.0,
            evidence=evidence, explanation=explanation,
        )


__all__ = ["JSONSchemaVerifier"]
