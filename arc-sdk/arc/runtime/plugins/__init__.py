"""Plugin registry (interface only).

Re-exports the :class:`~arc.types.Plugin` contract and declares the registry
interface the facade delegates to.
"""

from __future__ import annotations

from typing import List, Protocol, runtime_checkable

from ...types import Plugin


@runtime_checkable
class PluginRegistry(Protocol):
    """Stores plugins and drives their ``setup``/``teardown`` lifecycle."""

    def register(self, plugin: Plugin) -> None:
        """Add a plugin and invoke its ``setup`` hook."""
        ...

    def all(self) -> List[Plugin]:
        """Return every registered plugin."""
        ...


__all__ = ["Plugin", "PluginRegistry"]
