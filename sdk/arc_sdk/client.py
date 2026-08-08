"""
ARC SDK — Client module for interacting with the ARC Backend REST API.
"""

import json
import logging
from typing import List, Dict, Any, Optional

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

import urllib.request
import urllib.error

logger = logging.getLogger("arc_sdk.client")


class ARCClient:
    """
    ARCClient provides access to ARC (Agent Runtime Core) sessions, traces, and replays via HTTP API.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        server_url: str = "http://localhost:8000",
    ):
        """
        Initialize ARCClient.

        :param api_key: Optional ARC API key for authentication.
        :param server_url: Base URL of the ARC backend server (default: http://localhost:8000).
        """
        self.api_key = api_key
        self.server_url = server_url.rstrip("/")
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
            self.headers["X-API-Key"] = api_key

    def _get(self, endpoint: str) -> Any:
        """Internal helper for performing HTTP GET requests."""
        url = f"{self.server_url}{endpoint}"

        if HAS_HTTPX:
            try:
                with httpx.Client(timeout=10.0) as client:
                    resp = client.get(url, headers=self.headers)
                    resp.raise_for_status()
                    return resp.json()
            except Exception as e:
                logger.debug(f"httpx GET failed for {url}: {e}, trying fallback methods")

        if HAS_REQUESTS:
            try:
                resp = requests.get(url, headers=self.headers, timeout=10)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                logger.debug(f"requests GET failed for {url}: {e}, trying urllib fallback")

        # urllib fallback
        req = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                body = response.read().decode("utf-8")
                return json.loads(body)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            raise RuntimeError(f"ARC API HTTP Error {e.code}: {err_body}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to communicate with ARC server at {url}: {e}") from e

    def get_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieve list of active or completed agent sessions.

        :param limit: Maximum number of sessions to return (default: 50).
        :return: List of session detail dicts.
        """
        return self._get(f"/api/sessions?limit={limit}")

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieve detailed information for a specific session.

        :param session_id: UUID string of the session.
        :return: Session details dict.
        """
        return self._get(f"/api/sessions/{session_id}")

    def get_trace(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve full execution step trace for a session.

        :param session_id: UUID string of the session.
        :return: List of trace step dicts.
        """
        return self._get(f"/api/sessions/{session_id}/trace")

    def get_replay(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieve visual replay object for a session containing ordered steps, failure points, and recovery points.

        :param session_id: UUID string of the session.
        :return: Replay object dict.
        """
        return self._get(f"/api/sessions/{session_id}/replay")
