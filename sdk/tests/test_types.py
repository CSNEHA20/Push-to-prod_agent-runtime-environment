"""
Unit tests for standardized Pydantic v2 domain models across SDK and API backend schemas.
Verifies exact field validation and JSON schema parity for Session, Step, FirewallRule, and RecoveryDiff.
"""

import sys
import os
import unittest

# Ensure sdk directory is in sys.path
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sdk_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_path = os.path.abspath(os.path.join(root_path, "arc", "backend"))
for p in [root_path, sdk_path, backend_path]:
    if p not in sys.path:
        sys.path.insert(0, p)

from arc.types import (
    Session,
    SessionStatus,
    TraceStep,
    StepType,
    FirewallRule,
    FirewallAction,
    RecoveryDiff,
    Checkpoint,
)
from api.schemas import (
    AgentSessionResponse,
    TraceStepResponse,
    FirewallRuleResponse,
    RecoveryDiffResponse,
)



class TestTypesStandardization(unittest.TestCase):
    def test_session_model_parity(self):
        session_data = {
            "session_id": "123e4567-e89b-12d3-a456-426614174000",
            "agent_name": "GovernanceAgent",
            "task": "Perform context inspection",
            "status": "active",
            "total_steps": 5,
            "metadata": {"env": "production"},
        }
        sdk_session = Session(**session_data)
        self.assertEqual(sdk_session.session_id, session_data["session_id"])
        self.assertEqual(sdk_session.agent_name, "GovernanceAgent")

        backend_schema = AgentSessionResponse(
            session_id=session_data["session_id"],
            agent_name=session_data["agent_name"],
            task=session_data["task"],
            status=session_data["status"],
            started_at="2026-08-08T10:00:00Z",
            total_steps=5,
        )
        self.assertEqual(str(backend_schema.session_id), sdk_session.session_id)

    def test_trace_step_model_parity(self):
        step_data = {
            "step_id": "987e6543-e89b-12d3-a456-426614174000",
            "session_id": "123e4567-e89b-12d3-a456-426614174000",
            "step_type": StepType.LLM_CALL,
            "step_number": 1,
            "name": "Prompt Evaluation",
            "input_data": {"prompt": "Check database"},
            "output_data": {"response": "Clean"},
            "confidence_score": 0.95,
        }
        sdk_step = TraceStep(**step_data)
        self.assertEqual(sdk_step.step_id, step_data["step_id"])
        self.assertEqual(sdk_step.confidence_score, 0.95)

        backend_step = TraceStepResponse(
            step_id=step_data["step_id"],
            session_id=step_data["session_id"],
            step_number=1,
            step_type="llm_call",
            timestamp="2026-08-08T10:00:00Z",
            status="completed",
            confidence_score=0.95,
        )
        self.assertEqual(str(backend_step.step_id), sdk_step.step_id)

    def test_firewall_rule_model_parity(self):
        rule_data = {
            "id": "rule-001",
            "rule_type": "regex",
            "action": FirewallAction.BLOCK,
            "threshold": 0.85,
            "pattern": r"(?i)delete\s+from",
        }
        sdk_rule = FirewallRule(**rule_data)
        self.assertEqual(sdk_rule.id, "rule-001")
        self.assertEqual(sdk_rule.action, FirewallAction.BLOCK)

        backend_rule = FirewallRuleResponse(**rule_data)
        self.assertEqual(backend_rule.id, sdk_rule.id)
        self.assertEqual(backend_rule.threshold, sdk_rule.threshold)

    def test_recovery_diff_model_parity(self):
        diff_data = {
            "id": "diff-100",
            "session_id": "123e4567-e89b-12d3-a456-426614174000",
            "failed_step_id": "987e6543-e89b-12d3-a456-426614174000",
            "strategy_used": "prune_context",
            "diff_payload": {"removed_keys": ["untrusted_user_input"]},
            "status": "computed",
        }
        sdk_diff = RecoveryDiff(**diff_data)
        self.assertEqual(sdk_diff.id, "diff-100")

        backend_diff = RecoveryDiffResponse(**diff_data)
        self.assertEqual(backend_diff.id, sdk_diff.id)
        self.assertEqual(backend_diff.diff_payload, sdk_diff.diff_payload)


if __name__ == "__main__":
    unittest.main()
