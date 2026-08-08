"""Context security & conflict filtering (interface only)."""

from __future__ import annotations

from typing import Any, Dict, List, Protocol, Tuple, runtime_checkable

from ...types import ConflictItem


@runtime_checkable
class Firewall(Protocol):
    """Scores, filters, and provenance-tags context before model dispatch."""

    def filter(
        self, sources: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[ConflictItem]]:
        """Return surviving sources and any detected conflicts."""
        ...


__all__ = ["Firewall"]
