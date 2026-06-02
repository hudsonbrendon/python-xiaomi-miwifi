"""Async Python client for Xiaomi / MiWiFi routers over the LuCI HTTP API."""
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
    "MiWiFiClient",
    "MiWiFiStatus",
    "ClientDevice",
    "MeshNode",
    "parse_status",
    "merge_client_telemetry",
    "MiWiFiError",
    "MiWiFiConnectionError",
    "MiWiFiAuthError",
    "SUPPORTED_ROUTERS",
    "friendly_model",
    "TXPWR_OPTIONS",
    "WIFI_INDEX_24G",
    "WIFI_INDEX_5G",
]
__version__ = "0.6.0"
