"""Async client for Xiaomi / MiWiFi routers over the LuCI HTTP API."""
from __future__ import annotations

import hashlib
import json
import random
import re
import time
import urllib.parse
from typing import Any

import aiohttp

from .const import (
    DEFAULT_PORT,
    HTTP_TIMEOUT,
    HTTP_TIMEOUT_SLOW,
    PATH_AVAILABLE_CHANNELS,
    PATH_CHECK_ROM,
    PATH_DEVICELIST,
    PATH_INIT_INFO,
    PATH_LAN_INFO,
    PATH_LED,
    PATH_LOGIN,
    PATH_MAC_BIND,
    PATH_MAC_UNBIND,
    PATH_MACBIND_INFO,
    PATH_MACFILTER_INFO,
    PATH_NEWSTATUS,
    PATH_QOS_INFO,
    PATH_QOS_SWITCH,
    PATH_REBOOT,
    PATH_ROUTER_INFO,
    PATH_SET_MAC_FILTER,
    PATH_SET_WIFI,
    PATH_STATUS,
    PATH_TOPO_GRAPH,
    PATH_WAN_INFO,
    PATH_WAN_STATISTICS,
    PATH_WIFI_CONNECT_DEVICES,
    PATH_WIFI_DETAIL,
    PATH_WIFI_DOWN,
    PATH_WIFI_UP,
    WIFI_INDEX_5G,
    WIFI_INDEX_24G,
)
from .exceptions import MiWiFiAuthError, MiWiFiConnectionError, MiWiFiError
from .models import (
    ClientDevice,
    MiWiFiStatus,
    merge_client_telemetry,
    parse_status,
)

_KEY_RE = re.compile(r"key:\s*'([^']+)'")
_DEVICEID_RE = re.compile(r"deviceId\s*[=:]\s*'([^']+)'")

# Mutating LuCI paths that must not be reachable through the read-only passthrough.
_LUCI_BLOCKED_SUBSTRINGS = ("reboot", "set_", "upgrade", "_bind", "_unbind",
                            "wifi_up", "wifi_down", "mac_filter", "shutdown", "reset")


class MiWiFiClient:
    """Talks to one MiWiFi router (the gateway)."""

    def __init__(
        self,
        host: str,
        password: str,
        *,
        username: str = "admin",
        port: int = DEFAULT_PORT,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self._host = host
        self._password = password
        self._username = username
        self._port = port
        self._session = session
        self._owns_session = session is None
        self._token: str | None = None

    # -- properties -----------------------------------------------------
    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    @property
    def token(self) -> str | None:
        return self._token

    @property
    def _base(self) -> str:
        suffix = "" if self._port == 80 else f":{self._port}"
        return f"http://{self._host}{suffix}/cgi-bin/luci"

    # -- session --------------------------------------------------------
    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None:
            # No session was ever supplied: create and own one.
            self._session = aiohttp.ClientSession()
            self._owns_session = True
        elif self._session.closed:
            if not self._owns_session:
                raise MiWiFiConnectionError("provided session is closed")
            # We own a session that has been closed: recreate it.
            self._session = aiohttp.ClientSession()
        return self._session

    async def async_close(self) -> None:
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()

    # -- auth -----------------------------------------------------------
    def _make_nonce(self, device_id: str) -> str:
        return f"0_{device_id}_{int(time.time())}_{random.randint(0, 9999999)}"

    async def async_login(self) -> str:
        session = await self._ensure_session()
        timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT)
        try:
            async with session.get(f"{self._base}/web", timeout=timeout) as resp:
                page = await resp.text()
        except aiohttp.ClientError as err:
            raise MiWiFiConnectionError(f"cannot reach {self._host}: {err}") from err

        key_match = _KEY_RE.search(page)
        if not key_match:
            raise MiWiFiAuthError("login key not found on web page")
        key = key_match.group(1)
        device_match = _DEVICEID_RE.search(page)
        device_id = device_match.group(1) if device_match else "0"

        nonce = self._make_nonce(device_id)
        inner = hashlib.sha1((self._password + key).encode()).hexdigest()
        pwd_hash = hashlib.sha1((nonce + inner).encode()).hexdigest()

        form = {
            "username": self._username,
            "logtype": "2",
            "password": pwd_hash,
            "nonce": nonce,
        }
        try:
            async with session.post(
                f"{self._base}/{PATH_LOGIN}", data=form, timeout=timeout
            ) as resp:
                text = await resp.text()
        except aiohttp.ClientError as err:
            raise MiWiFiConnectionError(f"login transport error: {err}") from err

        try:
            payload = json.loads(text)
        except json.JSONDecodeError as err:
            raise MiWiFiConnectionError(f"bad JSON from login: {err}") from err

        token = payload.get("token") if isinstance(payload, dict) else None
        if not token:
            raise MiWiFiAuthError(f"login failed: {payload}")
        self._token = token
        return token

    # -- raw authenticated requests -------------------------------------
    async def _request(
        self,
        method: str,
        path: str,
        *,
        data: dict | None = None,
        timeout_s: int = HTTP_TIMEOUT,
        _retry: bool = True,
    ) -> dict[str, Any]:
        if self._token is None:
            await self.async_login()
        session = await self._ensure_session()
        timeout = aiohttp.ClientTimeout(total=timeout_s)
        url = f"{self._base}/;stok={self._token}/{path}"
        try:
            async with session.request(
                method, url, data=data, timeout=timeout
            ) as resp:
                text = await resp.text()
        except aiohttp.ClientError as err:
            raise MiWiFiConnectionError(f"request to {path} failed: {err}") from err

        try:
            payload = json.loads(text)
        except json.JSONDecodeError as err:
            raise MiWiFiConnectionError(f"bad JSON from {path}: {err}") from err

        if isinstance(payload, dict) and payload.get("code") == 401 and _retry:
            self._token = None
            await self.async_login()
            return await self._request(
                method, path, data=data, timeout_s=timeout_s, _retry=False
            )
        return payload

    async def _get(self, path: str, *, timeout_s: int = HTTP_TIMEOUT) -> dict[str, Any]:
        return await self._request("GET", path, timeout_s=timeout_s)

    async def _safe_get(self, path: str) -> dict:
        """GET returning {} on connection error (for optional endpoints)."""
        try:
            return await self._get(path)
        except MiWiFiConnectionError:
            return {}

    async def _post(self, path: str, data: dict) -> dict[str, Any]:
        return await self._request("POST", path, data=data)

    # -- read endpoints -------------------------------------------------
    async def async_get_newstatus(self) -> dict:
        return await self._get(PATH_NEWSTATUS)

    async def async_get_wan_info(self) -> dict:
        return await self._get(PATH_WAN_INFO)

    async def async_get_raw_status(self) -> dict:
        return await self._get(PATH_STATUS)

    async def async_get_topology(self) -> dict:
        return await self._get(PATH_TOPO_GRAPH)

    async def async_get_rom_update(self) -> dict:
        return await self._get(PATH_CHECK_ROM)

    async def async_get_wan_statistics(self) -> dict:
        return await self._get(PATH_WAN_STATISTICS)

    async def async_get_wifi_detail(self) -> dict:
        return await self._get(PATH_WIFI_DETAIL)

    async def async_get_macfilter(self) -> dict:
        """Read the MAC filter list. Slow endpoint — uses a longer timeout."""
        return await self._get(PATH_MACFILTER_INFO, timeout_s=HTTP_TIMEOUT_SLOW)

    async def async_get_led(self) -> dict:
        return await self._get(PATH_LED)

    async def async_get_router_info(self) -> dict:
        return await self._get(PATH_ROUTER_INFO)

    async def async_get_wifi_connect_devices(self) -> dict:
        return await self._get(PATH_WIFI_CONNECT_DEVICES)

    async def async_get_lan_info(self) -> dict:
        return await self._get(PATH_LAN_INFO)

    async def async_get_available_channels(self, wifi_index: int) -> list[str]:
        """Return the list of channel numbers (as strings; "0" = auto)
        available for a band. wifi_index: 1 = 2.4G, 2 = 5G.
        """
        data = await self._get(f"{PATH_AVAILABLE_CHANNELS}?wifiIndex={wifi_index}")
        items = data.get("list", []) if isinstance(data, dict) else []
        return [str(i.get("c")) for i in items if isinstance(i, dict) and "c" in i]

    async def async_get_init_info(self) -> dict:
        return await self._get(PATH_INIT_INFO)

    async def async_get_qos_info(self) -> dict:
        return await self._get(PATH_QOS_INFO)

    async def async_luci_request(self, path: str) -> dict:
        """Generic READ-ONLY GET passthrough to any LuCI API path.

        ``path`` is the API path WITHOUT the leading ``;stok=`` prefix,
        e.g. ``"api/misystem/router_info"``. Strips a leading slash.

        Mutating paths (reboot, set_*, upgrade, bind/unbind, etc.) are
        rejected so this cannot change router state.
        """
        clean = path.lstrip("/")
        lowered = clean.lower()
        if any(b in lowered for b in _LUCI_BLOCKED_SUBSTRINGS):
            raise MiWiFiError(f"refusing mutating path via read-only request: {path}")
        return await self._get(clean)

    async def async_get_status(self) -> MiWiFiStatus:
        """Aggregate all read endpoints into a MiWiFiStatus.

        The three secondary endpoints (wan_statistics, wifi_detail, led) are
        fetched best-effort: a MiWiFiConnectionError on any one of them yields
        an empty dict rather than failing the whole status.
        """
        newstatus = await self.async_get_newstatus()
        wan = await self.async_get_wan_info()
        status = await self.async_get_raw_status()
        topo = await self.async_get_topology()
        rom = await self.async_get_rom_update()

        wan_stats = await self._safe_get(PATH_WAN_STATISTICS)
        wifi_detail = await self._safe_get(PATH_WIFI_DETAIL)
        led = await self._safe_get(PATH_LED)
        router_info = await self._safe_get(PATH_ROUTER_INFO)
        lan_info = await self._safe_get(PATH_LAN_INFO)
        init_info = await self._safe_get(PATH_INIT_INFO)
        qos_info = await self._safe_get(PATH_QOS_INFO)

        return parse_status(
            newstatus=newstatus,
            wan=wan,
            status=status,
            topo=topo,
            rom=rom,
            wan_stats=wan_stats,
            wifi_detail=wifi_detail,
            led=led,
            router_info=router_info,
            lan_info=lan_info,
            init_info=init_info,
            qos_info=qos_info,
        )

    async def async_get_blocked_devices(self) -> list[dict]:
        data = await self.async_get_macfilter()
        return data.get("flist", []) if isinstance(data, dict) else []

    async def async_get_clients(self) -> list[ClientDevice]:
        data = await self._get(PATH_DEVICELIST)
        entries = data.get("list", []) if isinstance(data, dict) else []
        clients = [ClientDevice.from_entry(e) for e in entries]
        status_devs: list = []
        connect_devs: list = []
        try:
            raw = await self._get(PATH_STATUS)
            status_devs = raw.get("dev", []) if isinstance(raw, dict) else []
        except MiWiFiConnectionError:
            pass
        try:
            cd = await self._get(PATH_WIFI_CONNECT_DEVICES)
            connect_devs = cd.get("list", []) if isinstance(cd, dict) else []
        except MiWiFiConnectionError:
            pass
        return merge_client_telemetry(clients, status_devs, connect_devs)

    async def async_get_dhcp_reservations(self) -> list[dict]:
        data = await self._get(PATH_MACBIND_INFO)
        return data.get("list", []) if isinstance(data, dict) else []

    # -- write controls -------------------------------------------------
    @staticmethod
    def _ok(payload: dict) -> bool:
        return isinstance(payload, dict) and payload.get("code") == 0

    async def async_reboot(self) -> bool:
        """Reboot the router. Disruptive — never call from tests."""
        return self._ok(await self._get(PATH_REBOOT))

    async def async_set_wifi_enabled(self, ifname: str, enabled: bool) -> bool:
        """Enable/disable a radio (wl0=5G, wl1=2.4G). Disruptive."""
        path = PATH_WIFI_UP if enabled else PATH_WIFI_DOWN
        return self._ok(await self._post(path, {"ifname": ifname}))

    async def async_add_dhcp_reservation(
        self, mac: str, ip: str, name: str
    ) -> bool:
        """Add/replace a DHCP reservation.

        The router uses replace semantics: the full list must be POSTed or
        existing reservations are wiped. We therefore read the current list,
        merge the new entry (replacing any with the same MAC), and POST all.
        """
        current = await self.async_get_dhcp_reservations()
        merged = [r for r in current if r.get("mac", "").upper() != mac.upper()]
        merged.append({"ip": ip, "mac": mac, "name": name})
        body = {"data": json.dumps(
            [
                {"ip": r["ip"], "mac": r["mac"], "name": r.get("name", "")}
                for r in merged
            ]
        )}
        return self._ok(await self._post(PATH_MAC_BIND, body))

    async def async_remove_dhcp_reservation(self, mac: str) -> bool:
        """Remove a single DHCP reservation by MAC."""
        return self._ok(await self._post(PATH_MAC_UNBIND, {"mac": mac}))

    async def async_block_device(self, mac: str) -> bool:
        """Block a device's internet access (set_mac_filter wan=0)."""
        return self._ok(
            await self._post(PATH_SET_MAC_FILTER, {"mac": mac, "wan": "0"})
        )

    async def async_unblock_device(self, mac: str) -> bool:
        """Restore a device's internet access (set_mac_filter wan=1)."""
        return self._ok(
            await self._post(PATH_SET_MAC_FILTER, {"mac": mac, "wan": "1"})
        )

    _IFNAME_FOR_INDEX = {WIFI_INDEX_24G: "wl1", WIFI_INDEX_5G: "wl0"}

    async def _radio_config(self, wifi_index: int) -> dict:
        """Return the current wifi_detail_all entry for a band, or raise."""
        detail = await self._get(PATH_WIFI_DETAIL)
        ifname = self._IFNAME_FOR_INDEX.get(wifi_index)
        info = detail.get("info", []) if isinstance(detail, dict) else []
        for radio in info:
            if isinstance(radio, dict) and radio.get("ifname") == ifname:
                return radio
        raise MiWiFiError(f"radio wifiIndex={wifi_index} not found")

    async def _set_wifi(self, wifi_index: int, overrides: dict) -> bool:
        """Read-modify-write set_wifi: resend the full current radio config
        with the given field(s) overridden. Disruptive (restarts the radio).
        """
        radio = await self._radio_config(wifi_index)
        chan_info = radio.get("channelInfo") or {}
        # Prefer the resolved operating channel (channelInfo) over the stored
        # "channel" field, which is "0" (auto) when the band is on auto-select.
        channel = chan_info.get("channel") or radio.get("channel") or "0"
        bandwidth = chan_info.get("bandwidth") or radio.get("bandwidth") or "0"
        params = {
            "wifiIndex": str(wifi_index),
            "on": "1",
            "ssid": radio.get("ssid", ""),
            "pwd": radio.get("password", ""),
            "encryption": radio.get("encryption", ""),
            "channel": str(channel),
            "bandwidth": str(bandwidth),
            "txpwr": radio.get("txpwr", "max"),
            "hidden": str(radio.get("hidden", "0")),
            "ax": str(radio.get("ax", "0")),
            "txbf": str(radio.get("txbf", "3")),
        }
        params.update(overrides)
        query = urllib.parse.urlencode(params)
        return self._ok(await self._get(f"{PATH_SET_WIFI}?{query}"))

    async def async_set_wifi_channel(self, wifi_index: int, channel: str) -> bool:
        """Set a band's channel (1=2.4G, 2=5G). "0" = auto. Disruptive."""
        return await self._set_wifi(wifi_index, {"channel": str(channel)})

    async def async_set_wifi_txpwr(self, wifi_index: int, txpwr: str) -> bool:
        """Set a band's transmit power (max/mid/min). Disruptive."""
        return await self._set_wifi(wifi_index, {"txpwr": txpwr})

    async def async_set_qos(self, enabled: bool) -> bool:
        """Enable/disable QoS."""
        on = 1 if enabled else 0
        return self._ok(await self._get(f"{PATH_QOS_SWITCH}?on={on}"))

    async def __aenter__(self) -> MiWiFiClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.async_close()
