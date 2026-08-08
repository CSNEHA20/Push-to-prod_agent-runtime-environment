# ARC Python SDK (`arc-sdk`) — Developer Technical Guide

## Overview

The `arc-sdk` package is the official Python client library for **Agent Runtime Core (ARC)** — a reliability layer designed for Claude AI agents. It integrates three runtime engines directly into agent workflows:

1. **Flight Recorder:** Execution step tracing, token tracking, and interactive visual replays.
2. **Context Firewall:** Dynamic context filtering, factual & numerical conflict detection, and provenance tagging.
3. **Recovery Engine:** State checkpointing, low-confidence failure detection, automated rollback, and recovery execution.

---

## Installation & Setup

```bash
pip install arc-sdk
```

---

## Top-Level API Specification (`import arc`)

### `arc.init()`
```python
arc.init(
    api_key: Optional[str] = None,
    anthropic_api_key: Optional[str] = None,
    server_url: str = "http://localhost:8000",
    dashboard_url: str = "http://localhost:3000"
)
```
Configures global SDK credentials and default client settings.

### `arc.Agent()`
```python
agent = arc.Agent(name="Financial Analyst", task="Analyze earnings reports")
```
Instantiates an `ARCAgent` session wrapper.

### `arc.run()`
```python
res = arc.run(agent)
# OR
res = arc.run(my_function, arg1, arg2)
```
Executes an `ARCAgent` session to completion or wraps a function under ARC protection.

### `arc.trace()`
```python
trace = arc.trace("session_uuid")
```
Fetches the ordered list of execution steps recorded by Flight Recorder.

### `arc.replay()`
```python
replay_data = arc.replay("session_uuid")
```
Fetches timeline replay data, failure points, and recovery state changes.

### `arc.inspect()`
```python
info = arc.inspect("session_uuid")
```
Fetches session status, timing metrics, and token usage summary.

### `arc.recover()`
```python
recovery_info = arc.recover("session_uuid")
```
Inspects recovery status and available state checkpoints.

### `arc.verify()`
```python
verification = arc.verify(session_id_or_trace_list)
```
Evaluates trace logs against Context Firewall rules to verify factual consistency.

---

## CLI Usage (`arc` command)

The SDK installs a command-line tool `arc`:

```bash
arc --version
arc init --api-key "your-key"
arc inspect <session_id>
arc trace <session_id>
arc replay <session_id>
arc recover <session_id>
arc verify <session_id>
```

---

## Semantic Release & Versioning Strategy

Version management uses Semantic Versioning (`MAJOR.MINOR.PATCH`). Automated publishing to PyPI and GitHub releases is configured via GitHub Actions (`.github/workflows/release.yml`) and `.releaserc.json`.
