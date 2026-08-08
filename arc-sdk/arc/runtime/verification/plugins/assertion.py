"""Assertion / predicate verification.

Runs a set of named predicates against the response. Each predicate takes the
:class:`VerificationContext` (or, for convenience, the response text) and
returns a bool. The score is the fraction of assertions that passed; per-
assertion outcomes are recorded as evidence.
"""

from __future__ import annotations

import inspect
from typing import Any, Callable, Dict, List, Mapping, Sequence, Tuple, Union

from .. import VerificationCheck, VerificationContext

#: A predicate over the context, or over just the response text.
Predicate = Union[Callable[[VerificationContext], bool], Callable[[str], bool]]
#: Assertions as ``{name: predicate}`` or a sequence of ``(name, predicate)``.
Assertions = Union[Mapping[str, Predicate], Sequence[Tuple[str, Predicate]]]


class AssertionVerifier:
    """Verifies the response against a set of named predicates."""

    verifier_type = "assertion"

    def __init__(
        self,
        assertions: Assertions,
        *,
        require_all: bool = True,
        name: str = "assertion",
    ) -> None:
        self._assertions: List[Tuple[str, Predicate]] = (
            list(assertions.items()) if isinstance(assertions, Mapping) else list(assertions)
        )
        self._require_all = require_all
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def applies(self, context: VerificationContext) -> bool:
        return bool(self._assertions)

    def verify(self, context: VerificationContext) -> VerificationCheck:
        results: Dict[str, Any] = {}
        passed_count = 0
        for label, predicate in self._assertions:
            try:
                ok = bool(self._call(predicate, context))
                results[label] = ok
                passed_count += int(ok)
            except Exception as exc:  # noqa: BLE001 - a bad predicate = failed assertion
                results[label] = f"error: {exc}"

        total = len(self._assertions)
        score = passed_count / total if total else 1.0
        passed = passed_count == total if self._require_all else passed_count > 0
        failed = [label for label, ok in results.items() if ok is not True]
        explanation = (
            f"{passed_count}/{total} assertions passed"
            + (f"; failed: {failed}." if failed else ".")
        )
        return VerificationCheck(
            name=self._name, verifier=self.verifier_type, passed=passed, score=score,
            evidence={"assertions": results, "passed": passed_count, "total": total},
            explanation=explanation,
        )

    @staticmethod
    def _call(predicate: Predicate, context: VerificationContext) -> bool:
        try:
            params = inspect.signature(predicate).parameters
        except (TypeError, ValueError):
            params = {}
        # A single-parameter predicate is treated as text-based for convenience.
        if len(params) == 1:
            first = next(iter(params))
            if first in {"text", "output", "response", "s"}:
                return predicate(context.output_text)  # type: ignore[arg-type]
        return predicate(context)  # type: ignore[arg-type]


__all__ = ["AssertionVerifier", "Predicate", "Assertions"]
