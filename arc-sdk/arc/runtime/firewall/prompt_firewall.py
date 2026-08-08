"""Prompt Firewall — inspects and sanitizes system prompts, messages, tool outputs,
retrieved documents, memory, and attachments before they reach the provider.
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Tuple

from arc.types import ConflictItem, FirewallFinding, PromptFirewallResult, RequestContext
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

RELEVANCE_FLOOR = 0.3


def _relevance(source: Dict[str, Any]) -> float:
    """Return the source's declared relevance score, defaulting to 1.0."""
    val = source.get("relevance", source.get("score", 1.0))
    try:
        return float(val)
    except (TypeError, ValueError):
        return 1.0


class PromptFirewall:
    """Enterprise Prompt Firewall with pluggable detector pipeline.

    Inspects:
    * System prompts
    * Messages
    * Tool outputs
    * Retrieved documents
    * Memory
    * Attachments
    """

    def __init__(
        self,
        detectors: List[BaseDetector] | None = None,
        relevance_floor: float = RELEVANCE_FLOOR,
        strict_block: bool = False,
    ) -> None:
        self.relevance_floor = relevance_floor
        self.strict_block = strict_block
        if detectors is None:
            self.detectors: List[BaseDetector] = [
                PromptInjectionDetector(),
                JailbreakDetector(),
                PIIDetector(),
                SecretsDetector(),
                RecursivePromptingDetector(),
                PromptLeakageDetector(),
                ContextExplosionDetector(),
                DuplicateContextDetector(),
            ]
        else:
            self.detectors = detectors

    def filter(
        self, sources: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[ConflictItem]]:
        """Legacy interface: filter context sources by relevance and detect conflicts."""
        surviving: List[Dict[str, Any]] = []
        for src in sources:
            if _relevance(src) >= self.relevance_floor:
                sanitized_src, _ = self._sanitize_text("retrieved_document", src.get("content", ""))
                src_copy = dict(src)
                src_copy["content"] = sanitized_src
                surviving.append(src_copy)

        return surviving, self._detect_conflicts(surviving)

    def inspect_and_sanitize(self, request: RequestContext) -> PromptFirewallResult:
        """Inspect all 6 input targets and sanitize payload before provider dispatch."""
        payload = copy.deepcopy(request.payload)
        context_sources = copy.deepcopy(request.context_sources)
        findings: List[FirewallFinding] = []

        # Reset duplicate detectors if present
        for detector in self.detectors:
            if hasattr(detector, "reset") and callable(getattr(detector, "reset")):
                detector.reset()

        # 1. System Prompt Inspection & Sanitization
        if "system" in payload and payload["system"]:
            payload["system"], sys_findings = self._sanitize_system(payload["system"])
            findings.extend(sys_findings)

        # 2. Messages & Tool Outputs Inspection & Sanitization
        if "messages" in payload and isinstance(payload["messages"], list):
            payload["messages"], msg_findings = self._sanitize_messages(payload["messages"])
            findings.extend(msg_findings)

        # 3. Retrieved Documents Inspection & Sanitization
        sanitized_sources, conflicts = self.filter(context_sources)

        # 4. Memory Inspection & Sanitization
        if "memory" in payload:
            payload["memory"], mem_findings = self._sanitize_memory(payload["memory"])
            findings.extend(mem_findings)

        # 5. Attachments Inspection & Sanitization
        if "attachments" in payload:
            payload["attachments"], att_findings = self._sanitize_attachments(payload["attachments"])
            findings.extend(att_findings)

        is_safe = not any(f.severity in ("high", "critical") and f.action_taken == "block" for f in findings)
        if self.strict_block and any(f.severity in ("high", "critical") for f in findings):
            is_safe = False

        return PromptFirewallResult(
            is_safe=is_safe,
            sanitized_payload=payload,
            sanitized_sources=sanitized_sources,
            findings=findings,
            conflicts=conflicts,
        )

    def _sanitize_text(
        self, context_type: str, text: str
    ) -> Tuple[str, List[FirewallFinding]]:
        findings: List[FirewallFinding] = []
        current = text
        for detector in self.detectors:
            current, det_findings = detector.sanitize(context_type, current)
            findings.extend(det_findings)
        return current, findings

    def _sanitize_system(self, system: Any) -> Tuple[Any, List[FirewallFinding]]:
        if isinstance(system, str):
            return self._sanitize_text("system_prompt", system)
        elif isinstance(system, list):
            findings: List[FirewallFinding] = []
            sanitized_list = []
            for block in system:
                if isinstance(block, dict) and "text" in block:
                    txt, f = self._sanitize_text("system_prompt", str(block["text"]))
                    findings.extend(f)
                    b_copy = dict(block)
                    b_copy["text"] = txt
                    sanitized_list.append(b_copy)
                else:
                    sanitized_list.append(block)
            return sanitized_list, findings
        return system, []

    def _sanitize_messages(self, messages: List[Any]) -> Tuple[List[Any], List[FirewallFinding]]:
        findings: List[FirewallFinding] = []
        sanitized_msgs = []
        for idx, msg in enumerate(messages):
            if not isinstance(msg, dict):
                sanitized_msgs.append(msg)
                continue
            role = msg.get("role", "user")
            content = msg.get("content")
            m_copy = dict(msg)

            if isinstance(content, str):
                ctx_name = f"messages[{idx}].{role}"
                txt, f = self._sanitize_text(ctx_name, content)
                findings.extend(f)
                m_copy["content"] = txt
            elif isinstance(content, list):
                sanitized_blocks = []
                for b_idx, block in enumerate(content):
                    if isinstance(block, dict):
                        b_type = block.get("type")
                        if b_type == "text":
                            ctx_name = f"messages[{idx}].{role}.text[{b_idx}]"
                            txt, f = self._sanitize_text(ctx_name, block.get("text", ""))
                            findings.extend(f)
                            b_copy = dict(block)
                            b_copy["text"] = txt
                            sanitized_blocks.append(b_copy)
                        elif b_type == "tool_result":
                            ctx_name = f"messages[{idx}].tool_output[{block.get('tool_use_id', b_idx)}]"
                            res_content = block.get("content", "")
                            if isinstance(res_content, str):
                                txt, f = self._sanitize_text(ctx_name, res_content)
                                findings.extend(f)
                                b_copy = dict(block)
                                b_copy["content"] = txt
                                sanitized_blocks.append(b_copy)
                            else:
                                sanitized_blocks.append(block)
                        else:
                            sanitized_blocks.append(block)
                    else:
                        sanitized_blocks.append(block)
                m_copy["content"] = sanitized_blocks

            sanitized_msgs.append(m_copy)

        return sanitized_msgs, findings

    def _sanitize_memory(self, memory: Any) -> Tuple[Any, List[FirewallFinding]]:
        if isinstance(memory, str):
            return self._sanitize_text("memory", memory)
        elif isinstance(memory, list):
            findings: List[FirewallFinding] = []
            sanitized_list = []
            for item in memory:
                if isinstance(item, str):
                    txt, f = self._sanitize_text("memory", item)
                    findings.extend(f)
                    sanitized_list.append(txt)
                else:
                    sanitized_list.append(item)
            return sanitized_list, findings
        return memory, []

    def _sanitize_attachments(self, attachments: Any) -> Tuple[Any, List[FirewallFinding]]:
        if isinstance(attachments, list):
            findings: List[FirewallFinding] = []
            sanitized_list = []
            for item in attachments:
                if isinstance(item, dict) and "content" in item:
                    txt, f = self._sanitize_text("attachment", str(item["content"]))
                    findings.extend(f)
                    i_copy = dict(item)
                    i_copy["content"] = txt
                    sanitized_list.append(i_copy)
                elif isinstance(item, str):
                    txt, f = self._sanitize_text("attachment", item)
                    findings.extend(f)
                    sanitized_list.append(txt)
                else:
                    sanitized_list.append(item)
            return sanitized_list, findings
        return attachments, []

    def _detect_conflicts(self, sources: List[Dict[str, Any]]) -> List[ConflictItem]:
        conflicts: List[ConflictItem] = []
        seen: Dict[str, Any] = {}
        for source in sources:
            key = source.get("key")
            claim = source.get("claim")
            if key is None or claim is None:
                continue
            if key in seen and seen[key] != claim:
                conflicts.append(
                    ConflictItem(
                        source_id=str(source.get("id", key)),
                        conflict_type="contradiction",
                        description=f"Conflicting claims for '{key}'",
                    )
                )
            else:
                seen[key] = claim
        return conflicts


__all__ = ["PromptFirewall", "RELEVANCE_FLOOR"]
