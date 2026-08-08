"""Gemini provider adapter — translates planner decisions into SDK params.

Registered under ``"gemini"``.

Translations
------------
DISPATCH node config → Gemini SDK ``generation_config`` kwargs:

+-------------------+--------------------+-------------------------------------------+
| Config key        | Value              | Injected kwarg                            |
+===================+====================+===========================================+
| reasoning         | ``extended``       | ``generation_config`` →                   |
|                   |                    |   ``thinking_config={"mode":"enabled",``  |
|                   |                    |   ``"budget": thinking_budget}``          |
+-------------------+--------------------+-------------------------------------------+
| reasoning         | ``step_by_step``   | ``generation_config`` →                   |
|                   |                    |   ``thinking_config={"mode":"auto"}``     |
+-------------------+--------------------+-------------------------------------------+
| reasoning         | ``direct``         | no thinking config injected               |
+-------------------+--------------------+-------------------------------------------+

The Gemini SDK accepts ``generation_config`` as either a dict or a
``GenerationConfig`` object. This adapter uses a plain dict so it does not
require the ``google-generativeai`` package to be installed.

All injection is **additive** — developer-set keys are never overridden.
"""

from __future__ import annotations

from typing import Any, Dict

from ...runtime.graph import ExecutionNode
from ..adapter import register_adapter


class GeminiParamAdapter:
    """Translates the DISPATCH node's abstract config into Gemini SDK kwargs."""

    name: str = "gemini"

    def prepare(
        self,
        payload: Dict[str, Any],
        dispatch_node: ExecutionNode,
    ) -> Dict[str, Any]:
        """Return an enriched copy of ``payload`` with Gemini-specific params."""
        enriched = dict(payload)
        cfg = dispatch_node.config

        self._inject_thinking_config(enriched, cfg)
        return enriched

    # -- private helpers --------------------------------------------------

    @staticmethod
    def _inject_thinking_config(enriched: Dict[str, Any], cfg: Dict[str, Any]) -> None:
        """Inject thinking_config inside generation_config."""
        reasoning = cfg.get("reasoning", "direct")
        if reasoning == "direct":
            return

        # Build or merge into the existing generation_config dict.
        gen_cfg = enriched.get("generation_config")
        if gen_cfg is None:
            gen_cfg = {}
        elif not isinstance(gen_cfg, dict):
            # GenerationConfig object — cannot safely introspect; skip injection.
            return

        # Never override an explicit thinking_config.
        if "thinking_config" in gen_cfg:
            return

        if reasoning == "extended":
            budget = int(cfg.get("thinking_budget", 0))
            thinking: Dict[str, Any] = {"mode": "enabled"}
            if budget > 0:
                thinking["budget"] = budget
            gen_cfg = dict(gen_cfg)
            gen_cfg["thinking_config"] = thinking
        elif reasoning == "step_by_step":
            gen_cfg = dict(gen_cfg)
            gen_cfg["thinking_config"] = {"mode": "auto"}

        enriched["generation_config"] = gen_cfg


# ---------------------------------------------------------------------------
# Self-registration
# ---------------------------------------------------------------------------

register_adapter("gemini", GeminiParamAdapter)


__all__ = ["GeminiParamAdapter"]
