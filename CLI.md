# ARC CLI Tool Specification

The `arc` CLI tool (`sdk/arc/cli.py`) provides terminal commands to inspect, replay, recover, and verify agent sessions directly from the command line.

---

## Commands Syntax

```bash
# Display CLI version
arc --version

# Initialize local configuration (.arc.json)
arc init --api-key <key> --server-url http://localhost:8000

# Inspect session state and step metrics
arc inspect <session_id>

# Retrieve and print full execution step trace
arc trace <session_id>

# Retrieve visual replay timeline
arc replay <session_id>

# Check available recovery checkpoints
arc recover <session_id>

# Verify trace compliance against Context Firewall rules
arc verify <session_id>
```

---

## Environment Variables

- `ARC_API_KEY`: API key for ARC control plane authentication.
- `ARC_SERVER_URL`: Base URL of ARC backend server (default: `http://localhost:8000`).
- `ANTHROPIC_API_KEY`: Anthropic API key for Claude integration.
