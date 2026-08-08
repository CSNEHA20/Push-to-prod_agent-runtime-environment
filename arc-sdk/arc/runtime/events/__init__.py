"""Event broker & pub/sub dispatcher (interface only).

Re-exports the :class:`~arc.types.EventHandler` contract and declares the event
bus interface backing :meth:`arc.ARC.event`.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ...types import Event, EventHandler


@runtime_checkable
class EventBus(Protocol):
    """Registers handlers and dispatches runtime events to subscribers."""

    def subscribe(self, name: str, handler: EventHandler) -> None:
        """Register ``handler`` for events of type ``name``."""
        ...

    def emit(self, event: Event) -> None:
        """Dispatch ``event`` to all matching subscribers."""
        ...


__all__ = ["Event", "EventHandler", "EventBus"]
