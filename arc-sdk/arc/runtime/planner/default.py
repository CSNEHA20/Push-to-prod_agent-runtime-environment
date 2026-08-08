"""Default Adaptive Planner + the first-middleware factory.

``AdaptivePlanner`` derives a complexity score from provider-independent request
signals and maps it to a full :class:`ExecutionPlan`. It reads only
cross-provider concepts (``messages``, ``tools``, ``max_tokens`` and the ARC
``context_sources``) — never Anthropic-specific structures — so the same
planner works for any provider.
"""

from __future__ import annotations

from typing import Any, Callable, Dict

from ...config import ARCConfig
from ...types import (
    Event,
    EventType,
    ExecutionPlan,
    Middleware,
    ReasoningStrategy,
    RecoveryPolicy,
    RequestContext,
    RetrievalStrategy,
    ToolStrategy,
    VerificationStrategy,
)

_CHARS_PER_TOKEN = 4
_MAX_CONTEXT_BUDGET = 200_000


def extract_signals(request: RequestContext) -> Dict[str, Any]:
    """Derive provider-independent signals from a request.

    Uses only keys common across chat-completion providers, so no provider
    coupling leaks into the planner.
    """
    payload = request.payload
    messages = payload.get("messages")
    message_count = len(messages) if isinstance(messages, list) else 0

    input_chars = 0
    if isinstance(messages, list):
        for msg in messages:
            content = msg.get("content") if isinstance(msg, dict) else None
            if content is not None:
                input_chars += len(str(content))

    tools = payload.get("tools")
    tool_count = len(tools) if isinstance(tools, list) else 0
    max_tokens = payload.get("max_tokens")

    return {
        "message_count": message_count,
        "approx_input_tokens": input_chars // _CHARS_PER_TOKEN,
        "tool_count": tool_count,
        "max_tokens": int(max_tokens) if isinstance(max_tokens, int) else None,
        "reasoning_hint": bool(payload.get("thinking") or payload.get("reasoning")),
        "context_source_count": len(request.context_sources),
    }


class AdaptivePlanner:
    """Heuristic, provider-independent planner.

    Satisfies the :class:`arc.runtime.planner.Planner` interface.

    :param config: used only to respect the global ``auto_recover`` switch — the
        planner never selects :attr:`RecoveryPolicy.RETRY_ONCE` (which re-bills
        a model call) unless recovery is enabled.
    """

    def __init__(self, config: ARCConfig) -> None:
        self._config = config

    def plan(self, request: RequestContext) -> ExecutionPlan:
        signals = extract_signals(request)
        score = self._score(signals)
        reasoning = self._reasoning(score, signals["reasoning_hint"])
        return ExecutionPlan(
            reasoning_strategy=reasoning,
            thinking_budget=self._thinking_budget(reasoning, signals),
            context_budget=self._context_budget(signals),
            retrieval_strategy=self._retrieval(signals),
            tool_strategy=self._tools(signals),
            verification_strategy=self._verification(score, signals),
            recovery_policy=self._recovery(score, signals),
            rationale=self._rationale(score, reasoning),
            signals=signals,
        )

    # -- scoring ----------------------------------------------------------

    @staticmethod
    def _score(s: Dict[str, Any]) -> int:
        # The first message is the baseline; only extra turns add complexity.
        score = min(max(0, s["message_count"] - 1), 10)
        tokens = s["approx_input_tokens"]
        if tokens > 2000:
            score += 3
        elif tokens > 500:
            score += 1
        score += s["tool_count"] * 2
        if s["reasoning_hint"]:
            score += 3
        return score

    @staticmethod
    def _reasoning(score: int, reasoning_hint: bool) -> ReasoningStrategy:
        if reasoning_hint or score >= 6:
            # An explicit thinking/reasoning request is honoured directly.
            return ReasoningStrategy.EXTENDED
        if score >= 2:
            return ReasoningStrategy.STEP_BY_STEP
        return ReasoningStrategy.DIRECT

    @staticmethod
    def _thinking_budget(reasoning: ReasoningStrategy, s: Dict[str, Any]) -> int:
        base = {
            ReasoningStrategy.DIRECT: 0,
            ReasoningStrategy.STEP_BY_STEP: 2048,
            ReasoningStrategy.EXTENDED: 8192,
        }[reasoning]
        max_tokens = s["max_tokens"]
        if base and max_tokens:
            # keep the reasoning budget strictly below the output ceiling
            return max(0, min(base, max_tokens - 1))
        return base

    @staticmethod
    def _context_budget(s: Dict[str, Any]) -> int:
        headroom = int(s["approx_input_tokens"] * 1.5) + 512
        return min(headroom, _MAX_CONTEXT_BUDGET)

    @staticmethod
    def _retrieval(s: Dict[str, Any]) -> RetrievalStrategy:
        count = s["context_source_count"]
        if count >= 4:
            return RetrievalStrategy.AGGRESSIVE
        if count >= 1:
            return RetrievalStrategy.LIGHT
        return RetrievalStrategy.NONE

    @staticmethod
    def _tools(s: Dict[str, Any]) -> ToolStrategy:
        if s["tool_count"] == 0:
            return ToolStrategy.NONE
        if s["tool_count"] >= 3:
            return ToolStrategy.PARALLEL
        return ToolStrategy.AUTO

    @staticmethod
    def _verification(score: int, s: Dict[str, Any]) -> VerificationStrategy:
        if s["tool_count"] > 0 or score >= 6:
            return VerificationStrategy.STRICT
        if score == 0:
            return VerificationStrategy.SKIP
        return VerificationStrategy.STANDARD

    def _recovery(self, score: int, s: Dict[str, Any]) -> RecoveryPolicy:
        if score == 0 and s["tool_count"] == 0:
            return RecoveryPolicy.NONE
        # RETRY_ONCE re-bills a model call — only when recovery is enabled.
        if self._config.auto_recover and (score >= 6 or s["tool_count"] > 0):
            return RecoveryPolicy.RETRY_ONCE
        return RecoveryPolicy.CHECKPOINT

    @staticmethod
    def _rationale(score: int, reasoning: ReasoningStrategy) -> str:
        return f"complexity score {score} -> {reasoning.value} reasoning"


def make_planner_middleware(
    get_planner: Callable[[], Any], emit: Callable[[Event], None]
) -> Middleware:
    """Build the first middleware: plan, publish, then continue the chain.

    The plan is stored on ``request.metadata['execution_plan']`` so every inner
    stage can follow it, and a ``plan_created`` event is emitted. ``get_planner``
    is resolved on every request so a swapped-in planner takes effect live.
    """

    def planner_middleware(request: RequestContext, call_next):  # type: ignore[no-untyped-def]
        plan = get_planner().plan(request)
        request.metadata["execution_plan"] = plan
        emit(
            Event(
                type=EventType.PLAN_CREATED.value,
                session_id=request.session_id,
                payload=plan.to_dict(),
            )
        )
        return call_next(request)

    return planner_middleware


__all__ = ["AdaptivePlanner", "make_planner_middleware", "extract_signals"]
