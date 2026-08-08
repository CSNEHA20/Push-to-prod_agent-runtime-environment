import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Union
from contextlib import asynccontextmanager

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from db.database import AsyncSessionLocal
    from models.session import AgentSession
    from models.trace import TraceStep
except ImportError:
    from arc.backend.db.database import AsyncSessionLocal
    from arc.backend.models.session import AgentSession
    from arc.backend.models.trace import TraceStep

logger = logging.getLogger("arc.flight_recorder")


class FlightRecorder:
    """
    Engine 1: Flight Recorder
    Records full execution trace for Claude AI agents to DB (PostgreSQL/SQLAlchemy).
    Tracks LLM calls, tool executions, confidence scores, reasoning summaries, and replay frames.
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

    @staticmethod
    def calculate_confidence_score(response_text: Optional[str]) -> float:
        """
        Heuristic confidence scoring:
        - Start at 0.8
        - If response contains 'I think', 'probably', 'I'm not sure', 'might be' -> subtract 0.1 each
        - If response length < 50 chars -> subtract 0.2
        - Clamp between 0.1 and 1.0
        """
        score = 0.8
        if not response_text:
            score -= 0.2
            return max(0.1, min(1.0, round(score, 2)))

        text_lower = response_text.lower()
        phrases = ["i think", "probably", "i'm not sure", "might be"]
        for phrase in phrases:
            if phrase in text_lower:
                score -= 0.1

        if len(response_text) < 50:
            score -= 0.2

        return max(0.1, min(1.0, round(score, 2)))

    @staticmethod
    def generate_reasoning_summary(response_text: Optional[str]) -> str:
        """
        Generates reasoning_summary as the first 100 chars of response cleaned up.
        """
        if not response_text:
            return ""
        cleaned = " ".join(response_text.strip().split())
        return cleaned[:100]

    async def start_session(
        self,
        agent_name: str,
        task: str,
        session_id: Optional[Union[uuid.UUID, str]] = None,
        session: Optional[AsyncSession] = None,
    ) -> AgentSession:
        """
        Creates AgentSession in DB and returns session object.
        """
        parsed_id = self._parse_uuid(session_id) if session_id else uuid.uuid4()
        try:
            async with self._get_db(session) as db:
                agent_session = AgentSession(
                    session_id=parsed_id,
                    agent_name=agent_name,
                    task=task,
                    status="running",
                    total_steps=0,
                    started_at=datetime.now(timezone.utc),
                )
                db.add(agent_session)
                await db.commit()
                await db.refresh(agent_session)
                logger.info(
                    f"Started session {agent_session.session_id} for agent '{agent_name}'"
                )
                return agent_session
        except Exception as e:
            logger.error(f"Failed to start session for agent '{agent_name}': {e}", exc_info=True)
            raise

    async def record_llm_call(
        self,
        session_id: Union[uuid.UUID, str],
        step_number: int,
        messages: Any,
        response_text: str,
        input_tokens: int,
        output_tokens: int,
        duration_ms: int,
        session: Optional[AsyncSession] = None,
    ) -> TraceStep:
        """
        Creates TraceStep with step_type="llm_call", calculates confidence_score using heuristic,
        generates reasoning_summary, and saves to DB.
        """
        parsed_session_id = self._parse_uuid(session_id)
        confidence = self.calculate_confidence_score(response_text)
        reasoning_summary = self.generate_reasoning_summary(response_text)

        input_data = {
            "messages": messages,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }

        try:
            async with self._get_db(session) as db:
                trace_step = TraceStep(
                    session_id=parsed_session_id,
                    step_number=step_number,
                    step_type="llm_call",
                    duration_ms=duration_ms,
                    input_data=input_data,
                    output_data=response_text,
                    confidence_score=confidence,
                    reasoning_summary=reasoning_summary,
                    status="success",
                    timestamp=datetime.now(timezone.utc),
                )
                db.add(trace_step)

                # Update total steps in AgentSession
                agent_sess = await db.get(AgentSession, parsed_session_id)
                if agent_sess:
                    agent_sess.total_steps = max(agent_sess.total_steps or 0, step_number)

                await db.commit()
                await db.refresh(trace_step)
                logger.info(
                    f"Recorded LLM call step {step_number} for session {parsed_session_id} (confidence: {confidence})"
                )
                return trace_step
        except Exception as e:
            logger.error(
                f"Failed to record LLM call for session {session_id}, step {step_number}: {e}",
                exc_info=True,
            )
            raise

    async def record_tool_call(
        self,
        session_id: Union[uuid.UUID, str],
        step_number: int,
        tool_name: str,
        tool_input: Any,
        tool_output: Any,
        success: bool,
        duration_ms: int,
        session: Optional[AsyncSession] = None,
    ) -> TraceStep:
        """
        Creates TraceStep with step_type="tool_call" and saves to DB.
        """
        parsed_session_id = self._parse_uuid(session_id)
        output_str = str(tool_output) if tool_output is not None else None
        status_str = "success" if success else "failed"

        try:
            async with self._get_db(session) as db:
                trace_step = TraceStep(
                    session_id=parsed_session_id,
                    step_number=step_number,
                    step_type="tool_call",
                    duration_ms=duration_ms,
                    tool_name=tool_name,
                    tool_input=tool_input,
                    tool_output=output_str,
                    tool_success=success,
                    status=status_str,
                    timestamp=datetime.now(timezone.utc),
                )
                db.add(trace_step)

                # Update total steps in AgentSession
                agent_sess = await db.get(AgentSession, parsed_session_id)
                if agent_sess:
                    agent_sess.total_steps = max(agent_sess.total_steps or 0, step_number)

                await db.commit()
                await db.refresh(trace_step)
                logger.info(
                    f"Recorded tool call '{tool_name}' step {step_number} for session {parsed_session_id} (success: {success})"
                )
                return trace_step
        except Exception as e:
            logger.error(
                f"Failed to record tool call for session {session_id}, step {step_number}: {e}",
                exc_info=True,
            )
            raise

    async def end_session(
        self,
        session_id: Union[uuid.UUID, str],
        status: str,
        error: Optional[str] = None,
        session: Optional[AsyncSession] = None,
    ) -> Optional[AgentSession]:
        """
        Updates AgentSession with ended_at and final status.
        """
        parsed_session_id = self._parse_uuid(session_id)
        try:
            async with self._get_db(session) as db:
                agent_sess = await db.get(AgentSession, parsed_session_id)
                if not agent_sess:
                    logger.warning(f"Session {session_id} not found when ending session.")
                    return None

                agent_sess.status = status
                agent_sess.ended_at = datetime.now(timezone.utc)
                if status == "failed" and error:
                    agent_sess.failed_at_step = agent_sess.total_steps

                await db.commit()
                await db.refresh(agent_sess)
                logger.info(f"Ended session {parsed_session_id} with status '{status}'")
                return agent_sess
        except Exception as e:
            logger.error(f"Failed to end session {session_id}: {e}", exc_info=True)
            raise

    async def get_session(
        self,
        session_id: Union[uuid.UUID, str],
        session: Optional[AsyncSession] = None,
    ) -> Optional[AgentSession]:
        """
        Returns AgentSession from DB by session_id.
        """
        parsed_session_id = self._parse_uuid(session_id)
        try:
            async with self._get_db(session) as db:
                agent_sess = await db.get(AgentSession, parsed_session_id)
                return agent_sess
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}", exc_info=True)
            raise

    async def get_trace(
        self,
        session_id: Union[uuid.UUID, str],
        session: Optional[AsyncSession] = None,
    ) -> List[TraceStep]:
        """
        Returns all TraceSteps for session ordered by step_number ascending.
        """
        parsed_session_id = self._parse_uuid(session_id)
        try:
            async with self._get_db(session) as db:
                stmt = (
                    select(TraceStep)
                    .where(TraceStep.session_id == parsed_session_id)
                    .order_by(TraceStep.step_number.asc())
                )
                result = await db.execute(stmt)
                steps = list(result.scalars().all())
                return steps
        except Exception as e:
            logger.error(f"Failed to get trace for session {session_id}: {e}", exc_info=True)
            raise

    async def get_replay(
        self,
        session_id: Union[uuid.UUID, str],
        session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """
        Returns dict with session + steps + failure_point + recovery_point.
        """
        parsed_session_id = self._parse_uuid(session_id)
        try:
            agent_sess = await self.get_session(parsed_session_id, session=session)
            steps = await self.get_trace(parsed_session_id, session=session)

            failure_point: Optional[int] = None
            recovery_point: Optional[int] = None

            if agent_sess:
                failure_point = agent_sess.failed_at_step

            # If failure_point not set on session, inspect steps
            if failure_point is None:
                for step in steps:
                    if step.status == "failed" or step.error:
                        failure_point = step.step_number
                        break

            # Find recovery point if any
            for step in steps:
                if step.was_recovered:
                    recovery_point = step.step_number
                    break

            return {
                "session": agent_sess,
                "steps": steps,
                "failure_point": failure_point,
                "recovery_point": recovery_point,
            }
        except Exception as e:
            logger.error(f"Failed to get replay for session {session_id}: {e}", exc_info=True)
            raise
