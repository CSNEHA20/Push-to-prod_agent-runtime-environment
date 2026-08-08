"""ARC integration — OpenAI Agents SDK wrapper.

Intercepts ``Runner.run(...)`` / ``agent.run(...)`` so every OpenAI
Agents SDK execution is recorded in the Flight Recorder without
modifying agent definitions.

Duck-type detection:
    ``hasattr(agent, "run") and hasattr(agent, "tools") and hasattr(agent, "model")``.
"""

from __future__ import annotations

from typing import Any

from ..._runtime import ARCRuntime


class OpenAIAgentsWrapper:
    """ARC-instrumented proxy for an OpenAI Agents SDK ``Agent`` or ``Runner``.

    ``run`` and ``run_sync`` are intercepted.  All other attributes
    delegate to the original object unchanged.
    """

    def __init__(self, agent: Any, runtime: ARCRuntime, name: str = "openai_agents") -> None:
        self._agent = agent
        self._runtime = runtime
        self._name = name

    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Intercept ``agent.run(...)`` / ``Runner.run(...)``."""
        return self._runtime.run_agent_call(
            invoke=lambda: self._agent.run(*args, **kwargs),
            args=args,
            kwargs=kwargs,
            name=f"{self._name}.run",
        )

    def run_sync(self, *args: Any, **kwargs: Any) -> Any:
        """Intercept ``agent.run_sync(...)`` if present."""
        return self._runtime.run_agent_call(
            invoke=lambda: self._agent.run_sync(*args, **kwargs),
            args=args,
            kwargs=kwargs,
            name=f"{self._name}.run_sync",
        )

    def __getattr__(self, name: str) -> Any:
        return getattr(self._agent, name)

    def __repr__(self) -> str:
        return (
            f"OpenAIAgentsWrapper(name={self._name!r}, "
            f"session_id={self._runtime.session_id!r})"
        )


__all__ = ["OpenAIAgentsWrapper"]
