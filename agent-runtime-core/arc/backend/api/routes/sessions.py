import uuid
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from db.database import get_db
    from models.session import AgentSession
    from api.schemas import AgentSessionResponse, DeleteSessionResponse
except ImportError:
    from arc.backend.db.database import get_db
    from arc.backend.models.session import AgentSession
    from arc.backend.api.schemas import AgentSessionResponse, DeleteSessionResponse

logger = logging.getLogger("arc.api.sessions")

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("", response_model=List[AgentSessionResponse], status_code=status.HTTP_200_OK)
async def list_sessions(
    limit: int = Query(default=50, ge=1, le=100, description="Max sessions to return"),
    db: AsyncSession = Depends(get_db),
):
    """
    List all agent sessions ordered by started_at descending (limit: 50 by default).
    """
    try:
        stmt = (
            select(AgentSession)
            .order_by(AgentSession.started_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        sessions = list(result.scalars().all())
        return sessions
    except Exception as e:
        logger.error(f"Error listing sessions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sessions.",
        )


@router.get("/{session_id}", response_model=AgentSessionResponse, status_code=status.HTTP_200_OK)
async def get_session_details(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed information for a specific agent session.
    """
    try:
        session = await db.get(AgentSession, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with ID '{session_id}' not found.",
            )
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session details.",
        )


@router.delete("/{session_id}", response_model=DeleteSessionResponse, status_code=status.HTTP_200_OK)
async def delete_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete an agent session and all associated trace steps/checkpoints.
    """
    try:
        session = await db.get(AgentSession, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with ID '{session_id}' not found.",
            )

        await db.delete(session)
        await db.commit()
        logger.info(f"Successfully deleted session {session_id} and all related records")
        return DeleteSessionResponse(
            message="Session and all associated traces deleted successfully.",
            session_id=session_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session.",
        )
