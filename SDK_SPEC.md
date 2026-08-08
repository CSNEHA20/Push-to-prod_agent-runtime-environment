# ARC SDK Specification (`arc-sdk`)

The `arc-sdk` Python package provides production-grade agent reliability, context firewalling, step tracing, and auto-recovery across multiple LLM providers and agent frameworks.

---

## 1. Top-Level Imports & Exports (`arc`)

```python
import arc

# Core Initialization & Configuration
arc.init(
    api_key="arc_dev_key",
    server_url="http://localhost:8000",
    provider="anthropic", # anthropic | openai | gemini
)

# High-Level Agent Wrappers
agent = arc.Agent(
    name="Data Analyst",
    task="Analyze sales trends",
    provider="openai",    # Optional provider override
    model="gpt-4o",
)

# Protection Decorator Pattern
@arc.protected(name="Financial Engine", task="Calculate Risk Ratio")
def compute_risk(portfolio_val: float) -> float:
    return portfolio_val * 0.15
```

---

## 2. Provider-Agnostic Client Interfaces

```python
from arc import ARC, AsyncARC

# Synchronous HTTP Client
with ARC(server_url="http://localhost:8000") as client:
    session = client.create_session(agent_name="Analyst", task="Analyze data")
    trace = client.get_trace(session.session_id)

# Asynchronous HTTP Client
async with AsyncARC(server_url="http://localhost:8000") as client:
    session = await client.acreate_session(agent_name="Analyst", task="Analyze data")
    trace = await client.aget_trace(session.session_id)
```

---

## 3. Provider Adapters (`arc.providers`)

- **`arc.providers.AnthropicAdapter`**: Native adapter for Anthropic Claude.
- **`arc.providers.OpenAIAdapter`**: Native adapter for OpenAI GPT & O-series models.
- **`arc.providers.GeminiAdapter`**: Native adapter for Google Gemini 1.5/2.0 models.

---

## 4. Framework Integration Adapters (`arc.integrations`)

- **`arc.integrations.langgraph.LangGraphAdapter`**: Protection middleware for LangGraph StateGraph nodes.
- **`arc.integrations.crewai.CrewAIAdapter`**: Protection middleware for CrewAI tasks and agents.
- **`arc.integrations.autogen.AutoGenAdapter`**: Protection middleware for AutoGen conversational agent loops.
- **`arc.integrations.openhands.OpenHandsAdapter`**: Protection middleware for OpenHands event stream execution.
- **`arc.integrations.mcp.MCPToolRouter`**: Protocol gateway for Model Context Protocol (MCP) tool servers.

---

## 5. Domain Data Models (`arc.types`)

```python
class Session(BaseModel):
    session_id: str
    agent_name: str
    task: str
    status: SessionStatus # active | running | completed | failed | recovered
    created_at: str
    total_steps: int
    metadata: Dict[str, Any]

class TraceStep(BaseModel):
    step_id: str
    session_id: str
    step_type: StepType   # llm_call | tool_call | checkpoint | verification | recovery_rollback
    step_number: int
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    confidence_score: float
    timestamp: str

class FirewallRule(BaseModel):
    id: str
    rule_type: str        # regex | vector | heuristic
    action: FirewallAction # allow | block | sanitize
    threshold: float
    pattern: Optional[str]

class RecoveryDiff(BaseModel):
    id: str
    session_id: str
    failed_step_id: str
    strategy_used: str
    diff_payload: Dict[str, Any]
    status: str
```
