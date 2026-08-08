# Project Specification: Agent Runtime Core (ARC)

This document is the authoritative single source of truth for the Agent Runtime Core (ARC) architecture, component contracts, runtime workflows, interfaces, and development standards.

---

## 1. Architecture

ARC is a governance, observability, and self-healing runtime platform designed for autonomous LLM agents. It operates as an execution wrapper and sidecar service that intercepts agent actions, validates context security, records complete execution telemetry, and recovers agents from execution failures.

```
+-----------------------------------------------------------------------+
|                              Agent Tier                               |
|   +-----------------------+              +------------------------+   |
|   |      User Agent       |              |      ARC SDK CLI       |   |
|   +-----------------------+              +------------------------+   |
+-------------------------------|---------------------------------------+
                                | REST / WebSockets
                                v
+-----------------------------------------------------------------------+
|                          Control Plane (API)                          |
|                       FastAPI Gateway Server                          |
+-------------------------------|---------------------------------------+
                                |
                                v
+-----------------------------------------------------------------------+
|                             Runtime Engine                            |
|  +---------------------+  +--------------------+  +----------------+  |
|  |  Context Firewall   |  |  Flight Recorder   |  | Recovery Engine|  |
|  |  (Engine 2)         |  |  (Engine 1)        |  | (Engine 3)     |  |
|  +---------------------+  +--------------------+  +----------------+  |
|  +-----------------------------------------------------------------+  |
|  |                    ARC Analytics & Predictors                   |  |
|  +-----------------------------------------------------------------+  |
+-------------------------------|---------------------------------------+
                                | Async SQLAlchemy
                                v
+-----------------------------------------------------------------------+
|                           Persistence Tier                            |
|                        SQLite Database Store                          |
+-----------------------------------------------------------------------+
                                ^ REST / WebSockets
                                |
+-----------------------------------------------------------------------+
|                            Management UI                              |
|                   React + Vite + Tailwind Dashboard                   |
+-----------------------------------------------------------------------+
```

---

## 2. Components

### 2.1 SDK Layer (`sdk/arc`)
- **`ARCClient`**: Low-level HTTP/WebSocket client interfacing with backend control plane.
- **`Agent`**: High-level execution wrapper auto-injecting session tracking, context verification, step recording, and automatic retry/recovery policies.
- **CLI (`arc`)**: Command-line developer interface for session inspection, replay triggering, and system verification.

### 2.2 Core Runtime (`arc/backend/core`)
- **Flight Recorder (Engine 1)**: Asynchronously records agent thoughts, tool calls, responses, confidence metrics, and state snapshots into immutable session logs.
- **Context Firewall (Engine 2)**: Analyzes incoming prompt context and tool outputs against security rules, confidence heuristics, and conflict filters before agent processing.
- **Recovery Engine (Engine 3)**: Detects failures, computes state diffs (`arc_diff`), selects recovery strategies (retry, context prune, fallback, human-in-the-loop), and restores session state.
- **ARC Analytics (`arc_score`, `arc_predict`, `arc_lens`)**: Evaluates agent performance metrics, predicts failure likelihood, and generates trace visualization payloads.

### 2.3 Storage Layer (`arc/backend/db`)
- Async SQLAlchemy ORM models managing persistent entities: Sessions, Steps, Firewall Logs, Recovery Diffs, and Metrics.

### 2.4 API Gateway (`arc/backend/api`)
- FastAPI endpoints providing structured REST routes and real-time WebSocket telemetry channels.

### 2.5 Frontend Dashboard (`arc/frontend`)
- Real-time developer UI featuring Session Viewer, Flight Recorder Replay, Context Firewall visualizer, and Recovery Diff inspector.

---

## 3. Runtime Flow

```
[Agent Initiates Step]
          |
          v
[1. Context Firewall Evaluation]
   ├── Approved  --> Continue to execution
   └── Blocked   --> Raise ContextPolicyException / Apply Sanitization
          |
          v
[2. Agent Execution (LLM / Tool Call)]
          |
          v
[3. Flight Recorder Capture]
   ├── Record Step Metadata & Confidence Heuristics
   └── Broadcast Live Telemetry via WebSockets
          |
          v
[4. Status Check]
   ├── Success   --> Commit Step & Return Result
   └── Failure   --> Invoke [5. Recovery Engine]
                          ├── Compute State Diff
                          ├── Select Strategy (Prune / Retry / Fallback)
                          └── Resume Execution Flow
```

---

## 4. APIs

### REST Endpoints

| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/sessions` | Initialize a new agent recording session |
| `GET` | `/api/v1/sessions` | List active and historical agent sessions |
| `GET` | `/api/v1/sessions/{id}` | Fetch full session trace & metrics |
| `POST` | `/api/v1/sessions/{id}/steps` | Record an execution step |
| `POST` | `/api/v1/firewall/evaluate` | Evaluate prompt/context safety |
| `POST` | `/api/v1/recovery/compute-diff` | Calculate recovery diff between steps |
| `POST` | `/api/v1/recovery/recover` | Trigger automated session recovery |
| `GET` | `/api/v1/analytics/score` | Compute overall ARC reliability score |

### WebSocket Protocol

| Path | Description | Payload |
| :--- | :--- | :--- |
| `/ws/sessions/{id}` | Live session streaming channel | Structured event messages (`step_created`, `firewall_blocked`, `recovery_triggered`) |

---

## 5. Folder Structure

```
agent-runtime-core/
├── PROJECT.md               # Single Source of Truth Architecture Spec
├── README.md                # Project Overview & Quickstart
├── CLAUDE.md                # Development Instructions & Commands
├── .agents/                 # Workspace Rules & Protocol Directives
├── sdk/                     # Standalone Arc Python SDK Package (arc-sdk)
│   ├── arc/                 # Core SDK Package Module
│   │   ├── __init__.py      # High-level exports
│   │   ├── agent.py         # Agent wrapper
│   │   ├── client.py        # API client
│   │   ├── cli.py           # CLI entry points
│   │   ├── types.py         # Data models & typings
│   │   └── exceptions.py   # Custom error types
│   ├── pyproject.toml       # Package metadata & build definition
│   └── tests/               # SDK test suite
├── arc/                     # Core Platform Implementation
│   ├── backend/             # FastAPI Server & Runtime Engines
│   │   ├── api/             # HTTP & WebSocket Controllers
│   │   ├── core/            # Flight Recorder, Firewall, Recovery Engine
│   │   ├── db/              # Database Models & Connections
│   │   └── main.py          # Backend Entry Point
│   ├── frontend/            # React + Vite Management Dashboard
│   └── demo/                # Synthetic Chaos Testing Scripts
└── docs/                    # Architectural Specifications & Guides
```

---

## 6. Interfaces & Data Models

### 6.1 Core Data Models

- **`Session`**: `id`, `agent_name`, `status`, `created_at`, `updated_at`, `metadata`
- **`Step`**: `id`, `session_id`, `step_index`, `type` (`thought` \| `tool_call` \| `response`), `input`, `output`, `confidence_score`, `timestamp`
- **`FirewallRule`**: `id`, `rule_type`, `action` (`allow` \| `block` \| `sanitize`), `threshold`, `pattern`
- **`RecoveryDiff`**: `id`, `session_id`, `failed_step_id`, `strategy_used`, `diff_payload`, `status`

### 6.2 Key Component Contracts

- **`ContextFirewall.evaluate(context: ContextPayload) -> FirewallResult`**
- **`FlightRecorder.record_step(session_id: str, step: StepPayload) -> Step`**
- **`RecoveryEngine.recover(session_id: str, error: Exception) -> RecoveryResult`**
- **`ARCClient.post_step(step_data: StepCreate) -> StepResponse`**

---

## 7. Roadmap

### Phase 1: Core Consolidation & Standardization (Current)
- Unify SDK into single production package (`sdk/arc`).
- Implement 8-step pre-implementation audit protocol.
- Fix event loop concurrency handling in SDK sync wrappers.

### Phase 2: Modular Architecture & Extensibility
- Introduce `StorageRepository` abstract interface to decouple backend engines from raw SQLite/ORM.
- Add Alembic DB migration system for zero-downtime schema evolution.
- Implement pluggable Context Firewall rule evaluators (regex, LLM-as-judge, vector embedding similarity).

### Phase 3: Distributed Execution & Enterprise Hardening
- Add Redis/NATS event broker for multi-instance telemetry streaming.
- Implement token bucket rate-limiting and OAuth2 authentication in API Gateway.
- Expand React dashboard with advanced step-by-step state diffing and interactive human-in-the-loop recovery prompts.

---

## 8. Coding Guidelines

1. **Mandatory Audit**: Every code change must undergo the 8-point pre-implementation review defined in `.agents/AGENTS.md`.
2. **Strict Typing**: All Python code must be 100% type-annotated (`mypy --strict` compliant).
3. **Async Standard**: All backend routines involving IO, database access, or network communication must be `async`/`await`.
4. **Pydantic Contract Enforcement**: Data transfers across API and SDK boundaries must use validated Pydantic models.
5. **No Masked Errors**: Never swallow exceptions silently. Log tracebacks and wrap errors in explicit domain exceptions (`ARCException`).
6. **Stateless Gateway**: Keep the API gateway stateless; persist session states in storage.

---

## 9. Design Principles

1. **Zero Impact on Happy Path**: Telemetry and context evaluation must execute with minimal latency penalty.
2. **Defensive by Default**: Intercept context conflicts and unsafe prompts *before* LLM execution.
3. **Deterministic Replay**: Ensure every recorded session step contains enough state payload to reproduce agent behavior.
4. **Self-Healing Automation**: Recover gracefully from transient failures before requesting human intervention.
5. **Developer First (DX)**: Simple SDK integration (`from arc import Agent`), clean error messages, and immediate visual feedback via dashboard.
