"""Default in-process Event Bus.

Dispatches runtime events to handlers registered via :meth:`arc.ARC.event`.
Handler resolution is delegated to a callable so the bus always sees the
current registry, even when handlers are registered after construction.
Handler failures are logged and swallowed — a bad subscriber must not break the
request pipeline (graceful degradation).
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from typing import Callable, List

from ...types import Event, EventHandler

logger = logging.getLogger("arc.events")


class DefaultEventBus:
    """Synchronous event dispatcher.

    Satisfies the :class:`arc.runtime.events.EventBus` interface.

    :param resolve: returns the handlers currently registered for an event name.
    """

    def __init__(self, resolve: Callable[[str], List[EventHandler]]) -> None:
        self._resolve = resolve

    def subscribe(self, name: str, handler: EventHandler) -> None:  # pragma: no cover
        raise NotImplementedError(
            "Subscribe through ARC.event(name); the bus reads that registry live."
        )

    def emit(self, event: Event) -> None:
        """Dispatch ``event`` to every handler registered for its type."""
        for handler in self._resolve(event.type):
            try:
                self._invoke(handler, event)
            except Exception as exc:  # noqa: BLE001 - subscribers must not break dispatch
                logger.debug("Event handler for %s failed: %s", event.type, exc)

    @staticmethod
    def _invoke(handler: EventHandler, event: Event) -> None:
        result = handler(event)
        if inspect.isawaitable(result):
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                asyncio.run(result)  # type: ignore[arg-type]
            else:
                # Inside a running loop: schedule and let it complete out of band.
                asyncio.ensure_future(result)  # type: ignore[arg-type]


__all__ = ["DefaultEventBus"]
