# ARC Control Plane API Specification

The FastAPI Control Plane exposes REST endpoints and real-time WebSocket channels for session governance, telemetry recording, firewall evaluation, and failure recovery.

---

## REST Endpoints

### Sessions & Traces
- `POST /api/sessions`: Initialize a new recording session.
- `GET /api/sessions`: List active and historical sessions.
- `GET /api/sessions/{session_id}`: Fetch detailed session information and step counts.
- `DELETE /api/sessions/{session_id}`: Delete session and associated telemetry traces.
- `GET /api/sessions/{session_id}/trace`: Fetch ordered array of recorded execution steps.
- `GET /api/sessions/{session_id}/replay`: Fetch full visual replay timeline and checkpoint payload.

### Context Firewall
- `POST /api/firewall/evaluate`: Score context sources, detect conflicts, and sanitize prompt context.
- `GET /api/context/conflicts/{session_id}`: Retrieve detected factual/numerical context conflicts.
- `GET /api/context/logs/{session_id}`: Fetch context filtering logs and provenance tag metadata.

### Recovery Engine
- `POST /api/recovery/compute-diff`: Calculate state diff between execution steps.
- `POST /api/recovery/recover`: Trigger manual or automated session rollback to latest valid checkpoint.
- `GET /api/recovery/status/{session_id}`: Retrieve recovery engine health and checkpoint counts.

### Playground & Analytics
- `POST /api/playground/run`: Run synthetic demo agent steps for live dashboard demonstration.
- `GET /api/features/score/{session_id}`: Fetch ARC score and reliability metrics.
- `GET /api/features/predict/{session_id}`: Fetch failure probability metrics.

---

## WebSocket Telemetry Streaming

- **URL**: `/ws/sessions/{session_id}`
- **Events**:
  - `step_started`: Broadcast when agent begins a step.
  - `step_created`: Broadcast when step execution is logged.
  - `firewall_blocked`: Broadcast when context source is dropped due to low score or conflict.
  - `recovery_triggered`: Broadcast when self-healing rollback executes.
