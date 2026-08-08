"""Duplicate Context Detector."""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Set, Tuple

from arc.types import FirewallFinding, SanitizationAction
from ..detector import BaseDetector


def _hash_content(text: str) -> str:
    return hashlib.md5(text.strip().encode("utf-8")).hexdigest()


class DuplicateContextDetector(BaseDetector):
    """Detects and deduplicates redundant or identical context blocks and messages."""

    name = "duplicate_context_detector"
    category = "duplicate_context"

    def __init__(self, action: SanitizationAction = SanitizationAction.DEDUPLICATE) -> None:
        self.action = action
        self._seen_hashes: Set[str] = set()

    def reset(self) -> None:
        """Reset internal hash state between requests."""
        self._seen_hashes.clear()

    def detect(
        self, context_type: str, content: str, metadata: Dict[str, Any] | None = None
    ) -> List[FirewallFinding]:
        findings: List[FirewallFinding] = []
        if not content or not content.strip():
            return findings

        chash = _hash_content(content)
        if chash in self._seen_hashes:
            findings.append(
                FirewallFinding(
                    detector_name=self.name,
                    category=self.category,
                    severity="medium",
                    message=f"Duplicate context block detected in {context_type}",
                    location=context_type,
                    action_taken=SanitizationAction.NONE,
                    matched_text=content[:100] + "...",
                )
            )
        else:
            self._seen_hashes.add(chash)
        return findings

    def sanitize(
        self, context_type: str, content: str, metadata: Dict[str, Any] | None = None
    ) -> Tuple[str, List[FirewallFinding]]:
        if not content or not content.strip():
            return content, []

        findings: List[FirewallFinding] = []
        chash = _hash_content(content)

        if chash in self._seen_hashes:
            findings.append(
                FirewallFinding(
                    detector_name=self.name,
                    category=self.category,
                    severity="medium",
                    message=f"Deduplicated redundant context block in {context_type}",
                    location=context_type,
                    action_taken=self.action,
                    matched_text=content[:100] + "...",
                )
            )
            if self.action == SanitizationAction.DEDUPLICATE:
                return "", findings
        else:
            self._seen_hashes.add(chash)

        return content, findings


__all__ = ["DuplicateContextDetector"]
