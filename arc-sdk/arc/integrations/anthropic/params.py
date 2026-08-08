"""Anthropic provider adapter — translates planner decisions into SDK params.

Registered under ``"anthropic"`` and ``"async_anthropic"`` so it fires for
both the sync (``anthropic.Anthropic``) and async (``anthropic.AsyncAnthropic``)
client paths.

Translations
------------
DISPATCH node config → Anthropic SDK request kwargs:

+-------------------+--------------------+-------------------------------------------+
| Config key        | Value              | Injected kwarg                            |
+===================+====================+===========================================+
| reasoning         | ``extended``       | ``thinking={"type":"enabled",``           |
|                   |                    |   ``"budget_tokens": thinking_budget}``   |
+-------------------+--------------------+-------------------------------------------+
| reasoning         | ``step_by_step``   | no thinking injected (model reasons       |
|                   |                    | internally from chain-of-thought prompts) |
+-------------------+--------------------+-------------------------------------------+
| tool_strategy     | ``auto``           | ``tool_choice={"type":"auto"}``           |
+-------------------+--------------------+-------------------------------------------+
| tool_strategy     | ``parallel``       | ``tool_choice={"type":"any"}``            |
+-------------------+--------------------+-------------------------------------------+
| tool_strategy     | ``none``           | ``tool_choice={"type":"none"}``           |
|                   |                    | (only when tools list is non-empty)       |
+-------------------+--------------------+-------------------------------------------+

All injection is **additive** — if the developer already set the target key,
the adapter leaves it untouched. ``max_tokens`` is corrected if it would fall
below the thinking budget (Anthropic rejects such requests).
"""

from __future__ import annotations

from typing import Any, Dict

from ...runtime.graph import ExecutionNode
from ..adapter import register_adapter


class AnthropicParamAdapter:
    """Translates the DISPATCH node's abstract config into Anthropic SDK kwargs."""

    name: str = "anthropic"

    def prepare(
        self,
        payload: Dict[str, Any],
        dispatch_node: ExecutionNode,
    ) -> Dict[str, Any]:
        """Return an enriched copy of ``payload`` with Anthropic-specific params."""
        enriched = dict(payload)
        cfg = dispatch_node.config

        self._inject_thinking(enriched, cfg)
        self._inject_tool_choice(enriched, cfg)
        return enriched

    # -- private helpers --------------------------------------------------

    @staticmethod
    def _inject_thinking(enriched: Dict[str, Any], cfg: Dict[str, Any]) -> None:
        """Inject extended-thinking params when strategy warrants it."""
        # Honour the developer's explicit setting — never override.
        if "thinking" in enriched:
            return

        reasoning = cfg.get("reasoning", "direct")
        budget = int(cfg.get("thinking_budget", 0))

        if reasoning != "extended" or budget <= 0:
            return

        # Anthropic requires max_tokens > budget_tokens.
        max_tokens = enriched.get("max_tokens")
        if isinstance(max_tokens, int) and max_tokens <= budget:
            enriched["max_tokens"] = budget + 1

        enriched["thinking"] = {"type": "enabled", "budget_tokens": budget}

    @staticmethod
    def _inject_tool_choice(enriched: Dict[str, Any], cfg: Dict[str, Any]) -> None:
        """Inject tool_choice when the plan specifies a tool strategy."""
        # Honour the developer's explicit setting — never override.
        if "tool_choice" in enriched:
            return

        # tool_choice is irrelevant without a tools list.
        tools = enriched.get("tools")
        if not isinstance(tools, list) or len(tools) == 0:
            return

        strategy = cfg.get("tool_strategy", "none")
        mapping = {
            "auto": {"type": "auto"},
            "parallel": {"type": "any"},
            "none": {"type": "none"},
        }
        choice = mapping.get(strategy)
        if choice is not None:
            enriched["tool_choice"] = choice


# ---------------------------------------------------------------------------
# Self-registration
# ---------------------------------------------------------------------------

register_adapter("anthropic", AnthropicParamAdapter)
# AsyncAnthropic clients follow the same Anthropic API surface.
register_adapter("async_anthropic", AnthropicParamAdapter)


__all__ = ["AnthropicParamAdapter"]
