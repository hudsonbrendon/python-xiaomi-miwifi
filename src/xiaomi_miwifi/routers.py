"""Support table for Xiaomi / MiWiFi router hardware codes.

Start with the models present on the maintainer's network. Add new hardware
codes here as they are validated. The hardware code is the `platform` field
from `api/misystem/newstatus` (also `hardware` in topo_graph).
"""
from __future__ import annotations

# hardware code -> human-friendly marketing name
SUPPORTED_ROUTERS: dict[str, str] = {
    "R1D": "Xiaomi Mi Router R1D",
    "R2D": "Xiaomi Mi Router R2D",
    "R3": "Xiaomi Mi Router 3",
    "R3G": "Xiaomi Mi Router 3G",
    "R3P": "Xiaomi Mi Router 3 Pro",
    "R3D": "Xiaomi Mi Router HD",
    "R3L": "Xiaomi Mi Router 3C",
    "R3A": "Xiaomi Mi Router 3A",
    "R4": "Xiaomi Mi Router 4",
    "R4C": "Xiaomi Mi Router 4C",
    "R4CM": "Xiaomi Mi Router 4C",
    "R4A": "Xiaomi Mi Router 4A",
    "R4AC": "Xiaomi Mi Router 4A",
    "R4AV2": "Xiaomi Mi Router 4A v2",
    "D01": "Xiaomi Mi Router Mesh",
    "R2100": "Xiaomi Mi Router AC2100",
    "RM2100": "Redmi Router AC2100",
    "R3600": "Xiaomi AIoT Router AX3600",
    "RM1800": "Xiaomi Router AX1800",
    "RA67": "Redmi Router AX5",
    "R2350": "Xiaomi Mi AIoT Router AC2350",
    "R1350": "Xiaomi Mi Router 4 Pro",
    "RA69": "Redmi Router AX6",
    "RA72": "Xiaomi Router AX6000",
    "RA50": "Redmi Router AX5400",
    "RA70": "Xiaomi Router AX9000",
    "CR6606": "Xiaomi Router CR6606",
    "RA81": "Redmi Router AX3000",
    "RA80": "Xiaomi Router AX3000",
    "RB03": "Redmi Router AX6000",
    "RA71": "Redmi Router AX1800",
    "RB01": "Xiaomi Router BE7000",
    "RA82": "Xiaomi Router AX3000T",
    "CR8808": "Xiaomi Router CR8808",
    "RB02": "Redmi Router BE5000",
    "RB04": "Xiaomi Router BE3600",
    "RA74": "Xiaomi Mesh System AX3000",
    "RB06": "Xiaomi Router AX3000T",
    "RB08": "Xiaomi Router BE3600 2.5G",
    "CB0401": "Xiaomi 5G CPE Pro",
    "RC06": "Redmi Router AX6000",
    "RD03": "Xiaomi Router AX3000T NE",
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
