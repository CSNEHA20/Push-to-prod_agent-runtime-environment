"""Read back what the transport recorded: trace, replay, verify, recover, inspect.

With a provider client attached (see 04_intercept_anthropic.py), these reflect
intercepted calls. Here we show the shape against a fresh, empty session.
"""

from __future__ import annotations

from arc import ARC

arc = ARC(offline=True)


def main() -> None:
    print("session:", arc.session_id)
    print("inspect ->", arc.inspect().status.value, "| steps:", arc.inspect().total_steps)
    print("trace   ->", arc.trace())
    print("replay  ->", arc.replay().status.value)
    print("verify  ->", arc.verify().is_valid)
    print("recover ->", arc.recover().status)


if __name__ == "__main__":
    main()
