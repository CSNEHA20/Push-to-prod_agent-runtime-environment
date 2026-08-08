"""Secrets Detector."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from arc.types import FirewallFinding, SanitizationAction
from ..detector import BaseDetector

SECRET_PATTERNS: Dict[str, str] = {
    "AWS_KEY": r"\b(AKIA|ASIA)[0-9A-Z]{16}\b",
    "GITHUB_TOKEN": r"\b(ghp|gho|ghu|ghs|ghr)_[a-zA-Z0-9_]{36}\b",
    "BEARER_TOKEN": r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}",
    "PRIVATE_KEY": r"-----BEGIN\s+(RSA|EC|OPENSSH|DSA|PGP|PRIVATE)\s+KEY-----[\s\S]+?-----END\s+\1\s+KEY-----",
    "GENERIC_API_KEY": r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-]{20,})['\"]?",
    "JWT_TOKEN": r"\beyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\b",
}


class SecretsDetector(BaseDetector):
    """Detects and redacts credentials, private keys, and API tokens."""

    name = "secrets_detector"
    category = "secrets"

    def __init__(self, action: SanitizationAction = SanitizationAction.REDACT) -> None:
        self.action = action
        self._compiled = {k: re.compile(v) for k, v in SECRET_PATTERNS.items()}

    def detect(
        self, context_type: str, content: str, metadata: Dict[str, Any] | None = None
    ) -> List[FirewallFinding]:
        findings: List[FirewallFinding] = []
        if not content:
            return findings

        for secret_type, regex in self._compiled.items():
            for match in regex.finditer(content):
                findings.append(
                    FirewallFinding(
                        detector_name=self.name,
                        category=self.category,
                        severity="critical",
                        message=f"Secret/Credential ({secret_type}) detected in {context_type}",
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

        for secret_type, regex in self._compiled.items():
            matches = list(regex.finditer(sanitized))
            for match in matches:
                findings.append(
                    FirewallFinding(
                        detector_name=self.name,
                        category=self.category,
                        severity="critical",
                        message=f"Redacted Secret ({secret_type}) in {context_type}",
                        location=context_type,
                        action_taken=self.action,
                        matched_text=match.group(0),
                    )
                )
            if self.action in (SanitizationAction.REDACT, SanitizationAction.DROP):
                sanitized = regex.sub(f"[REDACTED_SECRET:{secret_type}]", sanitized)

        return sanitized, findings


__all__ = ["SecretsDetector"]
