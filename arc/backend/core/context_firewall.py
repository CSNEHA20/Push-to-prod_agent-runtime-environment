import uuid
import logging
import re
import inspect
import itertools
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Union
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from db.database import AsyncSessionLocal
from models.context import ContextConflict, ContextLog

logger = logging.getLogger("arc.context_firewall")


class ContextFirewall:
    """
    Engine 2: Context Firewall
    Filters, rates relevance, detects conflicts, and adds provenance tags
    to context sources before passing them to the agent.
    """

    def __init__(self, client: Any = None, db_session: Optional[AsyncSession] = None):
        """
        Takes the Anthropic client as a constructor argument.
        Optionally accepts an active AsyncSession.
        """
        self.client = client
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

    async def _call_claude(self, prompt: str) -> str:
        """
        Helper method to call Claude using model='claude-sonnet-4-6' and max_tokens=100.
        Supports both sync and async Anthropic clients or mocks.
        """
        if self.client is None:
            logger.warning("Anthropic client is not initialized in ContextFirewall.")
            return ""

        try:
            res = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}],
            )
            if inspect.isawaitable(res):
                res = await res

            if hasattr(res, "content") and res.content:
                if isinstance(res.content, list):
                    text_parts = []
                    for block in res.content:
                        if hasattr(block, "text"):
                            text_parts.append(block.text)
                        elif isinstance(block, dict) and "text" in block:
                            text_parts.append(block["text"])
                        else:
                            text_parts.append(str(block))
                    return "".join(text_parts).strip()
                return str(res.content).strip()
            elif isinstance(res, str):
                return res.strip()
            elif isinstance(res, dict) and "content" in res:
                return str(res["content"]).strip()
            return str(res).strip()
        except Exception as e:
            logger.error(f"Error calling Claude (claude-sonnet-4-6): {e}")
            return ""

    @staticmethod
    def _parse_score(response_text: str) -> float:
        """
        Parses relevance score from Claude response text.
        Extracts first floating point number found and clamps to [0.0, 1.0].
        """
        if not response_text:
            return 0.0
        match = re.search(r"(\d+(?:\.\d+)?)", response_text)
        if match:
            try:
                score = float(match.group(1))
                return max(0.0, min(1.0, score))
            except ValueError:
                pass
        return 0.0

    @staticmethod
    def _parse_conflict_type(response_text: str) -> str:
        """
        Parses conflict classification (numerical, temporal, factual, logical).
        Defaults to 'factual'.
        """
        text_lower = response_text.lower()
        if "numerical" in text_lower:
            return "numerical"
        elif "temporal" in text_lower:
            return "temporal"
        elif "logical" in text_lower:
            return "logical"
        elif "factual" in text_lower:
            return "factual"
        return "factual"

    async def filter(
        self,
        session_id: Union[uuid.UUID, str],
        step_number: int,
        sources: List[Dict[str, Any]],
        task: str,
        db_session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """
        Runs the Context Firewall filtering pipeline:
        Step 1 — Score relevance (filter out score < 0.3)
        Step 2 — Detect conflicts between all pairs of remaining sources
        Step 3 — Build provenance tags
        Step 4 — Assemble and return FilteredContext dict & save summary to DB context_logs
        """
        parsed_session_id = self._parse_uuid(session_id)
        total_received = len(sources)

        # Step 1 — Score relevance
        passed_sources = []
        provenance_map: Dict[str, float] = {}

        for source in sources:
            name = source.get("name", "unknown_source")
            content = source.get("content", "")

            prompt = (
                f"Rate how relevant this content is to the task '{task}' on a scale of 0.0 to 1.0. "
                f"Return only a number.\n"
                f"Content: {content}"
            )

            res_text = await self._call_claude(prompt)
            score = self._parse_score(res_text)

            if score >= 0.3:
                passed_sources.append((source, score))
                provenance_map[name] = round(score, 2)

        # Step 2 — Detect conflicts
        conflicts_list: List[Dict[str, Any]] = []
        db_conflicts_to_save: List[ContextConflict] = []

        for src_a_item, src_b_item in itertools.combinations(passed_sources, 2):
            source_a, score_a = src_a_item
            source_b, score_b = src_b_item
            content_a = source_a.get("content", "")
            content_b = source_b.get("content", "")
            name_a = source_a.get("name", "Source A")
            name_b = source_b.get("name", "Source B")

            prompt = (
                "Do these two pieces of information conflict with each other? "
                "If yes, describe the conflict in one sentence and classify it as: numerical, temporal, factual, or logical. "
                "If no conflict, return 'NO_CONFLICT'.\n"
                f"Source A: {content_a}\n"
                f"Source B: {content_b}"
            )

            res_text = await self._call_claude(prompt)

            if "NO_CONFLICT" not in res_text.strip().upper():
                conflict_type = self._parse_conflict_type(res_text)
                description = res_text.strip()

                conflict_obj = ContextConflict(
                    conflict_id=uuid.uuid4(),
                    session_id=parsed_session_id,
                    step_number=step_number,
                    conflict_type=conflict_type,
                    description=description,
                    severity="medium",
                    source_a_id=str(name_a),
                    source_b_id=str(name_b),
                    detected_at=datetime.now(timezone.utc),
                )
                db_conflicts_to_save.append(conflict_obj)

                conflicts_list.append({
                    "conflict_id": str(conflict_obj.conflict_id),
                    "session_id": str(parsed_session_id),
                    "step_number": step_number,
                    "conflict_type": conflict_type,
                    "description": description,
                    "severity": "medium",
                    "source_a_id": str(name_a),
                    "source_b_id": str(name_b),
                })

        # Step 3 — Build provenance tags & Step 4 — Assemble final context
        tagged_chunks = []
        for source, score in passed_sources:
            name = source.get("name", "unknown_source")
            content = source.get("content", "")
            tag = f"[SOURCE: {name} | CONFIDENCE: {score:.2f}]"
            tagged_content = f"{content}\n{tag}"
            tagged_chunks.append(tagged_content)

        final_context = "\n\n".join(tagged_chunks)
        passed_count = len(passed_sources)
        rejected_count = total_received - passed_count

        result = {
            "final_context": final_context,
            "total_received": total_received,
            "passed": passed_count,
            "rejected": rejected_count,
            "conflicts": conflicts_list,
            "provenance_map": provenance_map,
        }

        # Save summary log & conflicts to DB
        try:
            async with self._get_db(db_session) as db:
                context_log = ContextLog(
                    log_id=uuid.uuid4(),
                    session_id=parsed_session_id,
                    step_number=step_number,
                    total_received=total_received,
                    passed=passed_count,
                    rejected=rejected_count,
                    final_context=final_context,
                    provenance_map=provenance_map,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(context_log)
                for conflict in db_conflicts_to_save:
                    db.add(conflict)
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to save ContextLog to DB for session {parsed_session_id}: {e}")
            try:
                if db_session:
                    await db_session.rollback()
                elif self._db_session:
                    await self._db_session.rollback()
            except Exception:
                pass

        return result

    def inspect_prompt(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inspects and sanitizes system prompts, messages, tool outputs, retrieved documents,
        memory, and attachments in payload before sending to model provider.
        """
        try:
            from arc.runtime.firewall import PromptFirewall
            from arc.types import RequestContext
            pf = PromptFirewall()
            req = RequestContext(payload=payload, context_sources=payload.get("context_sources", []))
            res = pf.inspect_and_sanitize(req)
            return res.sanitized_payload
        except Exception as e:
            logger.warning(f"Fallback during inspect_prompt: {e}")
            return payload

