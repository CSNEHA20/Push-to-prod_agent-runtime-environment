"""Tests for Hardened Event Bus resiliency features."""

from __future__ import annotations

import asyncio
import time
from typing import List

import pytest
from arc.runtime.events import HardenedEventBus
from arc.types import CircuitState, Event, EventHandler


def test_fault_isolation_subscriber_crash_does_not_affect_runtime() -> None:
    events: List[Event] = []

    def bad_subscriber(e: Event) -> None:
        raise RuntimeError("Subscriber crashed horribly!")

    def good_subscriber(e: Event) -> None:
        events.append(e)

    handlers = [bad_subscriber, good_subscriber]
    bus = HardenedEventBus(resolve=lambda t: handlers)

    event = Event(type="test_event", payload={"data": 123})

    # Should not raise exception
    bus.emit(event)

    assert len(events) == 1
    assert events[0].payload["data"] == 123

    stats = bus.stats()
    assert stats.events_emitted == 1
    assert stats.failures > 0


@pytest.mark.asyncio
async def test_async_subscriber_timeout() -> None:
    async def slow_subscriber(e: Event) -> None:
        await asyncio.sleep(1.0)

    bus = HardenedEventBus(
        resolve=lambda t: [slow_subscriber], timeout_seconds=0.1, max_retries=0
    )

    event = Event(type="slow_event", payload={})
    bus.emit(event)

    await asyncio.sleep(0.3)

    stats = bus.stats()
    assert stats.timeouts >= 1
    assert bus.dlq.size() >= 1


def test_retry_mechanism_on_transient_failure() -> None:
    attempts = 0

    def flaky_subscriber(e: Event) -> None:
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise ValueError("Transient network glitch")

    bus = HardenedEventBus(
        resolve=lambda t: [flaky_subscriber], max_retries=2, timeout_seconds=1.0
    )

    event = Event(type="retry_event", payload={})
    bus.emit(event)

    assert attempts == 2
    stats = bus.stats()
    assert stats.retries >= 1
    assert stats.events_processed == 1


def test_dead_letter_queue_retention() -> None:
    def failing_subscriber(e: Event) -> None:
        raise ValueError("Fatal subscriber error")

    bus = HardenedEventBus(
        resolve=lambda t: [failing_subscriber], max_retries=1, timeout_seconds=1.0
    )

    event = Event(type="dlq_event", session_id="sess_123", payload={"key": "val"})
    bus.emit(event)

    assert bus.dlq.size() == 1
    item = bus.dlq.list()[0]
    assert item.event.type == "dlq_event"
    assert "Fatal subscriber error" in item.error
    assert item.attempts == 2


def test_circuit_breaker_trips_open_after_failures() -> None:
    def broken_subscriber(e: Event) -> None:
        raise RuntimeError("Permanent failure")

    bus = HardenedEventBus(
        resolve=lambda t: [broken_subscriber],
        failure_threshold=3,
        cooldown_seconds=10.0,
        max_retries=0,
    )

    event = Event(type="circuit_event", payload={})

    # Trip breaker by running 3 times
    for _ in range(3):
        bus.emit(event)

    stats = bus.stats()
    cb_state = stats.circuit_breakers.get("broken_subscriber")
    assert cb_state == CircuitState.OPEN.value

    # 4th emit should skip subscriber
    dlq_before = bus.dlq.size()
    bus.emit(event)
    assert bus.dlq.size() == dlq_before + 1
    latest_dlq = bus.dlq.list()[0]
    assert "Circuit breaker OPEN" in latest_dlq.error


def test_metrics_collection() -> None:
    def dummy_handler(e: Event) -> None:
        pass

    bus = HardenedEventBus(resolve=lambda t: [dummy_handler])

    for i in range(5):
        bus.emit(Event(type="metric_event", payload={"i": i}))

    stats = bus.stats()
    assert stats.events_emitted == 5
    assert stats.events_processed == 5
    assert stats.failures == 0
    assert stats.timeouts == 0
