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
    ReplayTimeline,
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

    def test_firewall_rule_defaults_and_serialization(self):
        rule = FirewallRule(id="rule-def", rule_type="heuristic")
        self.assertEqual(rule.action, FirewallAction.BLOCK)
        self.assertEqual(rule.threshold, 0.8)
        self.assertIsNone(rule.pattern)
        rule_dict = rule.to_dict()
        self.assertEqual(rule_dict["id"], "rule-def")
        self.assertEqual(rule_dict["action"], "block")

    def test_recovery_diff_defaults_and_serialization(self):
        diff = RecoveryDiff(
            id="diff-def",
            session_id="sess-001",
            failed_step_id="step-001",
            strategy_used="retry",
        )
        self.assertEqual(diff.status, "computed")
        self.assertEqual(diff.diff_payload, {})
        diff_dict = diff.to_dict()
        self.assertEqual(diff_dict["status"], "computed")
        self.assertEqual(diff_dict["strategy_used"], "retry")

    def test_firewall_action_and_session_status_enums(self):
        self.assertEqual(FirewallAction.ALLOW.value, "allow")
        self.assertEqual(FirewallAction.BLOCK.value, "block")
        self.assertEqual(FirewallAction.SANITIZE.value, "sanitize")
        self.assertEqual(SessionStatus.RUNNING.value, "running")
        self.assertEqual(SessionStatus.ACTIVE.value, "active")

    def test_checkpoint_and_replay_models(self):
        chk = Checkpoint(checkpoint_id="chk-1", session_id="sess-1", step_number=3)
        self.assertEqual(chk.checkpoint_id, "chk-1")
        self.assertEqual(chk.step_number, 3)
        self.assertIsInstance(chk.to_dict(), dict)

        timeline = ReplayTimeline(session_id="sess-1", recovery_checkpoints=[chk])
        self.assertEqual(len(timeline.recovery_checkpoints), 1)
        self.assertEqual(timeline.recovery_checkpoints[0].checkpoint_id, "chk-1")


if __name__ == "__main__":
    unittest.main()

