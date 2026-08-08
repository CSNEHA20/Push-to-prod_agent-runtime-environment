# ARC Master Architecture Specification

This document details the provider-agnostic system architecture, component abstractions, runtime flow, engine specifications, and MCP integration layer for Agent Runtime Core (ARC).

---

## 1. Provider-Agnostic Abstraction Layer

ARC decouples execution logic from specific LLM providers via the `BaseProviderAdapter` interface:

```python
class BaseProviderAdapter(ABC):
    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> ProviderResponse:
        """Provider-agnostic response generation."""
        pass
```

### Supported Provider Implementations:
- **`AnthropicAdapter`**: Supports Claude models (`claude-3-7-sonnet`, `claude-3-5-haiku`) with native system prompt & tool use mapping.
- **`OpenAIAdapter`**: Supports GPT models (`gpt-4o`, `gpt-4o-mini`, `o3-mini`) with function calling & system message mapping.
- **`GeminiAdapter`**: Supports Google Gemini models (`gemini-1.5-pro`, `gemini-2.0-flash`) via Vertex AI / Google AI SDK integration.

---

## 2. Framework Integration Layer

ARC provides native middleware adapters for leading AI agent frameworks via `BaseFrameworkAdapter`:

1. **`LangGraphAdapter`**: Wraps LangGraph state nodes to inject Flight Recorder tracing, step checkpointing, and Context Firewall evaluation before graph transitions.
2. **`CrewAIAdapter`**: Intercepts task assignments and agent delegations in CrewAI multi-agent teams.
3. **`AutoGenAdapter`**: Monitors conversational turns between AutoGen agents, enforcing context conflict resolution.
4. **`OpenHandsAdapter`**: Integrates with OpenHands event streams to validate file system and terminal tool actions.
5. **`CustomAgentAdapter`**: Lightweight wrapper (`@arc.protected`) for custom python agent loops.

---

## 3. Model Context Protocol (MCP) Server Integration

ARC acts as an **MCP Tool Gateway**:
- **Tool Discovery**: Scans connected MCP servers for exported tool schemas.
- **Firewall Verification**: Evaluates MCP tool inputs against Context Firewall rules prior to invocation.
- **Trace Capture**: Records MCP tool calls and returned payloads into Flight Recorder.

```
[Agent] ---> [ARC MCP Router] ---> [Context Firewall] ---> [MCP Server]
                                          |
                                          v
                                 [Flight Recorder]
```

---

## 4. Engine Architecture & Runtime Pipeline

```
[Agent Call Initiated]
          |
          v
[Engine 2: Context Firewall]
   ├── Relevance Scoring (Filter < 0.3)
   ├── Pairwise Conflict Detection
   └── System Prompt Formatting + Provenance Tagging
          |
          v
[Provider Adapter Dispatch (Anthropic / OpenAI / Gemini)]
          |
          v
[Engine 1: Flight Recorder]
   ├── Record Step Metadata & Heuristic Confidence Score
   └── Broadcast Live Telemetry via WebSockets / Redis PubSub
          |
          v
[Confidence Check]
   ├── Score >= 0.2 --> Commit & Return Result
   └── Score < 0.2  --> [Engine 3: Recovery Engine]
                             ├── Compute State Diff
                             ├── Select Checkpoint
                             ├── Prune Conflicting Context
                             └── Re-execute (Single Retry Guarded)
```

---

## 5. Persistence Tier & Migration Strategy

- **Relational Store**: SQLite (Development) / PostgreSQL (Production) managed by SQLAlchemy async engine.
- **Schema Migrations**: Versioned database migrations powered by Alembic (`arc/backend/migrations`).
- **Telemetry Streaming**: In-memory event broker with optional Redis PubSub backend for multi-instance scaling.
