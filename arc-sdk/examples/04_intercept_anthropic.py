"""Intercept every Anthropic request with one line: ``ARC(client)``.

The developer keeps writing normal Anthropic SDK code — ARC transparently runs
each ``messages.create`` through the runtime pipeline (middleware → firewall →
event bus → flight recorder → verification → recovery → Anthropic → replay →
dashboard), then returns the SDK's response object unchanged.

Runs against the real API when ANTHROPIC_API_KEY is set; otherwise it uses a
tiny inline stand-in so the ergonomics are still demonstrable offline.
"""

from __future__ import annotations

import os
from types import SimpleNamespace

from arc import ARC
from arc.types import Event


def _get_client() -> object:
    if os.getenv("ANTHROPIC_API_KEY"):
        from anthropic import Anthropic  # imported lazily; optional dependency

        return Anthropic()

    class _Msg:
        content = [SimpleNamespace(type="text", text="Hello from a stand-in client.")]
        usage = SimpleNamespace(input_tokens=8, output_tokens=6)
        stop_reason = "end_turn"

    class _Messages:
        def create(self, **kwargs: object) -> object:
            return _Msg()

    return SimpleNamespace(messages=_Messages(), beta=SimpleNamespace(messages=_Messages()))


def main() -> None:
    arc = ARC(_get_client())

    @arc.event("step_recorded")
    def _log(evt: Event) -> None:
        print(f"[arc] recorded step (confidence={evt.payload['confidence']})")

    response = arc.messages.create(
        model="claude-opus-4-8",
        max_tokens=16000,
        messages=[{"role": "user", "content": "Say hello."}],
    )
    print("response:", response.content[0].text)
    print("session:", arc.session_id)
    print("dashboard:", arc.dashboard_url)
    print("trace steps:", len(arc.trace()))
    print("verified:", arc.verify().is_valid)


if __name__ == "__main__":
    main()
