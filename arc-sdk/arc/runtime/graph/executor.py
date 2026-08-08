"""Event-driven graph executor.

The executor is the *only* component that walks the graph. At each node it
publishes a :class:`GraphEvent`; the runtime services react. It performs three
things itself — assign the step number, enrich the payload via the provider
adapter, call the provider at the dispatch node, and apply the single recovery
retry the plan may request — everything else is done by subscribers reacting
to the events it emits.

Provider enrichment
-------------------
Before calling ``dispatch(payload)``, the executor resolves the DISPATCH node
from the graph and calls :meth:`ProviderAdapter.prepare` with the developer's
payload. The adapter returns an **enriched copy** (never mutating the original)
that carries provider-specific params derived from the planner's abstract
decisions (e.g. ``thinking``, ``reasoning_effort``, ``tool_choice``).

The enriched payload is written back to ``ctx.request.payload`` so that the
recorded ``input_summary`` and traces reflect the actual parameters sent to
the provider.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, Optional

from . import (
    ExecutionContext,
    ExecutionNode,
    GraphBus,
    GraphEvent,
    GraphEventType,
    NodeKind,
    node_topic,
)

Dispatch = Callable[[Dict[str, Any]], Any]


def _find_dispatch_node(ctx: ExecutionContext) -> Optional[ExecutionNode]:
    """Return the DISPATCH node from the graph, or None if absent."""
    for node in ctx.graph.nodes:
        if node.kind is NodeKind.DISPATCH:
            return node
    return None


class EventDrivenGraphExecutor:
    """Walks an :class:`ExecutionGraph`, publishing events for services to react to.

    :param bus: the graph event bus services subscribe to.
    :param next_step_number: assigns the step number for an attempt (per session).
    :param adapter: optional provider adapter that enriches the payload with
        provider-specific params before the dispatch node fires. Defaults to a
        no-op passthrough if omitted.
    """

    def __init__(
        self,
        bus: GraphBus,
        next_step_number: Callable[[str], int],
        adapter: Any = None,
    ) -> None:
        self._bus = bus
        self._next_step_number = next_step_number
        self._adapter = adapter  # ProviderAdapter | None

    # -- synchronous, non-streaming --------------------------------------

    def execute(self, ctx: ExecutionContext, dispatch: Dispatch) -> ExecutionContext:
        """Run the full graph, applying at most one recovery retry."""
        self._attempt(ctx, dispatch)
        if ctx.retry_requested and not ctx.retried:
            ctx.retried = True
            ctx.retry_requested = False
            ctx.reset_attempt()
            self._attempt(ctx, dispatch)
        if ctx.exception is not None:
            raise ctx.exception
        return ctx

    def _attempt(self, ctx: ExecutionContext, dispatch: Dispatch) -> None:
        ctx.step_number = self._next_step_number(ctx.session_id)
        self._publish(GraphEventType.GRAPH_STARTED.value, ctx)
        self._run_pre(ctx)

        enriched = self._enrich(ctx)

        start = time.perf_counter()
        try:
            ctx.response = dispatch(enriched)
        except Exception as exc:  # noqa: BLE001 - record, then re-raise unchanged
            ctx.latency_ms = (time.perf_counter() - start) * 1000.0
            ctx.exception = exc
            ctx.error = str(exc)
            self._publish(GraphEventType.GRAPH_FAILED.value, ctx)
            return

        ctx.latency_ms = (time.perf_counter() - start) * 1000.0
        self._run_post(ctx)
        self._publish(GraphEventType.GRAPH_COMPLETED.value, ctx)

    # -- asynchronous, non-streaming -------------------------------------

    async def execute_async(
        self, ctx: ExecutionContext, dispatch: Callable[[Dict[str, Any]], Any]
    ) -> ExecutionContext:
        """Async variant. Services stay synchronous; only dispatch is awaited.

        Async recovery retries are intentionally not applied (a retry would
        re-issue a billed call in an event loop the caller controls).
        """
        ctx.step_number = self._next_step_number(ctx.session_id)
        self._publish(GraphEventType.GRAPH_STARTED.value, ctx)
        self._run_pre(ctx)

        enriched = self._enrich(ctx)

        start = time.perf_counter()
        try:
            ctx.response = await dispatch(enriched)
        except Exception as exc:  # noqa: BLE001
            ctx.latency_ms = (time.perf_counter() - start) * 1000.0
            ctx.exception = exc
            ctx.error = str(exc)
            self._publish(GraphEventType.GRAPH_FAILED.value, ctx)
            raise

        ctx.latency_ms = (time.perf_counter() - start) * 1000.0
        self._run_post(ctx)
        self._publish(GraphEventType.GRAPH_COMPLETED.value, ctx)
        return ctx

    # -- streaming (dispatch happens outside the executor) ---------------

    def begin_stream(self, ctx: ExecutionContext) -> None:
        """Run the pre-dispatch nodes for a stream (dispatch is the SDK stream)."""
        ctx.step_number = self._next_step_number(ctx.session_id)
        self._publish(GraphEventType.GRAPH_STARTED.value, ctx)
        self._run_pre(ctx)
        # Enrich the stream payload so the SDK stream call also gets provider params.
        enriched = self._enrich(ctx)
        ctx.request.payload = enriched

    def finish_stream(self, ctx: ExecutionContext) -> None:
        """Run the post-dispatch nodes once the stream has completed."""
        if ctx.error is not None:
            self._publish(GraphEventType.GRAPH_FAILED.value, ctx)
            return
        self._run_post(ctx)
        self._publish(GraphEventType.GRAPH_COMPLETED.value, ctx)

    # -- provider enrichment ---------------------------------------------

    def _enrich(self, ctx: ExecutionContext) -> Dict[str, Any]:
        """Apply the provider adapter to the current request payload.

        Returns an enriched copy. Writes the enriched payload back to
        ``ctx.request.payload`` so recorded traces reflect actual params sent
        to the provider.
        """
        if self._adapter is None:
            return dict(ctx.request.payload)

        dispatch_node = _find_dispatch_node(ctx)
        if dispatch_node is None:
            return dict(ctx.request.payload)

        try:
            enriched = self._adapter.prepare(ctx.request.payload, dispatch_node)
        except Exception:  # noqa: BLE001 - adapter failure must never break dispatch
            enriched = dict(ctx.request.payload)

        # Write back so input_summary and traces show the actual params.
        ctx.request.payload = enriched
        return enriched

    # -- internals --------------------------------------------------------

    def _run_pre(self, ctx: ExecutionContext) -> None:
        for node in ctx.graph.pre_nodes():
            self._publish(node_topic(node.kind), ctx, node)

    def _run_post(self, ctx: ExecutionContext) -> None:
        for node in ctx.graph.post_nodes():
            self._publish(node_topic(node.kind), ctx, node)

    def _publish(self, topic: str, ctx: ExecutionContext, node: Any = None) -> None:
        self._bus.publish(GraphEvent(topic=topic, context=ctx, node=node))


__all__ = ["EventDrivenGraphExecutor", "Dispatch"]
