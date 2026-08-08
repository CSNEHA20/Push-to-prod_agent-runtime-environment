# Project Specification: Agent Runtime Core (ARC)

This document is the single source of truth for the Agent Runtime Core (ARC) production architecture, provider-agnostic abstractions, framework integrations, and developer guidelines.

---

## 1. Vision & Core Architecture

ARC (Agent Runtime Core) is a provider-agnostic, open-source reliability runtime layer for AI agents. It intercepts LLM calls, tool executions, and agent decisions to enforce real-time context security, record deterministic execution telemetry, and perform automated failure recovery.

```
+---------------------------------------------------------------------------------------------------+
|                                             AGENT TIER                                            |
|   +---------------+  +------------+  +-----------+  +----------+  +-----------+  +------------+   |
|   | Custom Agents |  | LangGraph  |  |  CrewAI   |  | AutoGen  |  | OpenHands |  | MCP Client |   |
|   +---------------+  +------------+  +-----------+  +----------+  +-----------+  +------------+   |
+-------------------------------------------------|-------------------------------------------------+
                                                  | Unified Middleware Protocol
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                      ARC PROVIDER-AGNOSTIC CORE                                   |
|   +-------------------------------------------------------------------------------------------+   |
|   |                                Control Plane (FastAPI Gateway)                            |   |
|   +-------------------------------------------------------------------------------------------+   |
|   +-------------------+   +--------------------+   +-------------------+   +------------------+   |
|   | Context Firewall  |   |  Flight Recorder   |   |  Recovery Engine  |   |   MCP Registry   |   |
|   | (Engine 2)        |   |  (Engine 1)        |   |  (Engine 3)       |   |   (Tools Router) |   |
|   +-------------------+   +--------------------+   +-------------------+   +------------------+   |
+-------------------------------------------------|-------------------------------------------------+
                                                  | Provider Adapter Interface
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                          PROVIDER ADAPTERS                                        |
|   +------------------------+        +-----------------------+        +------------------------+   |
|   | AnthropicAdapter (4.6) |        | OpenAIAdapter (GPT-4o)|        | GeminiAdapter (1.5/2.0)|   |
|   +------------------------+        +-----------------------+        +------------------------+   |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. Core Pillars

1. **Provider-Agnostic Core**: Zero hardcoded vendor lock-in. Support Anthropic, OpenAI, Google Gemini, and custom OpenAI-compatible providers through a unified `BaseProviderAdapter` contract.
2. **Context Security & Firewall (Engine 2)**: Intercept prompt context before model dispatch. Score relevance, filter prompt injections, resolve pairwise factual conflicts, and enforce provenance tags.
3. **Flight Recorder Telemetry (Engine 1)**: Asynchronously log thoughts, tool invocations, token counts, and heuristic confidence scores into immutable trace logs with replay support.
4. **Self-Healing Recovery (Engine 3)**: Checkpoint agent state after steps. Automatically calculate state diffs, prune invalid context, roll back state, and retry failed executions.
5. **Model Context Protocol (MCP) Support**: Native MCP server discovery, tool registration, and execution routing for external tools.

---

## 3. Provider & Framework Integration Matrix

| Component | Target Systems | Protection Mechanism |
| :--- | :--- | :--- |
| **Provider Adapters** | Anthropic, OpenAI, Gemini | Middleware HTTP wrapper intercepting `chat.completions` and `messages.create` |
| **Framework Adapters** | LangGraph, CrewAI, AutoGen, OpenHands, Custom | Middleware hooks wrapping graph nodes, multi-agent messages, and tool loops |
| **Protocol Integration** | Model Context Protocol (MCP) | Dynamic MCP tool discovery, verification, and sandboxed execution |

---

## 4. Modular Folder Structure (`arc-sdk`)

```
arc-sdk/
├── runtime/                 # Modular Core Execution Engines
│   ├── scheduler/           # Execution scheduling & loop management
│   ├── recovery/            # Self-healing rollback & state checkpointing
│   ├── verifier/            # Compliance & policy verification
│   ├── firewall/            # Context security & conflict filtering
│   ├── recorder/            # Execution step tracing (Flight Recorder)
│   ├── plugins/             # Extensible runtime plugins
│   ├── middleware/          # Interceptor middleware pipeline
│   └── events/              # Event broker & pub-sub dispatcher
├── sdk/                     # Core Python SDK Interfaces & Client
├── cli/                     # Command-line developer tool (`arc`)
├── dashboard/               # Real-time management UI frontend
├── integrations/            # Framework Adapters & Middleware
│   ├── anthropic/           # Anthropic Claude client wrapper
│   ├── openai/              # OpenAI API protection wrapper
│   ├── gemini/              # Google Gemini client protection wrapper
│   ├── langgraph/           # LangGraph state protection adapter
│   ├── crewai/              # CrewAI multi-agent workflow adapter
│   ├── autogen/             # AutoGen conversational agent adapter
│   └── openhands/           # OpenHands runtime execution adapter
├── mcp/                     # Model Context Protocol (MCP) Tool Router
├── examples/                # Integration examples & demos
├── tests/                   # Unit & integration test suite
└── docs/                    # Architectural specifications & guides
```

---

## 5. Coding & Architectural Standards

1. **Strict Decoupling**: Core engines MUST NOT depend on vendor-specific SDK classes. All provider interactions go through `BaseProviderAdapter`.
2. **Mandatory 8-Step Audit**: All code changes must pass the 8-point audit process (`Architecture`, `API`, `Dependency`, `Runtime`, `Security`, `SDK`, `Performance`, `DX`).
3. **100% Type Completeness**: Every module must be PEP 561 typed and pass `mypy --strict`.
4. **Pydantic v2 Contracts**: All data schemas across API, SDK, and DB interfaces use Pydantic v2 with `ConfigDict(from_attributes=True, populate_by_name=True)`.
