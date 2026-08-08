"""ARC — Agent Runtime Core SDK.

A provider-agnostic reliability runtime for AI agents: a Context Firewall, a
Flight Recorder, and a self-healing Recovery Engine behind one facade.

Quickstart
----------
>>> from arc import ARC
>>> arc = ARC(api_key="...", provider_api_key="...")   # doctest: +SKIP
>>> protected = arc.wrap(my_client)                    # doctest: +SKIP

The public surface is intentionally small: construct :class:`ARC`, then use
``wrap``, ``run``, ``trace``, ``recover``, ``verify``, ``replay``, ``inspect``
and the extension points ``middleware``, ``plugin``, ``event``.
"""

from __future__ import annotations

from ._facade import ARC
from .config import ARCConfig
from .exceptions import (
    APIConnectionError,
    APIError,
    ARCError,
    AuthenticationError,
    ConfigurationError,
    MiddlewareError,
    NotFoundError,
    PluginError,
    RecoveryError,
    ServerError,
    VerificationError,
)
from .runtime.planner import Planner
from .types import (
    Checkpoint,
    ConflictItem,
    Event,
    EventHandler,
    EventType,
    ExecutionPlan,
    Middleware,
    Plugin,
    ReasoningStrategy,
    RecoveryPlan,
    RecoveryPolicy,
    ReplayTimeline,
    RequestContext,
    ResponseContext,
    RetrievalStrategy,
    Runnable,
    Session,
    SessionStatus,
    StepType,
    ToolStrategy,
    TraceStep,
    VerificationResult,
    VerificationStrategy,
)
from .version import __version__

__all__ = [
    # Facade + configuration
    "ARC",
    "ARCConfig",
    "__version__",
    # Data contracts
    "Session",
    "TraceStep",
    "Checkpoint",
    "ConflictItem",
    "VerificationResult",
    "ReplayTimeline",
    "RecoveryPlan",
    "Event",
    "ExecutionPlan",
    "RequestContext",
    "ResponseContext",
    "SessionStatus",
    "StepType",
    "EventType",
    "ReasoningStrategy",
    "RetrievalStrategy",
    "ToolStrategy",
    "VerificationStrategy",
    "RecoveryPolicy",
    # Extension-point interfaces
    "Middleware",
    "Plugin",
    "Planner",
    "EventHandler",
    "Runnable",
    # Exceptions
    "ARCError",
    "ConfigurationError",
    "APIError",
    "APIConnectionError",
    "AuthenticationError",
    "NotFoundError",
    "ServerError",
    "VerificationError",
    "RecoveryError",
    "MiddlewareError",
    "PluginError",
]
