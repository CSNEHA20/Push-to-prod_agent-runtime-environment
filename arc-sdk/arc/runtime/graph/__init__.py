"""Execution Graph — the source of truth for runtime behaviour.

The Adaptive Planner produces an :class:`~arc.types.ExecutionPlan`; the graph
:func:`~arc.runtime.graph.builder.build_execution_graph` turns that plan into an
:class:`ExecutionGraph` of typed nodes. A :class:`GraphExecutor` walks the graph
and publishes :class:`GraphEvent`\\ s to a :class:`GraphBus`; the runtime
services (firewall, recorder, verifier, recovery, replay) **subscribe** to those
events and coordinate only through the shared :class:`ExecutionContext` — they
never call one another directly.

This module declares the contracts. Concrete pieces live alongside it:
``builder.py`` (plan → graph), ``bus.py`` (in-process bus), ``executor.py``
(event-driven executor), and ``services.py`` (the subscribing services).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from ...types import (
    ExecutionPlan,
    RequestContext,
    TraceStep,
    VerificationResult,
)


class NodeKind(str, Enum):
    """The kind of work a graph node represents."""

    FIREWALL = "firewall"
    DISPATCH = "dispatch"
    RECORD = "record"
    VERIFY = "verify"
    RECOVER = "recover"
    REPLAY = "replay"


class NodePhase(str, Enum):
    """When a node runs relative to the provider dispatch."""

    PRE = "pre"
    DISPATCH = "dispatch"
    POST = "post"


class GraphEventType(str, Enum):
    """Lifecycle events published by the executor (graph-level)."""

    GRAPH_STARTED = "graph.started"
    GRAPH_COMPLETED = "graph.completed"
    GRAPH_FAILED = "graph.failed"


def node_topic(kind: NodeKind) -> str:
    """Bus topic a node of ``kind`` publishes to (e.g. ``node.firewall``)."""
    return f"node.{kind.value}"


class ExecutionNode(BaseModel):
    """A single typed step in the execution graph."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str = Field(..., description="Unique node id within the graph")
    kind: NodeKind = Field(..., description="Node kind")
    phase: NodePhase = Field(..., description="Pre/dispatch/post phase")
    config: Dict[str, Any] = Field(default_factory=dict, description="Node parameters")
    depends_on: List[str] = Field(default_factory=list, description="Upstream node ids")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class ExecutionGraph(BaseModel):
    """The typed, provider-independent plan for executing one request."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    nodes: List[ExecutionNode] = Field(default_factory=list, description="Graph nodes")
    plan: ExecutionPlan = Field(..., description="Plan this graph was built from")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Graph metadata")

    def pre_nodes(self) -> List[ExecutionNode]:
        return [n for n in self.nodes if n.phase is NodePhase.PRE]

    def post_nodes(self) -> List[ExecutionNode]:
        return [n for n in self.nodes if n.phase is NodePhase.POST]

    def kinds(self) -> List[NodeKind]:
        return [n.kind for n in self.nodes]

    def has(self, kind: NodeKind) -> bool:
        return any(n.kind is kind for n in self.nodes)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


@dataclass
class ExecutionContext:
    """Mutable per-request state shared between subscribing services.

    This is the *only* channel through which services exchange data — they read
    and write fields here in reaction to graph events rather than invoking each
    other. Holds live SDK objects, so it is a dataclass, not a Pydantic model.
    """

    request: RequestContext
    plan: ExecutionPlan
    graph: ExecutionGraph
    session_id: str
    input_summary: Dict[str, Any]
    observable: bool = True   # False for a low-level stream=True iterator
    streaming: bool = False
    is_async: bool = False

    step_number: int = 0
    response: Any = None
    final_message: Any = None
    latency_ms: float = 0.0
    error: Optional[str] = None
    exception: Optional[BaseException] = None

    conflicts: List[Any] = field(default_factory=list)
    step: Optional[TraceStep] = None
    verification: Optional[VerificationResult] = None
    replay_timeline: Any = None
    retry_requested: bool = False
    retried: bool = False

    @property
    def observed(self) -> Any:
        """The response object to record — the final message for streams."""
        return self.final_message if self.streaming else self.response

    def reset_attempt(self) -> None:
        """Clear per-attempt state before a recovery retry."""
        self.response = None
        self.final_message = None
        self.latency_ms = 0.0
        self.error = None
        self.exception = None
        self.step = None
        self.verification = None


@dataclass
class GraphEvent:
    """An event published on the :class:`GraphBus`."""

    topic: str
    context: ExecutionContext
    node: Optional[ExecutionNode] = None


@runtime_checkable
class GraphBus(Protocol):
    """Pub/sub broker connecting the executor to the runtime services."""

    def subscribe(self, topic: str, handler: Callable[[GraphEvent], None]) -> None:
        """Register ``handler`` for ``topic``."""
        ...

    def publish(self, event: GraphEvent) -> None:
        """Dispatch ``event`` to every handler subscribed to its topic."""
        ...


@runtime_checkable
class GraphExecutor(Protocol):
    """Walks an :class:`ExecutionGraph`, publishing events at each node."""

    def execute(self, ctx: ExecutionContext, dispatch: Callable[[Dict[str, Any]], Any]) -> ExecutionContext:
        """Run the full graph (pre → dispatch → post) with recovery retries."""
        ...


__all__ = [
    "NodeKind",
    "NodePhase",
    "GraphEventType",
    "node_topic",
    "ExecutionNode",
    "ExecutionGraph",
    "ExecutionContext",
    "GraphEvent",
    "GraphBus",
    "GraphExecutor",
]
