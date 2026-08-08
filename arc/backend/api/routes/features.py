import uuid
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from db.database import get_db
    from models.session import AgentSession
    from core.flight_recorder import FlightRecorder
    from core.arc_predict import FailurePredictor
    from core.arc_score import ARCScoreCalculator
    from core.arc_diff import SessionDiffer
    from core.arc_lens import ARCLensEngine
except ImportError:
    from arc.backend.db.database import get_db
    from arc.backend.models.session import AgentSession
    from arc.backend.core.flight_recorder import FlightRecorder
    from arc.backend.core.arc_predict import FailurePredictor
    from arc.backend.core.arc_score import ARCScoreCalculator
    from arc.backend.core.arc_diff import SessionDiffer
    from arc.backend.core.arc_lens import ARCLensEngine

logger = logging.getLogger("arc.api.features")

router = APIRouter(prefix="/api/sessions", tags=["wow_features"])

predictor = FailurePredictor()
score_calculator = ARCScoreCalculator()
differ = SessionDiffer()
lens_engine = ARCLensEngine()


async def _get_session_dict(session_id: uuid.UUID, db: AsyncSession) -> Dict[str, Any]:
    recorder = FlightRecorder(db_session=db)
    session = await recorder.get_session(session_id)
    if not session:
        # Fallback dummy session if DB doesn't have it yet for real-time memory sessions
        return {
            "session_id": str(session_id),
            "agent_name": "DemoAgent",
            "task": "Interactive Agent Task",
            "status": "running",
            "steps": [],
            "context_stats": {"avg_relevance": 0.88, "rejected_ratio": 0.12}
        }
    
    steps = await recorder.get_trace(session_id)
    steps_list = []
    for s in steps:
        steps_list.append({
            "step_number": getattr(s, "step_number", 1),
            "decision": getattr(s, "decision", "Call LLM"),
            "confidence": getattr(s, "confidence", 0.9),
            "status": getattr(s, "status", "success"),
            "output": getattr(s, "output", ""),
            "error": getattr(s, "error", None)
        })

    return {
        "session_id": str(session.session_id),
        "agent_name": session.agent_name,
        "task": session.task,
        "status": session.status,
        "recovered": getattr(session, "has_recovered", False),
        "steps": steps_list,
        "context_stats": {"avg_relevance": 0.88, "rejected_ratio": 0.12}
    }


@router.post("/{session_id}/lens")
async def ask_arc_lens(
    session_id: uuid.UUID,
    payload: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    ARC Lens - Natural Language Agent Debugging.
    Parses execution trace and answers user's natural language question.
    """
    question = payload.get("question", "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question prompt is required.")

    session_dict = await _get_session_dict(session_id, db)
    res = await lens_engine.ask_lens(session_dict, question)
    return res


@router.get("/{session_id}/predict")
async def predict_failure(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    ARC Predict - Failure prediction before it happens.
    Evaluates confidence trends, context decay, and tool errors.
    """
    session_dict = await _get_session_dict(session_id, db)
    steps = session_dict.get("steps", [])
    prediction = predictor.predict_failure(steps, session_dict.get("context_stats"))
    return prediction


@router.get("/diff/compare")
async def compare_sessions(
    session_a: uuid.UUID = Query(..., description="First session ID"),
    session_b: uuid.UUID = Query(..., description="Second session ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    ARC Diff - Side-by-side run trace comparison & divergence detection.
    """
    dict_a = await _get_session_dict(session_a, db)
    dict_b = await _get_session_dict(session_b, db)
    result = differ.compare_sessions(dict_a, dict_b)
    return result


@router.get("/{session_id}/score")
async def get_arc_score(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    ARC Score - Composite 0 to 100 agent quality rating.
    """
    session_dict = await _get_session_dict(session_id, db)
    score_res = score_calculator.calculate_score(session_dict)
    return score_res
