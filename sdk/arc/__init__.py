"""
ARC SDK - Agent Runtime Core Python SDK
Reliability layer for Claude AI agents: Flight Recorder, Context Firewall, Recovery Engine.
"""

import os
from typing import Optional, List, Dict, Any, Union

from .version import __version__
from .exceptions import (
    ARCError,
    APIError,
    APIConnectionError,
    AuthenticationError,
    NotFoundError,
    ServerError,
    ARCClientError,
    ARCServerError,
    ARCVerificationError,
    ARCRecoveryError,
)
from .types import (
    Session,
    SessionList,
    TraceStep,
    ReplayTimeline,
    VerificationResult,
    ConflictItem,
    RecoveryPlan,
    Checkpoint,
    SessionStatus,
    StepType,
)
from .client import ARC, AsyncARC, ARCClient, AsyncARCClient
from .agent import ARCAgent, AsyncARCAgent, wrap, protected

_default_client: Optional[ARC] = None
_global_config = {
    "api_key": None,
    "anthropic_api_key": None,
    "server_url": "http://localhost:8000",
    "dashboard_url": "http://localhost:3000",
}


def init(
    api_key: Optional[str] = None,
    anthropic_api_key: Optional[str] = None,
    server_url: str = "http://localhost:8000",
    dashboard_url: str = "http://localhost:3000",
) -> None:
    """
    Initialize global credentials and configuration for ARC SDK.

    :param api_key: ARC API key for backend authentication.
    :param anthropic_api_key: Anthropic API key for Claude model access.
    :param server_url: Base URL of ARC backend server (default: http://localhost:8000).
    :param dashboard_url: Base URL of ARC frontend dashboard (default: http://localhost:3000).
    """
    global _default_client, _global_config
    _global_config["api_key"] = api_key
    _global_config["anthropic_api_key"] = anthropic_api_key
    _global_config["server_url"] = server_url
    _global_config["dashboard_url"] = dashboard_url

    if api_key:
        os.environ["ARC_API_KEY"] = api_key
    if anthropic_api_key:
        os.environ["ANTHROPIC_API_KEY"] = anthropic_api_key

    _default_client = ARC(api_key=api_key, server_url=server_url)


def get_default_client() -> ARC:
    """Get or instantiate default ARC client using global configuration."""
    global _default_client
    if _default_client is None:
        _default_client = ARC(
            api_key=_global_config.get("api_key"),
            server_url=_global_config.get("server_url", "http://localhost:8000"),
        )
    return _default_client


# Clean API Aliases
Agent = ARCAgent
Client = ARCClient


def run(
    target: Any,
    *args,
    name: str = "ARC Managed Run",
    task: str = "Execute task function",
    **kwargs,
) -> Any:
    """
    Execute an ARCAgent instance or wrap and execute a callable target under ARC protection.

    :param target: ARCAgent instance or function callable.
    :return: Execution output result.
    """
    if isinstance(target, (ARCAgent, AsyncARCAgent)):
        if args and callable(args[0]):
            fn = args[0]
            return target.run_tool(getattr(fn, "__name__", "fn"), kwargs, fn)
        return target.complete()
    elif callable(target):
        agent = ARCAgent(name=name, task=task)
        res = agent.run_tool(getattr(target, "__name__", "run_target"), kwargs, target)
        agent.complete(output=res)
        return res
    else:
        raise ValueError(f"Cannot run object of type {type(target)}. Expected ARCAgent or Callable.")


def trace(session_id: str) -> List[TraceStep]:
    """Retrieve execution step trace for a session ID."""
    return get_default_client().get_trace(session_id)


def replay(session_id: str) -> ReplayTimeline:
    """Retrieve visual replay timeline data for a session ID."""
    return get_default_client().get_replay(session_id)


def inspect(session_id: str) -> Session:
    """Inspect detailed session information and metadata for a session ID."""
    return get_default_client().get_session(session_id)


def recover(session_id: str) -> RecoveryPlan:
    """Retrieve recovery status, rollback checkpoints, or plan for a session ID."""
    return get_default_client().get_recovery(session_id)


def verify(
    session_id_or_trace: Union[str, List[Dict[str, Any]], List[TraceStep]],
    rules: Optional[List[Dict[str, Any]]] = None,
) -> VerificationResult:
    """Verify session trace compliance using Context Firewall rules."""
    return get_default_client().verify_session(session_id_or_trace, rules=rules)


__all__ = [
    "init",
    "wrap",
    "protected",
    "run",
    "trace",
    "replay",
    "inspect",
    "recover",
    "verify",
    "Agent",
    "Client",
    "ARC",
    "AsyncARC",
    "ARCClient",
    "AsyncARCClient",
    "ARCAgent",
    "AsyncARCAgent",
    "Session",
    "SessionList",
    "TraceStep",
    "ReplayTimeline",
    "VerificationResult",
    "ConflictItem",
    "RecoveryPlan",
    "Checkpoint",
    "SessionStatus",
    "StepType",
    "ARCError",
    "APIError",
    "APIConnectionError",
    "AuthenticationError",
    "NotFoundError",
    "ServerError",
    "ARCClientError",
    "ARCServerError",
    "ARCVerificationError",
    "ARCRecoveryError",
    "__version__",
]
