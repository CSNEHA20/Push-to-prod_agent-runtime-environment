"""ARC provider adapter interface.

A :class:`ProviderAdapter` is the bridge between the execution graph's
abstract DISPATCH node config and the concrete parameters a vendor SDK
expects. It is the **only** component allowed to introduce provider-specific
keys into a request payload.

Design rules
------------
* The adapter receives a **copy** of the developer's payload — it MUST return
  a new dict and MUST NOT mutate its input.
* Injection is **additive**: if the developer already set a key the adapter
  would inject (e.g. ``thinking``), the adapter leaves it unchanged.
* Adapters MUST be provider-independent at the interface level — the
  ``ProviderAdapter`` Protocol never imports a vendor SDK.

How it fits in the graph
------------------------
::

    ExecutionPlanner → ExecutionPlan
         ↓
    build_execution_graph → ExecutionGraph (DISPATCH node carries abstract config)
         ↓
    ProviderAdapter.prepare(payload, dispatch_node) → enriched_payload
         ↓
    dispatch(enriched_payload) → raw_response
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Protocol, runtime_checkable

from ..runtime.graph import ExecutionNode


@runtime_checkable
class ProviderAdapter(Protocol):
    """Translates a graph DISPATCH node's abstract config into provider params.

    Implementations are registered per-provider name (e.g. ``"anthropic"``).
    The runtime selects the adapter that matches ``ARCConfig.provider``.
    """

    #: Stable provider identifier, e.g. ``"anthropic"``.
    name: str

    def prepare(
        self,
        payload: Dict[str, Any],
        dispatch_node: ExecutionNode,
    ) -> Dict[str, Any]:
        """Return an enriched copy of ``payload`` with provider-specific params.

        Rules:
        * MUST return a new dict — never mutate ``payload``.
        * Injection is additive: skip any key the developer already set.
        * MUST NOT introduce auth credentials or any sensitive value.

        :param payload:       The developer's original request kwargs.
        :param dispatch_node: The graph DISPATCH node whose ``config`` holds
                              abstract planner decisions (``reasoning``,
                              ``thinking_budget``, ``tool_strategy``, …).
        :returns: A new dict suitable for passing to the provider SDK.
        """
        ...


class PassthroughAdapter:
    """No-op adapter for unknown or unregistered providers.

    Returns the payload unchanged (as a shallow copy so callers are always
    guaranteed a fresh dict).
    """

    name: str = "passthrough"

    def prepare(
        self,
        payload: Dict[str, Any],
        dispatch_node: ExecutionNode,
    ) -> Dict[str, Any]:
        return dict(payload)


# ---------------------------------------------------------------------------
# Registry & factory
# ---------------------------------------------------------------------------

_REGISTRY: Dict[str, Callable[[], ProviderAdapter]] = {}


def register_adapter(name: str, factory: Callable[[], ProviderAdapter]) -> None:
    """Register a ``factory`` callable for provider ``name``.

    Called once at import time by each provider adapter module. The factory is
    a zero-argument callable so imports are deferred until the adapter is
    actually requested.
    """
    _REGISTRY[name] = factory


def make_provider_adapter(provider: Optional[str]) -> ProviderAdapter:
    """Return the adapter for ``provider``, falling back to :class:`PassthroughAdapter`."""
    if provider and provider in _REGISTRY:
        return _REGISTRY[provider]()
    return PassthroughAdapter()


# ---------------------------------------------------------------------------
# Trigger adapter auto-registration on import
# ---------------------------------------------------------------------------

def _bootstrap() -> None:
    """Import each provider params module so they self-register."""
    # Errors are intentionally swallowed: a missing optional dependency must
    # never break the import of arc itself.
    try:
        from .anthropic import params as _  # noqa: F401
    except Exception:  # noqa: BLE001
        pass
    try:
        from .openai import params as _  # noqa: F401
    except Exception:  # noqa: BLE001
        pass
    try:
        from .gemini import params as _  # noqa: F401
    except Exception:  # noqa: BLE001
        pass


_bootstrap()


__all__ = [
    "ProviderAdapter",
    "PassthroughAdapter",
    "register_adapter",
    "make_provider_adapter",
]
