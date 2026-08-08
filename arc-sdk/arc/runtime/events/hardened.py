"""Hardened Event Bus providing fault isolation, timeouts, retries, async dispatch,
backpressure, Dead Letter Queue (DLQ), circuit breakers, and metrics.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import time
from typing import Any, Callable, Dict, List, Optional

from arc.types import Event, EventBusStats, EventHandler
from .circuit_breaker import CircuitBreakerRegistry
from .dlq import DeadLetterQueue
from .metrics import EventBusMetrics

logger = logging.getLogger("arc.events.hardened")


def _handler_name(handler: EventHandler) -> str:
    """Extract a human-readable name for a handler callable."""
    if hasattr(handler, "__name__"):
        return str(getattr(handler, "__name__"))
    elif hasattr(handler, "__class__"):
        return handler.__class__.__name__
    return str(handler)


class HardenedEventBus:
    """Fault-isolated, resilient, async event bus.

    Ensures that bad, failing, slow, or crashing subscribers NEVER crash
    the main application or block model execution.
    """

    def __init__(
        self,
        resolve: Callable[[str], List[EventHandler]],
        *,
        timeout_seconds: float = 2.0,
        max_retries: int = 2,
        max_queue_size: int = 1000,
        failure_threshold: int = 5,
        cooldown_seconds: float = 30.0,
        max_dlq_size: int = 500,
    ) -> None:
        self._resolve = resolve
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.max_queue_size = max_queue_size

        self.metrics = EventBusMetrics()
        self.circuits = CircuitBreakerRegistry(
            failure_threshold=failure_threshold, cooldown_seconds=cooldown_seconds
        )
        self.dlq = DeadLetterQueue(max_size=max_dlq_size)

        self._queue: Optional[asyncio.Queue[Tuple[Event, List[EventHandler]]]] = None
        self._worker_task: Optional[asyncio.Task[None]] = None
        self._custom_handlers: Dict[str, List[EventHandler]] = {}

    def subscribe(self, name: str, handler: EventHandler) -> None:
        """Register a subscriber handler for event topic ``name``."""
        self._custom_handlers.setdefault(name, []).append(handler)

    def stats(self) -> EventBusStats:
        """Retrieve live metrics and circuit breaker stats."""
        return self.metrics.stats(
            dlq_size=self.dlq.size(), circuit_states=self.circuits.states()
        )

    def emit(self, event: Event) -> None:
        """Non-blocking event dispatch. Pushes event to subscribers in isolated tasks."""
        self.metrics.record_emit()
        handlers = list(self._resolve(event.type))
        if event.type in self._custom_handlers:
            handlers.extend(self._custom_handlers[event.type])

        if not handlers:
            return

        # Attempt to schedule on active async loop without blocking caller
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is not None and loop.is_running():
            for handler in handlers:
                asyncio.create_task(self._safe_dispatch(handler, event))
        else:
            # Sync execution fallback with strict fault isolation
            for handler in handlers:
                self._sync_safe_dispatch(handler, event)

    async def _safe_dispatch(self, handler: EventHandler, event: Event) -> None:
        name = _handler_name(handler)
        cb = self.circuits.get(name)

        if not cb.can_execute():
            logger.warning(
                "Skipping event subscriber '%s' (circuit breaker OPEN for event '%s')",
                name,
                event.type,
            )
            self.dlq.add(event, name, "Circuit breaker OPEN", attempts=0)
            return

        attempts = 0
        last_error = ""

        while attempts <= self.max_retries:
            attempts += 1
            if attempts > 1:
                self.metrics.record_retry()
                await asyncio.sleep(0.05 * (2 ** (attempts - 2)))

            try:
                res = handler(event)
                if inspect.isawaitable(res):
                    await asyncio.wait_for(res, timeout=self.timeout_seconds)
                cb.record_success()
                self.metrics.record_processed()
                return
            except asyncio.TimeoutError:
                self.metrics.record_timeout()
                last_error = f"TimeoutError (> {self.timeout_seconds}s)"
                cb.record_failure()
                logger.warning(
                    "Subscriber '%s' timed out after %.1fs on event '%s' (attempt %d/%d)",
                    name,
                    self.timeout_seconds,
                    event.type,
                    attempts,
                    self.max_retries + 1,
                )
            except Exception as exc:
                self.metrics.record_failure()
                last_error = f"{type(exc).__name__}: {exc}"
                cb.record_failure()
                logger.warning(
                    "Subscriber '%s' raised exception on event '%s' (attempt %d/%d): %s",
                    name,
                    event.type,
                    attempts,
                    self.max_retries + 1,
                    exc,
                )

        # Retries exhausted -> send to Dead Letter Queue
        self.dlq.add(event, name, last_error, attempts=attempts)

    def _sync_safe_dispatch(self, handler: EventHandler, event: Event) -> None:
        name = _handler_name(handler)
        cb = self.circuits.get(name)

        if not cb.can_execute():
            logger.warning(
                "Skipping event subscriber '%s' (circuit breaker OPEN for event '%s')",
                name,
                event.type,
            )
            self.dlq.add(event, name, "Circuit breaker OPEN", attempts=0)
            return

        attempts = 0
        last_error = ""

        while attempts <= self.max_retries:
            attempts += 1
            if attempts > 1:
                self.metrics.record_retry()
                time.sleep(0.05 * (2 ** (attempts - 2)))

            try:
                res = handler(event)
                if inspect.isawaitable(res):
                    asyncio.run(res)
                cb.record_success()
                self.metrics.record_processed()
                return
            except Exception as exc:
                self.metrics.record_failure()
                last_error = f"{type(exc).__name__}: {exc}"
                cb.record_failure()
                logger.warning(
                    "Subscriber '%s' raised exception on event '%s' (attempt %d/%d): %s",
                    name,
                    event.type,
                    attempts,
                    self.max_retries + 1,
                    exc,
                )

        self.dlq.add(event, name, last_error, attempts=attempts)


__all__ = ["HardenedEventBus"]
