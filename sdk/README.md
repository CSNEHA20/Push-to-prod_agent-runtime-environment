# ARC Python SDK (`arc-sdk`)

> **Agent Runtime Core (ARC)** - Production-grade Python SDK for Claude AI agents featuring Flight Recorder step tracing, Context Firewall filtering, and Recovery Engine auto-rollback.

Built to Anthropic's enterprise SDK standards: fully typed (PEP 561), native sync & async HTTP clients (`ARC` & `AsyncARC`), exponential backoff retries, transparent Anthropic client middleware wrapping, context managers, and CLI tooling.

---

## ⚡ Quick Start

### 1. Installation

```bash
pip install arc-sdk
```

Or install in editable mode from source:
```bash
git clone https://github.com/Vishallakshmikanthan/agent-runtime-core.git
cd agent-runtime-core/sdk
pip install -e .
```

---

## 🚀 Usage Examples

### Synchronous Usage with Anthropic Client Wrapping

```python
import anthropic
import arc

# 1. Initialize global credentials
arc.init(api_key="arc_dev_key", anthropic_api_key="sk-ant-...")

# 2. Wrap existing Anthropic client in ARC protection middleware
client = anthropic.Anthropic()
protected_agent = arc.wrap(client, name="Market Analyst", task="Analyze Q3 trends")

# 3. Call Claude under ARC protection
response = protected_agent.call_claude([{"role": "user", "content": "Summarize key findings"}])
print("Response:", response)

# 4. View live dashboard link
print("Dashboard URL:", protected_agent.dashboard_url)
```

### Asynchronous Native Usage (`AsyncARC` & `AsyncARCAgent`)

```python
import asyncio
from arc import AsyncARC, AsyncARCAgent

async def main():
    async with AsyncARC(server_url="http://localhost:8000") as arc_client:
        agent = AsyncARCAgent(name="Stream Processor", task="Process live data", arc_client=arc_client, mock_mode=True)
        
        # Protected step tracing context manager
        async with agent.atrace_step("fetch_data", input_data={"stream_id": 42}):
            # Perform processing step
            await asyncio.sleep(0.1)

        result = await agent.acomplete(output={"status": "success"})
        print("Async Session Complete:", result)

asyncio.run(main())
```

### Function Decorator Pattern (`@arc.protected`)

```python
import arc

@arc.protected(name="Financial Engine", task="Calculate Risk Ratio")
def compute_risk(portfolio_value: float, volatility: float) -> float:
    return portfolio_value * volatility

risk_score = compute_risk(100000.0, 0.15)
print("Risk Score:", risk_score)
```

---

## 📖 Public API Surface Reference

The `arc-sdk` package exposes the following primary functions and models on the `arc` namespace:

| Symbol | Type | Description |
| :--- | :--- | :--- |
| `arc.init(...)` | Function | Initialize global API keys, server URLs, and default client settings. |
| `arc.wrap(client)` | Function | Wrap an Anthropic sync/async client in ARC protection middleware. |
| `arc.protected(...)` | Decorator | Decorator for protecting functions with step tracing and recovery. |
| `arc.ARC` | Class | Production-grade synchronous HTTP client built natively on `httpx.Client`. |
| `arc.AsyncARC` | Class | Production-grade asynchronous HTTP client built natively on `httpx.AsyncClient`. |
| `arc.ARCAgent` | Class | Synchronous agent protection wrapper. |
| `arc.AsyncARCAgent` | Class | Asynchronous agent protection wrapper. |
| `arc.Session` | Model | Strongly typed Session data model (Pydantic). |
| `arc.TraceStep` | Model | Strongly typed TraceStep data model (Pydantic). |
| `arc.VerificationResult` | Model | Strongly typed Context Firewall verification result. |
| `arc.FirewallRule` | Model | Strongly typed Context Firewall security rule model. |
| `arc.RecoveryDiff` | Model | Strongly typed Recovery Engine state diff model. |
| `arc.ReplayTimeline` | Model | Visual replay timeline data model. |
| `arc.RecoveryPlan` | Model | Recovery Engine strategy data model. |


---

## 🖥️ Command Line Interface (CLI)

The `arc-sdk` package registers the `arc` terminal command.

```bash
# Print version
arc --version

# Initialize local config file (.arc.json)
arc init --api-key "arc_key_123" --server-url "http://localhost:8000"

# Inspect session details
arc inspect <session_id>

# Retrieve execution trace
arc trace <session_id>

# Retrieve visual replay timeline
arc replay <session_id>

# Inspect recovery checkpoints
arc recover <session_id>

# Verify Context Firewall trace compliance
arc verify <session_id>
```

---

## 🛡️ Core Reliability Engines

- **Flight Recorder (Engine 1):** Step-by-step trace recording, token tracking, confidence heuristics, and timeline replay.
- **Context Firewall (Engine 2):** Context filtering, factual/numerical conflict detection ($7.3B vs $8.1B funding), and provenance tagging.
- **Recovery Engine (Engine 3):** Automated state checkpointing, low-confidence failure detection, rollback, and single-step retry recovery.

---

## 🧪 Testing & Verification

Run the test suite using `pytest`:

```bash
cd sdk
pytest tests -v
```

---

## 🔗 Documentation & Links
- **Technical Guide:** [docs/SDK_GUIDE.md](file:///c:/Users/Lenovo/Downloads/agent-runtime-core/docs/SDK_GUIDE.md)
- **ARC Backend API:** `http://localhost:8000/docs`
- **ARC Developer Dashboard:** `http://localhost:3000`
