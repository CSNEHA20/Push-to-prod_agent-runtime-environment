"""
ARC SDK — Client module for interacting with the ARC Backend REST API.
"""

import json
import logging
from typing import List, Dict, Any, Optional, Union

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

from .exceptions import ARCClientError, ARCServerError

logger = logging.getLogger("arc.client")


class ARCClient:
    """
    ARCClient provides access to ARC (Agent Runtime Core) sessions, traces, replays,
    recovery checkpoints, and firewall verification via HTTP API.
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

    def _request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Any:
        """Internal helper for performing HTTP requests with fallback libraries."""
        url = f"{self.server_url}{endpoint}"

        if HAS_HTTPX:
            try:
                with httpx.Client(timeout=2.0) as client:
                    if method.upper() == "POST":
                        resp = client.post(url, headers=self.headers, json=data)
                    else:
                        resp = client.get(url, headers=self.headers)
                    resp.raise_for_status()
                    return resp.json()
            except Exception as e:
                logger.debug(f"httpx {method} failed for {url}: {e}, trying fallbacks")

        if HAS_REQUESTS:
            try:
                if method.upper() == "POST":
                    resp = requests.post(url, headers=self.headers, json=data, timeout=2.0)
                else:
                    resp = requests.get(url, headers=self.headers, timeout=2.0)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                logger.debug(f"requests {method} failed for {url}: {e}, trying urllib fallback")

        # urllib fallback
        payload = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(url, data=payload, headers=self.headers, method=method.upper())
        try:
            with urllib.request.urlopen(req, timeout=2.0) as response:
                body = response.read().decode("utf-8")
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            if e.code >= 500:
                raise ARCServerError(f"ARC Server Error ({e.code}): {err_body}") from e
            raise ARCClientError(f"ARC Client HTTP Error ({e.code}): {err_body}") from e
        except Exception as e:
            raise ARCClientError(f"Failed to communicate with ARC server at {url}: {e}") from e

    def _get(self, endpoint: str) -> Any:
        return self._request("GET", endpoint)

    def _post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("POST", endpoint, data=data)

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

    def get_recovery(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieve recovery plan or rollback checkpoint details for a session.

        :param session_id: UUID string of the session.
        :return: Recovery status and plan details dict.
        """
        return self._get(f"/api/recovery/{session_id}")

    def verify_session(self, session_id_or_trace: Union[str, List[Dict[str, Any]]], rules: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Verify session trace compliance using Context Firewall rules.

        :param session_id_or_trace: Session ID string or raw trace list.
        :param rules: Optional list of validation rule dicts.
        :return: Verification outcome dict containing conflict analysis and status.
        """
        if isinstance(session_id_or_trace, str):
            payload = {"session_id": session_id_or_trace, "rules": rules or []}
            return self._post(f"/api/context/verify", data=payload)
        else:
            payload = {"trace": session_id_or_trace, "rules": rules or []}
            return self._post("/api/context/verify", data=payload)
