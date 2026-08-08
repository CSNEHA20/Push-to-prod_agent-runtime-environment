"""Prompt Leakage Detector."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from arc.types import FirewallFinding, SanitizationAction
from ..detector import BaseDetector

LEAKAGE_PATTERNS = [
    r"(?i)(repeat|output|print|reveal|show)\s+.*?(system|initial)\s+(prompt|instructions?)",
    r"(?i)repeat\s+(your\s+)?system\s+prompt\s+verbatim",
    r"(?i)what\s+are\s+your\s+exact\s+system\s+instructions\?",
]


class PromptLeakageDetector(BaseDetector):
    """Detects attempts to extract or leak the system prompt and confidential instructions."""

    name = "prompt_leakage_detector"
    category = "prompt_leakage"

    def __init__(self, action: SanitizationAction = SanitizationAction.REDACT) -> None:
        self.action = action
        self._regexes = [re.compile(p) for p in LEAKAGE_PATTERNS]

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
                        message=f"Prompt leakage extraction attempt detected in {context_type}",
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
                        message=f"Sanitized prompt leakage attempt in {context_type}",
                        location=context_type,
                        action_taken=self.action,
                        matched_text=match.group(0),
                    )
                )
            if self.action in (SanitizationAction.REDACT, SanitizationAction.DROP):
                sanitized = regex.sub("[REDACTED_PROMPT_LEAKAGE_ATTEMPT]", sanitized)

        return sanitized, findings


__all__ = ["PromptLeakageDetector"]
