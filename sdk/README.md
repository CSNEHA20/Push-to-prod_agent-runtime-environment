# ARC Python SDK (`arc-sdk`)

> **Agent Runtime Core (ARC)** — Clean Python SDK for Claude AI agents with Flight Recorder step tracing, Context Firewall filtering, and Recovery Engine auto-rollback.

---

## ⚡ Quick Start

### 1. Installation

```bash
pip install arc-sdk
```

### 2. 5-Line Minimal Example

```python
import arc_sdk

# 1. Initialize credentials
arc_sdk.init(api_key="arc_dev_key", anthropic_api_key="sk-ant-...")

# 2. Create ARC-protected agent session
agent = arc_sdk.Agent(name="My Agent", task="Do something")

# 3. Call Claude via ARC Runtime
result = agent.call_claude([{"role": "user", "content": "Summarize key findings"}])

# 4. View live execution dashboard URL
print(agent.dashboard_url)
```

---

## 🛡️ Core Features

- **Flight Recorder (Engine 1):** Step-by-step trace recording, token tracking, confidence heuristics, and timeline replay.
- **Context Firewall (Engine 2):** Context filtering, factual/numerical conflict detection ($7.3B vs $8.1B funding), and provenance tagging.
- **Recovery Engine (Engine 3):** Automated state checkpointing, low-confidence failure detection, rollback, and single-step retry recovery.

---

## 📖 Core API Reference

### `ARCClient`
```python
from arc_sdk import ARCClient

client = ARCClient(server_url="http://localhost:8000")

# List recent sessions
sessions = client.get_sessions(limit=50)

# Get specific session details
session = client.get_session("<session-id>")

# Get step trace
trace = client.get_trace("<session-id>")

# Get visual replay object
replay = client.get_replay("<session-id>")
```

### `ARCAgent`
```python
import arc_sdk

agent = arc_sdk.Agent(name="Research Agent", task="Analyze financial data")

# Call Claude with Context Firewall conflict detection
response = agent.call_claude(
    messages=[{"role": "user", "content": "Write financial analysis"}],
    context_sources=[
        {"name": "report1.pdf", "content": "Q3 Revenue was $7.3B"},
        {"name": "blog.html", "content": "Q3 Revenue was $8.1B"}
    ]
)

# Run tool with Flight Recorder step tracing and state checkpointing
tool_res = agent.run_tool("search_overview", {"query": "Anthropic"}, search_fn)

# Mark session completed
agent.complete(output=response)

print("Dashboard URL:", agent.dashboard_url)
```

---

## 🔗 Documentation & Links
- **ARC GitHub Repository:** [Agent Runtime Core](https://github.com/Vishallakshmikanthan/agent-runtime-core)
- **ARC Backend API:** `http://localhost:8000/docs`
- **ARC Developer Dashboard:** `http://localhost:3000`
