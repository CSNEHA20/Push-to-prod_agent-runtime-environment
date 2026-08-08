"""ARC integration — Anthropic SDK client wrapper.

When ``arc.wrap(anthropic_client)`` is called with an Anthropic SDK client,
the returned :class:`WrappedAgent` routes ``messages.create`` and
``messages.stream`` through the ARC transport proxy (identical to the
``ARC(client).messages`` surface), so every call is intercepted, recorded,
and verified without changing the caller's code.
"""

from __future__ import annotations

from typing import Any

from ..._runtime import ARCRuntime
from ..._transport import _MessagesProxy, _NamespaceProxy


class AnthropicClientWrapper:
    """Drop-in replacement for an Anthropic SDK client with ARC interception.

    ``messages`` and ``beta`` are proxied through the transport layer.
    All other attributes (``models``, ``count_tokens``, etc.) pass through.
    """

    def __init__(self, client: Any, runtime: ARCRuntime) -> None:
        self._client = client
        self._runtime = runtime

    @property
    def messages(self) -> _MessagesProxy:
        """Intercepting proxy over ``client.messages``."""
        return _MessagesProxy(self._client.messages, self._runtime)

    @property
    def beta(self) -> _NamespaceProxy:
        """Intercepting proxy over ``client.beta``."""
        return _NamespaceProxy(self._client.beta, self._runtime)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)

    def __repr__(self) -> str:
        return f"AnthropicClientWrapper(session_id={self._runtime.session_id!r})"


__all__ = ["AnthropicClientWrapper"]
