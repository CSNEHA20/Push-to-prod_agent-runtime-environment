"""
ARC SDK - Client module providing production-grade synchronous (`ARC`) and asynchronous (`AsyncARC`) clients.
Uses `httpx` natively with automatic exponential backoff retries, header management, and typed responses.
"""

import os
import time
import asyncio
import logging
from typing import List, Dict, Any, Optional, Union

import httpx

from .version import __version__
from .exceptions import (
    ARCError,
    APIError,
    APIConnectionError,
    AuthenticationError,
    NotFoundError,
    ServerError,
)
from .types import (
    Session,
    TraceStep,
    ReplayTimeline,
    VerificationResult,
    RecoveryPlan,
    ConflictItem,
    Checkpoint,
    SessionStatus,
    StepType,
)

logger = logging.getLogger("arc.client")


def _map_http_error(resp: httpx.Response) -> APIError:
    """Map httpx response status code to structured ARC exception."""
    status = resp.status_code
    try:
        data = resp.json()
        message = data.get("detail") or data.get("message") or resp.text
    except Exception:
        data = resp.text
        message = resp.text or f"HTTP status {status}"

    if status in (401, 403):
        return AuthenticationError(f"Authentication failed ({status}): {message}", status_code=status, response_body=data)
    elif status == 404:
        return NotFoundError(f"Resource not found ({status}): {message}", status_code=status, response_body=data)
    elif status >= 500:
        return ServerError(f"ARC Server Error ({status}): {message}", status_code=status, response_body=data)
    else:
        return APIError(f"API Error ({status}): {message}", status_code=status, response_body=data)


class ARC:
    """
    Synchronous client for ARC (Agent Runtime Core) REST API.
    Handles sessions, traces, visual replays, firewall verification, and recovery plans.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        server_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        self.api_key = api_key or os.getenv("ARC_API_KEY")
        base = server_url or os.getenv("ARC_SERVER_URL", "http://localhost:8000")
        self.server_url = base.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": f"arc-python-sdk/{__version__}",
        }
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
            self.headers["X-API-Key"] = self.api_key

        self._client = httpx.Client(
            base_url=self.server_url,
            headers=self.headers,
            timeout=httpx.Timeout(self.timeout),
        )

    def close(self) -> None:
        """Close the underlying HTTP client transport."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Perform HTTP request with exponential backoff retries for transient errors."""
        url = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        retries = 0
        backoff = 0.5

        while True:
            try:
                if method.upper() == "POST":
                    resp = self._client.post(url, json=data, params=params)
                elif method.upper() == "PUT":
                    resp = self._client.put(url, json=data, params=params)
                else:
                    resp = self._client.get(url, params=params)

                if resp.is_success:
                    return resp.json()

                error = _map_http_error(resp)

                if resp.status_code in (429, 502, 503, 504) and retries < self.max_retries:
                    retries += 1
                    logger.warning(f"Transient HTTP {resp.status_code} for {url}. Retrying ({retries}/{self.max_retries}) in {backoff}s...")
                    time.sleep(backoff)
                    backoff *= 2.0
                    continue

                raise error

            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
                if retries < self.max_retries:
                    retries += 1
                    logger.warning(f"Network error communicating with {self.server_url}{url}: {e}. Retrying ({retries}/{self.max_retries}) in {backoff}s...")
                    time.sleep(backoff)
                    backoff *= 2.0
                    continue
                raise APIConnectionError(f"Failed to connect to ARC server at {self.server_url}{url}: {e}", cause=e) from e

    def get_sessions(self, limit: int = 50) -> List[Session]:
        """Retrieve list of active or completed agent sessions."""
        res = self._request("GET", "/api/sessions", params={"limit": limit})
        sessions_data = res if isinstance(res, list) else res.get("sessions", [])
        return [Session.model_validate(s) for s in sessions_data]

    def get_session(self, session_id: str) -> Session:
        """Retrieve detailed metadata for a specific session."""
        res = self._request("GET", f"/api/sessions/{session_id}")
        return Session.model_validate(res)

    def create_session(
        self,
        agent_name: str,
        task: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Session:
        """Register or create a new session on the ARC server."""
        payload = {
            "agent_name": agent_name,
            "task": task,
        }
        if session_id:
            payload["session_id"] = session_id
        if metadata:
            payload["metadata"] = metadata

        res = self._request("POST", "/api/sessions", data=payload)
        return Session.model_validate(res)

    def get_trace(self, session_id: str) -> List[TraceStep]:
        """Retrieve full execution step trace for a session."""
        res = self._request("GET", f"/api/sessions/{session_id}/trace")
        trace_list = res if isinstance(res, list) else res.get("trace", [])
        return [TraceStep.model_validate(step) for step in trace_list]

    def record_step(
        self,
        session_id: str,
        step_type: str = "llm_call",
        name: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        latency_ms: float = 0.0,
        token_usage: Optional[Dict[str, int]] = None,
        confidence_score: float = 1.0,
    ) -> TraceStep:
        """Record a single step (LLM call or tool execution) into Flight Recorder."""
        payload = {
            "session_id": session_id,
            "step_type": step_type,
            "name": name or step_type,
            "input_data": input_data or {},
            "output_data": output_data or {},
            "latency_ms": latency_ms,
            "token_usage": token_usage or {},
            "confidence_score": confidence_score,
        }
        res = self._request("POST", f"/api/sessions/{session_id}/steps", data=payload)
        return TraceStep.model_validate(res)

    def get_replay(self, session_id: str) -> ReplayTimeline:
        """Retrieve visual replay object containing ordered timeline steps, failures, and checkpoints."""
        res = self._request("GET", f"/api/sessions/{session_id}/replay")
        return ReplayTimeline.model_validate(res)

    def get_recovery(self, session_id: str) -> RecoveryPlan:
        """Retrieve recovery plan or rollback checkpoint details for a session."""
        res = self._request("GET", f"/api/recovery/{session_id}")
        return RecoveryPlan.model_validate(res)

    def verify_session(
        self,
        session_id_or_trace: Union[str, List[Dict[str, Any]], List[TraceStep]],
        rules: Optional[List[Dict[str, Any]]] = None,
    ) -> VerificationResult:
        """Verify session trace compliance using Context Firewall rules."""
        if isinstance(session_id_or_trace, str):
            payload = {"session_id": session_id_or_trace, "rules": rules or []}
        else:
            trace_payload = [
                step.to_dict() if hasattr(step, "to_dict") else step
                for step in session_id_or_trace
            ]
            payload = {"trace": trace_payload, "rules": rules or []}

        res = self._request("POST", "/api/context/verify", data=payload)
        return VerificationResult.model_validate(res)


class AsyncARC:
    """
    Asynchronous client for ARC (Agent Runtime Core) REST API.
    Powered natively by `httpx.AsyncClient`.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        server_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        self.api_key = api_key or os.getenv("ARC_API_KEY")
        base = server_url or os.getenv("ARC_SERVER_URL", "http://localhost:8000")
        self.server_url = base.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": f"arc-python-sdk/{__version__}",
        }
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
            self.headers["X-API-Key"] = self.api_key

        self._client = httpx.AsyncClient(
            base_url=self.server_url,
            headers=self.headers,
            timeout=httpx.Timeout(self.timeout),
        )

    async def aclose(self) -> None:
        """Close the underlying async HTTP client transport."""
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Perform async HTTP request with exponential backoff retries."""
        url = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        retries = 0
        backoff = 0.5

        while True:
            try:
                if method.upper() == "POST":
                    resp = await self._client.post(url, json=data, params=params)
                elif method.upper() == "PUT":
                    resp = await self._client.put(url, json=data, params=params)
                else:
                    resp = await self._client.get(url, params=params)

                if resp.is_success:
                    return resp.json()

                error = _map_http_error(resp)

                if resp.status_code in (429, 502, 503, 504) and retries < self.max_retries:
                    retries += 1
                    logger.warning(f"Transient HTTP {resp.status_code} for {url}. Retrying ({retries}/{self.max_retries}) in {backoff}s...")
                    await asyncio.sleep(backoff)
                    backoff *= 2.0
                    continue

                raise error

            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
                if retries < self.max_retries:
                    retries += 1
                    logger.warning(f"Network error communicating with {self.server_url}{url}: {e}. Retrying ({retries}/{self.max_retries}) in {backoff}s...")
                    await asyncio.sleep(backoff)
                    backoff *= 2.0
                    continue
                raise APIConnectionError(f"Failed to connect to ARC server at {self.server_url}{url}: {e}", cause=e) from e

    async def get_sessions(self, limit: int = 50) -> List[Session]:
        res = await self._request("GET", "/api/sessions", params={"limit": limit})
        sessions_data = res if isinstance(res, list) else res.get("sessions", [])
        return [Session.model_validate(s) for s in sessions_data]

    async def get_session(self, session_id: str) -> Session:
        res = await self._request("GET", f"/api/sessions/{session_id}")
        return Session.model_validate(res)

    async def create_session(
        self,
        agent_name: str,
        task: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Session:
        payload = {
            "agent_name": agent_name,
            "task": task,
        }
        if session_id:
            payload["session_id"] = session_id
        if metadata:
            payload["metadata"] = metadata

        res = await self._request("POST", "/api/sessions", data=payload)
        return Session.model_validate(res)

    async def get_trace(self, session_id: str) -> List[TraceStep]:
        res = await self._request("GET", f"/api/sessions/{session_id}/trace")
        trace_list = res if isinstance(res, list) else res.get("trace", [])
        return [TraceStep.model_validate(step) for step in trace_list]

    async def record_step(
        self,
        session_id: str,
        step_type: str = "llm_call",
        name: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        latency_ms: float = 0.0,
        token_usage: Optional[Dict[str, int]] = None,
        confidence_score: float = 1.0,
    ) -> TraceStep:
        payload = {
            "session_id": session_id,
            "step_type": step_type,
            "name": name or step_type,
            "input_data": input_data or {},
            "output_data": output_data or {},
            "latency_ms": latency_ms,
            "token_usage": token_usage or {},
            "confidence_score": confidence_score,
        }
        res = await self._request("POST", f"/api/sessions/{session_id}/steps", data=payload)
        return TraceStep.model_validate(res)

    async def get_replay(self, session_id: str) -> ReplayTimeline:
        res = await self._request("GET", f"/api/sessions/{session_id}/replay")
        return ReplayTimeline.model_validate(res)

    async def get_recovery(self, session_id: str) -> RecoveryPlan:
        res = await self._request("GET", f"/api/recovery/{session_id}")
        return RecoveryPlan.model_validate(res)

    async def verify_session(
        self,
        session_id_or_trace: Union[str, List[Dict[str, Any]], List[TraceStep]],
        rules: Optional[List[Dict[str, Any]]] = None,
    ) -> VerificationResult:
        if isinstance(session_id_or_trace, str):
            payload = {"session_id": session_id_or_trace, "rules": rules or []}
        else:
            trace_payload = [
                step.to_dict() if hasattr(step, "to_dict") else step
                for step in session_id_or_trace
            ]
            payload = {"trace": trace_payload, "rules": rules or []}

        res = await self._request("POST", "/api/context/verify", data=payload)
        return VerificationResult.model_validate(res)


# Legacy Client Aliases for Backward Compatibility
ARCClient = ARC
AsyncARCClient = AsyncARC
