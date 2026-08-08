# ARC — Sequential Build Prompts for ChatGPT
## Vibe Coding Guide — Feed These In Order

---

> **How to use this:** Copy each prompt into ChatGPT one by one.
> Wait for the full output before moving to the next prompt.
> Paste generated code directly into the file structure.
> Do not skip prompts — each one builds on the previous.

---

## ⚙️ PHASE 1: PROJECT SETUP

---

### PROMPT 1 — Project Scaffold

```
I am building ARC (Agent Runtime Core) — a reliability layer for Claude AI agents with three core engines:
1. Flight Recorder (records every agent decision for replay)
2. Context Firewall (filters and validates context before it reaches Claude)
3. Recovery Engine (checkpoints agent state and recovers from failures)

Create the complete project scaffold with these exact directories:

arc/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   └── core/ api/ models/ db/ (empty __init__.py files)
├── frontend/
│   └── (Vite + React scaffold — package.json + src/App.jsx)
├── sdk/
│   └── arc_sdk/__init__.py
├── demo/
│   └── demo_agent.py (empty)
└── docker-compose.yml

Tech stack:
- Backend: Python FastAPI + SQLAlchemy + asyncpg + Redis + WebSockets
- Frontend: React + Vite + Tailwind CSS
- Database: PostgreSQL

Give me:
1. requirements.txt with all dependencies
2. main.py FastAPI skeleton with CORS enabled and health check route
3. docker-compose.yml with FastAPI + PostgreSQL + Redis + React
4. .env.example with all environment variables
5. package.json for React frontend with Tailwind + Recharts + Reactflow

Make it production-ready with async support.
```

---

### PROMPT 2 — Database Models

```
I am building ARC — Agent Runtime Core. 

Create SQLAlchemy models for PostgreSQL in backend/models/:

File: backend/models/session.py
- AgentSession model with fields:
  session_id (UUID primary key), agent_name, task (text), status (running/completed/failed/recovered), started_at, ended_at, total_steps, failed_at_step, recovered (bool)

File: backend/models/trace.py  
- TraceStep model with fields:
  step_id (UUID), session_id (FK), step_number, step_type (llm_call/tool_call/decision), timestamp, duration_ms, input_data (JSON), output_data (text), tool_name, tool_input (JSON), tool_output (text), tool_success (bool), confidence_score (float), reasoning_summary, context_used (JSON), status, error, was_recovered (bool)

File: backend/models/context.py
- ContextConflict model: conflict_id, session_id (FK), step_number, conflict_type (factual/temporal/numerical/logical), description, resolution, severity (low/medium/high/critical), source_a_id, source_b_id, detected_at

File: backend/models/checkpoint.py
- Checkpoint model: checkpoint_id, session_id (FK), step_number, timestamp, agent_state (JSON), messages_history (JSON), context_snapshot (text), tool_results (JSON), is_valid (bool), validation_score (float), was_used_for_recovery (bool)
- FailureEvent model: failure_id, session_id (FK), step_number, failure_type (api_error/bad_output/timeout/logic_error), error_message, timestamp, recovery_attempted, recovery_checkpoint_id, recovery_success, steps_replayed

Also create:
- backend/db/database.py with async SQLAlchemy engine, session factory, and Base
- backend/db/redis_client.py with Redis async client

Use async SQLAlchemy with asyncpg driver.
```

---

## 🛫 PHASE 2: FLIGHT RECORDER ENGINE

---

### PROMPT 3 — Flight Recorder Core

```
I am building ARC — Agent Runtime Core. The Flight Recorder is Engine 1.

Create backend/core/flight_recorder.py with a FlightRecorder class that:

1. start_session(agent_name, task) → creates AgentSession in DB, returns session object

2. record_llm_call(session_id, step_number, messages, response_text, input_tokens, output_tokens, duration_ms) → creates TraceStep with step_type="llm_call", calculates confidence_score using this heuristic:
   - Start at 0.8
   - If response contains "I think", "probably", "I'm not sure", "might be" → subtract 0.1 each
   - If response length < 50 chars → subtract 0.2
   - Clamp between 0.1 and 1.0
   - Generate reasoning_summary as first 100 chars of response cleaned up
   - Save to DB

3. record_tool_call(session_id, step_number, tool_name, tool_input, tool_output, success, duration_ms) → creates TraceStep with step_type="tool_call"

4. end_session(session_id, status, error=None) → updates AgentSession with ended_at and final status

5. get_session(session_id) → returns AgentSession

6. get_trace(session_id) → returns all TraceSteps for session ordered by step_number

7. get_replay(session_id) → returns dict with session + steps + failure_point + recovery_point

All methods should be async. Use the SQLAlchemy async session from db/database.py.
Include full error handling and logging.
```

---

### PROMPT 4 — Flight Recorder API Routes

```
I am building ARC — Agent Runtime Core.

Create backend/api/routes/sessions.py and backend/api/routes/traces.py with these FastAPI routes:

sessions.py:
- GET /api/sessions → list all sessions, ordered by started_at desc, limit 50
- GET /api/sessions/{session_id} → get session details
- DELETE /api/sessions/{session_id} → delete session and all its traces

traces.py:
- GET /api/sessions/{session_id}/trace → get all trace steps for session
- GET /api/sessions/{session_id}/replay → get replay object (session + steps + metadata)
- GET /api/sessions/{session_id}/trace/step/{step_number} → get specific step

Also create backend/api/websocket.py:
- WebSocket endpoint at /ws/sessions/{session_id}
- Accepts connections and subscribes to a Redis pub/sub channel for that session
- Forwards any messages published to that channel to the WebSocket client
- Handle disconnection gracefully

Create a publish_event(session_id, event_type, data) helper function that publishes JSON to the Redis channel.

Return Pydantic schemas for all responses. Include proper HTTP status codes.
```

---

## 🛡️ PHASE 3: CONTEXT FIREWALL ENGINE

---

### PROMPT 5 — Context Firewall Core

```
I am building ARC — Agent Runtime Core. The Context Firewall is Engine 2.

Create backend/core/context_firewall.py with a ContextFirewall class.

It takes the Anthropic client as a constructor argument.

Main method: async filter(session_id, step_number, sources, task) where sources is a list of dicts with {name, content, source_type, confidence}

The filter method runs this pipeline:

Step 1 — Score relevance:
For each source, call Claude claude-sonnet-4-6 with this prompt:
"Rate how relevant this content is to the task '{task}' on a scale of 0.0 to 1.0. Return only a number."
Content: {source content}
Filter out sources with score < 0.3

Step 2 — Detect conflicts:
For every pair of remaining sources, call Claude with:
"Do these two pieces of information conflict with each other? If yes, describe the conflict in one sentence and classify it as: numerical, temporal, factual, or logical. If no conflict, return 'NO_CONFLICT'.
Source A: {content_a}
Source B: {content_b}"
Parse the response. If not NO_CONFLICT, create a ContextConflict record and save to DB.

Step 3 — Build provenance tags:
For each chunk that passed, create a tag: [SOURCE: {name} | CONFIDENCE: {score:.2f}]
Append this tag to each chunk's content.

Step 4 — Assemble and return FilteredContext:
Return a dict with:
- final_context: all passed chunks joined with newlines
- total_received: int
- passed: int  
- rejected: int
- conflicts: list of conflict objects
- provenance_map: {source_name: confidence_score}

Also save a summary to the DB context_log table (create this model too if needed).

All Claude calls should use model="claude-sonnet-4-6" and max_tokens=100.
```

---

### PROMPT 6 — Context Firewall API Routes

```
I am building ARC — Agent Runtime Core.

Create backend/api/routes/context.py with:

- GET /api/context/{session_id}/log → get all context filtering decisions for a session
- GET /api/context/{session_id}/conflicts → get all conflicts detected, ordered by severity (critical first)
- GET /api/context/{session_id}/provenance → get the provenance map for the session

Create Pydantic response schemas:
- ConflictResponse: conflict_id, conflict_type, description, severity, resolution, detected_at
- ProvenanceResponse: source_name, confidence, chunks_used, chunks_rejected

Include these summary stats in the conflicts response:
- total_conflicts: int
- by_severity: {critical: n, high: n, medium: n, low: n}
- by_type: {numerical: n, temporal: n, factual: n, logical: n}
```

---

## ⚡ PHASE 4: RECOVERY ENGINE

---

### PROMPT 7 — Recovery Engine Core

```
I am building ARC — Agent Runtime Core. The Recovery Engine is Engine 3.

Create backend/core/recovery_engine.py with a RecoveryEngine class.

1. async checkpoint(session_id, step_number, agent_state, messages_history, context_snapshot, tool_results):
   - Serialize all inputs to JSON
   - Calculate validation_score:
     * Start at 1.0
     * messages_history empty → score = 0.0, is_valid = False
     * agent_state missing required keys → subtract 0.2
     * context_snapshot empty → subtract 0.1
   - Save Checkpoint to PostgreSQL
   - Also save to Redis with key "checkpoint:{session_id}:{step_number}" with 24hr TTL (for fast access during recovery)
   - Return checkpoint object

2. async detect_failure(output_text, expected_type=None, tool_success=None, error=None):
   - Returns (is_failure: bool, failure_type: str)
   - is_failure = True if any of:
     * error is not None → failure_type = "api_error"
     * tool_success is False → failure_type = "tool_error"  
     * output_text is None or len < 5 → failure_type = "empty_output"
     * expected_type == "json" and output_text is not valid JSON → failure_type = "bad_output"

3. async recover(session_id, failed_at_step, failure_type, error_message):
   - Create FailureEvent in DB
   - Find best checkpoint: query DB for checkpoints where session_id matches and step_number < failed_at_step and is_valid = True, order by step_number desc, limit 1
   - If no checkpoint found: return None
   - Load full checkpoint
   - Mark checkpoint as was_used_for_recovery = True
   - Update FailureEvent with recovery info
   - Publish WebSocket event: {type: "recovery_complete", session_id, recovered_from_step, steps_lost}
   - Return dict with checkpoint data ready to restore

4. async get_checkpoints(session_id) → list of all checkpoints for session
5. async get_failures(session_id) → list of all failure events for session
```

---

### PROMPT 8 — Recovery Engine API Routes

```
I am building ARC — Agent Runtime Core.

Create backend/api/routes/recovery.py with:

- GET /api/recovery/{session_id}/checkpoints → list all checkpoints, ordered by step_number
- GET /api/recovery/{session_id}/failures → list all failure events  
- GET /api/recovery/{session_id}/status → return recovery summary:
  {
    total_checkpoints: int,
    valid_checkpoints: int,
    total_failures: int,
    recoveries_attempted: int,
    recoveries_successful: int,
    last_checkpoint_step: int | null,
    last_failure_step: int | null,
    overall_health: "healthy" | "degraded" | "failed"
  }
  
Health calculation:
- healthy: no failures
- degraded: failures but all recovered successfully
- failed: failures with unsuccessful recovery

Create Pydantic response schemas for all responses.
Include checkpoint validation_score and is_valid in response.
```

---

## 🧠 PHASE 5: ARC RUNTIME ORCHESTRATOR

---

### PROMPT 9 — ARC Runtime Core

```
I am building ARC — Agent Runtime Core.

Create backend/core/arc_runtime.py with an ARCRuntime class that wires all three engines together.

Constructor: __init__(self, anthropic_client, agent_name, task)
- Creates FlightRecorder, ContextFirewall, RecoveryEngine instances
- Calls flight_recorder.start_session(agent_name, task)
- Stores session_id
- step_counter starts at 0

Main method: async call_claude(messages, tools=None, context_sources=None)
Pipeline:
1. step_counter += 1
2. If context_sources provided: run through ContextFirewall.filter()
   - Publish websocket event: {type: "context_filtered", conflicts_found: n}
   - Inject filtered context as system message
3. Call Anthropic claude-sonnet-4-6 API with messages + tools
4. Record in FlightRecorder.record_llm_call()
5. Publish websocket event: {type: "step_completed", step_number, confidence, summary}
6. Check for failure: FlightRecorder detected confidence < 0.2 → is_failure
7. Checkpoint: RecoveryEngine.checkpoint(session_id, step_number, state, messages, context)
8. If failure detected: RecoveryEngine.recover() → restore state → retry once
9. Return response text

Method: async run_tool(tool_name, tool_input, tool_fn)
- Execute tool_fn(tool_input)
- Record in FlightRecorder.record_tool_call()
- Checkpoint state
- Return result

Method: complete(final_output)
- flight_recorder.end_session(session_id, "completed")
- Publish {type: "session_complete", session_id}

Property: session_id → returns current session_id
Property: dashboard_url → returns f"http://localhost:3000/sessions/{session_id}"
```

---

## 🎨 PHASE 6: FRONTEND DASHBOARD

---

### PROMPT 10 — Dashboard Layout + Dark UI

```
I am building ARC — Agent Runtime Core dashboard in React + Vite + Tailwind CSS.

Create the base layout with a dark, professional design:

Color palette:
- Background: #0A0A0F (near black)
- Surface: #12121A (cards)
- Border: #1E1E2E
- Accent: #6366F1 (indigo — for active states)
- Success: #10B981 (green)
- Warning: #F59E0B (amber)
- Danger: #EF4444 (red)
- Text primary: #F1F5F9
- Text secondary: #94A3B8

Create src/App.jsx with:
- Sidebar navigation (left, 240px wide) with links: Dashboard, Sessions, Playground
- Top header with "ARC" logo (monospace font) and connection status indicator
- Main content area (right side)

Create src/pages/Dashboard.jsx:
- Stats row at top: Total Sessions | Active Sessions | Success Rate | Avg Recovery Time
- "Live Feed" section below showing recent agent activity as a scrolling list
- Each feed item shows: session name, status badge (colored), current step, time ago

Create src/components/Dashboard/AgentCard.jsx:
- Card showing: agent name, task (truncated), status badge, step counter, duration
- Status badges: running (indigo pulse), completed (green), failed (red), recovered (amber)

Use Tailwind CSS only. No external component libraries.
Make it feel like a developer tool — clean, dense, professional.
```

---

### PROMPT 11 — Flight Recorder UI

```
I am building ARC — the Flight Recorder tab shows a visual replay of every agent decision.

Create src/pages/SessionView.jsx that:
- Fetches session data from GET /api/sessions/{session_id}
- Fetches trace from GET /api/sessions/{session_id}/trace
- Shows three tabs: "Flight Recorder" | "Context Firewall" | "Recovery Engine"

Create src/components/FlightRecorder/TraceTimeline.jsx:
- Vertical timeline of all trace steps
- Each step is a card showing:
  * Step number (circle badge, colored by type: purple=llm_call, blue=tool_call, gray=decision)
  * Step type label
  * reasoning_summary text
  * Duration badge (e.g. "1.2s")
  * Confidence bar (colored: green>0.7, amber 0.4-0.7, red<0.4)
  * If was_recovered: amber "↺ Recovered" badge
  * If status=failed: red "✕ Failed" badge
- Clicking a step expands it to show full input_data and output_data as JSON

Create src/components/FlightRecorder/ReplayControls.jsx:
- Play/Pause button
- Step forward / Step back buttons
- Progress bar showing current replay position
- When playing: highlight the current step in the timeline with a pulsing border
- Speed control: 0.5x / 1x / 2x

Use the dark color palette from the previous prompt.
Make the timeline feel like a debugger, not a chat log.
```

---

### PROMPT 12 — Context Firewall UI

```
I am building ARC — the Context Firewall tab shows what context was filtered and why.

Create src/components/ContextFirewall/ContextGraph.jsx:
- A visual diagram showing context flow
- Left column: "Raw Sources" — list of all sources with confidence bars
- Middle: "Firewall" — shows filter stats (X passed, Y rejected)
- Right column: "To Claude" — only the sources that passed

Each source card shows:
- Source name
- Source type icon (document/api/user)
- Relevance score as a percentage bar
- "PASSED" (green) or "REJECTED" (red with reason) badge

Create src/components/ContextFirewall/ConflictAlert.jsx:
- List of all conflicts detected
- Each conflict card shows:
  * Severity badge (critical=red, high=orange, medium=amber, low=gray)
  * Conflict type (Numerical / Temporal / Factual / Logical)
  * Description text
  * Resolution taken
  * The two conflicting sources side by side
- Sort by severity (critical first)
- If no conflicts: show green "✓ No conflicts detected" message

Create src/components/ContextFirewall/ProvenanceTag.jsx:
- Small inline tag component showing source name + confidence
- Used inside the final context display to tag each piece of information

Integrate these into the "Context Firewall" tab of SessionView.jsx
```

---

### PROMPT 13 — Recovery Engine UI

```
I am building ARC — the Recovery Engine tab shows checkpoints and failure recovery.

Create src/components/RecoveryEngine/CheckpointList.jsx:
- Horizontal timeline at the top showing all steps
- Green circles for successful checkpoints
- Red X for failure points
- Amber arrows showing recovery jumps (from failure step back to checkpoint step)
- Tooltip on hover showing: step number, timestamp, validation_score

Create src/components/RecoveryEngine/RecoveryStatus.jsx:
- Summary card at top:
  * Total checkpoints saved
  * Failures detected
  * Recovery success rate
  * Overall health badge (Healthy/Degraded/Failed)

- Failures section below:
  Each failure card shows:
  * Failure type badge
  * Error message
  * "Recovered from Step X" with arrow if recovered
  * Steps lost count
  * Recovery time

Create src/hooks/useWebSocket.js:
- Custom hook that connects to WebSocket ws://localhost:8000/ws/sessions/{sessionId}
- Maintains connection with auto-reconnect on disconnect
- Returns: { events, isConnected, lastEvent }

Create src/components/Dashboard/LiveFeed.jsx:
- Uses useWebSocket hook
- Shows real-time events as they come in
- Event types styled differently:
  * step_completed: subtle gray row
  * conflict_detected: amber highlighted row
  * failure_detected: red highlighted row
  * recovery_complete: green highlighted row
  * session_complete: bold green row

Integrate into the "Recovery Engine" tab of SessionView.jsx
```

---

### PROMPT 14 — Playground Page

```
I am building ARC — the Playground page lets users run a demo agent and watch ARC in action.

Create src/pages/Playground.jsx:

Left panel (40% width):
- Task input: large textarea "What should the agent do?"
- Pre-built scenarios dropdown:
  * "Research a company" 
  * "Analyze a document"
  * "Answer with conflicting sources" (triggers conflict detection)
  * "Long task with API failure" (triggers recovery)
- "Inject Chaos" toggle: when on, will randomly fail midway
- "Run Agent" button (indigo, full width)

Right panel (60% width):
- Live trace appears here as the agent runs
- Use the TraceTimeline component but in "live mode" — steps appear one by one as WebSocket events arrive
- Show a pulsing "Agent Running..." indicator at the bottom while session is active
- When done: show summary card with:
  * Total steps
  * Conflicts detected
  * Recoveries made
  * Link to full session view

When "Run Agent" is clicked:
- POST to /api/playground/run with {task, scenario, inject_chaos}
- Get back session_id
- Connect WebSocket to /ws/sessions/{session_id}
- Render live trace as events arrive

This is the main DEMO PAGE. Make it feel exciting to watch.
Make the live trace reveal feel like watching code compile — technical and satisfying.
```

---

## 🎮 PHASE 7: DEMO AGENT

---

### PROMPT 15 — Demo Agent + Chaos Injector

```
I am building ARC — Agent Runtime Core.

Create demo/demo_agent.py — a compelling demo agent that showcases all three ARC engines:

The agent task: "Research Anthropic, find their latest funding, key products, and write an investment brief"

The agent does these steps:
1. Search for Anthropic overview (simulated - return hardcoded realistic data)
2. Search for funding information (two conflicting sources - one says $7.3B, one says $8.1B → triggers Context Firewall conflict detection)
3. Search for products list (returns real data about Claude models)
4. Search for competitors (returns OpenAI, Google DeepMind data)
5. Write investment brief section 1 (Claude API call)
6. Write investment brief section 2 (Claude API call)  
7. Compile final brief (Claude API call)

Use ARCRuntime to wrap all calls:
```python
from core.arc_runtime import ARCRuntime
import anthropic

client = anthropic.Anthropic()
arc = ARCRuntime(client, "Investment Research Agent", 
                 "Research Anthropic and write investment brief")

# Each step calls arc.call_claude() or arc.run_tool()
```

Create demo/chaos_injector.py:
- ChaosInjector class
- inject_api_failure(probability=0.3): randomly raises an exception to simulate API failure
- inject_bad_output(text): randomly corrupts the output text
- inject_timeout(): simulates a timeout

Create backend/api/routes/playground.py:
- POST /api/playground/run: accepts {task, scenario, inject_chaos}
- Runs the demo agent in a background task
- Returns {session_id, dashboard_url} immediately
- Agent runs async in background, publishing WebSocket events

Make the demo visually compelling — the conflict between funding figures should be dramatic, and the recovery from the injected failure should be satisfying to watch.
```

---

## 🔗 PHASE 8: SDK

---

### PROMPT 16 — ARC Python SDK

```
I am building ARC — Agent Runtime Core.

Create a clean Python SDK in sdk/arc_sdk/:

File: sdk/arc_sdk/client.py
- ARCClient class
- __init__(self, api_key, server_url="http://localhost:8000")
- Methods:
  * get_sessions() → list of sessions
  * get_session(session_id) → session details
  * get_trace(session_id) → full trace
  * get_replay(session_id) → replay object

File: sdk/arc_sdk/agent.py  
- ARCAgent class that wraps any callable agent
- __init__(self, name, task, arc_client, anthropic_client)
- call_claude(messages, context_sources=None) → calls Anthropic via ARC runtime
- run_tool(tool_name, tool_input, tool_fn) → runs tool via ARC runtime
- complete(output) → marks session done
- Property: session_id
- Property: dashboard_url → "http://localhost:3000/sessions/{session_id}"

File: sdk/arc_sdk/__init__.py
Export clean API:
```python
import arc_sdk

arc_sdk.init(api_key="...", anthropic_api_key="...")

agent = arc_sdk.Agent(name="My Agent", task="Do something")
result = agent.call_claude([{"role": "user", "content": "..."}])
print(agent.dashboard_url)
```

File: sdk/README.md
Quick start guide with:
- Installation: pip install arc-sdk
- 5-line minimal example
- Link to full docs

Make the SDK feel as clean as the Anthropic SDK itself.
```

---

## 🎨 PHASE 9: POLISH

---

### PROMPT 17 — Final Polish + README

```
I am building ARC — Agent Runtime Core.

1. Create the root README.md with:
- Big "ARC — Agent Runtime Core" header
- Tagline: "The missing reliability layer between Claude and the real world"
- Three-line problem statement
- Three engine descriptions with icons
- Quick start (Docker Compose one-liner)
- SDK example (10 lines of code)
- Screenshot descriptions (placeholders)
- Architecture diagram in ASCII art

2. Add loading states to all React pages:
- Skeleton loaders for session cards
- Pulsing animation while agent is running
- Smooth fade-in for trace steps appearing

3. Add error states:
- "No sessions yet — run your first agent in the Playground"
- Connection lost banner with auto-reconnect countdown
- Failed step expanded to show full error in red

4. Add a "Copy session link" button to SessionView that copies the URL

5. Create a simple onboarding tooltip that appears on first load:
- Points to the Playground
- Says "Run a demo agent to see ARC in action"
- Dismissible with "Got it"

6. Make the dashboard header show:
- ARC logo in monospace font
- Green pulsing dot when WebSocket connected
- Gray dot when disconnected
- "X active agents" count

Keep everything in the dark color palette:
Background #0A0A0F, Surface #12121A, Accent #6366F1
```

---

## 🚀 PHASE 10: DEMO PREP

---

### PROMPT 18 — Demo Script Code

```
I am building ARC for a hackathon demo.

Create demo/hackathon_demo.py — a single file that runs the perfect hackathon demo:

The demo has three acts:

ACT 1 — "The Problem" (automatic, 30 seconds)
- Print beautiful colored terminal output showing an agent running WITHOUT ARC
- Show it failing silently on step 7
- Show "Error: unknown. Output: None. What happened? 🤷"
- Use rich library for colored terminal output

ACT 2 — "With ARC" (automatic, 90 seconds)  
- Same agent, same task, ARC is now on
- Print live trace as it runs with colors:
  * Each step: "▶ Step 3 | llm_call | Confidence: 87% | 'Claude searched for revenue data...'"
  * Conflict found: "⚠ CONFLICT DETECTED: Revenue figures disagree ($7.3B vs $8.1B) — flagging for review"
  * Failure injected: "✕ Step 7 FAILED: API timeout"
  * Recovery: "↺ Recovering from checkpoint at Step 6..."
  * Continue: "▶ Step 7 RETRY | Success | Confidence: 91%"
  * Complete: "✓ SESSION COMPLETE | 10 steps | 1 conflict resolved | 1 recovery | 18.4s"

ACT 3 — "The Replay" (interactive, 30 seconds)
- Print: "🎬 Opening Flight Recorder replay..."
- Show condensed replay of all 10 steps with timing
- Print: "🔗 Full dashboard: http://localhost:3000/sessions/{session_id}"

Use the rich library for beautiful terminal colors.
Use time.sleep() between steps for dramatic effect.
Make it feel like watching something real happen.

This is what we will run LIVE on stage.
```

---

## ✅ BUILD CHECKLIST

After all prompts, verify:

- [ ] `docker-compose up` starts everything
- [ ] Backend health check returns 200 at `http://localhost:8000/health`
- [ ] Frontend loads at `http://localhost:3000`
- [ ] WebSocket connects when session page opens
- [ ] Playground runs demo agent end to end
- [ ] Flight recorder shows steps in real time
- [ ] Context firewall shows conflict between funding figures
- [ ] Recovery engine shows checkpoint + recovery
- [ ] `python demo/hackathon_demo.py` runs the full demo
- [ ] All three tabs in SessionView work

---

## 🎯 FINAL PROMPT — If Anything Breaks

```
I am building ARC — Agent Runtime Core for a hackathon. 

Something is broken. Here is the error: [PASTE ERROR HERE]

The project structure is:
- Backend: FastAPI + PostgreSQL + Redis at localhost:8000
- Frontend: React + Vite at localhost:3000
- Three engines: FlightRecorder, ContextFirewall, RecoveryEngine
- Main orchestrator: ARCRuntime in backend/core/arc_runtime.py

Fix only the broken part. Do not rewrite anything else.
Give me the exact file and exact lines to change.
```
