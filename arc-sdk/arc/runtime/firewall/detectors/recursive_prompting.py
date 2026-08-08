"""Recursive Prompting Detector."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from arc.types import FirewallFinding, SanitizationAction
from ..detector import BaseDetector

RECURSIVE_PATTERNS = [
    r"(?i)recursively\s+(evaluate|expand|execute|process)\s+this\s+prompt",
    r"(?i)repeat\s+this\s+(process|prompt|step)\s+infinitely",
    r"(?i)generate\s+a\s+prompt\s+that\s+calls\s+yourself\s+recursively",
    r"(?i)loop\s+forever\s+evaluating",
    r"(?i)infinite\s+recursive\s+prompt",
]


class RecursivePromptingDetector(BaseDetector):
    """Detects recursive evaluation loops and infinite prompt expansion attempts."""

    name = "recursive_prompting_detector"
    category = "recursive_prompting"

    def __init__(self, action: SanitizationAction = SanitizationAction.REDACT) -> None:
        self.action = action
        self._regexes = [re.compile(p) for p in RECURSIVE_PATTERNS]

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
                        message=f"Recursive prompting loop detected in {context_type}",
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
                        message=f"Sanitized recursive prompting loop in {context_type}",
                        location=context_type,
                        action_taken=self.action,
                        matched_text=match.group(0),
                    )
                )
            if self.action in (SanitizationAction.REDACT, SanitizationAction.DROP):
                sanitized = regex.sub("[REDACTED_RECURSIVE_PROMPT]", sanitized)

        return sanitized, findings


__all__ = ["RecursivePromptingDetector"]
