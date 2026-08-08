# ARC Python SDK (`arc-sdk`)

> **Agent Runtime Core (ARC)** — The missing reliability layer between Claude and the real world.

The `arc-sdk` library allows Python developers to easily add Flight Recorder step tracing, Context Firewall filtering, and Recovery Engine auto-rollback protection to any Claude agent application.

---

## ⚡ Quick Start

### 1. Installation

```bash
pip install arc-sdk
```

### 2. 5-Line Minimal Example

```python
import arc_sdk

# Initialize SDK credentials
arc_sdk.init(api_key="arc_dev_key", anthropic_api_key="sk-ant-api03-...")

# Create an ARC-protected agent session
agent = arc_sdk.Agent(name="Research Agent", task="Summarize Q3 financial report")

# Call Claude with automatic ARC Flight Recorder & Context Firewall protection
response = agent.call_claude(
    messages=[{"role": "user", "content": "Summarize key growth drivers."}]
)

print("Claude Response:", response)
print("Live Session Dashboard URL:", agent.dashboard_url)
```

---

## 🛡️ Core Features

- **Flight Recorder (Engine 1):** Full execution step recording, token tracking, confidence heuristics, and step-by-step visual replay.
- **Context Firewall (Engine 2):** Real-time context filtering, relevance scoring, and numerical/temporal/factual conflict detection.
- **Recovery Engine (Engine 3):** Automated state checkpointing, failure detection, rollback, and single-step retry recovery.

---

## 📖 SDK Reference

### `ARCClient`
```python
from arc_sdk import ARCClient

client = ARCClient(server_url="http://localhost:8000")

# Fetch recent agent sessions
sessions = client.get_sessions(limit=10)

# Fetch trace steps for a session
trace = client.get_trace(session_id="<session-uuid>")

# Fetch visual replay object
replay = client.get_replay(session_id="<session-uuid>")
```

### `ARCAgent`
```python
agent = arc_sdk.Agent(name="My Agent", task="Perform workflow")

# Execute Claude API call
output = agent.call_claude(messages=[...], context_sources=[...])

# Execute agent tool with automatic tracing and checkpointing
tool_result = agent.run_tool("search_db", {"query": "Q3"}, search_fn)

# Mark session completed
agent.complete(output="Task finished")
```

---

## 🔗 Resources
- **ARC Backend API:** `http://localhost:8000`
- **ARC Developer Dashboard:** `http://localhost:3000`
