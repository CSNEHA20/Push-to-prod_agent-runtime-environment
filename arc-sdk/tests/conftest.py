"""Shared fakes for the transport tests.

These stand in for the Anthropic SDK so the *real* ARC transport can be driven
end-to-end without a network call or API key. The fakes mimic the SDK's shape
(``client.messages.create`` returning a ``Message``-like object, ``.stream``
returning a context manager, ``.beta.messages`` for MCP) — they are not a mock
of the ARC transport itself.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict, List


class FakeTextBlock:
    type = "text"

    def __init__(self, text: str) -> None:
        self.text = text


class FakeToolUseBlock:
    type = "tool_use"

    def __init__(self, name: str) -> None:
        self.name = name
        self.input: Dict[str, Any] = {}


class FakeMessage:
    def __init__(self, content: List[Any], input_tokens: int = 12, output_tokens: int = 34,
                 stop_reason: str = "end_turn") -> None:
        self.content = content
        self.usage = SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens)
        self.stop_reason = stop_reason


class FakeStreamManager:
    def __init__(self, message: FakeMessage) -> None:
        self._message = message
        self.entered = False

    def __enter__(self) -> "FakeStreamManager":
        self.entered = True
        return self

    def __exit__(self, *exc: Any) -> bool:
        return False

    @property
    def text_stream(self):  # noqa: ANN201 - test helper
        for block in self._message.content:
            if getattr(block, "type", None) == "text":
                yield block.text

    def get_final_message(self) -> FakeMessage:
        return self._message


class FakeMessages:
    def __init__(self, reply: str = "This is a confident and complete answer to the question.") -> None:
        self.reply = reply
        self.calls: List[Dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if kwargs.get("stream") is True:
            return iter([{"type": "message_start"}, {"type": "message_stop"}])
        return FakeMessage([FakeTextBlock(self.reply)])

    def stream(self, **kwargs: Any) -> FakeStreamManager:
        self.calls.append(kwargs)
        return FakeStreamManager(FakeMessage([FakeTextBlock(self.reply)]))

    def count_tokens(self, **kwargs: Any) -> Any:
        return SimpleNamespace(input_tokens=99)


class FakeClient:
    """A minimal stand-in for ``anthropic.Anthropic()``."""

    def __init__(self, reply: str = "This is a confident and complete answer to the question.") -> None:
        self.messages = FakeMessages(reply)
        self.beta = SimpleNamespace(messages=FakeMessages(reply))
