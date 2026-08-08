"""Prompt & Context Security Firewall."""

from __future__ import annotations

from typing import Any, Dict, List, Protocol, Tuple, runtime_checkable

from ...types import ConflictItem, PromptFirewallResult, RequestContext
from .default import ContextFirewall
from .detector import BaseDetector
from .detectors import (
    ContextExplosionDetector,
    DuplicateContextDetector,
    JailbreakDetector,
    PIIDetector,
    PromptInjectionDetector,
    PromptLeakageDetector,
    RecursivePromptingDetector,
    SecretsDetector,
)
from .prompt_firewall import PromptFirewall


@runtime_checkable
class Firewall(Protocol):
    """Inspects, scores, filters, and sanitizes prompt context before model dispatch."""

    def filter(
        self, sources: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[ConflictItem]]:
        """Return surviving sources and any detected conflicts."""
        ...

    def inspect_and_sanitize(self, request: RequestContext) -> PromptFirewallResult:
        """Inspect prompt inputs across targets and return sanitized result."""
        ...


__all__ = [
    "Firewall",
    "PromptFirewall",
    "ContextFirewall",
    "BaseDetector",
    "PromptInjectionDetector",
    "JailbreakDetector",
    "PIIDetector",
    "SecretsDetector",
    "RecursivePromptingDetector",
    "PromptLeakageDetector",
    "ContextExplosionDetector",
    "DuplicateContextDetector",
]
