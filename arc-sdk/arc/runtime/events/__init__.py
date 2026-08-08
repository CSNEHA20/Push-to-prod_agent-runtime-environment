"""Event broker & pub/sub dispatcher."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from arc.types import Event, EventBusStats, EventHandler
from .circuit_breaker import CircuitBreaker, CircuitBreakerRegistry
from .default import DefaultEventBus
from .dlq import DeadLetterQueue
from .hardened import HardenedEventBus
from .metrics import EventBusMetrics


@runtime_checkable
class EventBus(Protocol):
    """Registers handlers and dispatches runtime events to subscribers."""

    def subscribe(self, name: str, handler: EventHandler) -> None:
        """Register ``handler`` for events of type ``name``."""
        ...

    def emit(self, event: Event) -> None:
        """Dispatch ``event`` to all matching subscribers."""
        ...


__all__ = [
    "Event",
    "EventHandler",
    "EventBus",
    "HardenedEventBus",
    "DefaultEventBus",
    "CircuitBreaker",
    "CircuitBreakerRegistry",
    "DeadLetterQueue",
    "EventBusMetrics",
]
