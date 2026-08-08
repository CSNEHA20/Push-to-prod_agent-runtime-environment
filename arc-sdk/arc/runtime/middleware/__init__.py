"""Interceptor middleware pipeline (interface only).

Re-exports the :class:`~arc.types.Middleware` contract and declares the
pipeline interface that composes middleware around each runtime step.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ...types import Middleware, RequestContext, ResponseContext


@runtime_checkable
class MiddlewarePipeline(Protocol):
    """Composes registered middleware into an onion around dispatch."""

    def add(self, middleware: Middleware) -> None:
        """Append a middleware to the pipeline."""
        ...

    def execute(self, request: RequestContext) -> ResponseContext:
        """Run ``request`` through the full middleware chain."""
        ...


__all__ = ["Middleware", "MiddlewarePipeline"]
