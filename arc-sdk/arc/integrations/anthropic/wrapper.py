"""ARC integration — Anthropic SDK client wrapper.

When ``arc.wrap(client)`` is called with an Anthropic SDK client, the returned
wrapper routes ``messages.create`` and ``messages.stream`` through the ARC
transport proxy so every call is intercepted, recorded, and verified without
changing the caller's code.

Two wrapper classes are provided:

* :class:`AnthropicClientWrapper`      — for ``anthropic.Anthropic`` (sync)
* :class:`AsyncAnthropicClientWrapper` — for ``anthropic.AsyncAnthropic`` (async)

Both classes expose the same ``messages`` and ``beta`` proxy surfaces as
``ARC(client)`` does directly, and delegate all other attributes via
``__getattr__`` so the full SDK surface remains accessible.
"""

from __future__ import annotations

from typing import Any

from ..._runtime import ARCRuntime
from ..._transport import (
    AsyncMessagesProxy,
    AsyncNamespaceProxy,
    _MessagesProxy,
    _NamespaceProxy,
)


class AnthropicClientWrapper:
    """Drop-in replacement for a sync ``anthropic.Anthropic()`` client.

    ``messages`` and ``beta`` are proxied through the ARC transport layer.
    All other attributes (``models``, ``count_tokens``, ``batches``, etc.)
    pass through to the underlying client via ``__getattr__``.

    Example::

        client = anthropic.Anthropic(api_key="...")
        wrapped = arc.wrap(client)                # or ARC(client)
        response = wrapped.messages.create(...)   # identical API
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
        """Intercepting proxy over ``client.beta`` (e.g. MCP via ``beta.messages``)."""
        return _NamespaceProxy(self._client.beta, self._runtime)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)

    def __repr__(self) -> str:
        return (
            f"AnthropicClientWrapper(session_id={self._runtime.session_id!r})"
        )


class AsyncAnthropicClientWrapper:
    """Drop-in replacement for an async ``anthropic.AsyncAnthropic()`` client.

    ``messages`` and ``beta`` are proxied through the ARC async transport layer.
    All other attributes pass through via ``__getattr__``.

    Example::

        client = anthropic.AsyncAnthropic(api_key="...")
        wrapped = arc.wrap(client)
        response = await wrapped.messages.create(...)
    """

    def __init__(self, client: Any, runtime: ARCRuntime) -> None:
        self._client = client
        self._runtime = runtime

    @property
    def messages(self) -> AsyncMessagesProxy:
        """Async intercepting proxy over ``client.messages``."""
        return AsyncMessagesProxy(self._client.messages, self._runtime)

    @property
    def beta(self) -> AsyncNamespaceProxy:
        """Async intercepting proxy over ``client.beta``."""
        return AsyncNamespaceProxy(self._client.beta, self._runtime)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)

    def __repr__(self) -> str:
        return (
            f"AsyncAnthropicClientWrapper(session_id={self._runtime.session_id!r})"
        )


__all__ = ["AnthropicClientWrapper", "AsyncAnthropicClientWrapper"]
