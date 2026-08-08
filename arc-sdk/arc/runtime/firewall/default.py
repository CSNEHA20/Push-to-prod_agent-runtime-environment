"""Default Context Firewall implementation.

Scores each candidate context source for relevance, drops sources below the
relevance floor (0.3, matching the backend firewall), and flags trivially
conflicting sources. It never mutates the provider payload — surviving sources
are returned for the caller to inject, and telemetry is emitted regardless.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from ...types import ConflictItem

RELEVANCE_FLOOR = 0.3


def _relevance(source: Dict[str, Any]) -> float:
    """Return the source's declared relevance, defaulting to 1.0 when absent."""
    value = source.get("relevance", source.get("score", 1.0))
    try:
        return float(value)
    except (TypeError, ValueError):
        return 1.0


class ContextFirewall:
    """Relevance-filter + pairwise conflict detector for context sources.

    Satisfies the :class:`arc.runtime.firewall.Firewall` interface.
    """

    def __init__(self, relevance_floor: float = RELEVANCE_FLOOR) -> None:
        self.relevance_floor = relevance_floor

    def filter(
        self, sources: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[ConflictItem]]:
        """Return ``(surviving_sources, conflicts)`` for ``sources``."""
        surviving = [s for s in sources if _relevance(s) >= self.relevance_floor]
        return surviving, self._detect_conflicts(surviving)

    def _detect_conflicts(self, sources: List[Dict[str, Any]]) -> List[ConflictItem]:
        """Flag sources that declare a conflicting ``claim`` for the same ``key``."""
        conflicts: List[ConflictItem] = []
        seen: Dict[str, Any] = {}
        for source in sources:
            key = source.get("key")
            claim = source.get("claim")
            if key is None or claim is None:
                continue
            if key in seen and seen[key] != claim:
                conflicts.append(
                    ConflictItem(
                        source_id=str(source.get("id", key)),
                        conflict_type="contradiction",
                        description=f"Conflicting claims for '{key}'",
                    )
                )
            else:
                seen[key] = claim
        return conflicts


__all__ = ["ContextFirewall", "RELEVANCE_FLOOR"]
