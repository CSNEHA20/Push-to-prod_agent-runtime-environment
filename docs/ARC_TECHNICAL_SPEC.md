# ARC — Technical Specification
## All Three Engines: Data Models, APIs, Logic

---

## ENGINE 1: ✈️ FLIGHT RECORDER

### What it does
Records every single thing an agent does — every Claude call, every tool invocation, every decision point, every output — with full context, timing, and confidence data. Enables step-by-step replay of any agent run.

### Core Data Models

```python
# models/trace.py

class AgentSession:
    session_id: str          # Unique run ID
    agent_name: str          # Name of the agent
    task: str                # What the agent was asked to do
    status: str              # running | completed | failed | recovered
    started_at: datetime
    ended_at: datetime | None
    total_steps: int
    failed_at_step: int | None
    recovered: bool

class TraceStep:
    step_id: str
    session_id: str
    step_number: int
    step_type: str           # llm_call | tool_call | decision | context_load
    timestamp: datetime
    duration_ms: int

    # For LLM calls
    input_messages: list     # Full messages sent to Claude
    output_text: str         # What Claude returned
    input_tokens: int
    output_tokens: int
    
    # For tool calls
    tool_name: str | None
    tool_input: dict | None
    tool_output: str | None
    tool_success: bool | None

    # Reasoning metadata
    confidence_score: float  # 0.0 to 1.0 — how confident was Claude
    reasoning_summary: str   # One-line summary of what happened here
    context_used: list[str]  # Which context pieces were active
    
    # Status
    status: str              # success | failed | skipped
    error: str | None
    was_recovered: bool

class ReplayFrame:
    session_id: str
    steps: list[TraceStep]
    total_duration_ms: int
    failure_point: int | None
    recovery_point: int | None
```

### Flight Recorder Engine

```python
# core/flight_recorder.py

class FlightRecorder:
    """
    Wraps every Claude API call and tool execution.
    Records full trace to PostgreSQL.
    Streams live updates via WebSocket.
    """
    
    def start_session(self, agent_name, task) -> AgentSession:
        """Create new recording session"""
        
    def record_llm_call(self, session_id, step_number, 
                         messages, response, duration_ms) -> TraceStep:
        """Record a Claude API call with full input/output"""
        
    def record_tool_call(self, session_id, step_number,
                          tool_name, tool_input, tool_output,
                          success, duration_ms) -> TraceStep:
        """Record a tool invocation"""
        
    def record_decision(self, session_id, step_number,
                         decision, reasoning, confidence) -> TraceStep:
        """Record a key decision point"""
        
    def end_session(self, session_id, status, error=None):
        """Mark session complete/failed"""
        
    def get_replay(self, session_id) -> ReplayFrame:
        """Get full replay data for a session"""
        
    def _calculate_confidence(self, response_text, tool_calls) -> float:
        """
        Heuristic confidence scoring:
        - Low confidence phrases: "I think", "probably", "not sure"
        - Tool call failures reduce confidence
        - Contradictions in reasoning reduce confidence
        """
        
    def _summarise_step(self, step_type, input_data, output_data) -> str:
        """Generate one-line human-readable summary of each step"""
```

### Flight Recorder API Routes

```
GET  /api/sessions                    → List all agent sessions
GET  /api/sessions/{session_id}       → Get session details
GET  /api/sessions/{session_id}/trace → Get full trace
GET  /api/sessions/{session_id}/replay → Get replay frames
POST /api/sessions/{session_id}/replay/step/{n} → Get specific step
WS   /ws/sessions/{session_id}        → Live trace stream
```

---

## ENGINE 2: 🛡️ CONTEXT FIREWALL

### What it does
Sits between your data sources and Claude. Scores relevance, detects conflicts between sources, tracks provenance of every fact, and ensures Claude only receives clean, verified, sourced context.

### Core Data Models

```python
# models/context.py

class ContextSource:
    source_id: str
    name: str                # "Company 10-K 2024", "Wikipedia", "User Input"
    source_type: str         # document | api | user | memory | tool_output
    content: str
    timestamp: datetime
    confidence: float        # How trustworthy is this source? 0.0-1.0
    metadata: dict

class ContextChunk:
    chunk_id: str
    source_id: str
    content: str
    relevance_score: float   # 0.0-1.0 — how relevant to current task
    passed_firewall: bool    # Did it make it through to Claude?
    rejection_reason: str | None

class ContextConflict:
    conflict_id: str
    session_id: str
    chunk_a_id: str          # First conflicting piece
    chunk_b_id: str          # Second conflicting piece
    conflict_type: str       # factual | temporal | numerical | logical
    description: str         # Human-readable conflict description
    resolution: str          # ignored_a | ignored_b | flagged | merged
    severity: str            # low | medium | high | critical
    detected_at: datetime

class FilteredContext:
    session_id: str
    step_number: int
    total_chunks_received: int
    chunks_passed: int
    chunks_rejected: int
    conflicts_detected: int
    final_context: str       # What actually went to Claude
    provenance_map: dict     # {fact: source_id} mapping
```

### Context Firewall Engine

```python
# core/context_firewall.py

class ContextFirewall:
    """
    Filters, validates, and tags all context before it reaches Claude.
    Detects conflicts. Tracks provenance. Enforces quality thresholds.
    """
    
    def filter(self, session_id, step_number, 
               raw_context: list[ContextSource],
               task: str) -> FilteredContext:
        """
        Main firewall pipeline:
        1. Score relevance of each chunk to current task
        2. Detect conflicts between chunks
        3. Resolve or flag conflicts
        4. Build provenance map
        5. Assemble final clean context
        """
    
    def _score_relevance(self, chunk: str, task: str) -> float:
        """
        Uses Claude to score how relevant each context chunk is.
        Filters out chunks below threshold (default: 0.3)
        """
    
    def _detect_conflicts(self, 
                           chunks: list[ContextChunk]) -> list[ContextConflict]:
        """
        Detects conflicts between context chunks:
        - Numerical conflicts (different revenue figures)
        - Temporal conflicts (outdated vs current info)
        - Factual contradictions
        Uses Claude to identify semantic conflicts
        """
    
    def _resolve_conflict(self, conflict: ContextConflict) -> str:
        """
        Resolution strategies:
        - Prefer newer source (temporal)
        - Prefer higher confidence source
        - Flag to agent for human review
        - Merge with annotation
        """
    
    def _build_provenance_map(self, 
                               chunks: list[ContextChunk],
                               sources: list[ContextSource]) -> dict:
        """
        Tags every fact in final context with:
        - Source name
        - Source timestamp  
        - Confidence score
        Returns structured provenance map
        """
    
    def _assemble_context(self, 
                           chunks: list[ContextChunk],
                           provenance: dict) -> str:
        """
        Builds final context string with inline provenance tags.
        Format: [FACT: {fact} | SOURCE: {source} | CONFIDENCE: {score}]
        """
```

### Context Firewall API Routes

```
POST /api/context/filter              → Run context through firewall
GET  /api/context/{session_id}/log    → Get all context decisions for session
GET  /api/context/{session_id}/conflicts → Get all conflicts detected
GET  /api/context/{session_id}/provenance → Get provenance map
```

---

## ENGINE 3: ⚡ RECOVERY ENGINE

### What it does
Continuously checkpoints agent state. Detects failures — network errors, bad outputs, API timeouts, logic errors. Automatically recovers from the last valid checkpoint and continues execution.

### Core Data Models

```python
# models/checkpoint.py

class Checkpoint:
    checkpoint_id: str
    session_id: str
    step_number: int
    timestamp: datetime
    
    # Complete agent state at this point
    agent_state: dict        # Full serialised agent state
    messages_history: list   # Full conversation history
    context_snapshot: str    # Context active at this point
    tool_results: dict       # All tool results received so far
    
    # Validation
    is_valid: bool
    validation_score: float  # 0.0-1.0 quality score
    
    # Recovery metadata
    was_used_for_recovery: bool
    recovery_timestamp: datetime | None

class FailureEvent:
    failure_id: str
    session_id: str
    step_number: int
    failure_type: str        # api_error | bad_output | timeout | logic_error
    error_message: str
    timestamp: datetime
    
    # Recovery
    recovery_attempted: bool
    recovery_checkpoint_id: str | None
    recovery_success: bool
    steps_replayed: int

class RecoveryResult:
    session_id: str
    original_failure: FailureEvent
    checkpoint_used: Checkpoint
    steps_lost: int          # Steps that had to be redone
    recovery_time_ms: int
    success: bool
    continued_from_step: int
```

### Recovery Engine

```python
# core/recovery_engine.py

class RecoveryEngine:
    """
    Checkpoint-based agent recovery.
    Detects failures. Finds best checkpoint. Resumes execution.
    """
    
    def checkpoint(self, session_id, step_number, 
                    agent_state, messages, context) -> Checkpoint:
        """
        Save agent state after every successful step.
        Validates the checkpoint before storing.
        Stores in Redis for fast access + PostgreSQL for persistence.
        """
    
    def detect_failure(self, step_output: str, 
                        expected_schema: dict | None,
                        tool_result: dict | None) -> tuple[bool, str]:
        """
        Multi-signal failure detection:
        - API error codes
        - Output schema validation failure
        - Hallucination detection (contradicts earlier context)
        - Confidence below threshold
        - Tool call returned error
        Returns (is_failure, failure_type)
        """
    
    def recover(self, session_id, 
                 failure: FailureEvent) -> RecoveryResult:
        """
        Recovery pipeline:
        1. Find best valid checkpoint before failure point
        2. Restore agent state from checkpoint
        3. Reconstruct messages history
        4. Restore context snapshot
        5. Return recovery result for agent to continue
        """
    
    def _find_best_checkpoint(self, session_id, 
                               before_step: int) -> Checkpoint | None:
        """
        Finds most recent valid checkpoint before failure.
        Validates checkpoint integrity before returning.
        """
    
    def _validate_checkpoint(self, checkpoint: Checkpoint) -> float:
        """
        Scores checkpoint quality:
        - Messages history complete and consistent
        - Context snapshot not empty
        - Agent state schema valid
        Returns validation score 0.0-1.0
        """
    
    def _validate_output(self, output: str, 
                          context: str) -> tuple[bool, float]:
        """
        Uses Claude to validate agent output:
        - Does it contradict the context?
        - Is it internally consistent?
        - Does it answer the actual task?
        Returns (is_valid, confidence_score)
        """
```

### Recovery Engine API Routes

```
GET  /api/recovery/{session_id}/checkpoints  → List all checkpoints
GET  /api/recovery/{session_id}/failures     → List all failures
POST /api/recovery/{session_id}/recover      → Trigger manual recovery
GET  /api/recovery/{session_id}/status       → Current recovery status
```

---

## MASTER ORCHESTRATOR: ARC Runtime

```python
# core/arc_runtime.py

class ARCRuntime:
    """
    The master orchestrator. Wires all three engines together.
    Every Claude agent call goes through this.
    """
    
    def __init__(self, anthropic_client, session_name, task):
        self.flight_recorder = FlightRecorder()
        self.context_firewall = ContextFirewall(anthropic_client)
        self.recovery_engine = RecoveryEngine()
        self.client = anthropic_client
        self.session = self.flight_recorder.start_session(session_name, task)
    
    def call_claude(self, messages, tools=None, 
                     context_sources=None) -> str:
        """
        The main wrapped Claude call:
        1. Run context through firewall
        2. Call Claude with clean context
        3. Record the call in flight recorder
        4. Checkpoint the state
        5. Validate the output
        6. If failure: trigger recovery
        7. Return result
        """
    
    def run_tool(self, tool_name, tool_input) -> dict:
        """
        Wrapped tool execution:
        1. Execute tool
        2. Record in flight recorder
        3. Validate output
        4. Return result or trigger recovery
        """
    
    def complete(self, final_output: str):
        """Mark session as successfully completed"""
    
    def get_session_id(self) -> str:
        """Return current session ID for dashboard link"""
```

---

## ARC SDK (What Developers Use)

```python
# sdk/arc_sdk/agent.py

import arc_sdk as arc

# Initialize ARC
arc.init(api_key="your-arc-key")

# Wrap any Claude agent with ARC
@arc.agent(name="Research Agent", checkpoint_every=1)
def research_agent(company_name: str) -> str:
    
    # ARC automatically:
    # - Records every Claude call
    # - Filters context through firewall  
    # - Checkpoints after each step
    # - Recovers from failures
    
    context = arc.context([
        {"source": "web_search", "content": search(company_name)},
        {"source": "database", "content": db.get(company_name)},
    ])
    
    result = arc.call_claude(
        messages=[{"role": "user", "content": f"Research {company_name}"}],
        context=context
    )
    
    return result

# Run it — ARC handles everything
output = research_agent("Anthropic")
print(f"Dashboard: https://arc.dev/sessions/{arc.last_session_id}")
```

### SDK Installation
```bash
pip install arc-sdk
```

### Environment Variables
```bash
ARC_API_KEY=your_arc_key
ARC_SERVER_URL=http://localhost:8000
ANTHROPIC_API_KEY=your_anthropic_key
```

---

## WebSocket — Live Trace Streaming

```python
# Real-time events pushed to dashboard

# Event types:
{
  "type": "step_started",
  "session_id": "abc123",
  "step_number": 4,
  "step_type": "llm_call",
  "timestamp": "2026-08-08T10:30:00Z"
}

{
  "type": "step_completed", 
  "session_id": "abc123",
  "step_number": 4,
  "duration_ms": 1240,
  "confidence": 0.87,
  "summary": "Claude searched for revenue data and found Q3 2025 figures"
}

{
  "type": "conflict_detected",
  "session_id": "abc123",
  "conflict": {
    "type": "numerical",
    "description": "Revenue figure differs: Source A says $1.2B, Source B says $980M",
    "severity": "high"
  }
}

{
  "type": "failure_detected",
  "session_id": "abc123",
  "step_number": 7,
  "failure_type": "api_error",
  "recovering": true
}

{
  "type": "recovery_complete",
  "session_id": "abc123",
  "recovered_from_step": 6,
  "steps_lost": 1,
  "continuing": true
}

{
  "type": "session_complete",
  "session_id": "abc123",
  "total_steps": 10,
  "total_duration_ms": 18400,
  "recovered": true
}
```

---

## Database Schema

```sql
-- Sessions
CREATE TABLE agent_sessions (
    session_id VARCHAR PRIMARY KEY,
    agent_name VARCHAR NOT NULL,
    task TEXT NOT NULL,
    status VARCHAR DEFAULT 'running',
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    total_steps INTEGER DEFAULT 0,
    failed_at_step INTEGER,
    recovered BOOLEAN DEFAULT FALSE
);

-- Trace Steps  
CREATE TABLE trace_steps (
    step_id VARCHAR PRIMARY KEY,
    session_id VARCHAR REFERENCES agent_sessions(session_id),
    step_number INTEGER NOT NULL,
    step_type VARCHAR NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    duration_ms INTEGER,
    input_data JSONB,
    output_data TEXT,
    tool_name VARCHAR,
    tool_input JSONB,
    tool_output TEXT,
    tool_success BOOLEAN,
    confidence_score FLOAT,
    reasoning_summary TEXT,
    context_used JSONB,
    status VARCHAR DEFAULT 'success',
    error TEXT,
    was_recovered BOOLEAN DEFAULT FALSE
);

-- Context Conflicts
CREATE TABLE context_conflicts (
    conflict_id VARCHAR PRIMARY KEY,
    session_id VARCHAR REFERENCES agent_sessions(session_id),
    step_number INTEGER,
    conflict_type VARCHAR,
    description TEXT,
    resolution VARCHAR,
    severity VARCHAR,
    source_a_id VARCHAR,
    source_b_id VARCHAR,
    detected_at TIMESTAMP DEFAULT NOW()
);

-- Checkpoints
CREATE TABLE checkpoints (
    checkpoint_id VARCHAR PRIMARY KEY,
    session_id VARCHAR REFERENCES agent_sessions(session_id),
    step_number INTEGER NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    agent_state JSONB,
    messages_history JSONB,
    context_snapshot TEXT,
    tool_results JSONB,
    is_valid BOOLEAN DEFAULT TRUE,
    validation_score FLOAT,
    was_used_for_recovery BOOLEAN DEFAULT FALSE
);

-- Failure Events
CREATE TABLE failure_events (
    failure_id VARCHAR PRIMARY KEY,
    session_id VARCHAR REFERENCES agent_sessions(session_id),
    step_number INTEGER,
    failure_type VARCHAR,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT NOW(),
    recovery_attempted BOOLEAN DEFAULT FALSE,
    recovery_checkpoint_id VARCHAR,
    recovery_success BOOLEAN,
    steps_replayed INTEGER
);

-- Indexes
CREATE INDEX idx_trace_session ON trace_steps(session_id);
CREATE INDEX idx_checkpoint_session ON checkpoints(session_id);
CREATE INDEX idx_failure_session ON failure_events(session_id);
```

---

## Environment Variables

```bash
# .env.example

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Database
DATABASE_URL=postgresql://arc:arc@localhost:5432/arc
REDIS_URL=redis://localhost:6379

# ARC Server
ARC_SECRET_KEY=your-secret-key-here
ARC_PORT=8000
ARC_ENV=development

# Firewall Settings
CONTEXT_RELEVANCE_THRESHOLD=0.3
CONFLICT_DETECTION_ENABLED=true
MAX_CONTEXT_CHUNKS=20

# Recovery Settings
CHECKPOINT_EVERY_N_STEPS=1
MAX_RECOVERY_ATTEMPTS=3
CHECKPOINT_RETENTION_HOURS=24

# Frontend
VITE_ARC_WS_URL=ws://localhost:8000/ws
VITE_ARC_API_URL=http://localhost:8000/api
```

---

## Docker Compose

```yaml
version: '3.8'

services:
  arc-server:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://arc:arc@postgres:5432/arc
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app

  arc-frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_ARC_API_URL=http://localhost:8000/api
      - VITE_ARC_WS_URL=ws://localhost:8000/ws

  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: arc
      POSTGRES_PASSWORD: arc
      POSTGRES_DB: arc
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

---
