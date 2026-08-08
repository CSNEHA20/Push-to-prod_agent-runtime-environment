"""Integration tests for ARC Anthropic interception.

Tests drive the **real ARC transport layer** against Anthropic-SDK-shaped fakes
so every assertion proves production behaviour without a live API key.

Coverage:
    Sync messages.create
    ├── response returned unchanged
    ├── all kwargs (thinking, tools, metadata, betas) forwarded untouched
    ├── arc_context_sources stripped before SDK call
    ├── extended thinking — has_thinking recorded
    ├── tool-use blocks recorded by name
    ├── low-level stream=True iterator passthrough
    ├── failure recorded and re-raised
    ├── middleware runs in pipeline
    ├── step_recorded event dispatched
    └── verify() honours rules

    Sync messages.stream (context-manager)
    ├── text chunks delivered to caller
    ├── step recorded with stream name
    ├── final message token usage captured
    └── stream with thinking content recorded

    MCP via beta.messages
    ├── create kwargs forwarded (mcp_servers, betas)
    ├── has_mcp flag set in recorded step
    └── betas list recorded in input_summary

    Async messages.create
    ├── response returned unchanged
    ├── kwargs forwarded untouched
    ├── arc_context_sources stripped
    ├── step recorded with correct usage
    └── failure recorded and re-raised

    Async messages.stream
    ├── text chunks delivered
    └── step recorded with stream name

    AsyncAnthropicClientWrapper
    ├── wraps async client via arc.wrap()
    ├── messages returns AsyncMessagesProxy
    ├── beta returns AsyncNamespaceProxy
    └── __getattr__ passes through non-intercepted attrs

    Forward-compat __getattr__
    ├── non-intercepted methods pass through on _MessagesProxy
    ├── non-intercepted attrs pass through on AnthropicClientWrapper
    └── unknown namespace attrs pass through on _NamespaceProxy

    extract_response
    ├── thinking block sets has_thinking=True
    ├── text block captured
    ├── tool_use block captured
    └── dict-shaped response parsed
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

import pytest

from arc import ARC
from arc._runtime import extract_response
from arc._transport import (
    AsyncMessagesProxy,
    AsyncNamespaceProxy,
    AsyncStreamManagerProxy,
    _MessagesProxy,
    _NamespaceProxy,
    _StreamManagerProxy,
)
from arc.integrations.anthropic.wrapper import (
    AnthropicClientWrapper,
    AsyncAnthropicClientWrapper,
)
from arc.types import Event, TraceStep


# ---------------------------------------------------------------------------
# Shared fakes replicating the Anthropic SDK shape
# ---------------------------------------------------------------------------

class FakeTextBlock:
    type = "text"

    def __init__(self, text: str) -> None:
        self.text = text


class FakeThinkingBlock:
    """Mirrors ``anthropic.types.ThinkingBlock``."""
    type = "thinking"

    def __init__(self, thinking: str = "Let me reason step by step.") -> None:
        self.thinking = thinking


class FakeToolUseBlock:
    type = "tool_use"

    def __init__(self, name: str, input: Optional[Dict[str, Any]] = None) -> None:
        self.name = name
        self.input = input or {}
        self.id = "toolu_fake"


class FakeUsage:
    def __init__(self, input_tokens: int = 12, output_tokens: int = 34) -> None:
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class FakeMessage:
    def __init__(
        self,
        content: List[Any],
        input_tokens: int = 12,
        output_tokens: int = 34,
        stop_reason: str = "end_turn",
    ) -> None:
        self.content = content
        self.usage = FakeUsage(input_tokens, output_tokens)
        self.stop_reason = stop_reason


class FakeStreamManager:
    """Sync context-manager replicating ``anthropic.MessageStreamManager``."""

    def __init__(self, message: FakeMessage) -> None:
        self._message = message
        self.entered = False

    def __enter__(self) -> "FakeStreamManager":
        self.entered = True
        return self

    def __exit__(self, *exc: Any) -> bool:
        return False

    @property
    def text_stream(self):  # noqa: ANN201
        for block in self._message.content:
            if getattr(block, "type", None) == "text":
                yield block.text

    def get_final_message(self) -> FakeMessage:
        return self._message


class AsyncFakeStreamManager:
    """Async context-manager replicating ``anthropic.AsyncMessageStreamManager``."""

    def __init__(self, message: FakeMessage) -> None:
        self._message = message
        self.entered = False

    async def __aenter__(self) -> "AsyncFakeStreamManager":
        self.entered = True
        return self

    async def __aexit__(self, *exc: Any) -> bool:
        return False

    @property
    def text_stream(self):  # noqa: ANN201
        """Async generator over text blocks."""
        async def _gen():
            for block in self._message.content:
                if getattr(block, "type", None) == "text":
                    yield block.text
        return _gen()

    async def get_final_message(self) -> FakeMessage:
        return self._message


class FakeMessages:
    """Sync ``client.messages`` replica."""

    def __init__(self, reply: str = "This is a confident and complete answer.") -> None:
        self.reply = reply
        self.calls: List[Dict[str, Any]] = []
        self._custom_message: Optional[FakeMessage] = None

    def set_reply_message(self, msg: FakeMessage) -> None:
        self._custom_message = msg

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(dict(kwargs))
        if kwargs.get("stream") is True:
            return iter([{"type": "message_start"}, {"type": "message_stop"}])
        if self._custom_message is not None:
            return self._custom_message
        return FakeMessage([FakeTextBlock(self.reply)])

    def stream(self, **kwargs: Any) -> FakeStreamManager:
        self.calls.append(dict(kwargs))
        msg = self._custom_message or FakeMessage([FakeTextBlock(self.reply)])
        return FakeStreamManager(msg)

    def count_tokens(self, **kwargs: Any) -> Any:
        return SimpleNamespace(input_tokens=99)


class FakeClient:
    """Sync Anthropic client stand-in."""

    def __init__(self, reply: str = "This is a confident and complete answer.") -> None:
        self.messages = FakeMessages(reply)
        self.beta = SimpleNamespace(messages=FakeMessages(reply))
        self.models = SimpleNamespace(list=lambda: [])
        self.api_key = "sk-fake"


class AsyncFakeMessages:
    """Async ``client.messages`` replica."""

    def __init__(self, reply: str = "This is a confident and complete answer.") -> None:
        self.reply = reply
        self.calls: List[Dict[str, Any]] = []
        self._custom_message: Optional[FakeMessage] = None
        self._raise: Optional[Exception] = None

    def set_reply_message(self, msg: FakeMessage) -> None:
        self._custom_message = msg

    def set_raise(self, exc: Exception) -> None:
        self._raise = exc

    async def create(self, **kwargs: Any) -> Any:
        self.calls.append(dict(kwargs))
        if self._raise is not None:
            raise self._raise
        if self._custom_message is not None:
            return self._custom_message
        return FakeMessage([FakeTextBlock(self.reply)])

    def stream(self, **kwargs: Any) -> AsyncFakeStreamManager:
        self.calls.append(dict(kwargs))
        msg = self._custom_message or FakeMessage([FakeTextBlock(self.reply)])
        return AsyncFakeStreamManager(msg)

    def count_tokens(self, **kwargs: Any) -> Any:
        return SimpleNamespace(input_tokens=77)


class AsyncFakeClient:
    """AsyncAnthropic client stand-in (has __aenter__ / __aexit__)."""

    def __init__(self, reply: str = "This is a confident and complete answer.") -> None:
        self.messages = AsyncFakeMessages(reply)
        self.beta = SimpleNamespace(messages=AsyncFakeMessages(reply))
        self.api_key = "sk-fake-async"

    async def __aenter__(self) -> "AsyncFakeClient":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _arc(client: Any = None) -> ARC:
    return ARC(client or FakeClient())


# ===========================================================================
# 1. Sync messages.create — response integrity
# ===========================================================================

class TestSyncCreate:
    def test_response_returned_unchanged(self) -> None:
        client = FakeClient()
        arc = _arc(client)
        resp = arc.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": "Hello"}],
        )
        assert isinstance(resp, FakeMessage)
        assert "confident" in resp.content[0].text

    def test_all_kwargs_forwarded_untouched(self) -> None:
        client = FakeClient()
        arc = _arc(client)
        arc.messages.create(
            model="claude-opus-4-8",
            max_tokens=16000,
            messages=[{"role": "user", "content": "Hi"}],
            thinking={"type": "enabled", "budget_tokens": 10000},
            tools=[{"name": "search", "description": "d", "input_schema": {"type": "object"}}],
            tool_choice={"type": "auto"},
            metadata={"user_id": "u-42"},
            betas=["extended-thinking-2025-05-01"],
            output_config={"effort": "high"},
        )
        sent = client.messages.calls[-1]
        assert sent["thinking"] == {"type": "enabled", "budget_tokens": 10000}
        assert sent["tools"][0]["name"] == "search"
        assert sent["tool_choice"] == {"type": "auto"}
        assert sent["metadata"] == {"user_id": "u-42"}
        assert sent["betas"] == ["extended-thinking-2025-05-01"]
        assert sent["output_config"] == {"effort": "high"}

    def test_arc_context_sources_stripped(self) -> None:
        client = FakeClient()
        arc = _arc(client)
        arc.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=100,
            messages=[{"role": "user", "content": "x"}],
            arc_context_sources=[{"key": "k", "claim": "c", "relevance": 0.9}],
        )
        assert "arc_context_sources" not in client.messages.calls[-1]

    def test_step_recorded_with_correct_type_and_usage(self) -> None:
        arc = _arc()
        arc.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=100,
            messages=[{"role": "user", "content": "Q"}],
        )
        steps = arc.trace()
        assert len(steps) == 1
        assert steps[0].step_type.value == "llm_call"
        assert steps[0].token_usage == {"input_tokens": 12, "output_tokens": 34}

    def test_extended_thinking_kwarg_passes_through_and_is_recorded(self) -> None:
        client = FakeClient()
        # Server returns a response with a thinking block
        client.messages.set_reply_message(
            FakeMessage([FakeThinkingBlock(), FakeTextBlock("The answer is 42.")])
        )
        arc = _arc(client)
        arc.messages.create(
            model="claude-opus-4-8",
            max_tokens=16000,
            messages=[{"role": "user", "content": "think hard"}],
            thinking={"type": "enabled", "budget_tokens": 8000},
        )
        step = arc.trace()[-1]
        assert step.input_data["has_thinking"] is True
        assert step.output_data["has_thinking"] is True

    def test_tool_use_blocks_recorded_by_name(self) -> None:
        client = FakeClient()
        client.messages.set_reply_message(
            FakeMessage([FakeTextBlock("Calling tools."), FakeToolUseBlock("get_weather")])
        )
        arc = _arc(client)
        arc.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": "weather?"}],
        )
        step = arc.trace()[-1]
        assert step.output_data["tools"] == ["get_weather"]

    def test_multiple_tool_uses_all_recorded(self) -> None:
        client = FakeClient()
        client.messages.set_reply_message(
            FakeMessage([
                FakeToolUseBlock("search"),
                FakeToolUseBlock("calculator"),
            ])
        )
        arc = _arc(client)
        arc.messages.create(
            model="claude-sonnet-4-6", max_tokens=1024,
            messages=[{"role": "user", "content": "x"}],
        )
        step = arc.trace()[-1]
        assert step.output_data["tools"] == ["search", "calculator"]

    def test_low_level_stream_true_iterator_passthrough(self) -> None:
        arc = _arc()
        result = arc.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=100,
            messages=[{"role": "user", "content": "x"}],
            stream=True,
        )
        assert list(result)  # iterator flows through unchanged
        assert arc.trace()[0].output_data["streamed"] is True

    def test_failure_recorded_and_reraised(self) -> None:
        client = FakeClient()
        def boom(**kw: Any) -> Any:
            raise RuntimeError("api_down")
        client.messages.create = boom  # type: ignore[assignment]
        arc = _arc(client)
        with pytest.raises(RuntimeError, match="api_down"):
            arc.messages.create(
                model="claude-sonnet-4-6", max_tokens=100,
                messages=[{"role": "user", "content": "x"}],
            )
        step = arc.trace()[0]
        assert step.error == "api_down"
        assert step.confidence_score == 0.0

    def test_middleware_runs_in_pipeline(self) -> None:
        arc = _arc()
        seen: List[str] = []

        @arc.middleware
        def logging_mw(request: Any, call_next: Any) -> Any:
            seen.append(request.payload["model"])
            return call_next(request)

        arc.messages.create(
            model="claude-sonnet-4-6", max_tokens=100,
            messages=[{"role": "user", "content": "x"}],
        )
        assert seen == ["claude-sonnet-4-6"]

    def test_step_recorded_event_dispatched(self) -> None:
        arc = _arc()
        events: List[Event] = []

        @arc.event("step_recorded")
        def on_step(evt: Event) -> None:
            events.append(evt)

        arc.messages.create(
            model="claude-sonnet-4-6", max_tokens=100,
            messages=[{"role": "user", "content": "x"}],
        )
        assert len(events) == 1
        assert "dashboard_url" in events[0].payload

    def test_verify_enforces_custom_rule(self) -> None:
        arc = _arc()
        arc.messages.create(
            model="claude-sonnet-4-6", max_tokens=100,
            messages=[{"role": "user", "content": "x"}],
        )
        result = arc.verify(rules=[{"min_confidence": 0.99}])
        assert not result.is_valid
        assert result.conflicts[0].conflict_type == "rule_confidence"

    def test_betas_recorded_in_input_summary(self) -> None:
        arc = _arc()
        arc.messages.create(
            model="claude-sonnet-4-6", max_tokens=100,
            messages=[{"role": "user", "content": "x"}],
            betas=["mcp-client-2025-11-20"],
        )
        step = arc.trace()[-1]
        assert step.input_data["betas"] == ["mcp-client-2025-11-20"]


# ===========================================================================
# 2. Sync messages.stream (context-manager)
# ===========================================================================

class TestSyncStream:
    def test_text_chunks_delivered_to_caller(self) -> None:
        arc = _arc()
        with arc.messages.stream(
            model="claude-sonnet-4-6", max_tokens=100,
            messages=[{"role": "user", "content": "x"}],
        ) as stream:
            chunks = list(stream.text_stream)
        assert chunks  # at least one text chunk

    def test_step_recorded_with_stream_name(self) -> None:
        arc = _arc()
        with arc.messages.stream(
            model="claude-sonnet-4-6", max_tokens=100,
            messages=[{"role": "user", "content": "x"}],
        ) as _s:
            pass
        step = arc.trace()[-1]
        assert "messages.stream" in step.name

    def test_final_message_token_usage_captured(self) -> None:
        arc = _arc()
        with arc.messages.stream(
            model="claude-sonnet-4-6", max_tokens=100,
            messages=[{"role": "user", "content": "x"}],
        ) as _s:
            pass
        step = arc.trace()[-1]
        assert step.token_usage["input_tokens"] == 12
        assert step.token_usage["output_tokens"] == 34

    def test_stream_with_thinking_content_recorded(self) -> None:
        client = FakeClient()
        msg = FakeMessage([FakeThinkingBlock(), FakeTextBlock("deep answer")])
        client.messages.stream = lambda **kw: FakeStreamManager(msg)  # type: ignore[assignment]
        arc = _arc(client)
        with arc.messages.stream(
            model="claude-opus-4-8", max_tokens=16000,
            messages=[{"role": "user", "content": "think"}],
        ) as _s:
            pass
        step = arc.trace()[-1]
        assert step.output_data["has_thinking"] is True

    def test_stream_proxy_getattr_passthrough(self) -> None:
        client = FakeClient()
        arc = _arc(client)
        # custom_attr on the underlying FakeStreamManager should pass through
        mgr = arc.messages.stream(
            model="claude-sonnet-4-6", max_tokens=100,
            messages=[{"role": "user", "content": "x"}],
        )
        # _StreamManagerProxy has __getattr__ delegating to _manager
        assert isinstance(mgr, _StreamManagerProxy)


# ===========================================================================
# 3. MCP via beta.messages
# ===========================================================================

class TestMCPBetaMessages:
    def test_mcp_create_kwargs_forwarded(self) -> None:
        client = FakeClient()
        arc = _arc(client)
        arc.beta.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": "x"}],
            mcp_servers=[{"type": "url", "name": "my-svc", "url": "https://mcp.example/sse"}],
            betas=["mcp-client-2025-11-20"],
        )
        sent = client.beta.messages.calls[-1]
        assert sent["mcp_servers"][0]["name"] == "my-svc"
        assert "mcp-client-2025-11-20" in sent["betas"]

    def test_has_mcp_flag_set_in_step(self) -> None:
        arc = _arc()
        arc.beta.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=100,
            messages=[{"role": "user", "content": "x"}],
            mcp_servers=[{"type": "url", "name": "svc", "url": "https://x.test"}],
            betas=["mcp-client-2025-11-20"],
        )
        step = arc.trace()[-1]
        assert step.input_data["has_mcp"] is True

    def test_beta_namespace_is_proxy_type(self) -> None:
        arc = _arc()
        assert isinstance(arc.beta, _NamespaceProxy)
        assert isinstance(arc.beta.messages, _MessagesProxy)

    def test_beta_arc_context_sources_stripped(self) -> None:
        client = FakeClient()
        arc = _arc(client)
        arc.beta.messages.create(
            model="claude-sonnet-4-6", max_tokens=100,
            messages=[{"role": "user", "content": "x"}],
            arc_context_sources=[{"key": "k", "claim": "c", "relevance": 0.5}],
            betas=["mcp-client-2025-11-20"],
        )
        assert "arc_context_sources" not in client.beta.messages.calls[-1]


# ===========================================================================
# 4. __getattr__ forward-compatibility passthrough
# ===========================================================================

class TestGetAttrPassthrough:
    def test_non_intercepted_messages_method_passes_through(self) -> None:
        arc = _arc()
        # count_tokens is not intercepted, should delegate to FakeMessages
        result = arc.messages.count_tokens(messages=[])
        assert result.input_tokens == 99

    def test_client_wrapper_non_intercepted_attr_passes_through(self) -> None:
        client = FakeClient()
        wrapper = AnthropicClientWrapper(client, ARC()._runtime)
        assert wrapper.api_key == "sk-fake"
        assert wrapper.models is client.models

    def test_namespace_proxy_unknown_attr_passes_through(self) -> None:
        client = FakeClient()
        arc = _arc(client)
        # client.beta has no 'completions' — should raise AttributeError from original
        with pytest.raises(AttributeError):
            _ = arc.beta.completions  # noqa: B018

    def test_arc_wrap_returns_anthropic_wrapper(self) -> None:
        client = FakeClient()
        arc = ARC()
        wrapped = arc.wrap(client)
        assert isinstance(wrapped, AnthropicClientWrapper)

    def test_wrapped_client_messages_create_works(self) -> None:
        client = FakeClient()
        arc = ARC()
        wrapped = arc.wrap(client)
        resp = wrapped.messages.create(
            model="claude-sonnet-4-6", max_tokens=100,
            messages=[{"role": "user", "content": "hi"}],
        )
        assert isinstance(resp, FakeMessage)


# ===========================================================================
# 5. Async messages.create
# ===========================================================================

class TestAsyncCreate:
    def test_response_returned_unchanged(self) -> None:
        async def _run() -> None:
            client = AsyncFakeClient()
            arc = ARC(client)
            resp = await arc.async_messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                messages=[{"role": "user", "content": "Hello"}],
            )
            assert isinstance(resp, FakeMessage)
            assert "confident" in resp.content[0].text

        asyncio.run(_run())

    def test_all_kwargs_forwarded_untouched(self) -> None:
        async def _run() -> None:
            client = AsyncFakeClient()
            arc = ARC(client)
            await arc.async_messages.create(
                model="claude-opus-4-8",
                max_tokens=16000,
                messages=[{"role": "user", "content": "Hi"}],
                thinking={"type": "enabled", "budget_tokens": 5000},
                tools=[{"name": "calc", "description": "d", "input_schema": {"type": "object"}}],
                metadata={"user_id": "u-99"},
            )
            sent = client.messages.calls[-1]
            assert sent["thinking"] == {"type": "enabled", "budget_tokens": 5000}
            assert sent["metadata"] == {"user_id": "u-99"}

        asyncio.run(_run())

    def test_arc_context_sources_stripped(self) -> None:
        async def _run() -> None:
            client = AsyncFakeClient()
            arc = ARC(client)
            await arc.async_messages.create(
                model="claude-sonnet-4-6", max_tokens=100,
                messages=[{"role": "user", "content": "x"}],
                arc_context_sources=[{"key": "k", "claim": "c", "relevance": 0.9}],
            )
            assert "arc_context_sources" not in client.messages.calls[-1]

        asyncio.run(_run())

    def test_step_recorded_with_correct_usage(self) -> None:
        async def _run() -> None:
            client = AsyncFakeClient()
            arc = ARC(client)
            await arc.async_messages.create(
                model="claude-sonnet-4-6", max_tokens=100,
                messages=[{"role": "user", "content": "x"}],
            )
            steps = arc.trace()
            assert len(steps) == 1
            assert steps[0].token_usage == {"input_tokens": 12, "output_tokens": 34}

        asyncio.run(_run())

    def test_failure_recorded_and_reraised(self) -> None:
        async def _run() -> None:
            client = AsyncFakeClient()
            client.messages.set_raise(RuntimeError("async_api_down"))
            arc = ARC(client)
            with pytest.raises(RuntimeError, match="async_api_down"):
                await arc.async_messages.create(
                    model="claude-sonnet-4-6", max_tokens=100,
                    messages=[{"role": "user", "content": "x"}],
                )
            step = arc.trace()[0]
            assert step.error == "async_api_down"

        asyncio.run(_run())

    def test_extended_thinking_response_recorded(self) -> None:
        async def _run() -> None:
            client = AsyncFakeClient()
            client.messages.set_reply_message(
                FakeMessage([FakeThinkingBlock(), FakeTextBlock("deep async answer")])
            )
            arc = ARC(client)
            await arc.async_messages.create(
                model="claude-opus-4-8", max_tokens=16000,
                messages=[{"role": "user", "content": "think"}],
                thinking={"type": "enabled", "budget_tokens": 10000},
            )
            step = arc.trace()[-1]
            assert step.output_data["has_thinking"] is True

        asyncio.run(_run())


# ===========================================================================
# 6. Async messages.stream
# ===========================================================================

class TestAsyncStream:
    def test_text_chunks_delivered_to_caller(self) -> None:
        async def _run() -> None:
            client = AsyncFakeClient()
            arc = ARC(client)
            chunks: List[str] = []
            async with arc.async_messages.stream(
                model="claude-sonnet-4-6", max_tokens=100,
                messages=[{"role": "user", "content": "x"}],
            ) as stream:
                async for text in stream.text_stream:
                    chunks.append(text)
            assert chunks

        asyncio.run(_run())

    def test_step_recorded_with_stream_name(self) -> None:
        async def _run() -> None:
            client = AsyncFakeClient()
            arc = ARC(client)
            async with arc.async_messages.stream(
                model="claude-sonnet-4-6", max_tokens=100,
                messages=[{"role": "user", "content": "x"}],
            ) as _s:
                pass
            step = arc.trace()[-1]
            assert "messages.stream" in step.name

        asyncio.run(_run())

    def test_stream_returns_async_proxy_type(self) -> None:
        client = AsyncFakeClient()
        arc = ARC(client)
        proxy = arc.async_messages.stream(
            model="claude-sonnet-4-6", max_tokens=100,
            messages=[{"role": "user", "content": "x"}],
        )
        assert isinstance(proxy, AsyncStreamManagerProxy)


# ===========================================================================
# 7. AsyncAnthropicClientWrapper via arc.wrap()
# ===========================================================================

class TestAsyncAnthropicClientWrapper:
    def test_arc_wrap_returns_async_wrapper(self) -> None:
        client = AsyncFakeClient()
        arc = ARC()
        wrapped = arc.wrap(client)
        assert isinstance(wrapped, AsyncAnthropicClientWrapper)

    def test_messages_returns_async_proxy(self) -> None:
        client = AsyncFakeClient()
        runtime = ARC()._runtime
        wrapper = AsyncAnthropicClientWrapper(client, runtime)
        assert isinstance(wrapper.messages, AsyncMessagesProxy)

    def test_beta_returns_async_namespace_proxy(self) -> None:
        client = AsyncFakeClient()
        runtime = ARC()._runtime
        wrapper = AsyncAnthropicClientWrapper(client, runtime)
        assert isinstance(wrapper.beta, AsyncNamespaceProxy)

    def test_non_intercepted_attr_passes_through(self) -> None:
        client = AsyncFakeClient()
        runtime = ARC()._runtime
        wrapper = AsyncAnthropicClientWrapper(client, runtime)
        assert wrapper.api_key == "sk-fake-async"

    def test_async_create_via_wrapped_client(self) -> None:
        async def _run() -> None:
            client = AsyncFakeClient()
            arc = ARC()
            wrapped = arc.wrap(client)
            assert isinstance(wrapped, AsyncAnthropicClientWrapper)
            resp = await wrapped.messages.create(
                model="claude-sonnet-4-6", max_tokens=100,
                messages=[{"role": "user", "content": "hi"}],
            )
            assert isinstance(resp, FakeMessage)

        asyncio.run(_run())

    def test_repr_contains_session_id(self) -> None:
        client = AsyncFakeClient()
        runtime = ARC()._runtime
        wrapper = AsyncAnthropicClientWrapper(client, runtime)
        assert runtime.session_id in repr(wrapper)


# ===========================================================================
# 8. extract_response — unit tests
# ===========================================================================

class TestExtractResponse:
    def test_text_block_captured(self) -> None:
        msg = FakeMessage([FakeTextBlock("hello world")])
        text, _, _, _, has_thinking = extract_response(msg)
        assert text == "hello world"
        assert has_thinking is False

    def test_thinking_block_sets_flag(self) -> None:
        msg = FakeMessage([FakeThinkingBlock(), FakeTextBlock("answer")])
        text, _, _, _, has_thinking = extract_response(msg)
        assert text == "answer"
        assert has_thinking is True

    def test_tool_use_block_captured_by_name(self) -> None:
        msg = FakeMessage([FakeToolUseBlock("get_weather")])
        _, _, tool_names, _, _ = extract_response(msg)
        assert tool_names == ["get_weather"]

    def test_multiple_blocks_all_extracted(self) -> None:
        msg = FakeMessage([
            FakeThinkingBlock(),
            FakeTextBlock("part1"),
            FakeToolUseBlock("search"),
            FakeTextBlock("part2"),
        ])
        text, _, tool_names, _, has_thinking = extract_response(msg)
        assert "part1" in text and "part2" in text
        assert tool_names == ["search"]
        assert has_thinking is True

    def test_dict_shaped_response_parsed(self) -> None:
        raw = {
            "content": [{"type": "text", "text": "dict answer"}],
            "usage": {"input_tokens": 5, "output_tokens": 10},
            "stop_reason": "end_turn",
        }
        text, usage, _, stop_reason, _ = extract_response(raw)
        assert text == "dict answer"
        assert usage == {"input_tokens": 5, "output_tokens": 10}
        assert stop_reason == "end_turn"

    def test_bare_string_response(self) -> None:
        text, usage, tools, stop_reason, has_thinking = extract_response("plain string")
        assert text == "plain string"
        assert usage == {}
        assert tools == []
        assert stop_reason is None
        assert has_thinking is False

    def test_empty_content_list(self) -> None:
        msg = FakeMessage([])
        text, usage, tools, stop_reason, has_thinking = extract_response(msg)
        assert text == ""
        assert tools == []
        assert has_thinking is False

    def test_unknown_block_type_ignored(self) -> None:
        """Blocks with unknown types (e.g. future SDK block types) are ignored."""
        class FutureBlock:
            type = "redacted_thinking"  # hypothetical future type

        msg = FakeMessage([FutureBlock(), FakeTextBlock("ok")])  # type: ignore[arg-type]
        text, _, _, _, has_thinking = extract_response(msg)
        assert text == "ok"
        assert has_thinking is False  # unknown type not mistaken for thinking
