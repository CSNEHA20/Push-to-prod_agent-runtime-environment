# ARC Master Implementation Roadmap & Milestones

This document details the granular, ordered development milestones for converting ARC into an enterprise open-source AI runtime. Each milestone takes under 1 hour, modifies minimal files, is independently testable, and has clear success criteria.

---

## Phase 1: Core Consolidation & Storage Abstraction

### M1.1: Remove Legacy SDK Copies [COMPLETED]
- **Files**: Delete duplicate `arc/sdk/` directory.
- **Goal**: Consolidate SDK source of truth exclusively to `sdk/arc/`.
- **Test**: `pytest sdk/tests/` succeeds.
- **Success Criteria**: Clean SDK directory layout.

### M1.2: Strict Async-Safe Event Loops in SDK
- **Files**: `sdk/arc/agent.py`
- **Goal**: Replace blocking `asyncio.run()` in sync wrappers with loop-aware async dispatchers.
- **Test**: `pytest sdk/tests/test_client_and_agent.py`.
- **Success Criteria**: No event loop collision when wrapping agents in active async contexts.

### M1.3: Standardize Pydantic v2 Models Across API and SDK [COMPLETED]
- **Files**: `sdk/arc/types.py`, `arc/backend/api/schemas.py`, `sdk/tests/test_types.py`
- **Goal**: Align Pydantic schemas between SDK and backend (`Session`, `Step`, `FirewallRule`, `RecoveryDiff`).
- **Test**: `pytest sdk/tests/test_types.py`.
- **Success Criteria**: 100% field type and serialization parity.

### M1.4: Define Abstract `StorageRepository` Interface
- **Files**: `arc/backend/core/storage_interface.py`
- **Goal**: Create abstract base class defining storage contracts (`save_session`, `record_step`, `log_diff`).
- **Test**: Type-check interface with `mypy --strict`.
- **Success Criteria**: Clean storage abstraction without raw ORM coupling.

### M1.5: Integrate Alembic DB Migration System
- **Files**: `arc/backend/alembic.ini`, `arc/backend/migrations/`
- **Goal**: Setup Alembic migrations for database schema evolution.
- **Test**: Run `alembic upgrade head` on fresh database.
- **Success Criteria**: Database tables initialized via migration scripts.

---

## Phase 2: Provider-Agnostic Abstraction Layer

### M2.1: Implement `BaseProviderAdapter` Interface
- **Files**: `sdk/arc/providers/base.py`
- **Goal**: Create provider-agnostic base adapter contract for LLM invocation.
- **Test**: Type-check interface definitions.
- **Success Criteria**: Abstract base class defined with `generate_response` contract.

### M2.2: Implement `AnthropicAdapter`
- **Files**: `sdk/arc/providers/anthropic.py`
- **Goal**: Build Anthropic provider adapter supporting Claude models (`claude-3-7-sonnet`, `claude-3-5-haiku`).
- **Test**: `pytest sdk/tests/test_anthropic_adapter.py`.
- **Success Criteria**: Native prompt, tool, and system message mapping for Claude.

### M2.3: Implement `OpenAIAdapter`
- **Files**: `sdk/arc/providers/openai.py`
- **Goal**: Build OpenAI provider adapter supporting GPT models (`gpt-4o`, `gpt-4o-mini`, `o3-mini`).
- **Test**: `pytest sdk/tests/test_openai_adapter.py`.
- **Success Criteria**: Native function calling and completions mapping.

### M2.4: Implement `GeminiAdapter`
- **Files**: `sdk/arc/providers/gemini.py`
- **Goal**: Build Google Gemini provider adapter supporting `gemini-1.5-pro` and `gemini-2.0-flash`.
- **Test**: `pytest sdk/tests/test_gemini_adapter.py`.
- **Success Criteria**: Clean Vertex AI / Google AI SDK request mapping.

---

## Phase 3: Multi-Framework Integration Layer

### M3.1: Implement `LangGraphAdapter`
- **Files**: `sdk/arc/integrations/langgraph.py`
- **Goal**: Build state graph middleware adapter for LangGraph nodes.
- **Test**: `pytest sdk/tests/test_langgraph_adapter.py`.
- **Success Criteria**: Automatic step tracing and checkpointing during graph execution.

### M3.2: Implement `CrewAIAdapter`
- **Files**: `sdk/arc/integrations/crewai.py`
- **Goal**: Build task delegation middleware adapter for CrewAI multi-agent teams.
- **Test**: `pytest sdk/tests/test_crewai_adapter.py`.
- **Success Criteria**: Delegation step tracing and context firewall filtering in crew tasks.

### M3.3: Implement `AutoGenAdapter`
- **Files**: `sdk/arc/integrations/autogen.py`
- **Goal**: Build conversational turn middleware adapter for AutoGen agents.
- **Test**: `pytest sdk/tests/test_autogen_adapter.py`.
- **Success Criteria**: Conversational message filtering and step recording.

### M3.4: Implement `OpenHandsAdapter`
- **Files**: `sdk/arc/integrations/openhands.py`
- **Goal**: Build event stream execution adapter for OpenHands runtime.
- **Test**: `pytest sdk/tests/test_openhands_adapter.py`.
- **Success Criteria**: Action step tracing and terminal output verification.

---

## Phase 4: Model Context Protocol (MCP) Server Support

### M4.1: Implement MCP Tool Discovery Router
- **Files**: `sdk/arc/mcp/router.py`
- **Goal**: Build discovery and schema parser for connected Model Context Protocol (MCP) servers.
- **Test**: `pytest sdk/tests/test_mcp_router.py`.
- **Success Criteria**: MCP tools parsed and registered dynamically in ARC runtime.

### M4.2: Implement MCP Context Firewall & Trace Filter
- **Files**: `sdk/arc/mcp/firewall.py`
- **Goal**: Integrate Context Firewall verification and Flight Recorder tracing into MCP tool executions.
- **Test**: `pytest sdk/tests/test_mcp_firewall.py`.
- **Success Criteria**: Unsafe MCP tool calls blocked before execution.

---

## Phase 5: Enterprise Governance & Control Plane

### M5.1: Implement In-Memory & Redis Event Broker
- **Files**: `arc/backend/core/event_broker.py`, `arc/backend/api/websocket_router.py`
- **Goal**: Decouple engine events from WebSocket route handlers via pub-sub broker.
- **Test**: `pytest arc/backend/tests/test_event_broker.py`.
- **Success Criteria**: Real-time event streaming across multi-instance control plane.

### M5.2: Implement Interactive State Diff Viewer in Dashboard
- **Files**: `arc/frontend/src/components/RecoveryDiffViewer.jsx`
- **Goal**: Render visual JSON side-by-side state diffs for failure recoveries.
- **Test**: Browser UI verification.
- **Success Criteria**: Interactive diff highlights added, modified, and removed state keys.
