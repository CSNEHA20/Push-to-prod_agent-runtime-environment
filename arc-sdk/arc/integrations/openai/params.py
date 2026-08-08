"""OpenAI provider adapter — translates planner decisions into SDK params.

Registered under ``"openai"`` and ``"openai_client"``.

Translations
------------
DISPATCH node config → OpenAI SDK request kwargs:

+-------------------+--------------------+-------------------------------------------+
| Config key        | Value              | Injected kwarg                            |
+===================+====================+===========================================+
| reasoning         | ``extended``       | ``reasoning_effort="high"``               |
+-------------------+--------------------+-------------------------------------------+
| reasoning         | ``step_by_step``   | ``reasoning_effort="medium"``             |
+-------------------+--------------------+-------------------------------------------+
| reasoning         | ``direct``         | ``reasoning_effort="low"``                |
+-------------------+--------------------+-------------------------------------------+
| tool_strategy     | ``auto``           | ``tool_choice="auto"``                    |
+-------------------+--------------------+-------------------------------------------+
| tool_strategy     | ``parallel``       | ``tool_choice="required"``                |
+-------------------+--------------------+-------------------------------------------+
| tool_strategy     | ``none``           | ``tool_choice="none"``                    |
|                   |                    | (only when tools list is non-empty)       |
+-------------------+--------------------+-------------------------------------------+

Note: ``reasoning_effort`` applies to o-series models (o1, o3, o4-mini).
For GPT-4o models, the key is silently ignored by the OpenAI SDK.
All injection is **additive** — developer-set keys are never overridden.
"""

from __future__ import annotations

from typing import Any, Dict

from ...runtime.graph import ExecutionNode
from ..adapter import register_adapter


class OpenAIParamAdapter:
    """Translates the DISPATCH node's abstract config into OpenAI SDK kwargs."""

    name: str = "openai"

    def prepare(
        self,
        payload: Dict[str, Any],
        dispatch_node: ExecutionNode,
    ) -> Dict[str, Any]:
        """Return an enriched copy of ``payload`` with OpenAI-specific params."""
        enriched = dict(payload)
        cfg = dispatch_node.config

        self._inject_reasoning_effort(enriched, cfg)
        self._inject_tool_choice(enriched, cfg)
        return enriched

    # -- private helpers --------------------------------------------------

    @staticmethod
    def _inject_reasoning_effort(enriched: Dict[str, Any], cfg: Dict[str, Any]) -> None:
        """Inject reasoning_effort based on the planned reasoning strategy."""
        if "reasoning_effort" in enriched:
            return

        reasoning = cfg.get("reasoning", "direct")
        effort_map = {
            "extended": "high",
            "step_by_step": "medium",
            "direct": "low",
        }
        effort = effort_map.get(reasoning)
        if effort is not None:
            enriched["reasoning_effort"] = effort

    @staticmethod
    def _inject_tool_choice(enriched: Dict[str, Any], cfg: Dict[str, Any]) -> None:
        """Inject tool_choice when the plan specifies a tool strategy."""
        if "tool_choice" in enriched:
            return

        tools = enriched.get("tools")
        if not isinstance(tools, list) or len(tools) == 0:
            return

        strategy = cfg.get("tool_strategy", "none")
        mapping = {
            "auto": "auto",
            "parallel": "required",
            "none": "none",
        }
        choice = mapping.get(strategy)
        if choice is not None:
            enriched["tool_choice"] = choice


# ---------------------------------------------------------------------------
# Self-registration
# ---------------------------------------------------------------------------

register_adapter("openai", OpenAIParamAdapter)
register_adapter("openai_client", OpenAIParamAdapter)


__all__ = ["OpenAIParamAdapter"]
