"""
ARC SDK - Custom Exception Hierarchy.
Provides structured, actionable exceptions for network, authentication, API, verification, and recovery failures.
"""

from typing import Optional, Any, Dict


class ARCError(Exception):
    """Base exception class for all ARC SDK errors."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class APIError(ARCError):
    """Exception raised when an HTTP API request returns an error status code."""
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[Any] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body

    def __str__(self) -> str:
        if self.status_code:
            return f"APIError ({self.status_code}): {self.message}"
        return f"APIError: {self.message}"


class APIConnectionError(ARCError):
    """Exception raised when network connection to the ARC server fails or times out."""
    def __init__(self, message: str, cause: Optional[BaseException] = None):
        super().__init__(message)
        self.cause = cause
        if cause:
            self.__cause__ = cause


class AuthenticationError(APIError):
    """Exception raised when API authentication fails (401 Unauthorized / 403 Forbidden)."""
    pass


class NotFoundError(APIError):
    """Exception raised when a requested resource (session, trace, checkpoint) is not found (404)."""
    pass


class ServerError(APIError):
    """Exception raised when the ARC Backend server returns a 5xx server error."""
    pass


class ARCClientError(APIError):
    """Legacy alias for APIError for backward compatibility."""
    pass


class ARCServerError(ServerError):
    """Legacy alias for ServerError for backward compatibility."""
    pass


class ARCVerificationError(ARCError):
    """Exception raised when Context Firewall or verification rule checks fail."""
    def __init__(self, message: str, conflicts: Optional[list] = None):
        super().__init__(message)
        self.conflicts = conflicts or []


class ARCRecoveryError(ARCError):
    """Exception raised when Recovery Engine checkpointing or rollback fails."""
    pass
