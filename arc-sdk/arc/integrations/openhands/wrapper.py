"""ARC integration — OpenHands runtime wrapper.

Intercepts ``agent.run_task(...)`` and ``agent.run(...)`` so OpenHands
execution actions are recorded in the Flight Recorder without modifying
the agent or runtime configuration.

Duck-type detection:
    ``hasattr(agent, "run_task") and hasattr(agent, "config")``.
"""

from __future__ import annotations

from typing import Any

from ..._runtime import ARCRuntime


class OpenHandsWrapper:
    """ARC-instrumented proxy for an OpenHands ``AgentController`` / runtime.

    ``run_task`` and ``run`` are intercepted.  All other attributes
    delegate to the original agent unchanged.
    """

    def __init__(self, agent: Any, runtime: ARCRuntime, name: str = "openhands") -> None:
        self._agent = agent
        self._runtime = runtime
        self._name = name

    def run_task(self, *args: Any, **kwargs: Any) -> Any:
        """Intercept ``agent.run_task(...)``."""
        return self._runtime.run_agent_call(
            invoke=lambda: self._agent.run_task(*args, **kwargs),
            args=args,
            kwargs=kwargs,
            name=f"{self._name}.run_task",
        )

    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Intercept ``agent.run(...)``."""
        return self._runtime.run_agent_call(
            invoke=lambda: self._agent.run(*args, **kwargs),
            args=args,
            kwargs=kwargs,
            name=f"{self._name}.run",
        )

    def __getattr__(self, name: str) -> Any:
        return getattr(self._agent, name)

    def __repr__(self) -> str:
        return (
            f"OpenHandsWrapper(name={self._name!r}, "
            f"session_id={self._runtime.session_id!r})"
        )


__all__ = ["OpenHandsWrapper"]
