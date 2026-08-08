"""Jailbreak Detector."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from arc.types import FirewallFinding, SanitizationAction
from ..detector import BaseDetector

JAILBREAK_PATTERNS = [
    r"(?i)\bDAN\b\s+mode",
    r"(?i)do\s+anything\s+now",
    r"(?i)developer\s+mode\s+enabled",
    r"(?i)hypothetical\s+scenario\s+where\s+you\s+have\s+no\s+(rules|ethics|boundaries|constraints)",
    r"(?i)pretend\s+you\s+have\s+no\s+(rules|ethics|safety|filters)",
    r"(?i)roleplay\s+as\s+an?\s+unfiltered",
    r"(?i)bypass\s+(safety|content)\s+filter",
]


class JailbreakDetector(BaseDetector):
    """Detects adversarial jailbreak attempts and persona bypass attempts."""

    name = "jailbreak_detector"
    category = "jailbreak"

    def __init__(self, action: SanitizationAction = SanitizationAction.REDACT) -> None:
        self.action = action
        self._regexes = [re.compile(p) for p in JAILBREAK_PATTERNS]

    def detect(
        self, context_type: str, content: str, metadata: Dict[str, Any] | None = None
    ) -> List[FirewallFinding]:
        findings: List[FirewallFinding] = []
        if not content:
            return findings

        for regex in self._regexes:
            for match in regex.finditer(content):
                findings.append(
                    FirewallFinding(
                        detector_name=self.name,
                        category=self.category,
                        severity="critical",
                        message=f"Jailbreak framing detected in {context_type}",
                        location=context_type,
                        action_taken=SanitizationAction.NONE,
                        matched_text=match.group(0),
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

        for regex in self._regexes:
            matches = list(regex.finditer(sanitized))
            for match in matches:
                findings.append(
                    FirewallFinding(
                        detector_name=self.name,
                        category=self.category,
                        severity="critical",
                        message=f"Sanitized jailbreak framing in {context_type}",
                        location=context_type,
                        action_taken=self.action,
                        matched_text=match.group(0),
                    )
                )
            if self.action in (SanitizationAction.REDACT, SanitizationAction.DROP):
                sanitized = regex.sub("[REDACTED_JAILBREAK]", sanitized)

        return sanitized, findings


__all__ = ["JailbreakDetector"]
