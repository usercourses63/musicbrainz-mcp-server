"""
Custom exceptions for MusicBrainz MCP Server.

This module defines custom exception classes for handling various error
conditions that can occur when interacting with the MusicBrainz API.
"""

from typing import Optional


class MusicBrainzError(Exception):
    """Base exception for all MusicBrainz-related errors."""

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class MusicBrainzAPIError(MusicBrainzError):
    """Exception raised when the MusicBrainz API returns an error response."""

    def __init__(
        self,
        message: str,
        status_code: int,
        response_text: Optional[str] = None,
    ) -> None:
        super().__init__(message, status_code)
        self.response_text = response_text

    def __str__(self) -> str:
        base_msg = f"MusicBrainz API Error {self.status_code}: {self.message}"
        if self.response_text:
            base_msg += f"\nResponse: {self.response_text}"
        return base_msg


class MusicBrainzRateLimitError(MusicBrainzAPIError):
    """Exception raised when rate limit is exceeded (HTTP 503)."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None) -> None:
        super().__init__(message, 503)
        self.retry_after = retry_after

    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.retry_after:
            base_msg += f"\nRetry after: {self.retry_after} seconds"
        return base_msg


class MusicBrainzTimeoutError(MusicBrainzError):
    """Exception raised when a request times out."""

    def __init__(self, message: str = "Request timed out") -> None:
        super().__init__(message)


class MusicBrainzConnectionError(MusicBrainzError):
    """Exception raised when there's a connection error."""

    def __init__(self, message: str = "Connection error") -> None:
        super().__init__(message)


class MusicBrainzValidationError(MusicBrainzError):
    """Exception raised when input validation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class MusicBrainzNotFoundError(MusicBrainzAPIError):
    """Exception raised when a resource is not found (HTTP 404)."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, 404)


class MusicBrainzBadRequestError(MusicBrainzAPIError):
    """Exception raised when the request is malformed (HTTP 400)."""

    def __init__(self, message: str = "Bad request") -> None:
        super().__init__(message, 400)
