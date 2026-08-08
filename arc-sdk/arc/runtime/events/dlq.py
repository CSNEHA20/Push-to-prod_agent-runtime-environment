"""Dead Letter Queue (DLQ) for failed event subscriber dispatches."""

from __future__ import annotations

import time
import uuid
from typing import Dict, List, Optional

from arc.types import DLQItem, Event

DEFAULT_MAX_DLQ_SIZE = 500


class DeadLetterQueue:
    """Retains events that permanently failed subscriber handling."""

    def __init__(self, max_size: int = DEFAULT_MAX_DLQ_SIZE) -> None:
        self.max_size = max_size
        self._items: Dict[str, DLQItem] = {}

    def add(
        self, event: Event, handler_name: str, error: str, attempts: int = 1
    ) -> DLQItem:
        """Add a failed event dispatch to the Dead Letter Queue."""
        dlq_id = str(uuid.uuid4())
        item = DLQItem(
            dlq_id=dlq_id,
            event=event,
            handler_name=handler_name,
            error=error,
            attempts=attempts,
            failed_at=time.time(),
        )

        if len(self._items) >= self.max_size:
            # Evict oldest entry
            oldest_id = min(self._items.keys(), key=lambda k: self._items[k].failed_at)
            del self._items[oldest_id]

        self._items[dlq_id] = item
        return item

    def list(self) -> List[DLQItem]:
        """Return all items currently in the Dead Letter Queue."""
        return sorted(self._items.values(), key=lambda x: x.failed_at, reverse=True)

    def get(self, dlq_id: str) -> Optional[DLQItem]:
        """Retrieve a specific DLQ item by ID."""
        return self._items.get(dlq_id)

    def remove(self, dlq_id: str) -> bool:
        """Remove an item from the DLQ (e.g. after manual resolution)."""
        if dlq_id in self._items:
            del self._items[dlq_id]
            return True
        return False

    def clear(self) -> None:
        """Clear all entries in the Dead Letter Queue."""
        self._items.clear()

    def size(self) -> int:
        """Return the number of entries currently in the DLQ."""
        return len(self._items)


__all__ = ["DeadLetterQueue", "DEFAULT_MAX_DLQ_SIZE"]
