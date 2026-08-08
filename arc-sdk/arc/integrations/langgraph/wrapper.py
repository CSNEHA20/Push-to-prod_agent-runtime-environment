"""ARC integration — LangGraph graph/chain wrapper.

Intercepts ``graph.invoke(...)`` and ``graph.stream(...)`` so every
LangGraph execution step is recorded in the Flight Recorder without
any changes to the graph definition or calling code.

Duck-type detection: ``hasattr(agent, "invoke") and hasattr(agent, "get_graph")``.
"""

from __future__ import annotations

from typing import Any, Iterator

from ..._runtime import ARCRuntime


class LangGraphWrapper:
    """ARC-instrumented proxy for a LangGraph ``CompiledGraph``.

    Every ``invoke`` / ``stream`` call flows through the ARC pipeline.
    All other attributes delegate to the original graph unchanged.
    """

    def __init__(self, graph: Any, runtime: ARCRuntime, name: str = "langgraph") -> None:
        self._graph = graph
        self._runtime = runtime
        self._name = name

    def invoke(self, *args: Any, **kwargs: Any) -> Any:
        """Intercept ``graph.invoke(...)``."""
        return self._runtime.run_agent_call(
            invoke=lambda: self._graph.invoke(*args, **kwargs),
            args=args,
            kwargs=kwargs,
            name=f"{self._name}.invoke",
        )

    def stream(self, *args: Any, **kwargs: Any) -> Iterator[Any]:
        """Intercept ``graph.stream(...)`` — records the full iteration."""
        result = self._runtime.run_agent_call(
            invoke=lambda: list(self._graph.stream(*args, **kwargs)),
            args=args,
            kwargs=kwargs,
            name=f"{self._name}.stream",
        )
        return iter(result)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._graph, name)

    def __repr__(self) -> str:
        return (
            f"LangGraphWrapper(name={self._name!r}, "
            f"session_id={self._runtime.session_id!r})"
        )


__all__ = ["LangGraphWrapper"]
