"""Default middleware pipeline.

Composes registered middleware into an onion around the core dispatch: the
first-registered middleware is outermost. Middleware is resolved through a
callable so newly-registered middleware is always included.
"""

from __future__ import annotations

from typing import Callable, List

from ...types import Middleware, RequestContext, ResponseContext

Dispatch = Callable[[RequestContext], ResponseContext]


class MiddlewarePipeline:
    """Onion-model middleware executor.

    Satisfies the :class:`arc.runtime.middleware.MiddlewarePipeline` interface.

    :param resolve: returns the middleware currently registered, outermost-first.
    """

    def __init__(self, resolve: Callable[[], List[Middleware]]) -> None:
        self._resolve = resolve

    def add(self, middleware: Middleware) -> None:  # pragma: no cover
        raise NotImplementedError(
            "Register through ARC.middleware(); the pipeline reads that registry live."
        )

    def execute(self, request: RequestContext, dispatch: Dispatch) -> ResponseContext:
        """Run ``request`` through every middleware, then ``dispatch``."""
        middlewares = self._resolve()

        def build(index: int) -> Dispatch:
            if index >= len(middlewares):
                return dispatch
            mw = middlewares[index]
            nxt = build(index + 1)
            return lambda req: mw(req, nxt)

        return build(0)(request)


__all__ = ["MiddlewarePipeline"]
