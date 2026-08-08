# ARC Development Implementation TODO Plan

This document outlines the granular, ordered milestones for building, refining, and hardening Agent Runtime Core (ARC). Each milestone is designed to take under 1 hour, target minimal files, be independently testable, and have clear success criteria.

---

## Phase 1: Core Consolidation & Standardization

### M1.1: Remove Duplicate SDK Directory
- **Files**: Delete legacy `arc/sdk/` directory.
- **Goal**: Consolidate SDK source of truth exclusively to top-level `sdk/arc/`.
- **Test**: `pytest sdk/tests/` succeeds; `import arc` resolves to `sdk/arc`.
- **Success Criteria**: No residual references to `arc/sdk` in codebase imports or documentation.

### M1.2: Enforce Strict Async-Safe Event Loops in SDK
- **Files**: `sdk/arc/agent.py`
- **Goal**: Replace unsafe blocking `asyncio.run()` in synchronous wrappers with loop-aware async execution dispatchers (`get_running_loop` or worker threads).
- **Test**: Run sync and async agent test cases in `sdk/tests/test_agent.py` under an active `asyncio` loop.
- **Success Criteria**: No `RuntimeError: This event loop is already running` when wrapping agent calls within existing async contexts.

### M1.3: Standardize Pydantic v2 Models Across API and SDK [COMPLETED]
- **Files**: `sdk/arc/types.py`, `arc/backend/api/schemas.py`, `sdk/tests/test_types.py`
- **Goal**: Align Pydantic schemas between SDK and backend to guarantee 100% field type & serialization parity.
- **Test**: Execute `pytest sdk/tests/test_types.py`.
- **Success Criteria**: Exact JSON schema validation match for `Session`, `Step`, `FirewallRule`, and `RecoveryDiff`.


### M1.4: Add Structured Domain Exception Handling to SDK
- **Files**: `sdk/arc/exceptions.py`, `sdk/arc/client.py`
- **Goal**: Wrap low-level `httpx` and `websockets` exceptions in domain-specific `ARCException`, `ContextPolicyException`, and `SessionNotFoundException`.
- **Test**: Unit test error mapping in `sdk/tests/test_client_errors.py`.
- **Success Criteria**: SDK methods throw explicit ARC domain exceptions on 40x/50x HTTP responses and connection drops.

---

## Phase 2: Modular Architecture & Extensibility

### M2.1: Define Abstract `StorageRepository` Interface
- **Files**: `arc/backend/core/storage_interface.py`
- **Goal**: Create abstract base class (`ABC`) defining `save_session`, `get_session`, `record_step`, `get_steps`, and `log_diff`.
- **Test**: Type-check interface with `mypy --strict arc/backend/core/storage_interface.py`.
- **Success Criteria**: Clean abstract interface created without runtime implementation dependencies.

### M2.2: Refactor SQLite ORM to Implement `StorageRepository`
- **Files**: `arc/backend/db/repository.py`, `arc/backend/core/flight_recorder.py`
- **Goal**: Implement `SQLiteStorageRepository` class adhering to `StorageRepository` interface and decouple `FlightRecorder` from direct ORM calls.
- **Test**: `pytest arc/backend/tests/test_flight_recorder.py` passes using the repository abstraction.
- **Success Criteria**: `FlightRecorder` interacts exclusively with `StorageRepository` abstraction.

### M2.3: Integrate Alembic DB Migration System
- **Files**: `arc/backend/alembic.ini`, `arc/backend/migrations/`
- **Goal**: Initialize Alembic environment for backend database and generate initial revision from current SQLAlchemy metadata.
- **Test**: Run `alembic upgrade head` on a fresh SQLite DB instance.
- **Success Criteria**: Database tables successfully generated via versioned migration script.

### M2.4: Extract Pluggable Context Firewall Evaluator Interface
- **Files**: `arc/backend/core/evaluators.py`, `arc/backend/core/context_firewall.py`
- **Goal**: Define `BaseFirewallEvaluator` interface and implement concrete `RegexRuleEvaluator` and `HeuristicConfidenceEvaluator`.
- **Test**: `pytest arc/backend/tests/test_context_firewall.py` verifying independent evaluator execution.
- **Success Criteria**: Context Firewall dynamically executes registered evaluator pipelines.

---

## Phase 3: Distributed Execution & Enterprise Hardening

### M3.1: Implement Centralized In-Memory Event Broker for Telemetry
- **Files**: `arc/backend/core/event_broker.py`, `arc/backend/api/websocket_router.py`
- **Goal**: Build `AsyncEventBroker` pub-sub manager to decouple engine event triggers from WebSocket route handlers.
- **Test**: Run `pytest arc/backend/tests/test_event_broker.py` testing subscriber notifications.
- **Success Criteria**: Engine events automatically broadcast to active WebSocket client connections via broker.

### M3.2: Implement Token Bucket Rate Limiter in API Gateway
- **Files**: `arc/backend/api/middleware.py`
- **Goal**: Add ASGI middleware enforcing configurable rate limits per API token / IP address.
- **Test**: Execute rapid request test in `arc/backend/tests/test_rate_limiter.py`.
- **Success Criteria**: Exceeding rate threshold returns HTTP 429 Too Many Requests with standard retry headers.

### M3.3: Implement Interactive State Diff Viewer in Frontend Dashboard
- **Files**: `arc/frontend/src/components/RecoveryDiffViewer.jsx`
- **Goal**: Build visual JSON side-by-side diff renderer for recovery steps and failed state snapshots.
- **Test**: Verify UI component renders mock state diffs properly in browser.
- **Success Criteria**: Interactive diff highlights added, modified, and deleted keys clearly.

---

## Phase 4: Modular Architecture & Multi-Framework Integrations

### M4.1: Modularize Core Runtime Engines
- **Files**: `sdk/arc/runtime/` (`scheduler`, `recovery`, `verifier`, `firewall`, `recorder`, `plugins`, `middleware`, `events`)
- **Goal**: Refactor monolithic engine files into dedicated modular runtime sub-packages.
- **Test**: `pytest sdk/tests/test_runtime_modules.py`.
- **Success Criteria**: All runtime engines operate cleanly as decoupled sub-modules.

### M4.2: Implement Multi-Framework Integration Layer
- **Files**: `sdk/arc/integrations/` (`anthropic`, `openai`, `langgraph`, `crewai`, `autogen`, `openhands`)
- **Goal**: Build dedicated framework adapters for Anthropic, OpenAI, LangGraph, CrewAI, AutoGen, and OpenHands.
- **Test**: `pytest sdk/tests/test_integrations.py`.
- **Success Criteria**: Protection wrappers successfully intercept agent calls across all 6 target frameworks.

