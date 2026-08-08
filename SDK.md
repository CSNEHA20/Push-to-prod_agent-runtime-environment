# ARC Python SDK Specification (`arc-sdk`)

The `arc-sdk` Python package (`sdk/arc/`) provides an Anthropic-grade client and agent execution wrapper.

---

## Core Classes

- **`ARC` & `AsyncARC`**: Synchronous and asynchronous HTTP clients (`httpx`-based) interfacing with the ARC Control Plane.
- **`ARCAgent` & `AsyncARCAgent`**: High-level agent execution wrappers featuring automated step tracing, context firewall checks, and recovery loops.

---

## High-Level Convenience Functions

- **`arc.init(api_key, anthropic_api_key, server_url, dashboard_url)`**: Configure global SDK settings.
- **`arc.wrap(client, name, task)`**: Wrap an existing `anthropic.Anthropic` client in ARC protection middleware.
- **`arc.protected(name, task)`**: Function decorator wrapping python functions in ARC trace & recovery.
- **`arc.run(target, *args, **kwargs)`**: Execute function or agent under ARC protection.
- **`arc.trace(session_id)`**: Retrieve execution step trace array.
- **`arc.replay(session_id)`**: Retrieve visual replay timeline.
- **`arc.inspect(session_id)`**: Fetch session details.
- **`arc.recover(session_id)`**: Fetch recovery status and rollback checkpoints.
- **`arc.verify(session_id_or_trace)`**: Run Context Firewall compliance checks on trace.

---

## Domain Data Models (`arc.types`)

- **`Session`**: Agent session state (`session_id`, `agent_name`, `task`, `status`, `created_at`, `total_steps`).
- **`TraceStep`**: Recorded execution step (`step_id`, `step_type`, `step_number`, `input_data`, `output_data`, `confidence_score`).
- **`FirewallRule`**: Security rule model (`id`, `rule_type`, `action`, `threshold`, `pattern`).
- **`RecoveryDiff`**: State recovery diff model (`id`, `session_id`, `failed_step_id`, `strategy_used`, `diff_payload`).
- **`VerificationResult`**: Context verification result (`is_valid`, `conflicts`, `firewall_status`).
