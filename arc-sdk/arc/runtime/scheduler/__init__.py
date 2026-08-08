"""Execution scheduling & loop management (interface only)."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from ...types import RequestContext, ResponseContext


@runtime_checkable
class Scheduler(Protocol):
    """Drives a single protected step through the runtime pipeline."""

    def dispatch(self, request: RequestContext) -> ResponseContext:
        """Schedule and execute one request, returning its response."""
        ...

    def shutdown(self) -> None:
        """Stop accepting work and drain in-flight requests."""
        ...


__all__ = ["Scheduler"]
