# python-xiaomi-miwifi

[![Tests](https://github.com/hudsonbrendon/python-xiaomi-miwifi/actions/workflows/tests.yml/badge.svg)](https://github.com/hudsonbrendon/python-xiaomi-miwifi/actions/workflows/tests.yml)
[![PyPI version](https://img.shields.io/pypi/v/python-xiaomi-miwifi.svg)](https://pypi.org/project/python-xiaomi-miwifi/)
[![Python](https://img.shields.io/pypi/pyversions/python-xiaomi-miwifi.svg)](https://pypi.org/project/python-xiaomi-miwifi/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Async Python client for **Xiaomi / MiWiFi routers** over their LuCI HTTP API. Built to power the [`ha-xiaomi-miwifi`](https://github.com/hudsonbrendon/ha-xiaomi-miwifi) Home Assistant integration.

## Features

- 🔐 Token login with the MiWiFi `sha1(nonce + sha1(password + key))` signing scheme
- 📊 Aggregated status: WAN, throughput, client counts per band, firmware, mesh topology
- 🕸️ Mesh-aware: enumerates gateway + leaf nodes
- 🛠️ Controls: reboot, per-radio enable/disable, DHCP reservation add/remove
- ⚡ Fully async (`aiohttp`), typed (`py.typed`), zero-config session management

## Installation

```bash
pip install python-xiaomi-miwifi
```

## Quickstart

```python
import asyncio
from xiaomi_miwifi import MiWiFiClient


async def main() -> None:
    async with MiWiFiClient("192.168.31.1", password="your-password") as client:
        status = await client.async_get_status()
        print(status.model, status.client_count, status.wan_ip)
        for node in status.mesh_nodes:
            print("mesh:", node.name, node.model, node.ip)


asyncio.run(main())
```

## Supported routers

| Hardware code | Model |
|---------------|-------|
| `RM1800` | Xiaomi Router AX1800 |
| `RA82` | Xiaomi Router AX3000T |

> Have a different Xiaomi router? Open an issue with the output of `api/misystem/newstatus` and we'll add it.

## API overview

| Method | Description |
|--------|-------------|
| `async_login()` | Authenticate and cache the token |
| `async_get_status()` | Aggregated `MiWiFiStatus` |
| `async_get_clients()` | List of `ClientDevice` |
| `async_get_dhcp_reservations()` | Current MAC→IP reservations |
| `async_add_dhcp_reservation(mac, ip, name)` | Add/replace a reservation |
| `async_remove_dhcp_reservation(mac)` | Remove a reservation |
| `async_set_wifi_enabled(ifname, enabled)` | Toggle a radio (`wl0`=5G, `wl1`=2.4G) |
| `async_reboot()` | Reboot the router |

## Development

```bash
uv venv && uv pip install -e ".[test]"
pytest
ruff check .
```

## License

MIT © Hudson Brendon
