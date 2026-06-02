"""Typed data models parsed from MiWiFi LuCI API responses."""
from __future__ import annotations

from dataclasses import dataclass, field

from .routers import friendly_model

_WIFI_INDEX_BAND = {1: "2.4G", 2: "5G", 3: "5G Game"}
_MODE_NAMES = {0: "Router", 1: "Repeater", 2: "Access Point", 9: "Mesh"}


def _to_int(value: object, default: int = 0) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


@dataclass
class MeshNode:
    """A node in the mesh topology (gateway or leaf)."""

    name: str
    ip: str
    hardware: str
    ssid: str
    mode: int
    online: bool = True

    @property
    def model(self) -> str:
        return friendly_model(self.hardware)

    @property
    def is_gateway(self) -> bool:
        return self.mode == 0

    @classmethod
    def from_entry(cls, entry: dict) -> MeshNode:
        return cls(
            name=entry.get("name", ""),
            ip=entry.get("ip", ""),
            hardware=entry.get("hardware", ""),
            ssid=entry.get("ssid", ""),
            mode=_to_int(entry.get("mode"), 0),
            online=True,
        )


@dataclass
class ClientDevice:
    """A LAN client as reported by api/misystem/devicelist."""

    name: str
    mac: str
    ip: str
    online: bool
    parent: str
    is_router: bool
    signal: int = 0
    band: str = ""
    download_speed: int = 0
    upload_speed: int = 0
    download_total: int = 0
    upload_total: int = 0

    @classmethod
    def from_entry(cls, entry: dict) -> ClientDevice:
        ips = entry.get("ip") or []
        ip = ips[0].get("ip", "") if ips and isinstance(ips[0], dict) else ""
        return cls(
            name=entry.get("name") or entry.get("oname") or entry.get("mac", ""),
            mac=entry.get("mac", ""),
            ip=ip,
            online=bool(_to_int(entry.get("online"))),
            parent=entry.get("parent", ""),
            is_router=_to_int(entry.get("isap")) != 0,
        )


def merge_client_telemetry(
    clients: list[ClientDevice],
    status_devs: list,
    connect_devs: list,
) -> list[ClientDevice]:
    """Merge per-device speed/traffic (misystem/status) and signal/band
    (wifi_connect_devices) into the ClientDevice list, matched by MAC
    (case-insensitive). Unmatched clients keep their zero defaults.
    """
    by_status = {
        d["mac"].upper(): d
        for d in status_devs
        if isinstance(d, dict) and d.get("mac")
    }
    by_signal = {
        d["mac"].upper(): d
        for d in connect_devs
        if isinstance(d, dict) and d.get("mac")
    }
    for client in clients:
        mac = client.mac.upper()
        st = by_status.get(mac)
        if st:
            client.download_speed = _to_int(st.get("downspeed"))
            client.upload_speed = _to_int(st.get("upspeed"))
            client.download_total = _to_int(st.get("download"))
            client.upload_total = _to_int(st.get("upload"))
        sig = by_signal.get(mac)
        if sig:
            client.signal = _to_int(sig.get("signal"))
            client.band = _WIFI_INDEX_BAND.get(_to_int(sig.get("wifiIndex")), "")
    return clients


@dataclass
class MiWiFiStatus:
    """Aggregated router status from several LuCI endpoints."""

    online: bool
    hardware: str = ""
    firmware_version: str = ""
    serial: str = ""
    mac: str = ""
    client_count: int = 0
    mesh_node_count: int = 0
    cap_count: int = 0
    clients_24g: int = 0
    clients_5g: int = 0
    ssid_24g: str = ""
    ssid_5g: str = ""
    wan_ip: str = ""
    wan_gateway: str = ""
    wan_type: str = ""
    wan_uptime: int = 0
    wan_link: bool = False
    upload_speed: int = 0
    download_speed: int = 0
    update_available: bool = False
    wan_download_total: int = 0
    wan_upload_total: int = 0
    wan_max_download: int = 0
    wan_max_upload: int = 0
    led_on: bool = False
    channel_24g: int = 0
    channel_5g: int = 0
    encryption_24g: str = ""
    encryption_5g: str = ""
    txpwr_24g: str = ""
    txpwr_5g: str = ""
    country_code: str = ""
    qos_on: bool = False
    rom_changelog: str = ""
    rom_latest_version: str = ""
    mesh_nodes: list[MeshNode] = field(default_factory=list)
    mode: int = 0
    lan_ports: list[bool] = field(default_factory=list)

    @property
    def model(self) -> str:
        return friendly_model(self.hardware)

    @property
    def mode_name(self) -> str:
        return _MODE_NAMES.get(self.mode, f"Mode {self.mode}")

    @property
    def lan_ports_active(self) -> int:
        return sum(1 for up in self.lan_ports if up)


def parse_status(
    *,
    newstatus: dict,
    wan: dict,
    status: dict,
    topo: dict,
    rom: dict,
    wan_stats: dict | None = None,
    wifi_detail: dict | None = None,
    led: dict | None = None,
    router_info: dict | None = None,
    lan_info: dict | None = None,
    init_info=None,
    qos_info=None,
) -> MiWiFiStatus:
    """Combine the read endpoints into one MiWiFiStatus.

    Note: mesh_nodes contains leaf nodes only; the gateway's own data lives on
    the top-level MiWiFiStatus fields.
    """
    newstatus = newstatus if isinstance(newstatus, dict) else {}
    wan = wan if isinstance(wan, dict) else {}
    status = status if isinstance(status, dict) else {}
    topo = topo if isinstance(topo, dict) else {}
    rom = rom if isinstance(rom, dict) else {}
    wan_stats = wan_stats if isinstance(wan_stats, dict) else {}
    wifi_detail = wifi_detail if isinstance(wifi_detail, dict) else {}
    led = led if isinstance(led, dict) else {}
    router_info = router_info if isinstance(router_info, dict) else {}
    lan_info = lan_info if isinstance(lan_info, dict) else {}
    init_info = init_info if isinstance(init_info, dict) else {}
    qos_info = qos_info if isinstance(qos_info, dict) else {}

    hw = newstatus.get("hardware", {})
    band24 = newstatus.get("2g", {})
    band5 = newstatus.get("5g", {})

    wan_info = wan.get("info", {}) if isinstance(wan.get("info"), dict) else {}
    ipv4 = wan_info.get("ipv4") or []
    wan_ip = ipv4[0].get("ip", "") if ipv4 and isinstance(ipv4[0], dict) else ""

    devs = status.get("dev", [])
    up = sum(_to_int(d.get("upspeed")) for d in devs if isinstance(d, dict))
    down = sum(_to_int(d.get("downspeed")) for d in devs if isinstance(d, dict))

    # WAN statistics: cumulative totals + live speeds (preferred over dev[] sum).
    wstats = (
        wan_stats.get("statistics", {})
        if isinstance(wan_stats.get("statistics"), dict)
        else {}
    )
    if wan_stats:
        up = _to_int(wan_stats.get("upspeed"))
        down = _to_int(wan_stats.get("downspeed"))

    # Per-radio WiFi detail matched by ifname (wl1=2.4G, wl0=5G).
    raw_info = wifi_detail.get("info")
    info = raw_info if isinstance(raw_info, list) else []
    chan24 = chan5 = 0
    enc24 = enc5 = ""
    txpwr_24g = txpwr_5g = ""
    for radio in info:
        if not isinstance(radio, dict):
            continue
        raw_ci = radio.get("channelInfo")
        ci = raw_ci if isinstance(raw_ci, dict) else {}
        channel = _to_int(ci.get("channel", radio.get("channel")))
        encryption = radio.get("encryption", "")
        txpwr = radio.get("txpwr", "")
        if radio.get("ifname") == "wl1":
            chan24, enc24, txpwr_24g = channel, encryption, txpwr
        elif radio.get("ifname") == "wl0":
            chan5, enc5, txpwr_5g = channel, encryption, txpwr

    graph = topo.get("graph", {}) if isinstance(topo.get("graph"), dict) else {}
    leafs = graph.get("leafs", []) if isinstance(graph.get("leafs"), list) else []
    nodes = [MeshNode.from_entry(leaf) for leaf in leafs if isinstance(leaf, dict)]

    link_list = lan_info.get("linkList")
    lan_ports = (
        [bool(_to_int(x)) for x in link_list]
        if isinstance(link_list, list)
        else []
    )

    return MiWiFiStatus(
        online=True,
        hardware=hw.get("platform", ""),
        firmware_version=hw.get("version", ""),
        serial=hw.get("sn", ""),
        mac=hw.get("mac", ""),
        client_count=_to_int(newstatus.get("count")),
        mesh_node_count=_to_int(newstatus.get("re_count")),
        cap_count=_to_int(newstatus.get("cap_count")),
        clients_24g=_to_int(band24.get("online_sta_count")),
        clients_5g=_to_int(band5.get("online_sta_count")),
        ssid_24g=band24.get("ssid", ""),
        ssid_5g=band5.get("ssid", ""),
        wan_ip=wan_ip,
        wan_gateway=wan_info.get("gateWay", ""),
        wan_type=(wan_info.get("details", {}) or {}).get("wanType", ""),
        wan_uptime=_to_int(wan_info.get("uptime")),
        wan_link=bool(_to_int(wan_info.get("link"))),
        upload_speed=up,
        download_speed=down,
        update_available=bool(_to_int(rom.get("needUpdate"))),
        wan_download_total=_to_int(wstats.get("download")),
        wan_upload_total=_to_int(wstats.get("upload")),
        wan_max_download=_to_int(wstats.get("maxdownloadspeed")),
        wan_max_upload=_to_int(wstats.get("maxuploadspeed")),
        led_on=_to_int(led.get("status")) == 1,
        channel_24g=chan24,
        channel_5g=chan5,
        encryption_24g=enc24,
        encryption_5g=enc5,
        txpwr_24g=txpwr_24g,
        txpwr_5g=txpwr_5g,
        country_code=init_info.get("countrycode", ""),
        qos_on=bool(_to_int((qos_info.get("status") or {}).get("on"))),
        rom_changelog=rom.get("changeLog", ""),
        rom_latest_version=rom.get("version", ""),
        mesh_nodes=nodes,
        mode=_to_int(router_info.get("mode")),
        lan_ports=lan_ports,
    )
