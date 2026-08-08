# API Reference

## `ARC`

```python
ARC(
    api_key: str | None = None,
    provider_api_key: str | None = None,
    server_url: str | None = None,
    dashboard_url: str | None = None,
    *,
    config: ARCConfig | None = None,
    **options,
)
```

Construct the runtime facade. Configuration falls back to environment variables
(`ARC_API_KEY`, `ANTHROPIC_API_KEY`, `ARC_SERVER_URL`, `ARC_DASHBOARD_URL`) via
`ARCConfig.from_env`.

### Execution methods

- **`wrap(client, *, name=..., task=..., provider=None) -> Any`**
  Wrap a provider/agent client so every call is protected. Returns a drop-in
  replacement with identical call signatures.

- **`run(target, *args, name=..., task=..., **kwargs) -> Any`**
  Execute a callable or `invoke`-able object once under protection. Returns the
  target's value.

- **`trace(session_id) -> list[TraceStep]`**
  Ordered Flight Recorder steps for a session.

- **`recover(session_id) -> RecoveryPlan`**
  Compute (and optionally apply) a recovery plan.

- **`verify(session_or_trace, rules=None) -> VerificationResult`**
  Check a session id or trace against Context Firewall rules.

- **`replay(session_id) -> ReplayTimeline`**
  Deterministic, replayable timeline for a session.

- **`inspect(session_id) -> Session`**
  Session record and aggregate telemetry.

### Extension points

- **`middleware(mw=None) -> Middleware`**
  Register a `Middleware`. Callable directly or as a decorator.

- **`plugin(plugin=None) -> Plugin | type[Plugin]`**
  Register a `Plugin` instance or class. Usable as a decorator.

- **`event(name) -> Callable`**
  Return a decorator that subscribes a handler to event `name`.

### Introspection

- **`config -> ARCConfig`** — resolved configuration.
- **`middlewares -> list[Middleware]`** — registered middleware.
- **`plugins -> list[Plugin]`** — registered plugins.
- **`handlers(name) -> list[EventHandler]`** — handlers for an event.

## Data contracts

`Session`, `TraceStep`, `Checkpoint`, `ConflictItem`, `VerificationResult`,
`ReplayTimeline`, `RecoveryPlan`, `Event` — Pydantic v2 models exported from
`arc`.

## Exceptions

All derive from `ARCError`: `ConfigurationError`, `APIError`,
`APIConnectionError`, `AuthenticationError`, `NotFoundError`, `ServerError`,
`VerificationError`, `RecoveryError`, `MiddlewareError`, `PluginError`.
