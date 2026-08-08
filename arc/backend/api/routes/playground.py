"""
ARC Playground Route API
Endpoint to trigger interactive playground demo runs with background async agent execution and WebSocket event broadcasting.
"""

import uuid
import asyncio
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("arc.playground")

router = APIRouter(prefix="/api/playground", tags=["playground"])


class PlaygroundRunRequest(BaseModel):
    task: Optional[str] = Field(
        default="Research Anthropic, find their latest funding, key products, and write an investment brief",
        description="Task description for the agent"
    )
    scenario: Optional[str] = Field(
        default="research_company",
        description="Demo scenario ID: research_company, analyze_document, conflicting_sources, or api_failure_recovery"
    )
    inject_chaos: Optional[bool] = Field(
        default=False,
        description="Toggle chaos injection for API failure and recovery simulation"
    )


class PlaygroundRunResponse(BaseModel):
    session_id: str
    dashboard_url: str
    message: str
    scenario: str
    inject_chaos: bool


async def _run_agent_task(task: str, scenario: str, inject_chaos: bool, session_id: str):
    """Async wrapper to run the demo agent in background."""
    try:
        try:
            from demo.demo_agent import run_demo_agent
        except ImportError:
            try:
                from arc.demo.demo_agent import run_demo_agent
            except ImportError:
                from backend.demo.demo_agent import run_demo_agent

        logger.info(f"Background task starting agent session {session_id} for scenario '{scenario}'...")
        await run_demo_agent(
            task=task,
            scenario=scenario,
            inject_chaos=inject_chaos,
            session_id=session_id
        )
        logger.info(f"Background task completed agent session {session_id}.")
    except Exception as e:
        logger.error(f"Error executing background demo agent for session {session_id}: {e}", exc_info=True)


@router.post("/run", response_model=PlaygroundRunResponse)
async def run_playground_agent(
    request: PlaygroundRunRequest,
    background_tasks: BackgroundTasks
):
    """
    POST /api/playground/run
    Initializes a new demo agent session, launches background execution,
    and returns session_id and dashboard_url immediately.
    """
    session_id = str(uuid.uuid4())
    dashboard_url = f"http://localhost:3000/sessions/{session_id}"

    # Schedule background agent execution
    background_tasks.add_task(
        _run_agent_task,
        task=request.task or "Research Anthropic, find their latest funding, key products, and write an investment brief",
        scenario=request.scenario or "research_company",
        inject_chaos=bool(request.inject_chaos),
        session_id=session_id
    )

    logger.info(
        f"Playground run initiated: session_id={session_id}, scenario={request.scenario}, inject_chaos={request.inject_chaos}"
    )

    return PlaygroundRunResponse(
        session_id=session_id,
        dashboard_url=dashboard_url,
        message="Agent execution started asynchronously in background.",
        scenario=request.scenario or "research_company",
        inject_chaos=bool(request.inject_chaos)
    )
