"""Prompt Injection Detector."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from arc.types import FirewallFinding, SanitizationAction
from ..detector import BaseDetector

INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"(?i)disregard\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"(?i)forget\s+(all\s+)?(previous|prior|above)\s+(instructions?|rules|guidelines)",
    r"(?i)system\s+override",
    r"(?i)new\s+system\s+instructions?:",
    r"(?i)you\s+are\s+now\s+an?\s+unrestricted",
    r"(?i)override\s+system\s+prompt",
]


class PromptInjectionDetector(BaseDetector):
    """Detects direct and indirect prompt injection attempts."""

    name = "prompt_injection_detector"
    category = "prompt_injection"

    def __init__(self, action: SanitizationAction = SanitizationAction.REDACT) -> None:
        self.action = action
        self._regexes = [re.compile(p) for p in INJECTION_PATTERNS]

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
                        severity="high",
                        message=f"Prompt injection pattern detected in {context_type}",
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
                        severity="high",
                        message=f"Sanitized prompt injection pattern in {context_type}",
                        location=context_type,
                        action_taken=self.action,
                        matched_text=match.group(0),
                    )
                )
            if self.action in (SanitizationAction.REDACT, SanitizationAction.DROP):
                sanitized = regex.sub("[REDACTED_PROMPT_INJECTION]", sanitized)

        return sanitized, findings


__all__ = ["PromptInjectionDetector"]
