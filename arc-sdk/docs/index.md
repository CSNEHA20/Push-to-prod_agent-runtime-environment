# ARC SDK Documentation

ARC (Agent Runtime Core) is a provider-agnostic reliability runtime for AI
agents. This documentation covers the public SDK surface.

- [API Reference](./api.md) — every `ARC` method and its contract.

## Concepts

- **Session** — one protected agent run, identified by `session_id`.
- **Step** — a single recorded LLM or tool invocation (`TraceStep`).
- **Checkpoint** — a restorable snapshot created by the Recovery Engine.
- **Middleware** — an interceptor wrapped around each runtime step.
- **Plugin** — a lifecycle extension attached to an `ARC` instance.
- **Event** — a runtime signal (`step_recorded`, `recovery_triggered`, …).

## Architecture

The `ARC` facade composes eight decoupled runtime engines
(`arc.runtime.*`), a set of provider/framework adapters
(`arc.integrations.*`), and an MCP tool router (`arc.mcp`). Core engines depend
only on the interfaces declared in `arc.types` and `arc.integrations`, never on
a vendor SDK class — see PROJECT.md §5.

> **Scaffold status:** engine internals are not implemented in this package.
> Execution methods raise `NotImplementedError`; the interfaces and public API
> are stable.
