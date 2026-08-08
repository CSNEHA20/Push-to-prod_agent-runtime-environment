"""Metrics collector for hardened event bus execution monitoring."""

from __future__ import annotations

from typing import Callable, Dict

from arc.types import EventBusStats


class EventBusMetrics:
    """Tracks live execution metrics for the Event Bus."""

    def __init__(self) -> None:
        self.events_emitted: int = 0
        self.events_processed: int = 0
        self.failures: int = 0
        self.timeouts: int = 0
        self.retries: int = 0
        self.circuit_trips: int = 0

    def record_emit(self) -> None:
        self.events_emitted += 1

    def record_processed(self) -> None:
        self.events_processed += 1

    def record_failure(self) -> None:
        self.failures += 1

    def record_timeout(self) -> None:
        self.timeouts += 1

    def record_retry(self) -> None:
        self.retries += 1

    def record_circuit_trip(self) -> None:
        self.circuit_trips += 1

    def stats(
        self, dlq_size: int = 0, circuit_states: Dict[str, str] | None = None
    ) -> EventBusStats:
        """Assemble current snapshot into EventBusStats."""
        return EventBusStats(
            events_emitted=self.events_emitted,
            events_processed=self.events_processed,
            failures=self.failures,
            timeouts=self.timeouts,
            retries=self.retries,
            dlq_size=dlq_size,
            circuit_breakers=circuit_states or {},
        )


__all__ = ["EventBusMetrics"]
