"""Tests for the Verification Engine — confidence from evidence, not wording."""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from arc import (
    ARC,
    AssertionVerifier,
    ExecutionResult,
    ExecutionVerifier,
    ExternalAPIVerifier,
    JSONSchemaVerifier,
    JudgeVerdict,
    LLMJudgeVerifier,
    PydanticVerifier,
    ResponseIntegrityVerifier,
    ToolOutputVerifier,
    VerificationContext,
)
from arc.runtime.verification.engine import DefaultVerificationEngine
from tests.conftest import FakeClient

SHORT = [{"role": "user", "content": "Hi"}]


def ctx(text="", **kw) -> VerificationContext:  # type: ignore[no-untyped-def]
    return VerificationContext(output_text=text, **kw)


# -- the keyword heuristic is gone ---------------------------------------


def test_heuristic_confidence_function_removed() -> None:
    with pytest.raises(ImportError):
        from arc.runtime.recorder.default import calculate_confidence_score  # noqa: F401


def test_confidence_ignores_response_wording() -> None:
    # Under the old heuristic these hedging phrases + short length scored low.
    hedgy = "I think it's probably fine, I'm not sure."
    arc = ARC(FakeClient(reply=hedgy))
    arc.messages.create(model="m", max_tokens=100, messages=SHORT)
    # Integrity only cares that the response is present and complete -> 1.0.
    assert arc.trace()[0].confidence_score == 1.0


# -- response integrity (default, structural) ----------------------------


def test_integrity_complete_response() -> None:
    check = ResponseIntegrityVerifier().verify(ctx("A full answer.", stop_reason="end_turn"))
    assert check.passed and check.score == 1.0
    assert check.evidence["output_length"] > 0
    assert check.explanation


def test_integrity_empty_response_fails() -> None:
    check = ResponseIntegrityVerifier().verify(ctx("", stop_reason="end_turn"))
    assert not check.passed and check.score == 0.0
    assert "empty" in check.explanation.lower()


def test_integrity_refusal_fails() -> None:
    check = ResponseIntegrityVerifier().verify(ctx("", stop_reason="refusal"))
    assert not check.passed
    assert "refus" in check.explanation.lower()


def test_integrity_truncation_degrades() -> None:
    check = ResponseIntegrityVerifier().verify(ctx("partial", stop_reason="max_tokens"))
    assert 0.0 < check.score < 1.0
    assert "truncat" in check.explanation.lower()


# -- structured-output verifiers -----------------------------------------


def test_json_schema_pass_and_fail() -> None:
    schema = {
        "type": "object",
        "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
        "required": ["name", "age"],
    }
    v = JSONSchemaVerifier(schema)
    ok = v.verify(ctx('{"name": "Ada", "age": 36}'))
    assert ok.passed and ok.score == 1.0 and ok.evidence["errors"] == []
    bad = v.verify(ctx('{"name": "Ada"}'))
    assert not bad.passed and bad.evidence["errors"]
    nonjson = v.verify(ctx("not json"))
    assert not nonjson.passed and "parse_error" in nonjson.evidence


def test_pydantic_verifier() -> None:
    class Contact(BaseModel):
        name: str
        email: str

    v = PydanticVerifier(Contact)
    assert v.verify(ctx('{"name": "A", "email": "a@x.com"}')).passed
    bad = v.verify(ctx('{"name": "A"}'))
    assert not bad.passed and bad.evidence["error_count"] >= 1


# -- tool / external / judge / assertion / execution ---------------------


def test_tool_output_verifier() -> None:
    v = ToolOutputVerifier(expected_tools=["get_weather"])
    passing = v.verify(ctx("", tool_calls=[{"name": "get_weather", "input": {"city": "NYC"}}]))
    assert passing.passed and passing.evidence["called"] == ["get_weather"]
    failing = v.verify(ctx("", tool_calls=[{"name": "other", "input": {}}]))
    assert not failing.passed and failing.evidence["missing"] == ["get_weather"]


def test_external_api_verifier() -> None:
    def checker(context: VerificationContext) -> dict:
        return {"passed": "yes" in context.output_text, "score": 0.9, "source_url": "http://x"}

    v = ExternalAPIVerifier(checker)
    assert v.verify(ctx("yes")).passed
    fail = v.verify(ctx("no"))
    assert not fail.passed and fail.evidence.get("source_url") == "http://x"


def test_llm_judge_verifier() -> None:
    def judge(text: str, rubric: str, context: VerificationContext) -> JudgeVerdict:
        return JudgeVerdict(score=0.8, passed=True, explanation="looks correct")

    v = LLMJudgeVerifier(judge, rubric="is it correct?")
    check = v.verify(ctx("an answer"))
    assert check.passed and check.score == 0.8
    assert check.evidence["rubric"] == "is it correct?"
    assert check.explanation == "looks correct"


def test_assertion_verifier_fraction_and_evidence() -> None:
    v = AssertionVerifier(
        {
            "nonempty": lambda text: bool(text),
            "has_price": lambda text: "$" in text,
        }
    )
    check = v.verify(ctx("costs $5"))
    assert check.passed and check.score == 1.0
    partial = v.verify(ctx("no price"))
    assert not partial.passed and partial.score == 0.5
    assert partial.evidence["assertions"]["has_price"] is False


def test_execution_verifier() -> None:
    def runner(context: VerificationContext) -> ExecutionResult:
        return ExecutionResult(passed=True, return_code=0, stdout="ok")

    check = ExecutionVerifier(runner).verify(ctx("print('ok')"))
    assert check.passed and check.score == 1.0 and check.evidence["return_code"] == 0


# -- engine aggregation --------------------------------------------------


def test_engine_weighted_confidence() -> None:
    engine = DefaultVerificationEngine(
        [
            ResponseIntegrityVerifier(),  # 1.0
            AssertionVerifier({"x": lambda text: False}),  # 0.0
        ]
    )
    report = engine.verify(ctx("hello", stop_reason="end_turn"))
    assert report.verified
    assert report.confidence == 0.5   # weighted mean of 1.0 and 0.0
    assert not report.passed          # a required check failed
    assert len(report.checks) == 2
    assert all(c.explanation for c in report.checks)  # every check explains itself


def test_engine_unverified_when_no_verifier() -> None:
    report = DefaultVerificationEngine([]).verify(ctx("anything"))
    assert not report.verified
    assert report.passed
    assert report.confidence == 1.0
    assert "not verified" in report.explanation.lower()


def test_engine_captures_verifier_exceptions() -> None:
    class Boom:
        verifier_type = "boom"
        name = "boom"

        def applies(self, context):  # type: ignore[no-untyped-def]
            return True

        def verify(self, context):  # type: ignore[no-untyped-def]
            raise RuntimeError("kaboom")

    report = DefaultVerificationEngine([Boom()]).verify(ctx("x"))
    assert not report.passed
    assert report.checks[0].error == "kaboom"


# -- provider independence + integration ---------------------------------


def test_engine_is_provider_independent() -> None:
    # No Anthropic object anywhere — just the neutral context.
    engine = DefaultVerificationEngine([JSONSchemaVerifier({"type": "object"})])
    report = engine.verify(ctx('{"ok": true}'))
    assert report.verified and report.confidence == 1.0


def test_registered_verifier_shapes_step_confidence_and_evidence() -> None:
    arc = ARC(FakeClient())
    arc.verifier(AssertionVerifier({"mentions_spaceship": lambda text: "spaceship" in text}))
    arc.messages.create(model="m", max_tokens=100, messages=SHORT)
    step = arc.trace()[0]
    # integrity(1.0) + failing assertion(0.0) -> 0.5, derived from evidence.
    assert step.confidence_score == 0.5
    verification = step.output_data["verification"]
    assert verification["verified"] is True
    names = {c["name"] for c in verification["checks"]}
    assert {"response_integrity", "assertion"} <= names
    for check in verification["checks"]:
        assert "evidence" in check and "explanation" in check


def test_verifiers_registered_at_construction() -> None:
    arc = ARC(FakeClient(), verifiers=[AssertionVerifier({"never": lambda text: False})])
    arc.messages.create(model="m", max_tokens=100, messages=SHORT)
    assert arc.trace()[0].confidence_score == 0.5
