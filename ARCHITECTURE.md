# ARC System Architecture

Agent Runtime Core (ARC) is an enterprise governance, real-time observability, and self-healing runtime platform designed for autonomous LLM agents.

---

## High-Level System Tiering

```
+-----------------------------------------------------------------------+
|                              Agent Tier                               |
|   +-----------------------+              +------------------------+   |
|   |   User Agent / SDK    |              |      ARC SDK CLI       |   |
|   +-----------------------+              +------------------------+   |
+-------------------------------|---------------------------------------+
                                | REST (HTTP/2) & WebSockets
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
                                | Async SQLAlchemy (ORM)
                                v
+-----------------------------------------------------------------------+
|                           Persistence Tier                            |
|                        SQLite / Postgres Store                        |
+-----------------------------------------------------------------------+
                                ^ REST / WebSockets
                                |
+-----------------------------------------------------------------------+
|                            Management UI                              |
|                   React + Vite + Tailwind Dashboard                   |
+-----------------------------------------------------------------------+
```

---

## Core Engine Responsibilities

1. **Flight Recorder (Engine 1)**: Intercepts all LLM requests/responses and tool calls. Computes heuristic confidence scores, token metrics, and persists immutable execution traces.
2. **Context Firewall (Engine 2)**: Evaluates incoming context sources against security policies, regex rules, relevance thresholds (pruning score < 0.3), and pairwise factual conflict detectors before prompt dispatch.
3. **Recovery Engine (Engine 3)**: Creates state checkpoints after steps. Upon low-confidence responses (< 0.2) or step errors, computes state diffs, prunes conflicting context, rolls back state, and re-executes.
4. **ARC Analytics**: Provides real-time metrics (`arc_score`), failure risk prediction (`arc_predict`), state diffing (`arc_diff`), and trace visualization primitives (`arc_lens`).
