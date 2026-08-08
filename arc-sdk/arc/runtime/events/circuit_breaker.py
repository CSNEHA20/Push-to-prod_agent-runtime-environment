"""Per-subscriber Circuit Breaker for fault protection."""

from __future__ import annotations

import time
from typing import Dict

from arc.types import CircuitState


class CircuitBreaker:
    """Manages circuit state for a single subscriber handler."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        cooldown_seconds: float = 30.0,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.state: CircuitState = CircuitState.CLOSED
        self.consecutive_failures: int = 0
        self.last_state_change: float = time.time()
        self.total_trips: int = 0

    def can_execute(self) -> bool:
        """Return True if execution is allowed under the current circuit state."""
        now = time.time()
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            if now - self.last_state_change >= self.cooldown_seconds:
                self.state = CircuitState.HALF_OPEN
                self.last_state_change = now
                return True
            return False
        elif self.state == CircuitState.HALF_OPEN:
            return True
        return False

    def record_success(self) -> None:
        """Record a successful execution, resetting circuit state to CLOSED."""
        self.consecutive_failures = 0
        if self.state != CircuitState.CLOSED:
            self.state = CircuitState.CLOSED
            self.last_state_change = time.time()

    def record_failure(self) -> None:
        """Record a failed execution, potentially tripping the circuit to OPEN."""
        self.consecutive_failures += 1
        if self.consecutive_failures >= self.failure_threshold or self.state == CircuitState.HALF_OPEN:
            if self.state != CircuitState.OPEN:
                self.state = CircuitState.OPEN
                self.last_state_change = time.time()
                self.total_trips += 1


class CircuitBreakerRegistry:
    """Registry maintaining per-subscriber CircuitBreaker instances."""

    def __init__(
        self, failure_threshold: int = 5, cooldown_seconds: float = 30.0
    ) -> None:
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self._breakers: Dict[str, CircuitBreaker] = {}

    def get(self, handler_name: str) -> CircuitBreaker:
        """Retrieve or create the CircuitBreaker for handler_name."""
        if handler_name not in self._breakers:
            self._breakers[handler_name] = CircuitBreaker(
                name=handler_name,
                failure_threshold=self.failure_threshold,
                cooldown_seconds=self.cooldown_seconds,
            )
        return self._breakers[handler_name]

    def states(self) -> Dict[str, str]:
        """Return a snapshot dict mapping handler names to their current circuit state."""
        return {name: cb.state.value for name, cb in self._breakers.items()}


__all__ = ["CircuitBreaker", "CircuitBreakerRegistry"]
