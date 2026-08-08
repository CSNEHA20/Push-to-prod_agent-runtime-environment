"""Contract tests for the arc-sdk public surface.

These assert *structure*: exports, method presence, typed contracts, and
registration wiring — not runtime behaviour (which is intentionally absent).
"""

from __future__ import annotations

import pytest

import arc
from arc import ARC, ARCConfig
from arc.types import Event, RequestContext, ResponseContext

EXECUTION_METHODS = ("wrap", "run", "trace", "recover", "verify", "replay", "inspect")
EXTENSION_METHODS = ("middleware", "plugin", "event")


def test_version_is_exported() -> None:
    assert isinstance(arc.__version__, str)
    assert arc.__version__.count(".") >= 2


def test_facade_exposes_full_surface() -> None:
    for name in (*EXECUTION_METHODS, *EXTENSION_METHODS):
        assert callable(getattr(ARC, name)), f"ARC.{name} missing"


def test_public_exports_present() -> None:
    for name in ("ARC", "ARCConfig", "Session", "TraceStep", "ARCError", "Middleware"):
        assert name in arc.__all__
        assert hasattr(arc, name)


def test_config_resolves_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ARC_SERVER_URL", raising=False)
    instance = ARC(offline=True)
    assert isinstance(instance.config, ARCConfig)
    assert instance.config.server_url.startswith("http")
    assert instance.config.offline is True


def test_future_milestone_methods_are_scaffolded() -> None:
    # M0.3 is implemented: wrap() and run() no longer raise NotImplementedError.
    instance = ARC(offline=True)
    # run() should succeed and return the callable's result.
    assert instance.run(lambda: 42) == 42
    # wrap() should return a WrappedAgent proxy, not raise.
    from arc._agent import WrappedAgent
    wrapped = instance.wrap(lambda: None)
    assert isinstance(wrapped, WrappedAgent)


def test_observability_methods_work_without_client() -> None:
    instance = ARC(offline=True)
    assert instance.trace() == []
    assert instance.inspect().total_steps == 0
    assert instance.verify().is_valid
    assert instance.replay().timeline_steps == []
    assert instance.recover().status == "no_checkpoint"


def test_middleware_registration_direct_and_decorator() -> None:
    instance = ARC(offline=True)

    def mw(request: RequestContext, call_next):  # type: ignore[no-untyped-def]
        return call_next(request)

    instance.middleware(mw)

    @instance.middleware
    def deco_mw(request: RequestContext, call_next) -> ResponseContext:  # type: ignore[no-untyped-def]
        return call_next(request)

    assert mw in instance.middlewares
    assert deco_mw in instance.middlewares
    assert len(instance.middlewares) == 2


def test_plugin_registration_accepts_class_and_instance() -> None:
    instance = ARC(offline=True)

    @instance.plugin
    class MetricsPlugin:
        name = "metrics"

        def setup(self, arc: ARC) -> None: ...

        def teardown(self, arc: ARC) -> None: ...

    assert MetricsPlugin.__name__ == "MetricsPlugin"
    assert any(getattr(p, "name", None) == "metrics" for p in instance.plugins)


def test_event_handler_registration() -> None:
    instance = ARC(offline=True)
    received: list[Event] = []

    @instance.event("step_recorded")
    def handler(event: Event) -> None:
        received.append(event)

    assert handler in instance.handlers("step_recorded")
    assert instance.handlers("unknown") == []


def test_invalid_middleware_rejected() -> None:
    instance = ARC(offline=True)
    with pytest.raises(arc.MiddlewareError):
        instance.middleware(42)  # type: ignore[arg-type]


def test_repr_is_informative() -> None:
    assert "ARC(" in repr(ARC(offline=True))
