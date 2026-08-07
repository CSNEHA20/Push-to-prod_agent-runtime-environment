"""
ARC SDK — Agent Runtime Core Python SDK
Reliability layer for Claude AI agents: Flight Recorder, Context Firewall, Recovery Engine.
"""

import os
from typing import Optional

from .client import ARCClient
from .agent import ARCAgent

__version__ = "0.1.0"

_default_client: Optional[ARCClient] = None
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

    _default_client = ARCClient(api_key=api_key, server_url=server_url)


# Clean API exports
Agent = ARCAgent
Client = ARCClient

__all__ = [
    "init",
    "Agent",
    "ARCAgent",
    "Client",
    "ARCClient",
    "__version__",
]
