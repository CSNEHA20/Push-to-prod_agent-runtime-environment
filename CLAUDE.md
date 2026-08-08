# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What ARC is

ARC (Agent Runtime Core) is a reliability layer that sits between an application and the Claude API. It is composed of three engines that wrap every agent step:

1. **Flight Recorder** (`core/flight_recorder.py`) — records every LLM/tool step to the DB with a heuristic confidence score and a reasoning summary; powers replay.
2. **Context Firewall** (`core/context_firewall.py`) — before each Claude call, scores each context source for relevance (drops score < 0.3), detects pairwise conflicts, and tags surviving sources with provenance before injecting them as a system message.
3. **Recovery Engine** (`core/recovery_engine.py`) — checkpoints agent state (Postgres + Redis) after every step; on failure, finds the latest valid checkpoint before the failed step and restores it.

`core/arc_runtime.py` (`ARCRuntime`) is the orchestrator that wires the three engines together — read it first to understand control flow. Its `call_claude()` method is the full pipeline: firewall filter → Claude call → record step → checkpoint → if confidence < 0.2, recover and retry **once** (guarded by `_is_retry`).

The "wow" features (`core/arc_predict.py`, `arc_score.py`, `arc_diff.py`, `arc_lens.py`) are separate analytics layers over recorded sessions, exposed via `api/routes/features.py`. They operate on plain session dicts, not the ORM models directly.

## Modular Architectural Documentation

To inspect specific subsystems without rescanning the repository or loading large files, read the corresponding modular specification:

- **Architecture**: Read [ARCHITECTURE.md](file:///c:/Users/Lenovo/Downloads/agent-runtime-core/ARCHITECTURE.md)
- **APIs**: Read [API.md](file:///c:/Users/Lenovo/Downloads/agent-runtime-core/API.md)
- **Runtime Engines**: Read [RUNTIME.md](file:///c:/Users/Lenovo/Downloads/agent-runtime-core/RUNTIME.md)
- **SDK Reference**: Read [SDK.md](file:///c:/Users/Lenovo/Downloads/agent-runtime-core/SDK.md)
- **CLI Commands**: Read [CLI.md](file:///c:/Users/Lenovo/Downloads/agent-runtime-core/CLI.md)
- **Master Plan & Milestones**: Read [PROJECT.md](file:///c:/Users/Lenovo/Downloads/agent-runtime-core/PROJECT.md) and [TODO.md](file:///c:/Users/Lenovo/Downloads/agent-runtime-core/TODO.md)

---

## Repository layout


- `arc/backend/` — FastAPI service (the core product). Everything below is relative to here.
  - `core/` — the three engines + runtime + wow-feature analyzers
  - `api/routes/` — one router per domain (sessions, traces, context, recovery, playground, features); `api/websocket.py` handles live streaming
  - `models/` — SQLAlchemy ORM (`AgentSession`, `TraceStep`, `ContextConflict`/`ContextLog`, `Checkpoint`/`FailureEvent`)
  - `db/` — async SQLAlchemy engine (`database.py`) and Redis client (`redis_client.py`)
  - `tests/` — pytest-asyncio suite
- `arc/frontend/` — React + Vite + Tailwind dashboard
- `arc/sdk/arc_sdk/` and `sdk/arc_sdk/` — **two near-duplicate copies** of the Python SDK (see gotcha below)
- `arc/demo/` — standalone demo agent + `chaos_injector.py`
- `docs/` — planning/pitch docs (not code reference)

## Commands

Run backend commands from **`arc/backend/`** — imports are bare (`from core...`, `from db...`, `from models...`), so that directory must be the working dir / on `sys.path`. There is a `try/except ImportError` fallback to `arc.backend.*` for when the repo root is the CWD, but tests and `main.py` assume `arc/backend/`.

```bash
# Backend (from arc/backend/)
pip install -r requirements.txt
python main.py                    # serves on :8000 with reload

# Tests (from arc/backend/) — needs aiosqlite (NOT in requirements.txt; pip install it)
pytest                            # full suite
pytest tests/test_arc_runtime.py  # single file
pytest tests/test_arc_runtime.py::test_arc_runtime_init_properties  # single test

# Frontend (from arc/frontend/)
npm install
npm run dev                       # serves on :3000, proxies /api and /ws to :8000
npm run build
npm run lint                      # eslint, --max-warnings 0

# Full stack via Docker (from arc/)
docker-compose up                 # backend :8000, frontend :3000, postgres :5432, redis :6379

# Demo (from arc/demo/)
python demo_agent.py
```

## Conventions and non-obvious details

- **Claude model id is `claude-sonnet-4-6`**, hardcoded in `arc_runtime.py` and `context_firewall.py`. If you change the model, change it in both.
- **Tests use in-memory SQLite** (`sqlite+aiosqlite:///:memory:`) with a fresh `Base.metadata.create_all` per fixture and a `MagicMock` Anthropic client — no Postgres/Redis/network needed. Production defaults to Postgres (asyncpg) + Redis; `aiosqlite` must be installed separately to run tests.
- **Graceful degradation is intentional and load-bearing.** DB writes, Redis publishes, and Claude calls are wrapped in try/except that log-and-continue rather than raise. When editing engine code, preserve this — the demo and offline mode depend on it. The SDK and demo fall back to a `MockAnthropicClient` when `ANTHROPIC_API_KEY` is missing or a call returns 401.
- **Confidence scoring is a keyword heuristic**, not a model call — see `FlightRecorder.calculate_confidence_score` (starts 0.8, deducts for hedging phrases / short responses). The `< 0.2` recovery threshold in `ARCRuntime` depends on it.
- **WebSocket/live events go through Redis pub/sub**, channel `session:{session_id}`, via `publish_event()` in `api/websocket.py`. Engines call `publish_event` directly; there is no in-process event bus.
- **The two SDK copies (`sdk/` and `arc/sdk/`) must be kept in sync** — recent commits exist solely to re-synchronize them. Prefer editing one and mirroring, or ask which is canonical before diverging them.
- **Port mismatch to watch:** the frontend dev server and `ARCRuntime.dashboard_url` use **:3000**, but `README.md` and `.env.example` CORS also list `:5173` (Vite's default). The actual configured port is 3000 (`vite.config.js`).
- `README.md` references `LICENSE` and `CONTRIBUTING.md` that do not exist in the repo.

## Adding a feature engine or route

New analytics engines follow the `arc_score.py` pattern: a plain class taking a session dict, instantiated once at module load in `api/routes/features.py`, exposed as a route under the `/api/sessions` prefix. New ORM models must be imported in `models/__init__.py` so `Base.metadata.create_all` picks them up.

---

## ARC Development Rules

- Understand before implementing.
- Never rewrite existing architecture.
- Never modify unrelated files.
- Prefer composition over inheritance.
- Prefer interfaces over concrete implementations.
- Always reuse existing abstractions.
- Keep functions under 50 lines.
- Keep classes under 300 lines.
- Always type hints.
- Always write tests.
- Never duplicate code.
- Never implement multiple milestones.
- Only modify files required for current task.
- Never scan the repository unless requested.
- Always use PROJECT.md as architectural reference.
- Always update TODO.md after completing work.

