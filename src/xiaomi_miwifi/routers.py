"""Support table for Xiaomi / MiWiFi router hardware codes.

Start with the models present on the maintainer's network. Add new hardware
codes here as they are validated. The hardware code is the `platform` field
from `api/misystem/newstatus` (also `hardware` in topo_graph).
"""
from __future__ import annotations

# hardware code -> human-friendly marketing name
SUPPORTED_ROUTERS: dict[str, str] = {
    "RM1800": "Xiaomi Router AX1800",
    "RA82": "Xiaomi Router AX3000T",
}


def friendly_model(hardware: str | None) -> str:
    """Return the marketing name for a hardware code.

    Unknown codes fall back to ``Xiaomi Router (<CODE>)`` so the device still
    shows something meaningful in Home Assistant.
    """
    if not hardware:
        return "Xiaomi Router"
    key = hardware.strip().upper()
    if key in SUPPORTED_ROUTERS:
        return SUPPORTED_ROUTERS[key]
    return f"Xiaomi Router ({hardware})"
