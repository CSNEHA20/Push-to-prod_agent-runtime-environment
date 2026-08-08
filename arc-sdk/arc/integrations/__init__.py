"""ARC integrations — provider & framework adapters.

Provider adapters (``anthropic``, ``openai``, ``gemini``) normalise vendor SDKs
onto :class:`BaseProviderAdapter`. Framework adapters (``langgraph``,
``crewai``, ``autogen``, ``openhands``) wrap agent graphs and loops. Per
PROJECT.md §5, core engines depend only on these interfaces — never on a vendor
SDK class directly.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from ..types import RequestContext, ResponseContext


@runtime_checkable
class BaseProviderAdapter(Protocol):
    """Unified contract every model-provider adapter implements."""

    #: Stable adapter identifier, e.g. ``"anthropic"``.
    name: str

    def dispatch(self, request: RequestContext) -> ResponseContext:
        """Translate an ARC request to the vendor call and back."""
        ...


@runtime_checkable
class BaseFrameworkAdapter(Protocol):
    """Unified contract for agent-framework middleware adapters."""

    name: str

    def wrap(self, target: Any) -> Any:
        """Return ``target`` instrumented with ARC protection."""
        ...


__all__ = ["BaseProviderAdapter", "BaseFrameworkAdapter"]
