"""Async Python client for Xiaomi / MiWiFi routers over the LuCI HTTP API."""

from importlib import metadata

from .client import MiWiFiClient
from .const import TXPWR_OPTIONS, WIFI_INDEX_5G, WIFI_INDEX_24G
from .exceptions import MiWiFiAuthError, MiWiFiConnectionError, MiWiFiError
from .models import (
    ClientDevice,
    MeshNode,
    MiWiFiStatus,
    merge_client_telemetry,
    parse_status,
)
from .routers import SUPPORTED_ROUTERS, friendly_model

__all__ = [
    "SUPPORTED_ROUTERS",
    "TXPWR_OPTIONS",
    "WIFI_INDEX_5G",
    "WIFI_INDEX_24G",
    "ClientDevice",
    "MeshNode",
    "MiWiFiAuthError",
    "MiWiFiClient",
    "MiWiFiConnectionError",
    "MiWiFiError",
    "MiWiFiStatus",
    "friendly_model",
    "merge_client_telemetry",
    "parse_status",
]
try:
    __version__ = metadata.version("python-xiaomi-miwifi")
except metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"
