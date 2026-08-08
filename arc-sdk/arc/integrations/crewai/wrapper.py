"""ARC integration — CrewAI ``Crew`` wrapper.

Intercepts ``crew.kickoff(...)`` so every CrewAI multi-agent execution
is recorded in the Flight Recorder without modifying Crew definitions.

Duck-type detection: ``hasattr(agent, "kickoff") and hasattr(agent, "agents")``.
"""

from __future__ import annotations

from typing import Any

from ..._runtime import ARCRuntime


class CrewAIWrapper:
    """ARC-instrumented proxy for a CrewAI ``Crew``.

    ``kickoff`` is intercepted and routed through the ARC pipeline.
    All other attributes delegate to the original crew unchanged.
    """

    def __init__(self, crew: Any, runtime: ARCRuntime, name: str = "crewai") -> None:
        self._crew = crew
        self._runtime = runtime
        self._name = name

    def kickoff(self, *args: Any, **kwargs: Any) -> Any:
        """Intercept ``crew.kickoff(...)``."""
        return self._runtime.run_agent_call(
            invoke=lambda: self._crew.kickoff(*args, **kwargs),
            args=args,
            kwargs=kwargs,
            name=f"{self._name}.kickoff",
        )

    def kickoff_async(self, *args: Any, **kwargs: Any) -> Any:
        """Intercept ``crew.kickoff_async(...)`` if present."""
        return self._runtime.run_agent_call(
            invoke=lambda: self._crew.kickoff_async(*args, **kwargs),
            args=args,
            kwargs=kwargs,
            name=f"{self._name}.kickoff_async",
        )

    def __getattr__(self, name: str) -> Any:
        return getattr(self._crew, name)

    def __repr__(self) -> str:
        return (
            f"CrewAIWrapper(name={self._name!r}, "
            f"session_id={self._runtime.session_id!r})"
        )


__all__ = ["CrewAIWrapper"]
