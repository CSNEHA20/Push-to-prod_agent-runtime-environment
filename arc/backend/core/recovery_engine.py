import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Union, Tuple
from contextlib import asynccontextmanager

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from db.database import AsyncSessionLocal
    from db.redis_client import get_redis
    from models.checkpoint import Checkpoint, FailureEvent
    from api.websocket import publish_event
except ImportError:
    from arc.backend.db.database import AsyncSessionLocal
    from arc.backend.db.redis_client import get_redis
    from arc.backend.models.checkpoint import Checkpoint, FailureEvent
    from arc.backend.api.websocket import publish_event

logger = logging.getLogger("arc.recovery_engine")


class RecoveryEngine:
    """
    Engine 3: Recovery Engine
    Checkpoint-based agent recovery.
    Validates checkpoints, detects failures, restores agent state,
    and publishes WebSocket events on recovery.
    """

    def __init__(self, db_session: Optional[AsyncSession] = None):
        self._db_session = db_session

    @asynccontextmanager
    async def _get_db(self, session: Optional[AsyncSession] = None):
        """Helper async context manager to acquire an AsyncSession."""
        if session is not None:
            yield session
        elif self._db_session is not None:
            yield self._db_session
        else:
            async with AsyncSessionLocal() as db:
                yield db

    @staticmethod
    def _parse_uuid(session_id: Union[uuid.UUID, str]) -> uuid.UUID:
        """Helper to ensure session_id is a valid UUID object."""
        if isinstance(session_id, uuid.UUID):
            return session_id
        try:
            return uuid.UUID(str(session_id))
        except ValueError as e:
            logger.error(f"Invalid session_id format: {session_id}")
            raise ValueError(f"Invalid UUID string for session_id: '{session_id}'") from e

    async def checkpoint(
        self,
        session_id: Union[uuid.UUID, str],
        step_number: int,
        agent_state: Any,
        messages_history: List[Any],
        context_snapshot: Optional[Any] = None,
        tool_results: Optional[Any] = None,
        required_keys: Optional[List[str]] = None,
        session: Optional[AsyncSession] = None,
    ) -> Checkpoint:
        """
        Creates and stores a Checkpoint in PostgreSQL and Redis.
        Calculates validation_score and is_valid flag based on inputs.
        """
        parsed_session_id = self._parse_uuid(session_id)

        # 1. Validation logic
        validation_score = 1.0
        is_valid = True

        # Rule: messages_history empty -> score = 0.0, is_valid = False
        if not messages_history or len(messages_history) == 0:
            validation_score = 0.0
            is_valid = False
        else:
            # Rule: agent_state missing required keys -> subtract 0.2
            missing_agent_keys = False
            if not agent_state or not isinstance(agent_state, dict):
                missing_agent_keys = True
            elif required_keys:
                if any(k not in agent_state for k in required_keys):
                    missing_agent_keys = True
            elif len(agent_state) == 0:
                missing_agent_keys = True

            if missing_agent_keys:
                validation_score -= 0.2

            # Rule: context_snapshot empty -> subtract 0.1
            context_empty = False
            if context_snapshot is None:
                context_empty = True
            elif isinstance(context_snapshot, str) and len(context_snapshot.strip()) == 0:
                context_empty = True
            elif isinstance(context_snapshot, (list, dict)) and len(context_snapshot) == 0:
                context_empty = True

            if context_empty:
                validation_score -= 0.1

            validation_score = max(0.0, min(1.0, round(validation_score, 2)))
            if validation_score <= 0.0:
                is_valid = False

        # Prepare context_snapshot as string for DB column
        context_snapshot_str = None
        if context_snapshot is not None:
            if isinstance(context_snapshot, str):
                context_snapshot_str = context_snapshot
            else:
                try:
                    context_snapshot_str = json.dumps(context_snapshot)
                except Exception:
                    context_snapshot_str = str(context_snapshot)

        # 2. Save Checkpoint to PostgreSQL
        try:
            async with self._get_db(session) as db:
                checkpoint_obj = Checkpoint(
                    checkpoint_id=uuid.uuid4(),
                    session_id=parsed_session_id,
                    step_number=step_number,
                    timestamp=datetime.now(timezone.utc),
                    agent_state=agent_state,
                    messages_history=messages_history,
                    context_snapshot=context_snapshot_str,
                    tool_results=tool_results,
                    is_valid=is_valid,
                    validation_score=validation_score,
                    was_used_for_recovery=False,
                )
                db.add(checkpoint_obj)
                await db.commit()
                await db.refresh(checkpoint_obj)

                # 3. Save to Redis with key "checkpoint:{session_id}:{step_number}" with 24hr TTL
                try:
                    redis = await get_redis()
                    if redis:
                        redis_key = f"checkpoint:{parsed_session_id}:{step_number}"
                        checkpoint_data = {
                            "checkpoint_id": str(checkpoint_obj.checkpoint_id),
                            "session_id": str(parsed_session_id),
                            "step_number": step_number,
                            "timestamp": checkpoint_obj.timestamp.isoformat() if checkpoint_obj.timestamp else None,
                            "agent_state": agent_state,
                            "messages_history": messages_history,
                            "context_snapshot": context_snapshot_str,
                            "tool_results": tool_results,
                            "is_valid": is_valid,
                            "validation_score": validation_score,
                            "was_used_for_recovery": False,
                        }
                        await redis.set(redis_key, json.dumps(checkpoint_data), ex=86400)
                except Exception as redis_err:
                    logger.warning(f"Failed to cache checkpoint in Redis: {redis_err}")

                logger.info(
                    f"Created checkpoint step {step_number} for session {parsed_session_id} (valid: {is_valid}, score: {validation_score})"
                )
                return checkpoint_obj
        except Exception as e:
            logger.error(
                f"Failed to create checkpoint for session {session_id}, step {step_number}: {e}",
                exc_info=True,
            )
            raise

    async def detect_failure(
        self,
        output_text: Optional[str] = None,
        expected_type: Optional[str] = None,
        tool_success: Optional[bool] = None,
        error: Optional[Any] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Detects failure based on multiple signals:
        - error is not None -> failure_type = "api_error"
        - tool_success is False -> failure_type = "tool_error"
        - output_text is None or len < 5 -> failure_type = "empty_output"
        - expected_type == "json" and output_text is not valid JSON -> failure_type = "bad_output"
        Returns (is_failure: bool, failure_type: str | None)
        """
        if error is not None:
            return True, "api_error"

        if tool_success is False:
            return True, "tool_error"

        if output_text is None or len(str(output_text)) < 5:
            return True, "empty_output"

        if expected_type == "json":
            try:
                if not isinstance(output_text, str):
                    return True, "bad_output"
                json.loads(output_text)
            except Exception:
                return True, "bad_output"

        return False, None

    async def recover(
        self,
        session_id: Union[uuid.UUID, str],
        failed_at_step: int,
        failure_type: str,
        error_message: str,
        session: Optional[AsyncSession] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Executes agent recovery workflow:
        1. Query DB for best valid checkpoint where step_number < failed_at_step and is_valid = True.
        2. If none found, create FailureEvent in DB and return None.
        3. If found, mark was_used_for_recovery = True on checkpoint, record FailureEvent.
        4. Publish WebSocket event {type: "recovery_complete", session_id, recovered_from_step, steps_lost}.
        5. Return dict with restored checkpoint data.
        """
        parsed_session_id = self._parse_uuid(session_id)

        try:
            async with self._get_db(session) as db:
                # Find best checkpoint
                stmt = (
                    select(Checkpoint)
                    .where(
                        Checkpoint.session_id == parsed_session_id,
                        Checkpoint.step_number < failed_at_step,
                        Checkpoint.is_valid == True,
                    )
                    .order_by(Checkpoint.step_number.desc())
                    .limit(1)
                )
                result = await db.execute(stmt)
                best_checkpoint = result.scalars().first()

                if not best_checkpoint:
                    logger.warning(
                        f"No valid checkpoint found for session {parsed_session_id} prior to step {failed_at_step}"
                    )
                    failure_event = FailureEvent(
                        failure_id=uuid.uuid4(),
                        session_id=parsed_session_id,
                        step_number=failed_at_step,
                        failure_type=failure_type,
                        error_message=error_message,
                        timestamp=datetime.now(timezone.utc),
                        recovery_attempted=True,
                        recovery_checkpoint_id=None,
                        recovery_success=False,
                        steps_replayed=0,
                    )
                    db.add(failure_event)
                    await db.commit()
                    return None

                steps_lost = failed_at_step - best_checkpoint.step_number
                best_checkpoint.was_used_for_recovery = True

                failure_event = FailureEvent(
                    failure_id=uuid.uuid4(),
                    session_id=parsed_session_id,
                    step_number=failed_at_step,
                    failure_type=failure_type,
                    error_message=error_message,
                    timestamp=datetime.now(timezone.utc),
                    recovery_attempted=True,
                    recovery_checkpoint_id=best_checkpoint.checkpoint_id,
                    recovery_success=True,
                    steps_replayed=steps_lost,
                )
                db.add(failure_event)
                await db.commit()
                await db.refresh(best_checkpoint)
                await db.refresh(failure_event)

                ws_payload = {
                    "type": "recovery_complete",
                    "session_id": str(parsed_session_id),
                    "recovered_from_step": best_checkpoint.step_number,
                    "steps_lost": steps_lost,
                }
                await publish_event(
                    session_id=parsed_session_id,
                    event_type="recovery_complete",
                    data=ws_payload,
                )

                logger.info(
                    f"Recovered session {parsed_session_id} from step {best_checkpoint.step_number} (failed at step {failed_at_step}, lost {steps_lost} steps)"
                )

                return {
                    "checkpoint_id": str(best_checkpoint.checkpoint_id),
                    "session_id": str(best_checkpoint.session_id),
                    "step_number": best_checkpoint.step_number,
                    "agent_state": best_checkpoint.agent_state,
                    "messages_history": best_checkpoint.messages_history,
                    "context_snapshot": best_checkpoint.context_snapshot,
                    "tool_results": best_checkpoint.tool_results,
                    "validation_score": best_checkpoint.validation_score,
                    "is_valid": best_checkpoint.is_valid,
                    "recovered_from_step": best_checkpoint.step_number,
                    "steps_lost": steps_lost,
                    "failure_id": str(failure_event.failure_id),
                }
        except Exception as e:
            logger.error(
                f"Failed during recovery for session {session_id} at step {failed_at_step}: {e}",
                exc_info=True,
            )
            raise

    async def get_checkpoints(
        self,
        session_id: Union[uuid.UUID, str],
        session: Optional[AsyncSession] = None,
    ) -> List[Checkpoint]:
        """Returns all Checkpoints for session ordered by step_number ascending."""
        parsed_session_id = self._parse_uuid(session_id)
        try:
            async with self._get_db(session) as db:
                stmt = (
                    select(Checkpoint)
                    .where(Checkpoint.session_id == parsed_session_id)
                    .order_by(Checkpoint.step_number.asc())
                )
                result = await db.execute(stmt)
                return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Failed to get checkpoints for session {session_id}: {e}", exc_info=True)
            raise

    async def get_failures(
        self,
        session_id: Union[uuid.UUID, str],
        session: Optional[AsyncSession] = None,
    ) -> List[FailureEvent]:
        """Returns all FailureEvents for session ordered by step_number ascending."""
        parsed_session_id = self._parse_uuid(session_id)
        try:
            async with self._get_db(session) as db:
                stmt = (
                    select(FailureEvent)
                    .where(FailureEvent.session_id == parsed_session_id)
                    .order_by(FailureEvent.step_number.asc())
                )
                result = await db.execute(stmt)
                return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Failed to get failure events for session {session_id}: {e}", exc_info=True)
            raise
