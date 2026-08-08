# ARC Runtime Engine Specification

The core runtime (`arc/backend/core/`) consists of three engines orchestrated by `ARCRuntime` (`arc_runtime.py`).

---

## 1. Engine 1: Flight Recorder (`flight_recorder.py`)

- **Role**: Asynchronous execution logging and trace recording.
- **Workflow**:
  1. Intercepts step input, output, duration, and token usage.
  2. Computes heuristic confidence score (`calculate_confidence_score` starting at 0.8, deducting for hedging phrases or short responses).
  3. Writes step records to SQLite (`TraceStep` model).
  4. Emits real-time event notifications over WebSocket.

---

## 2. Engine 2: Context Firewall (`context_firewall.py`)

- **Role**: Defensive context verification before dispatching to LLM.
- **Workflow**:
  1. Scores context relevance against prompt (drops sources with score < 0.3).
  2. Detects pairwise numerical and factual conflicts between surviving context sources.
  3. Tags context items with provenance confidence scores.
  4. Formats surviving context into a system prompt instruction.

---

## 3. Engine 3: Recovery Engine (`recovery_engine.py`)

- **Role**: Automated state rollback and self-healing.
- **Workflow**:
  1. Captures cryptographic state checkpoint (`Checkpoint` model) after every successful step.
  2. On failure or low-confidence response (< 0.2), computes state diff (`arc_diff`).
  3. Identifies optimal rollback checkpoint prior to failure point.
  4. Restores agent state, prunes conflicting context, and re-executes step (guarded by `_is_retry` single-retry constraint).
