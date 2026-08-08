"""The Production Runtime Pipeline — every request runs through a graph.

The planner compiles each request into an ExecutionGraph (the source of truth
for which stages run). The executor walks the graph and publishes events; the
runtime services subscribe to those events instead of calling one another.

Public API is unchanged::

    from arc import ARC
    client = ARC(Anthropic())
    client.messages.create(...)   # everything else is automatic
"""

from __future__ import annotations

import os
from types import SimpleNamespace

from arc import ARC
from arc.types import Event


def _client() -> object:
    if os.getenv("ANTHROPIC_API_KEY"):
        from anthropic import Anthropic

        return Anthropic()

    class _Msg:
        content = [SimpleNamespace(type="text", text="A confident, complete answer.")]
        usage = SimpleNamespace(input_tokens=10, output_tokens=8)
        stop_reason = "end_turn"

    class _Messages:
        def create(self, **kwargs: object) -> object:
            return _Msg()

    return SimpleNamespace(messages=_Messages(), beta=SimpleNamespace(messages=_Messages()))


def main() -> None:
    client = ARC(_client())

    # Preview the graph a request would run through (no model call):
    trivial = client.graph(model="claude-opus-4-8", max_tokens=1024,
                           messages=[{"role": "user", "content": "Hi"}])
    tooled = client.graph(model="claude-opus-4-8", max_tokens=16000,
                          messages=[{"role": "user", "content": "Book a flight"}],
                          tools=[{"name": "book", "description": "d", "input_schema": {"type": "object"}}])
    print("trivial graph:", [n.value for n in trivial.kinds()])
    print("tooled graph :", [n.value for n in tooled.kinds()])

    # Observe the pipeline firing as services react to graph events:
    order: list[str] = []
    for name in ("plan_created", "graph_built", "request_started", "step_recorded"):
        client.event(name)(lambda evt, n=name: order.append(n))

    resp = client.messages.create(
        model="claude-opus-4-8", max_tokens=1024,
        messages=[{"role": "user", "content": "Hello"}],
    )
    print("response:", resp.content[0].text)
    print("pipeline events:", order)
    print("trace steps:", len(client.trace()))


if __name__ == "__main__":
    main()
