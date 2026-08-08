import unittest
from unittest.mock import MagicMock, patch
import arc


class TestARCTopLevelAPI(unittest.TestCase):
    def setUp(self):
        arc.init(
            api_key="test-key",
            anthropic_api_key="mock-key",
            server_url="http://localhost:8000",
            dashboard_url="http://localhost:3000",
        )

    def test_version_exported(self):
        self.assertEqual(arc.__version__, "0.1.0")

    def test_init_and_global_config(self):
        self.assertEqual(arc._global_config["api_key"], "test-key")
        self.assertEqual(arc._global_config["server_url"], "http://localhost:8000")

    def test_agent_factory(self):
        agent = arc.Agent(name="TestAgent", task="Testing task")
        self.assertIsInstance(agent, arc.ARCAgent)
        self.assertEqual(agent.name, "TestAgent")
        self.assertIsNotNone(agent.session_id)
        self.assertTrue(agent.dashboard_url.startswith("http://localhost:3000/sessions/"))

    def test_run_agent(self):
        agent = arc.Agent(name="Runner", task="Run task")
        res = arc.run(agent)
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("status"), "completed")

    def test_run_callable(self):
        def sample_task(x):
            return x * 2

        res = arc.run(sample_task, x=21)
        self.assertEqual(res, 42)

    @patch("arc.client.ARCClient.get_trace")
    def test_trace(self, mock_get_trace):
        mock_get_trace.return_value = [{"step_id": "step-1"}]
        result = arc.trace("session-123")
        mock_get_trace.assert_called_once_with("session-123")
        self.assertEqual(result, [{"step_id": "step-1"}])

    @patch("arc.client.ARCClient.get_replay")
    def test_replay(self, mock_get_replay):
        mock_get_replay.return_value = {"timeline": []}
        result = arc.replay("session-123")
        mock_get_replay.assert_called_once_with("session-123")
        self.assertEqual(result, {"timeline": []})

    @patch("arc.client.ARCClient.get_session")
    def test_inspect(self, mock_get_session):
        mock_get_session.return_value = {"session_id": "session-123", "status": "active"}
        result = arc.inspect("session-123")
        mock_get_session.assert_called_once_with("session-123")
        self.assertEqual(result.get("status"), "active")

    @patch("arc.client.ARCClient.get_recovery")
    def test_recover(self, mock_get_recovery):
        mock_get_recovery.return_value = {"recovery_plan": []}
        result = arc.recover("session-123")
        mock_get_recovery.assert_called_once_with("session-123")
        self.assertEqual(result, {"recovery_plan": []})

    @patch("arc.client.ARCClient.verify_session")
    def test_verify(self, mock_verify):
        mock_verify.return_value = {"valid": True, "conflicts": []}
        result = arc.verify("session-123")
        mock_verify.assert_called_once_with("session-123", rules=None)
        self.assertEqual(result, {"valid": True, "conflicts": []})


if __name__ == "__main__":
    unittest.main()
