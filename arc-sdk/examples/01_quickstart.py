"""Quickstart: construct ARC and wrap a client.

Execution methods are not implemented in this scaffold, so the wrap/run calls
are shown but guarded. Run with: ``python examples/01_quickstart.py``.
"""

from __future__ import annotations

from arc import ARC


def main() -> None:
    arc = ARC(api_key="demo-key", provider_api_key="mock-key", offline=True)
    print("Configured ARC:", arc)
    print("Server URL:", arc.config.server_url)

    try:
        protected = arc.wrap(object(), name="Docs Agent", task="Answer questions")
        print("Wrapped client:", protected)
    except NotImplementedError as exc:
        print("wrap() is scaffolded:", exc)


if __name__ == "__main__":
    main()
