import pytest
from core.arc_predict import FailurePredictor
from core.arc_score import ARCScoreCalculator
from core.arc_diff import SessionDiffer
from core.arc_lens import ARCLensEngine

def test_failure_predictor():
    predictor = FailurePredictor(risk_threshold=60.0)
    
    # Stable steps
    stable_steps = [
        {"confidence": 0.95, "status": "success"},
        {"confidence": 0.92, "status": "success"}
    ]
    res_stable = predictor.predict_failure(stable_steps)
    assert res_stable["will_fail"] is False
    assert res_stable["risk_percent"] < 60.0

    # Declining confidence + error steps
    failing_steps = [
        {"confidence": 0.90, "status": "success"},
        {"confidence": 0.55, "status": "failed", "output": "DatabaseError: timeout"}
    ]
    res_failing = predictor.predict_failure(failing_steps, {"rejected_ratio": 0.5, "avg_relevance": 0.5})
    assert res_failing["will_fail"] is True
    assert res_failing["risk_percent"] >= 60.0


def test_arc_score_calculator():
    calculator = ARCScoreCalculator()
    session_data = {
        "status": "completed",
        "recovered": True,
        "steps": [
            {"status": "success", "confidence": 0.92},
            {"status": "failed", "confidence": 0.35},
            {"status": "recovered", "confidence": 0.96}
        ],
        "context_stats": {"avg_relevance": 0.88, "rejected_ratio": 0.10}
    }
    score_res = calculator.calculate_score(session_data)
    assert 0 <= score_res["overall"] <= 100
    assert "metrics" in score_res
    assert score_res["metrics"]["recovery"] == 95.0


def test_session_differ():
    differ = SessionDiffer()
    session_a = {
        "session_id": "run-1",
        "steps": [
            {"confidence": 0.90, "decision": "Search DB", "context": "doc1"},
            {"confidence": 0.50, "decision": "Wrong choice", "context": "bad_doc"}
        ]
    }
    session_b = {
        "session_id": "run-2",
        "steps": [
            {"confidence": 0.90, "decision": "Search DB", "context": "doc1"},
            {"confidence": 0.95, "decision": "Correct choice", "context": "verified_doc"}
        ]
    }
    diff_res = differ.compare_sessions(session_a, session_b)
    assert diff_res["divergence_step_index"] == 2
    assert len(diff_res["aligned_steps"]) == 2


@pytest.mark.asyncio
async def test_arc_lens_engine():
    lens = ARCLensEngine()
    session = {
        "session_id": "test-session",
        "status": "recovered",
        "steps": [
            {"step_number": 1, "decision": "Fetch Data", "confidence": 0.90},
            {"step_number": 2, "decision": "SQL Query", "status": "failed", "error": "Database error"}
        ]
    }
    ans = await lens.ask_lens(session, "Why did the step fail?")
    assert "answer" in ans
    assert ans["question"] == "Why did the step fail?"
    assert 2 in ans["referenced_steps"]
