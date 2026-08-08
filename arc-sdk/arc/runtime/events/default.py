"""Default Event Bus implementation wrapping HardenedEventBus."""

from __future__ import annotations

from typing import Callable, List

from arc.types import Event, EventHandler
from .hardened import HardenedEventBus


class DefaultEventBus(HardenedEventBus):
    """Backwards-compatible alias for HardenedEventBus.

    Satisfies the :class:`arc.runtime.events.EventBus` interface.
    """

    def __init__(self, resolve: Callable[[str], List[EventHandler]]) -> None:
        super().__init__(resolve=resolve)


__all__ = ["DefaultEventBus"]
