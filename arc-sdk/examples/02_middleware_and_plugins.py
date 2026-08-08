"""Register middleware, a plugin, and an event handler.

These extension points are functional in the scaffold: registration records the
handlers into the ARC instance's registries.
"""

from __future__ import annotations

from arc import ARC
from arc.types import Event, RequestContext, ResponseContext

arc = ARC(offline=True)


@arc.middleware
def timing_middleware(request: RequestContext, call_next) -> ResponseContext:
    """Pass-through middleware; real timing added by the runtime."""
    return call_next(request)


@arc.plugin
class MetricsPlugin:
    name = "metrics"

    def setup(self, arc: ARC) -> None: ...

    def teardown(self, arc: ARC) -> None: ...


@arc.event("step_recorded")
def on_step(event: Event) -> None:
    print("step recorded:", event.payload)


def main() -> None:
    print("middlewares:", [m.__name__ for m in arc.middlewares])  # type: ignore[attr-defined]
    print("plugins:", [p.name for p in arc.plugins])
    print("handlers(step_recorded):", len(arc.handlers("step_recorded")))


if __name__ == "__main__":
    main()
