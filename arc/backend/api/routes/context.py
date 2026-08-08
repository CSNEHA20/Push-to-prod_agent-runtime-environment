import uuid
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, case
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from models.session import AgentSession
from models.context import ContextConflict, ContextLog
from api.schemas import (
    ContextLogResponse,
    ConflictResponse,
    ConflictSummaryResponse,
    ProvenanceResponse,
)

logger = logging.getLogger("arc.api.context")

router = APIRouter(prefix="/api/context", tags=["context"])


@router.get(
    "/{session_id}/log",
    response_model=List[ContextLogResponse],
    status_code=status.HTTP_200_OK,
)
async def get_context_log(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all context filtering decisions (logs) for a session.
    """
    try:
        session = await db.get(AgentSession, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with ID '{session_id}' not found.",
            )

        stmt = (
            select(ContextLog)
            .where(ContextLog.session_id == session_id)
            .order_by(ContextLog.step_number.asc())
        )
        result = await db.execute(stmt)
        logs = list(result.scalars().all())
        return logs
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching context log for session {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve context logs.",
        )


@router.get(
    "/{session_id}/conflicts",
    response_model=ConflictSummaryResponse,
    status_code=status.HTTP_200_OK,
)
async def get_context_conflicts(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all conflicts detected for a session, ordered by severity (critical first).
    Includes summary stats for conflicts by severity and by type.
    """
    try:
        session = await db.get(AgentSession, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with ID '{session_id}' not found.",
            )

        severity_order = case(
            (ContextConflict.severity == "critical", 1),
            (ContextConflict.severity == "high", 2),
            (ContextConflict.severity == "medium", 3),
            (ContextConflict.severity == "low", 4),
            else_=5,
        )

        stmt = (
            select(ContextConflict)
            .where(ContextConflict.session_id == session_id)
            .order_by(severity_order, ContextConflict.detected_at.desc())
        )
        result = await db.execute(stmt)
        conflicts = list(result.scalars().all())

        total_conflicts = len(conflicts)
        by_severity: Dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        by_type: Dict[str, int] = {"numerical": 0, "temporal": 0, "factual": 0, "logical": 0}

        for c in conflicts:
            sev = (c.severity or "medium").lower()
            if sev in by_severity:
                by_severity[sev] += 1
            else:
                by_severity[sev] = 1

            ctype = (c.conflict_type or "factual").lower()
            if ctype in by_type:
                by_type[ctype] += 1
            else:
                by_type[ctype] = 1

        conflict_responses = [
            ConflictResponse.model_validate(c) for c in conflicts
        ]

        return ConflictSummaryResponse(
            total_conflicts=total_conflicts,
            by_severity=by_severity,
            by_type=by_type,
            conflicts=conflict_responses,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching context conflicts for session {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve context conflicts.",
        )


@router.get(
    "/{session_id}/provenance",
    response_model=List[ProvenanceResponse],
    status_code=status.HTTP_200_OK,
)
async def get_context_provenance(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get the provenance map for a session aggregated across all context filtering steps.
    """
    try:
        session = await db.get(AgentSession, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with ID '{session_id}' not found.",
            )

        stmt = (
            select(ContextLog)
            .where(ContextLog.session_id == session_id)
            .order_by(ContextLog.step_number.asc())
        )
        result = await db.execute(stmt)
        logs = list(result.scalars().all())

        sources_map: Dict[str, Dict[str, Any]] = {}
        for log in logs:
            if log.provenance_map and isinstance(log.provenance_map, dict):
                for source_name, confidence in log.provenance_map.items():
                    if source_name not in sources_map:
                        sources_map[source_name] = {
                            "confidence_sum": 0.0,
                            "count": 0,
                            "chunks_used": 0,
                            "chunks_rejected": 0,
                        }
                    sources_map[source_name]["confidence_sum"] += float(confidence)
                    sources_map[source_name]["count"] += 1
                    sources_map[source_name]["chunks_used"] += 1

        provenance_list = []
        for source_name, data in sources_map.items():
            avg_confidence = (
                round(data["confidence_sum"] / data["count"], 2)
                if data["count"] > 0
                else 0.0
            )
            provenance_list.append(
                ProvenanceResponse(
                    source_name=source_name,
                    confidence=avg_confidence,
                    chunks_used=data["chunks_used"],
                    chunks_rejected=data["chunks_rejected"],
                )
            )

        return provenance_list
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching context provenance for session {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve context provenance map.",
        )
