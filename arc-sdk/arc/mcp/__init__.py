"""Model Context Protocol (MCP) tool router (interface only).

Declares the contract for discovering MCP servers, registering their tools, and
routing sandboxed tool executions. No transport logic is implemented here.
"""

from __future__ import annotations

from typing import Any, Dict, List, Protocol, runtime_checkable


@runtime_checkable
class MCPRouter(Protocol):
    """Discovers MCP servers and routes tool calls to them."""

    def discover(self, endpoint: str) -> List[Dict[str, Any]]:
        """Return the tool descriptors advertised by an MCP server."""
        ...

    def invoke(self, tool: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a registered MCP tool and return its result."""
        ...


__all__ = ["MCPRouter"]
