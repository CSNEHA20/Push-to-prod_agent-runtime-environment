"""Default Prompt & Context Firewall implementation.

Provides PromptFirewall engine and ContextFirewall compatibility layer.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from ...types import ConflictItem
from .prompt_firewall import RELEVANCE_FLOOR, PromptFirewall


class ContextFirewall(PromptFirewall):
    """Backwards-compatible alias for PromptFirewall.

    Satisfies the :class:`arc.runtime.firewall.Firewall` interface.
    """

    def __init__(self, relevance_floor: float = RELEVANCE_FLOOR) -> None:
        super().__init__(relevance_floor=relevance_floor)


__all__ = ["ContextFirewall", "PromptFirewall", "RELEVANCE_FLOOR"]
