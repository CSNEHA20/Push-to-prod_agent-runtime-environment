import sys
import unittest
from unittest.mock import patch, MagicMock
from io import StringIO

from arc.cli import main, cmd_version, cmd_init


class TestARCCLI(unittest.TestCase):
    @patch("sys.stdout", new_callable=StringIO)
    def test_cli_version(self, mock_stdout):
        with patch("sys.argv", ["arc", "version"]):
            main()
        output = mock_stdout.getvalue()
        self.assertIn("ARC SDK v0.1.0", output)

    @patch("arc.client.ARCClient.get_trace")
    @patch("sys.stdout", new_callable=StringIO)
    def test_cli_trace(self, mock_stdout, mock_trace):
        mock_trace.return_value = [{"step_id": "step-1"}]
        with patch("sys.argv", ["arc", "trace", "sess-123"]):
            main()
        output = mock_stdout.getvalue()
        self.assertIn("step-1", output)

    @patch("arc.client.ARCClient.get_replay")
    @patch("sys.stdout", new_callable=StringIO)
    def test_cli_replay(self, mock_stdout, mock_replay):
        mock_replay.return_value = {"status": "ok"}
        with patch("sys.argv", ["arc", "replay", "sess-123"]):
            main()
        output = mock_stdout.getvalue()
        self.assertIn("ok", output)

    @patch("arc.client.ARCClient.get_session")
    @patch("sys.stdout", new_callable=StringIO)
    def test_cli_inspect(self, mock_stdout, mock_inspect):
        mock_inspect.return_value = {"id": "sess-123"}
        with patch("sys.argv", ["arc", "inspect", "sess-123"]):
            main()
        output = mock_stdout.getvalue()
        self.assertIn("sess-123", output)


if __name__ == "__main__":
    unittest.main()
