"""The Adaptive Planner decides an execution plan before every request.

Preview plans with ``arc.plan(...)`` (no model call needed), and observe the
``plan_created`` event that fires as the first middleware on each real request.
"""

from __future__ import annotations

from arc import ARC
from arc.types import Event

arc = ARC(offline=True)


def show(label: str, **request: object) -> None:
    plan = arc.plan(**request)
    print(f"{label}: reasoning={plan.reasoning_strategy.value} "
          f"think={plan.thinking_budget} verify={plan.verification_strategy.value} "
          f"tools={plan.tool_strategy.value} recover={plan.recovery_policy.value}")


def main() -> None:
    show("trivial   ", model="claude-opus-4-8", max_tokens=1024,
         messages=[{"role": "user", "content": "Hi"}])
    show("with-tools", model="claude-opus-4-8", max_tokens=16000,
         messages=[{"role": "user", "content": "Book a flight"}],
         tools=[{"name": "book", "description": "d", "input_schema": {"type": "object"}}])
    show("thinking  ", model="claude-opus-4-8", max_tokens=16000,
         messages=[{"role": "user", "content": "Prove it"}], thinking={"type": "adaptive"})

    print("rationale:", arc.plan(model="m", max_tokens=100,
                                 messages=[{"role": "user", "content": "Hi"}]).rationale)


if __name__ == "__main__":
    main()
