"""Adaptive Planner — decides an execution plan before a request reaches the model.

The planner is the **first middleware** in the pipeline. For every request it
produces a provider-independent :class:`~arc.types.ExecutionPlan` covering the
reasoning strategy, thinking budget, context budget, retrieval strategy, tool
strategy, verification strategy, and recovery policy. Everything downstream
follows that plan.

This module declares the :class:`Planner` interface and re-exports the plan
contracts; the default heuristic implementation lives in ``default.py``.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ...types import (
    ExecutionPlan,
    ReasoningStrategy,
    RecoveryPolicy,
    RequestContext,
    RetrievalStrategy,
    ToolStrategy,
    VerificationStrategy,
)


@runtime_checkable
class Planner(Protocol):
    """Produces an :class:`ExecutionPlan` for a request.

    Implementations MUST be provider-independent: they may read only generic,
    cross-provider request signals (message count, tool presence, input size,
    context sources) and MUST NOT emit provider-specific request keys.
    """

    def plan(self, request: RequestContext) -> ExecutionPlan:
        """Return the execution plan for ``request``."""
        ...


__all__ = [
    "Planner",
    "ExecutionPlan",
    "ReasoningStrategy",
    "RetrievalStrategy",
    "ToolStrategy",
    "VerificationStrategy",
    "RecoveryPolicy",
]
