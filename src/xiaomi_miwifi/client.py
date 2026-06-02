"""Async client for Xiaomi / MiWiFi routers over the LuCI HTTP API."""
from __future__ import annotations

import hashlib
import json
import random
import re
import time
from typing import Any

import aiohttp

from .const import (
    DEFAULT_PORT,
    HTTP_TIMEOUT,
    PATH_CHECK_ROM,
    PATH_DEVICELIST,
    PATH_LOGIN,
    PATH_MAC_BIND,
    PATH_MAC_UNBIND,
    PATH_MACBIND_INFO,
    PATH_NEWSTATUS,
    PATH_REBOOT,
    PATH_STATUS,
    PATH_TOPO_GRAPH,
    PATH_WAN_INFO,
    PATH_WIFI_DOWN,
    PATH_WIFI_UP,
)
from .exceptions import MiWiFiAuthError, MiWiFiConnectionError
from .models import ClientDevice, MiWiFiStatus, parse_status

_KEY_RE = re.compile(r"key:\s*'([^']+)'")
_DEVICEID_RE = re.compile(r"deviceId\s*[=:]\s*'([^']+)'")


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
        self, method: str, path: str, *, data: dict | None = None, _retry: bool = True
    ) -> dict[str, Any]:
        if self._token is None:
            await self.async_login()
        session = await self._ensure_session()
        timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT)
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
            return await self._request(method, path, data=data, _retry=False)
        return payload

    async def _get(self, path: str) -> dict[str, Any]:
        return await self._request("GET", path)

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

    async def async_get_status(self) -> MiWiFiStatus:
        """Aggregate all read endpoints into a MiWiFiStatus."""
        newstatus = await self.async_get_newstatus()
        wan = await self.async_get_wan_info()
        status = await self.async_get_raw_status()
        topo = await self.async_get_topology()
        rom = await self.async_get_rom_update()
        return parse_status(
            newstatus=newstatus, wan=wan, status=status, topo=topo, rom=rom
        )

    async def async_get_clients(self) -> list[ClientDevice]:
        data = await self._get(PATH_DEVICELIST)
        entries = data.get("list", []) if isinstance(data, dict) else []
        return [ClientDevice.from_entry(e) for e in entries]

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

    async def __aenter__(self) -> MiWiFiClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.async_close()
