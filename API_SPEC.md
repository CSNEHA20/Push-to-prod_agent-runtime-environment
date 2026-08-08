# ARC Control Plane REST & WebSocket API Specification (v1)

The FastAPI Control Plane exposes OpenAPI 3.0 REST routes and real-time WebSocket channels for session governance, telemetry recording, firewall evaluation, MCP tool discovery, and failure recovery.

---

## 1. REST API Endpoint Reference

### 1.1 Sessions (`/api/v1/sessions`)

- `POST /api/v1/sessions`: Initialize a new recording session.
  - **Request Body**: `{"agent_name": "Analyst", "task": "Analyze data", "metadata": {}}`
  - **Response (201)**: `AgentSessionResponse`

- `GET /api/v1/sessions`: List active and historical agent sessions.
  - **Query Params**: `limit=50&offset=0&status=active`
  - **Response (200)**: `List[AgentSessionResponse]`

- `GET /api/v1/sessions/{session_id}`: Fetch detailed session information and step counts.
  - **Response (200)**: `AgentSessionResponse`

- `DELETE /api/v1/sessions/{session_id}`: Delete session and associated telemetry traces.
  - **Response (200)**: `{"message": "Session deleted", "session_id": "UUID"}`

### 1.2 Flight Recorder Traces (`/api/v1/sessions/{session_id}/trace`)

- `GET /api/v1/sessions/{session_id}/trace`: Fetch ordered trace steps.
  - **Response (200)**: `List[TraceStepResponse]`

- `POST /api/v1/sessions/{session_id}/steps`: Record an execution step.
  - **Request Body**: `{"step_type": "llm_call", "input_data": {}, "output_data": {}, "confidence_score": 0.95}`
  - **Response (201)**: `TraceStepResponse`

- `GET /api/v1/sessions/{session_id}/replay`: Fetch full visual replay timeline and checkpoint payload.
  - **Response (200)**: `ReplayResponse`

### 1.3 Context Firewall (`/api/v1/firewall`)

- `POST /api/v1/firewall/evaluate`: Score context sources, detect conflicts, and sanitize prompt context.
  - **Request Body**: `{"prompt": "str", "context_sources": [{"id": "doc1", "content": "str"}]}`
  - **Response (200)**: `{"is_valid": true, "conflicts": [], "surviving_context": []}`

- `GET /api/v1/firewall/rules`: List registered firewall rules.
  - **Response (200)**: `List[FirewallRuleResponse]`

### 1.4 Failure Recovery Engine (`/api/v1/recovery`)

- `POST /api/v1/recovery/compute-diff`: Calculate state diff between execution steps.
  - **Response (200)**: `RecoveryDiffResponse`

- `POST /api/v1/recovery/recover`: Trigger automated session rollback to latest valid checkpoint.
  - **Response (200)**: `{"status": "recovered", "target_checkpoint_id": "UUID"}`

### 1.5 Model Context Protocol (MCP) Server Router (`/api/v1/mcp`)

- `GET /api/v1/mcp/tools`: List discovered tools from connected MCP servers.
  - **Response (200)**: `List[MCPToolDefinition]`

- `POST /api/v1/mcp/tools/execute`: Execute a verified MCP tool call under Firewall protection.
  - **Request Body**: `{"tool_name": "read_file", "arguments": {"path": "data.json"}}`
  - **Response (200)**: `{"status": "success", "result": {}}`

---

## 2. WebSocket Protocol (`/ws/v1/sessions/{session_id}`)

- **Connection**: `ws://localhost:8000/ws/v1/sessions/{session_id}`
- **Subscribed Event Messages**:
  - `step_started`: Agent initiated a step execution.
  - `step_created`: Flight Recorder saved a step.
  - `firewall_blocked`: Context Firewall dropped an unsafe/conflicting source.
  - `recovery_triggered`: Recovery Engine executed a state rollback.
