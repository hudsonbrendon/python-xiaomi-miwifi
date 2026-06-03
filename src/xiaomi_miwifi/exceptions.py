"""Exceptions for the MiWiFi client."""
from __future__ import annotations


class MiWiFiError(Exception):
    """Base error for all MiWiFi client failures."""


class MiWiFiConnectionError(MiWiFiError):
    """Raised when the router is unreachable or returns a transport error."""


class MiWiFiAuthError(MiWiFiError):
    """Raised when login fails or a token cannot be obtained/refreshed."""
