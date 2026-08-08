# ARC — Agent Runtime Core

**The missing reliability layer between your AI agent and the real world.**

[![PyPI](https://img.shields.io/pypi/v/arc-agent-sdk?label=arc-agent-sdk)](https://pypi.org/project/arc-agent-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./arc-sdk/LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Node 18+](https://img.shields.io/badge/node-18%2B-green)](https://nodejs.org/)
![Hackathon](https://img.shields.io/badge/Hackathon-Push_to_Prod-orange)
![Powered By](https://img.shields.io/badge/Powered_By-Claude-blueviolet)
![Tests](https://img.shields.io/badge/tests-208%20passing-brightgreen)

---

## 🎯 The Problem

When you deploy an AI agent in production it either works perfectly — or fails silently, and you have no idea what it knew, what it decided, or how to fix it.

- No black-box recorder to replay decisions.
- No memory management to prevent hallucination from bad context.
- No automatic recovery when it crashes mid-task.
- No way to verify it actually did what it was supposed to.

**ARC is that missing layer.**

---

## 🚀 What ARC Is

ARC is a **provider-agnostic, open-source reliability runtime** for AI agents. It intercepts LLM calls, tool executions, and agent decisions to enforce:

| Engine | What it does |
|---|---|
| 🛫 **Flight Recorder** | Records every LLM/tool step — context, decision, tool calls, confidence — for deterministic replay |
| 🧠 **Prompt Firewall** | Scores, filters, and provenance-tags context before it reaches the model. Detects injection, jailbreak, PII, secrets, and more across 8 pluggable detectors |
| ⚡ **Recovery Engine** | Continuously checkpoints agent state; self-heals from failures and retries from the last good checkpoint |

Claude doesn't change. Your app barely changes. ARC sits in the middle and makes everything reliable.

---

## 🏗️ Architecture

```
+-------------------------------------------------------------------------------------------+
|                                      AGENT TIER                                           |
|  Custom Agents | LangGraph | CrewAI | AutoGen | OpenHands | MCP Client                   |
+-------------------------------------------------------------------------------------------+
                                          |  Unified Middleware Protocol
                                          v
+-------------------------------------------------------------------------------------------+
|                              ARC PROVIDER-AGNOSTIC CORE                                   |
|                                                                                           |
|   Adaptive Planner  →  Middleware Pipeline  →  Execution Graph                           |
|                                                                                           |
|   ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐  ┌──────────────────┐  |
|   │ Prompt Firewall  │  │ Flight Recorder  │  │ Recovery Engine │  │  Hardened Event  │  |
|   │ (8 detectors)    │  │ (trace + replay) │  │ (checkpoint)    │  │  Bus (DLQ+CB)    │  |
|   └──────────────────┘  └──────────────────┘  └─────────────────┘  └──────────────────┘  |
|                                                                                           |
|   ┌──────────────────────────────────────────────────────────────────────────────────┐    |
|   │              Verification Engine  (8 pluggable verifier plugins)                 │    |
|   └──────────────────────────────────────────────────────────────────────────────────┘    |
+-------------------------------------------------------------------------------------------+
                                          |  Provider Adapter Interface
                                          v
+-------------------------------------------------------------------------------------------+
|                               PROVIDER ADAPTERS                                           |
|   AnthropicAdapter (Claude)   |   OpenAIAdapter (GPT-4o)   |   GeminiAdapter (Gemini)   |
+-------------------------------------------------------------------------------------------+
```

---

## 🛠️ Repository Structure

```
Push-to-prod_agent-runtime-environment/
│
├── arc-sdk/                        ← Canonical Python SDK (pip install arc-agent-sdk)
│   ├── arc/
│   │   ├── __init__.py             # Public API: ARC() facade
│   │   ├── _facade.py              # wrap / run / trace / recover / verify / replay
│   │   ├── _runtime.py             # Core runtime pipeline (graph-driven)
│   │   ├── _transport.py           # Anthropic SDK interception layer
│   │   ├── _agent.py               # Agent protection & WrappedAgent proxy
│   │   ├── config.py               # ARCConfig
│   │   ├── types.py                # Pydantic v2 data contracts
│   │   ├── exceptions.py           # Exception hierarchy
│   │   ├── runtime/
│   │   │   ├── planner/            # Adaptive Execution Planner (M0.7)
│   │   │   ├── graph/              # Execution Graph engine (M0.8)
│   │   │   ├── firewall/           # Prompt Firewall + 8 detectors (M0.9)
│   │   │   ├── events/             # Hardened Event Bus + Circuit Breaker + DLQ (M0.10)
│   │   │   ├── recorder/           # Flight Recorder
│   │   │   ├── recovery/           # Self-healing recovery
│   │   │   ├── verification/       # Verification Engine + 8 plugins
│   │   │   ├── middleware/         # Middleware pipeline
│   │   │   └── scheduler/         # Execution scheduling
│   │   ├── integrations/
│   │   │   ├── anthropic/          # Anthropic Claude adapter + params
│   │   │   ├── openai/             # OpenAI adapter + params
│   │   │   ├── gemini/             # Gemini adapter + params
│   │   │   ├── langgraph/          # LangGraph middleware adapter
│   │   │   ├── crewai/             # CrewAI multi-agent adapter
│   │   │   ├── autogen/            # AutoGen conversational adapter
│   │   │   └── openhands/          # OpenHands event stream adapter
│   │   ├── mcp/                    # Model Context Protocol router
│   │   └── cli/                    # `arc` CLI console script
│   ├── examples/                   # 6 end-to-end examples
│   └── tests/                      # 208 passing tests
│
├── arc/
│   ├── backend/                    ← FastAPI control-plane server (:8000)
│   │   ├── core/
│   │   │   ├── arc_runtime.py      # ARCRuntime orchestrator
│   │   │   ├── flight_recorder.py  # Async step logging + confidence scoring
│   │   │   ├── context_firewall.py # Context relevance + conflict detection
│   │   │   ├── recovery_engine.py  # Checkpoint + rollback
│   │   │   ├── arc_predict.py      # Predictive analytics
│   │   │   ├── arc_score.py        # Session scoring
│   │   │   ├── arc_diff.py         # State diff engine
│   │   │   └── arc_lens.py         # Trace lens analyzer
│   │   ├── api/routes/             # REST API (sessions, traces, context, recovery, features)
│   │   ├── api/websocket.py        # WebSocket live streaming (Redis pub/sub)
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   ├── db/                     # Async SQLAlchemy engine + Redis client
│   │   ├── main.py                 # FastAPI server entry point
│   │   └── requirements.txt
│   ├── frontend/                   ← React + Vite + Tailwind dashboard (:5173)
│   │   └── src/
│   │       ├── pages/              # Dashboard, Sessions, SessionView, Playground
│   │       └── components/         # FlightRecorder, ContextFirewall, RecoveryEngine
│   └── demo/
│       ├── demo_agent.py           # Interactive demo agent
│       └── chaos_injector.py       # Failure injection simulator
│
├── sdk/                            ← Legacy SDK (migrating → arc-sdk)
├── docs/                           ← Planning docs, pitch scripts, quick reference
│
├── ARCHITECTURE.md                 # Full system architecture spec
├── PROJECT.md                      # Single source of truth for implementation
├── TODO.md                         # Ordered milestone roadmap
├── CLAUDE.md                       # Agent coding rules & conventions
├── RUNTIME.md                      # Runtime engine specification
├── API.md / API_SPEC.md            # REST API reference
├── SDK.md / SDK_SPEC.md            # SDK reference
└── CLI.md                          # CLI command reference
```

---

## 📦 Install the SDK

```bash
pip install arc-agent-sdk

# With Anthropic support
pip install "arc-agent-sdk[anthropic]"

# All provider adapters
pip install "arc-agent-sdk[all]"
```

---

## ⚡ Quickstart

### Intercept every Anthropic request — zero code change

```python
from anthropic import Anthropic
from arc import ARC

client = Anthropic()
arc = ARC(client)

# Normal Anthropic SDK code — ARC runs the full pipeline automatically
response = arc.messages.create(
    model="claude-opus-4-8",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Summarize this report"}],
)

# MCP / betas flow through unchanged:
arc.beta.messages.create(
    model="claude-opus-4-8", max_tokens=1024,
    messages=[{"role": "user", "content": "..."}],
    mcp_servers=[{"type": "url", "name": "svc", "url": "https://mcp.example/sse"}],
    betas=["mcp-client-2025-11-20"],
)

# Read back what ARC recorded:
arc.trace()       # recorded steps
arc.verify()      # firewall/confidence verification
arc.replay()      # deterministic timeline
arc.recover()     # recovery plan
arc.dashboard_url # live session URL
```

Every request flows through:
```
ARC → Adaptive Planner → Execution Graph → Prompt Firewall → Event Bus
   → Flight Recorder → Verification → Recovery → Anthropic SDK
   → Replay Store → Dashboard
```

Request kwargs and response objects are **never mutated**.

---

### Wrap any agent framework

```python
from arc import ARC

arc = ARC(client)

# LangGraph, CrewAI, AutoGen, OpenHands, or any custom agent
wrapped = arc.wrap(my_langgraph_agent)
result = wrapped.invoke({"task": "write a quarterly report"})

# Full trace available immediately
print(wrapped.arc_trace())
```

---

### Extension points

```python
@arc.middleware
def timing(request, call_next):
    response = call_next(request)
    return response

@arc.plugin
class MetricsPlugin:
    name = "metrics"
    def setup(self, arc): ...
    def teardown(self, arc): ...

@arc.event("step_recorded")
def on_step(event):
    print(event.type, event.payload)
```

---

## ✅ Completed Milestones

| Milestone | Description | Tests |
|---|---|---|
| **M0.1** | `arc-sdk` package scaffold — full ARC() facade surface, PEP 561 typed | ✅ |
| **M0.2** | Real Anthropic SDK interception transport (streaming, tool use, MCP, extended thinking) | ✅ 25 |
| **M0.3** | `wrap()` / `run()` — LangGraph, CrewAI, AutoGen, OpenHands, OpenAI, Generic Python | ✅ 69 |
| **M0.4** | Middleware pipeline (onion chain) + Event Bus dispatch | ✅ |
| **M0.7** | Adaptive Planner — provider-independent `ExecutionPlan` before every request | ✅ 85 |
| **M0.8** | Production Execution Graph — event-driven, service-subscribed pipeline | ✅ 148 |
| **M0.9** | Enterprise Prompt Firewall — 8 detectors (injection, jailbreak, PII, secrets…) | ✅ 202 |
| **M0.10** | Hardened Event Bus — circuit breaker, DLQ, retries, backpressure, metrics | ✅ **208** |

---

## 🔬 Core Feature Deep Dives

### 🛫 Flight Recorder
- Asynchronously records every step: input, output, duration, token usage, confidence score
- Heuristic confidence scoring (starts 0.8; deducts for hedging phrases / short responses)
- Writes to SQLite (dev) / PostgreSQL (prod) via SQLAlchemy async engine
- Streams live telemetry via WebSocket (Redis pub/sub channel `session:{id}`)
- Full deterministic **replay** from any point in the trace

### 🧠 Prompt Firewall (upgraded from Context Firewall)
Inspects 6 input targets across 8 pluggable detectors before dispatching to the provider:

| Detector | What it catches |
|---|---|
| Prompt Injection | Adversarial instruction overrides |
| Jailbreak | Policy bypass attempts |
| PII | Emails, phone numbers, SSNs |
| Secrets | API keys, tokens, passwords |
| Recursive Prompting | Self-referential prompt loops |
| Prompt Leakage | System prompt exposure |
| Context Explosion | Excessive context token bombs |
| Duplicate Context | Redundant / repeated context chunks |

100% backward-compatible with the original `ContextFirewall`.

### ⚡ Recovery Engine
- Continuous state checkpointing after every step
- Automatic confidence-threshold trigger (< 0.2 → recover)
- State diff computation, context pruning, rollback to last valid checkpoint
- Single guarded retry (`_is_retry` flag prevents infinite loops)

### 📊 Hardened Event Bus
- **Fault isolation** — crashing subscribers never affect model execution
- **Per-subscriber timeouts** and exponential backoff retries
- **Dead Letter Queue (DLQ)** for permanently failed dispatches
- **Circuit Breakers**: CLOSED → OPEN → HALF_OPEN trip states per subscriber
- **Live metrics**: `EventBusStats` for observability

### 🗺️ Adaptive Planner
Generates a provider-independent `ExecutionPlan` before every request:
- Reasoning strategy, thinking budget, context budget, retrieval strategy
- Tool strategy, verification strategy, recovery policy
- Installed as the **first (outermost) middleware** — governs the entire pipeline
- Swappable: `ARC(planner=MyPlanner())` or `arc.planner = ...`
- Previewable without model call: `arc.plan(**request)`

### 📈 Execution Graph (M0.8)
- Planner generates an `ExecutionGraph` — single source of truth for which stages run
- `EventDrivenGraphExecutor` walks the graph; services subscribe to events
- Services coordinate only via shared `ExecutionContext` — no direct cross-calls
- Covers: sync + async, streaming, tool use, MCP (`beta.messages`)

### 🔍 Verification Engine
8 pluggable verifier plugins:
`assertion` · `execution` · `external_api` · `integrity` · `json_schema` · `llm_judge` · `pydantic` · `tool_output`

---

## 🚦 Running Locally

### 1. Backend (FastAPI — port 8000)

```bash
cd arc/backend

python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env and add: ANTHROPIC_API_KEY=your-key-here

python main.py
# → http://localhost:8000
```

### 2. Frontend Dashboard (React/Vite — port 5173)

```bash
cd arc/frontend
npm install
npm run dev
# → http://localhost:5173
```

### 3. Demo Agent + Chaos Injector

```bash
cd arc/demo
python demo_agent.py
# Inject chaos from the dashboard UI to observe ARC in action
```

### 4. Full Stack via Docker

```bash
cd arc
docker-compose up
# backend :8000 | frontend :3000 | postgres :5432 | redis :6379
```

---

## 🧪 Running Tests

```bash
# SDK tests — 208 passing
cd arc-sdk
pytest

# Backend tests (needs aiosqlite for in-memory SQLite)
cd arc/backend
pip install aiosqlite
pytest

# Single file
pytest tests/test_arc_runtime.py

# Single test
pytest tests/test_arc_runtime.py::test_arc_runtime_init_properties
```

---

## 🌐 Provider & Framework Support

| Category | Supported |
|---|---|
| **LLM Providers** | Anthropic Claude, OpenAI GPT-4o, Google Gemini 1.5/2.0 |
| **Agent Frameworks** | LangGraph, CrewAI, AutoGen, OpenHands, Custom Python |
| **Protocol** | Model Context Protocol (MCP) via `beta.messages` |
| **Storage** | SQLite (dev), PostgreSQL/asyncpg (prod), Redis (pub/sub) |
| **CI/CD** | GitHub Actions → PyPI (`arc-agent-sdk`) |

---

## 📡 REST API Overview

Base URL: `http://localhost:8000/api`

| Endpoint | Method | Description |
|---|---|---|
| `/sessions` | GET, POST | List / create agent sessions |
| `/sessions/{id}/traces` | GET | Step trace for a session |
| `/sessions/{id}/context` | GET, POST | Context firewall rules |
| `/sessions/{id}/recovery` | GET, POST | Checkpoints and recovery |
| `/sessions/{id}/features` | GET | ARC analytics (predict, score, diff, lens) |
| `/playground` | POST | Interactive agent playground |
| `ws://.../ws/{id}` | WebSocket | Live step streaming |

See [API.md](./API.md) and [API_SPEC.md](./API_SPEC.md) for full reference.

---

## 🖥️ Dashboard Features

At `http://localhost:5173`:

- **Dashboard Overview** — live metrics, failure rates, context filtering stats, active agents
- **Flight Recorder Tab** — step-by-step visual replay, prompt logs, decision trees
- **Context Firewall Tab** — filtered vs. passed chunks, relevance scores, conflict flags
- **Recovery Engine Tab** — checkpoint diffs, state snapshots, trigger recovery
- **Playground** — interactive agent with live trace streaming

---

## 🗺️ Roadmap

**Next milestones:**
- M1.2 — Strict async-safe event loops in SDK
- M1.4 — Abstract `StorageRepository` interface
- M1.5 — Alembic database migrations
- M2.1–M2.4 — Full `BaseProviderAdapter` implementations
- M3.1–M3.4 — Framework adapter implementations
- M4.1–M4.2 — MCP Tool Discovery Router + Firewall
- M5.2 — Interactive State Diff Viewer in Dashboard

**Business Vision:**

| Tier | Description |
|---|---|
| **Open Source Core** | Free — community adoption, standard for agent reliability |
| **Cloud Hosted** | Managed ARC for teams — analytics, managed infra |
| **Enterprise** | Compliance, audit logs, SOC2 — mandatory for regulated deployments |

---

## 🤝 Contributing

Areas for contribution:
- Flight recorder visualizations
- Context filtering algorithms and new detectors
- Recovery strategies
- Dashboard UI improvements
- Additional language SDKs (TypeScript, Go)
- New provider adapters

---

## 🙏 Acknowledgments

Built for the **Push to Prod Hackathon** — Bangalore 2026

Organized by **Anthropic · Elevate · Mesa School of Business**

**Team:**
- [Vishallakshmikanthan](https://github.com/Vishallakshmikanthan) — arc-sdk, runtime architecture
- [CSNEHA20](https://github.com/CSNEHA20) — integration, deployment

---

## 📄 License

MIT — see [LICENSE](./arc-sdk/LICENSE)

---

**Made with ❤️ for the Claude agent ecosystem**

---

## 🎯 The Problem

Right now when you give Claude an agentic task — it either works perfectly or fails silently and you have no idea why, what it knew, what it decided, or how to fix it.

There's no black box recorder. No memory that persists correctly. No recovery when it breaks. No way to verify it did what it was supposed to.

**ARC is that missing layer.**

---

## 🚀 What ARC Actually Is

Three things fused into one runtime:

### 1. 🛫 Flight Recorder
*(From TRACE)*

Every single thing the agent does gets recorded:
- What context it had at each decision point
- What it decided and why
- What tools it called
- What it was uncertain about
- Where it failed

When something goes wrong — and it will — you don't guess. You replay exactly what happened. Step by step. Like Chrome DevTools but for agent reasoning.

**The demo moment:** Agent fails on a complex task. You open ARC. You see the exact decision where it went wrong, what context it was missing, and why. You fix it in one line. Run again. Perfect.

### 2. 🧠 Context Firewall
*(From ContextOS)*

Right now agents get confused because they receive too much context, contradictory context, or stale context. They hallucinate not because they're dumb — but because nobody is managing what they know.

ARC sits between your data and Claude and does three things:
- **Relevance filtering** — only sends what actually matters for this specific task
- **Conflict resolution** — if two sources say different things, ARC flags it before Claude acts on wrong information
- **Provenance tracking** — every piece of context is tagged with where it came from, when, and how confident it is

Claude doesn't get a dump of information. It gets curated, verified, sourced context.

**The demo moment:** Same agent, same task. Without ARC — hallucinates because it mixed up two conflicting documents. With ARC — flags the conflict, asks for clarification, executes correctly.

### 3. ⚡ Recovery Engine
*(TRACE + ContextOS combined)*

When an agent fails mid-task — currently everything dies. You restart from zero.

ARC checkpoints agent state continuously. When failure happens:
- It knows exactly where execution stopped
- It knows what context was valid at that point
- It recovers and continues from the last good checkpoint

Like Git commits but for agent execution.

**The demo moment:** Agent is 7 steps into a 10-step task. Network fails. External API returns garbage. Normally — dead. With ARC — recovers, replays from step 6, completes the task.

---

## 🏗️ Architecture

```
Your App
    ↓
ARC Runtime Layer
    ├── Context Firewall (what Claude knows)
    ├── Flight Recorder (what Claude did)
    └── Recovery Engine (what Claude retries)
    ↓
Claude
    ↓
Tools / APIs / World
```

Claude doesn't change. Your app doesn't change much. ARC sits in the middle and makes everything reliable.

---

## 🏆 Why This Wins the Hackathon

| Criterion | How ARC Hits It |
|-----------|-----------------|
| **New frontier capability** | Nobody has built agent reliability infrastructure on top of Claude |
| **Infrastructure others build on** | Every team building Claude agents needs this immediately |
| **Redefines a category** | LangGraph, CrewAI do orchestration — ARC does reliability. Completely different |
| **Technically deep** | Flight recorder + context firewall + recovery is genuinely hard engineering |
| **Claude as the core** | ARC makes Claude agents production-ready — Anthropic wants this to exist |

### Why Anthropic Judges Specifically Will Love This

They built Claude. They want people to build serious things with Claude. But right now every developer building Claude agents hits the same wall — unreliability in production.

You walk in and say:

> "We built the reliability layer that makes Claude agents production-ready. Here's the flight recorder showing exactly what Claude decided and why. Here's the context firewall preventing hallucination from bad inputs. Here's the recovery engine that means a Claude agent never fails silently again."

That's not a hackathon project to them. That's infrastructure they wish existed.

---

## 🛠️ What We Built in 2 Days

### Day 1:
- ✅ Flight recorder — wrap Claude API calls, log full decision trace, build the replay visualizer
- ✅ Context firewall — relevance scoring, conflict detection between sources
- ✅ Basic dashboard showing agent execution in real time

### Day 2:
- ✅ Recovery engine — checkpoint system, failure detection, resume from last good state
- ✅ Demo scenario — build one compelling end-to-end agent task that fails without ARC and works perfectly with it
- ✅ Clean UI that shows the flight recorder replay visually

---

## 🎬 The Demo Flow

**Step 1:** Show a Claude agent doing a complex real task. Research a company, write a report, send a summary. Works fine.

**Step 2:** Introduce chaos. Conflicting documents. API failure midway. Bad context injected.

**Step 3:** Without ARC — agent produces wrong output silently. No idea why.

**Step 4:** Turn on ARC. Run again. Context firewall catches the conflict. Flight recorder shows every decision. Recovery engine handles the API failure. Agent completes correctly.

**Step 5:** Open the flight recorder. Show the judges exactly what Claude was thinking at each step. Show the context provenance. Show the recovery checkpoint.

Judges lose their minds.

---

## 🚀 Quick Start & How to Run

### Prerequisites
- Python 3.9+
- Node.js 18+
- Anthropic API Key (optional for synthetic demo mode)

---

### Step-by-Step Installation & Running

#### 1. Setup & Start Backend (FastAPI)

```bash
# Navigate to the backend directory
cd arc/backend

# Create & activate a virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install python dependencies
pip install -r requirements.txt

# Create environment file from template
cp .env.example .env

# Add your ANTHROPIC_API_KEY to .env (if calling live Claude models)
# ANTHROPIC_API_KEY=your-api-key-here

# Start FastAPI server
python main.py
```
> The API backend will start running at `http://localhost:8000`.

#### 2. Start Frontend (React + Vite Dashboard)

```bash
# Open a new terminal and navigate to frontend directory
cd arc/frontend

# Install dependencies
npm install

# Start the frontend dev server
npm run dev
```
> Access the developer dashboard in your browser at `http://localhost:5173`.

#### 3. Run the Demo Agent & Chaos Simulator

```bash
# Open a terminal and navigate to demo directory
cd arc/demo

# Run the interactive demo agent script
python demo_agent.py
```
> You can also inject chaos scenarios directly from the dashboard UI to observe how ARC handles API timeouts, conflicting documents, and unexpected agent failures.

---

### 💻 Using the Python SDK in Your Own Code

You can wrap any custom Claude agent using the `arc_sdk`:

```python
from arc_sdk import ARC

# 1. Initialize ARC Client
arc = ARC(endpoint="http://localhost:8000", api_key="your-anthropic-api-key")

# 2. Start an ARC Session
session = arc.create_session(agent_name="ResearchAgent", task="Summarize quarterly report")

# 3. Filter input context with Context Firewall
clean_context = session.filter_context(
    documents=[doc1, doc2], 
    relevance_threshold=0.75
)

# 4. Record agent LLM & Tool decisions into Flight Recorder
session.record_step(
    decision="Searched financial database",
    tools_called=["search_db"],
    confidence=0.92
)

# 5. Save Checkpoints for Recovery Engine
session.checkpoint(state={"current_step": 4, "data_collected": [...]})

# 6. Replay or Recover when an error occurs
session.recover_last_checkpoint()
```

---

### 📊 Dashboard Features

Once the UI is running at `http://localhost:5173`:
- **Dashboard Overview**: View live session metrics, failure rates, context filtering stats, and active agents.
- **Flight Recorder Tab**: Inspect step-by-step visual replays, prompt logs, and decision trees for any agent session.
- **Context Firewall Tab**: View filtered vs. passed context chunks, relevance confidence scores, and source conflict flags.
- **Recovery Engine Tab**: View checkpoint diffs, execution state snapshots, and trigger recovery flows.

---

## 📁 Project Structure

```
agent-runtime-core/
├── arc/
│   ├── backend/           # Python backend with ARC runtime
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Core ARC logic
│   │   ├── main.py       # FastAPI server
│   │   └── requirements.txt
│   ├── frontend/         # React dashboard
│   │   ├── src/
│   │   ├── package.json
│   │   └── index.html
│   ├── sdk/              # Python SDK
│   │   └── arc_sdk/
│   └── demo/             # Demo agent
│       └── demo_agent.py
├── docs/                 # Documentation
├── docker-compose.yml    # Docker setup
└── README.md
```

---

## 🌟 The Startup Vision

### Open Source Core
- Gets adoption fast
- Community contributions
- Standard for agent reliability

### Paid Cloud Version
- Hosted ARC for teams building Claude agents
- Managed infrastructure
- Analytics and insights

### Enterprise
- Compliance, audit logs, SOC2
- Every enterprise deploying agents needs this for legal reasons alone

**Every company deploying Claude agents in production will pay for this. That's the entire Claude enterprise market.**

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Areas for Contribution
- Flight recorder visualizations
- Context filtering algorithms
- Recovery strategies
- Dashboard UI improvements
- Additional language SDKs

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

Built for **Push to Prod Hackathon** organized by:
- **Anthropic**
- **Elevate**
- **Mesa School of Business**

Bangalore, 2026

---

## 📞 Contact

- **Twitter:** [@arc_runtime](https://twitter.com/arc_runtime)
- **GitHub:** [agent-runtime-core](https://github.com/yourusername/agent-runtime-core)
- **Discord:** [Join our community](https://discord.gg/arc)

---

**Made with ❤️ for the Claude agent ecosystem**
