"""In-process synchronous graph event bus.

Dispatches :class:`GraphEvent`\\ s to subscribers in registration order, so the
service pipeline is deterministic. Subscriber exceptions propagate — the runtime
services are trusted internal components, and a genuine failure (e.g. the
recorder cannot record) should surface, not be silently swallowed.
"""

from __future__ import annotations

from typing import Callable, Dict, List

from . import GraphEvent


class InProcessGraphBus:
    """A minimal, deterministic pub/sub bus. Satisfies :class:`GraphBus`."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[GraphEvent], None]]] = {}

    def subscribe(self, topic: str, handler: Callable[[GraphEvent], None]) -> None:
        self._subscribers.setdefault(topic, []).append(handler)

    def publish(self, event: GraphEvent) -> None:
        for handler in self._subscribers.get(event.topic, ()):
            handler(event)

    def topics(self) -> List[str]:
        """Registered topics (introspection/testing aid)."""
        return list(self._subscribers)


__all__ = ["InProcessGraphBus"]
