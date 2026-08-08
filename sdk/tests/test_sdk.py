import sys
import os
import unittest

# Ensure sdk directory is in sys.path
sdk_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if sdk_path not in sys.path:
    sys.path.insert(0, sdk_path)

import arc
import arc_sdk
from arc_sdk import ARCClient, ARCAgent


class TestARCSDKLegacy(unittest.TestCase):
    def setUp(self):
        arc_sdk.init(
            api_key="test-api-key",
            anthropic_api_key="mock-key",
            server_url="http://localhost:8000",
            dashboard_url="http://localhost:3000",
        )

    def test_init_and_exports(self):
        self.assertEqual(arc_sdk._global_config["api_key"], "test-api-key")
        self.assertEqual(arc_sdk.Agent, ARCAgent)
        self.assertEqual(arc_sdk.Client, ARCClient)
        self.assertEqual(arc_sdk.__version__, arc.__version__)

    def test_agent_creation_and_properties(self):
        agent = arc_sdk.Agent(name="Test Agent", task="Run test suite")
        self.assertIsNotNone(agent.session_id)
        self.assertTrue(agent.dashboard_url.startswith("http://localhost:3000/sessions/"))
        self.assertIn(agent.session_id, agent.dashboard_url)

    def test_agent_call_claude(self):
        agent = arc_sdk.Agent(name="Test Agent", task="Run test suite")
        result = agent.call_claude([{"role": "user", "content": "Hello ARC"}])
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_agent_run_tool(self):
        def sample_tool(args):
            return {"echo": args["val"] * 2}

        agent = arc_sdk.Agent(name="Test Agent", task="Run test suite")
        res = agent.run_tool("sample_tool", {"val": 21}, sample_tool)
        self.assertEqual(res, {"echo": 42})

    def test_agent_complete(self):
        agent = arc_sdk.Agent(name="Test Agent", task="Run test suite")
        res = agent.complete(output="All done!")
        self.assertIsNotNone(res)

    def test_client_instantiation(self):
        client = ARCClient(api_key="test-key", server_url="http://localhost:8000")
        self.assertEqual(client.server_url, "http://localhost:8000")
        self.assertIn("Authorization", client.headers)


if __name__ == "__main__":
    unittest.main()
