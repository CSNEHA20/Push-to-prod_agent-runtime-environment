import uuid
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from db.database import get_db
    from models.session import AgentSession
    from core.recovery_engine import RecoveryEngine
    from api.schemas import (
        CheckpointResponse,
        FailureEventResponse,
        RecoveryStatusResponse,
    )
except ImportError:
    from arc.backend.db.database import get_db
    from arc.backend.models.session import AgentSession
    from arc.backend.core.recovery_engine import RecoveryEngine
    from arc.backend.api.schemas import (
        CheckpointResponse,
        FailureEventResponse,
        RecoveryStatusResponse,
    )

logger = logging.getLogger("arc.api.recovery")

router = APIRouter(prefix="/api/recovery", tags=["recovery"])


@router.get(
    "/{session_id}/checkpoints",
    response_model=List[CheckpointResponse],
    status_code=status.HTTP_200_OK,
)
async def get_checkpoints(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all checkpoints for a session, ordered by step_number ascending.
    """
    try:
        session = await db.get(AgentSession, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with ID '{session_id}' not found.",
            )

        engine = RecoveryEngine(db_session=db)
        checkpoints = await engine.get_checkpoints(session_id)
        return checkpoints
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching checkpoints for session {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve checkpoints.",
        )


@router.get(
    "/{session_id}/failures",
    response_model=List[FailureEventResponse],
    status_code=status.HTTP_200_OK,
)
async def get_failures(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all failure events for a session.
    """
    try:
        session = await db.get(AgentSession, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with ID '{session_id}' not found.",
            )

        engine = RecoveryEngine(db_session=db)
        failures = await engine.get_failures(session_id)
        return failures
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching failures for session {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve failure events.",
        )


@router.get(
    "/{session_id}/status",
    response_model=RecoveryStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_recovery_status(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get recovery status summary for a session.
    """
    try:
        session = await db.get(AgentSession, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with ID '{session_id}' not found.",
            )

        engine = RecoveryEngine(db_session=db)
        checkpoints = await engine.get_checkpoints(session_id)
        failures = await engine.get_failures(session_id)

        total_checkpoints = len(checkpoints)
        valid_checkpoints = sum(1 for c in checkpoints if c.is_valid)
        total_failures = len(failures)
        recoveries_attempted = sum(1 for f in failures if f.recovery_attempted)
        recoveries_successful = sum(1 for f in failures if f.recovery_success)

        last_checkpoint_step = (
            max((c.step_number for c in checkpoints), default=None)
            if checkpoints
            else None
        )
        last_failure_step = (
            max((f.step_number for f in failures), default=None)
            if failures
            else None
        )

        if total_failures == 0:
            overall_health = "healthy"
        elif recoveries_successful == total_failures:
            overall_health = "degraded"
        else:
            overall_health = "failed"

        return RecoveryStatusResponse(
            total_checkpoints=total_checkpoints,
            valid_checkpoints=valid_checkpoints,
            total_failures=total_failures,
            recoveries_attempted=recoveries_attempted,
            recoveries_successful=recoveries_successful,
            last_checkpoint_step=last_checkpoint_step,
            last_failure_step=last_failure_step,
            overall_health=overall_health,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching recovery status for session {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recovery status.",
        )
