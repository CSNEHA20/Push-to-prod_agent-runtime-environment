"""Build an :class:`ExecutionGraph` from an :class:`ExecutionPlan`.

The graph is a pure, deterministic function of the plan (plus two structural
flags the transport knows): whether the response is *observable* (a low-level
``stream=True`` iterator is not) and whether the call is *streaming* (a stream
cannot be re-invoked mid-flight, so it carries no recovery/retry node).

No provider-specific keys ever enter the graph — node ``config`` carries only
the plan's abstract strategy values.
"""

from __future__ import annotations

from ...types import ExecutionPlan, RecoveryPolicy
from . import ExecutionGraph, ExecutionNode, NodeKind, NodePhase


def build_execution_graph(
    plan: ExecutionPlan,
    *,
    observable: bool = True,
    streaming: bool = False,
) -> ExecutionGraph:
    """Derive the execution graph for a request from its plan."""
    nodes = [
        ExecutionNode(
            id="firewall",
            kind=NodeKind.FIREWALL,
            phase=NodePhase.PRE,
            config={"retrieval": plan.retrieval_strategy.value},
        ),
        ExecutionNode(
            id="dispatch",
            kind=NodeKind.DISPATCH,
            phase=NodePhase.DISPATCH,
            depends_on=["firewall"],
            config={
                "reasoning": plan.reasoning_strategy.value,
                "thinking_budget": plan.thinking_budget,
                "tool_strategy": plan.tool_strategy.value,
                "context_budget": plan.context_budget,
            },
        ),
        ExecutionNode(
            id="record", kind=NodeKind.RECORD, phase=NodePhase.POST, depends_on=["dispatch"]
        ),
    ]
    prev = "record"

    # Verification always runs for an observable response — confidence must be
    # derived from verification evidence, so there is always a verify node. The
    # plan's verification_strategy tunes strictness, not presence.
    if observable:
        nodes.append(
            ExecutionNode(
                id="verify",
                kind=NodeKind.VERIFY,
                phase=NodePhase.POST,
                depends_on=[prev],
                config={"strategy": plan.verification_strategy.value},
            )
        )
        prev = "verify"

    # A stream can't be re-invoked mid-flight, so it gets no recovery/retry node.
    if observable and not streaming and plan.recovery_policy is not RecoveryPolicy.NONE:
        nodes.append(
            ExecutionNode(
                id="recover",
                kind=NodeKind.RECOVER,
                phase=NodePhase.POST,
                depends_on=[prev],
                config={"policy": plan.recovery_policy.value},
            )
        )
        prev = "recover"

    nodes.append(
        ExecutionNode(id="replay", kind=NodeKind.REPLAY, phase=NodePhase.POST, depends_on=[prev])
    )

    return ExecutionGraph(
        nodes=nodes,
        plan=plan,
        metadata={"observable": observable, "streaming": streaming},
    )


__all__ = ["build_execution_graph"]
