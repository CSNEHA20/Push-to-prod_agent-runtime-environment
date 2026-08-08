"""Base Detector interface for Prompt Firewall pluggable detectors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

from arc.types import FirewallFinding, SanitizationAction


class BaseDetector(ABC):
    """Abstract base class for pluggable prompt firewall detectors."""

    name: str = "base_detector"
    category: str = "general"

    @abstractmethod
    def detect(
        self, context_type: str, content: str, metadata: Dict[str, Any] | None = None
    ) -> List[FirewallFinding]:
        """Inspect *content* of type *context_type* and return detected findings."""
        ...

    @abstractmethod
    def sanitize(
        self, context_type: str, content: str, metadata: Dict[str, Any] | None = None
    ) -> Tuple[str, List[FirewallFinding]]:
        """Sanitize *content* of type *context_type*, returning ``(sanitized_content, findings)``."""
        ...


__all__ = ["BaseDetector"]
