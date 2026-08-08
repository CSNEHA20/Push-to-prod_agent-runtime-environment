"""Context Explosion Detector."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from arc.types import FirewallFinding, SanitizationAction
from ..detector import BaseDetector

DEFAULT_MAX_CHARS = 100_000


class ContextExplosionDetector(BaseDetector):
    """Detects context bloat and token explosion exceeding configured length limits."""

    name = "context_explosion_detector"
    category = "context_explosion"

    def __init__(
        self,
        max_chars: int = DEFAULT_MAX_CHARS,
        action: SanitizationAction = SanitizationAction.TRUNCATE,
    ) -> None:
        self.max_chars = max_chars
        self.action = action

    def detect(
        self, context_type: str, content: str, metadata: Dict[str, Any] | None = None
    ) -> List[FirewallFinding]:
        findings: List[FirewallFinding] = []
        if not content:
            return findings

        if len(content) > self.max_chars:
            findings.append(
                FirewallFinding(
                    detector_name=self.name,
                    category=self.category,
                    severity="high",
                    message=(
                        f"Context explosion detected in {context_type}: "
                        f"{len(content)} chars exceeds limit of {self.max_chars}"
                    ),
                    location=context_type,
                    action_taken=SanitizationAction.NONE,
                    matched_text=content[:200] + "...",
                )
            )
        return findings

    def sanitize(
        self, context_type: str, content: str, metadata: Dict[str, Any] | None = None
    ) -> Tuple[str, List[FirewallFinding]]:
        if not content:
            return content, []

        findings: List[FirewallFinding] = []
        sanitized = content

        if len(content) > self.max_chars:
            findings.append(
                FirewallFinding(
                    detector_name=self.name,
                    category=self.category,
                    severity="high",
                    message=(
                        f"Truncated context explosion in {context_type} "
                        f"from {len(content)} to {self.max_chars} chars"
                    ),
                    location=context_type,
                    action_taken=self.action,
                    matched_text=content[:200] + "...",
                )
            )
            if self.action == SanitizationAction.TRUNCATE:
                sanitized = content[: self.max_chars] + "\n[TRUNCATED_CONTEXT_EXPLOSION]"

        return sanitized, findings


__all__ = ["ContextExplosionDetector", "DEFAULT_MAX_CHARS"]
