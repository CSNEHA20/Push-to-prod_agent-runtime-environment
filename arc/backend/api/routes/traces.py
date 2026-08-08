import uuid
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from db.database import get_db
    from models.session import AgentSession
    from models.trace import TraceStep
    from core.flight_recorder import FlightRecorder
    from api.schemas import TraceStepResponse, ReplayResponse
except ImportError:
    from arc.backend.db.database import get_db
    from arc.backend.models.session import AgentSession
    from arc.backend.models.trace import TraceStep
    from arc.backend.core.flight_recorder import FlightRecorder
    from arc.backend.api.schemas import TraceStepResponse, ReplayResponse

logger = logging.getLogger("arc.api.traces")

router = APIRouter(prefix="/api/sessions", tags=["traces"])


@router.get("/{session_id}/trace", response_model=List[TraceStepResponse], status_code=status.HTTP_200_OK)
async def get_session_trace(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all trace steps for a session ordered by step_number ascending.
    """
    try:
        recorder = FlightRecorder(db_session=db)
        session = await recorder.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with ID '{session_id}' not found.",
            )

        steps = await recorder.get_trace(session_id)
        return steps
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching trace for session {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve trace steps.",
        )


@router.get("/{session_id}/replay", response_model=ReplayResponse, status_code=status.HTTP_200_OK)
async def get_session_replay(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get full replay object containing session metadata, ordered steps, failure_point, and recovery_point.
    """
    try:
        recorder = FlightRecorder(db_session=db)
        session = await recorder.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with ID '{session_id}' not found.",
            )

        replay_data = await recorder.get_replay(session_id)
        return ReplayResponse(
            session=replay_data["session"],
            steps=replay_data["steps"],
            failure_point=replay_data.get("failure_point"),
            recovery_point=replay_data.get("recovery_point"),
            metadata={
                "total_steps": len(replay_data.get("steps", [])),
                "status": session.status,
                "agent_name": session.agent_name,
                "task": session.task,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating replay for session {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve replay object.",
        )


@router.get("/{session_id}/trace/step/{step_number}", response_model=TraceStepResponse, status_code=status.HTTP_200_OK)
async def get_trace_step(
    session_id: uuid.UUID,
    step_number: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific trace step by step number for a session.
    """
    try:
        # First verify session exists
        session = await db.get(AgentSession, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with ID '{session_id}' not found.",
            )

        stmt = select(TraceStep).where(
            TraceStep.session_id == session_id,
            TraceStep.step_number == step_number,
        )
        result = await db.execute(stmt)
        step = result.scalar_one_or_none()

        if not step:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trace step {step_number} not found for session '{session_id}'.",
            )
        return step
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error fetching step {step_number} for session {session_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve trace step.",
        )
