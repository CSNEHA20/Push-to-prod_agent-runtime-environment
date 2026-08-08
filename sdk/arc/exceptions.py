"""
ARC SDK — Custom Exceptions module.
"""


class ARCError(Exception):
    """Base exception class for all ARC SDK errors."""
    pass


class ARCClientError(ARCError):
    """Exception raised when an API client HTTP request fails."""
    pass


class ARCServerError(ARCError):
    """Exception raised when the ARC Backend server returns an internal error."""
    pass


class ARCVerificationError(ARCError):
    """Exception raised when Context Firewall or verification rule checks fail."""
    pass


class ARCRecoveryError(ARCError):
    """Exception raised when Recovery Engine checkpointing or rollback fails."""
    pass
