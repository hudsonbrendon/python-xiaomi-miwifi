import json
import re

import aiohttp
import pytest
from aioresponses import aioresponses

from xiaomi_miwifi import const
from xiaomi_miwifi.client import MiWiFiClient
from xiaomi_miwifi.exceptions import (
    MiWiFiAuthError,
    MiWiFiConnectionError,
    MiWiFiError,
)


def test_exception_hierarchy():
    assert issubclass(MiWiFiConnectionError, MiWiFiError)
    assert issubclass(MiWiFiAuthError, MiWiFiError)


def test_const_paths_present():
    assert const.DEFAULT_PORT == 80
    assert const.PATH_LOGIN == "api/xqsystem/login"
    assert const.PATH_NEWSTATUS == "api/misystem/newstatus"
    assert const.PATH_WAN_INFO == "api/xqnetwork/wan_info"
    assert const.PATH_TOPO_GRAPH == "api/misystem/topo_graph"
    assert const.PATH_CHECK_ROM == "api/xqsystem/check_rom_update"
    assert const.PATH_MACBIND_INFO == "api/xqnetwork/macbind_info"
    assert const.PATH_MAC_BIND == "api/xqnetwork/mac_bind"
    assert const.PATH_MAC_UNBIND == "api/xqnetwork/mac_unbind"
    assert const.PATH_REBOOT == "api/xqsystem/reboot"
    assert const.PATH_WAN_STATISTICS == "api/xqnetwork/wan_statistics"
    assert const.PATH_WIFI_DETAIL == "api/xqnetwork/wifi_detail_all"
    assert const.PATH_MACFILTER_INFO == "api/xqnetwork/wifi_macfilter_info"
    assert const.PATH_LED == "api/misystem/led"
    assert const.PATH_ROUTER_INFO == "api/misystem/router_info"
    assert const.PATH_SET_MAC_FILTER == "api/xqnetwork/set_mac_filter"
    assert const.PATH_WIFI_CONNECT_DEVICES == "api/xqnetwork/wifi_connect_devices"
    assert const.PATH_LAN_INFO == "api/xqnetwork/lan_info"
    assert const.PATH_AVAILABLE_CHANNELS == "api/xqnetwork/avaliable_channels"
    assert const.PATH_SET_WIFI == "api/xqnetwork/set_wifi"
    assert const.PATH_QOS_INFO == "api/misystem/qos_info"
    assert const.PATH_QOS_SWITCH == "api/misystem/qos_switch"
    assert const.PATH_INIT_INFO == "api/xqsystem/init_info"
    assert const.WIFI_INDEX_24G == 1
    assert const.WIFI_INDEX_5G == 2
    assert const.TXPWR_OPTIONS == ("max", "mid", "min")


async def test_login_parses_key_and_sets_token(host, base):
    from tests.conftest import LOGIN_HTML, LOGIN_OK

    client = MiWiFiClient(host, password="foco2021")
    with aioresponses() as m:
        m.get(f"{base}/web", body=LOGIN_HTML)
        m.post(re.compile(rf"{re.escape(base)}/api/xqsystem/login.*"), payload=LOGIN_OK)
        token = await client.async_login()
    assert token == "TESTTOKEN"
    assert client.token == "TESTTOKEN"
    await client.async_close()


async def test_login_failure_raises_auth_error(host, base):
    from tests.conftest import LOGIN_HTML

    client = MiWiFiClient(host, password="wrong")
    with aioresponses() as m:
        m.get(f"{base}/web", body=LOGIN_HTML)
        m.post(re.compile(rf"{re.escape(base)}/api/xqsystem/login.*"),
               payload={"code": 401})
        with pytest.raises(MiWiFiAuthError):
            await client.async_login()
    await client.async_close()


async def test_get_status_aggregates_live_endpoints(host, base):
    from tests import conftest as c

    client = MiWiFiClient(host, password="foco2021")
    with aioresponses() as m:
        m.get(f"{base}/web", body=c.LOGIN_HTML)
        m.post(
            re.compile(rf"{re.escape(base)}/api/xqsystem/login.*"),
            payload=c.LOGIN_OK,
        )
        tok = "TESTTOKEN"
        m.get(f"{base}/;stok={tok}/api/misystem/newstatus", payload=c.NEWSTATUS)
        m.get(f"{base}/;stok={tok}/api/xqnetwork/wan_info", payload=c.WAN)
        m.get(f"{base}/;stok={tok}/api/misystem/status", payload=c.STATUS)
        m.get(f"{base}/;stok={tok}/api/misystem/topo_graph", payload=c.TOPO)
        m.get(f"{base}/;stok={tok}/api/xqsystem/check_rom_update", payload=c.ROM)
        m.get(
            f"{base}/;stok={tok}/api/xqnetwork/wan_statistics",
            payload=c.WAN_STATS,
        )
        m.get(
            f"{base}/;stok={tok}/api/xqnetwork/wifi_detail_all",
            payload=c.WIFI_DETAIL,
        )
        m.get(f"{base}/;stok={tok}/api/misystem/led", payload=c.LED)
        status = await client.async_get_status()
    assert status.online is True
    assert status.client_count == 90
    # wan_statistics live speed preferred over the dev[] sum (225).
    assert status.download_speed == 400
    assert status.wan_download_total == 123456789
    assert status.channel_24g == 6
    assert status.channel_5g == 36
    assert status.led_on is True
    assert status.mesh_node_count == 2
    assert status.model == "Xiaomi Router AX1800"
    await client.async_close()


async def test_get_status_tolerates_secondary_endpoint_failure(host, base):
    """A failing secondary endpoint (led) must not break the whole status."""
    from tests import conftest as c

    client = MiWiFiClient(host, password="foco2021")
    with aioresponses() as m:
        m.get(f"{base}/web", body=c.LOGIN_HTML)
        m.post(
            re.compile(rf"{re.escape(base)}/api/xqsystem/login.*"),
            payload=c.LOGIN_OK,
        )
        tok = "TESTTOKEN"
        m.get(f"{base}/;stok={tok}/api/misystem/newstatus", payload=c.NEWSTATUS)
        m.get(f"{base}/;stok={tok}/api/xqnetwork/wan_info", payload=c.WAN)
        m.get(f"{base}/;stok={tok}/api/misystem/status", payload=c.STATUS)
        m.get(f"{base}/;stok={tok}/api/misystem/topo_graph", payload=c.TOPO)
        m.get(f"{base}/;stok={tok}/api/xqsystem/check_rom_update", payload=c.ROM)
        m.get(
            f"{base}/;stok={tok}/api/xqnetwork/wan_statistics",
            payload=c.WAN_STATS,
        )
        m.get(
            f"{base}/;stok={tok}/api/xqnetwork/wifi_detail_all",
            payload=c.WIFI_DETAIL,
        )
        # led returns non-JSON -> MiWiFiConnectionError -> treated as {}.
        m.get(f"{base}/;stok={tok}/api/misystem/led", body="<html>oops</html>")
        status = await client.async_get_status()
    assert status.online is True
    assert status.led_on is False  # secondary failure -> default
    assert status.channel_24g == 6  # other endpoints still parsed
    await client.async_close()


async def test_get_wan_statistics(host, base):
    from tests import conftest as c

    client = MiWiFiClient(host, password="foco2021")
    with aioresponses() as m:
        m.get(f"{base}/web", body=c.LOGIN_HTML)
        m.post(
            re.compile(rf"{re.escape(base)}/api/xqsystem/login.*"),
            payload=c.LOGIN_OK,
        )
        m.get(
            f"{base}/;stok=TESTTOKEN/api/xqnetwork/wan_statistics",
            payload=c.WAN_STATS,
        )
        data = await client.async_get_wan_statistics()
    assert data["statistics"]["download"] == "123456789"
    await client.async_close()


async def test_get_wifi_detail(host, base):
    from tests import conftest as c

    client = MiWiFiClient(host, password="foco2021")
    with aioresponses() as m:
        m.get(f"{base}/web", body=c.LOGIN_HTML)
        m.post(
            re.compile(rf"{re.escape(base)}/api/xqsystem/login.*"),
            payload=c.LOGIN_OK,
        )
        m.get(
            f"{base}/;stok=TESTTOKEN/api/xqnetwork/wifi_detail_all",
            payload=c.WIFI_DETAIL,
        )
        data = await client.async_get_wifi_detail()
    assert len(data["info"]) == 2
    await client.async_close()


async def test_get_led(host, base):
    from tests import conftest as c

    client = MiWiFiClient(host, password="foco2021")
    with aioresponses() as m:
        m.get(f"{base}/web", body=c.LOGIN_HTML)
        m.post(
            re.compile(rf"{re.escape(base)}/api/xqsystem/login.*"),
            payload=c.LOGIN_OK,
        )
        m.get(f"{base}/;stok=TESTTOKEN/api/misystem/led", payload=c.LED)
        data = await client.async_get_led()
    assert data["status"] == 1
    await client.async_close()


async def test_get_router_info(host, base):
    from tests import conftest as c

    client = MiWiFiClient(host, password="foco2021")
    with aioresponses() as m:
        m.get(f"{base}/web", body=c.LOGIN_HTML)
        m.post(
            re.compile(rf"{re.escape(base)}/api/xqsystem/login.*"),
            payload=c.LOGIN_OK,
        )
        m.get(
            f"{base}/;stok=TESTTOKEN/api/misystem/router_info",
            payload={"code": 0, "name": "Xiaomi", "mac": "AA"},
        )
        data = await client.async_get_router_info()
    assert data["name"] == "Xiaomi"
    await client.async_close()


async def test_get_blocked_devices(host, base):
    from tests import conftest as c

    client = MiWiFiClient(host, password="foco2021")
    with aioresponses() as m:
        m.get(f"{base}/web", body=c.LOGIN_HTML)
        m.post(
            re.compile(rf"{re.escape(base)}/api/xqsystem/login.*"),
            payload=c.LOGIN_OK,
        )
        m.get(
            f"{base}/;stok=TESTTOKEN/api/xqnetwork/wifi_macfilter_info",
            payload=c.MACFILTER,
        )
        blocked = await client.async_get_blocked_devices()
    assert blocked == [{"mac": "AA:BB:CC:DD:EE:FF", "name": "blocked-dev"}]
    await client.async_close()


async def test_block_device_posts_wan_zero(host, base):
    from tests import conftest as c

    captured: dict = {}

    def _capture(url, **kwargs):
        captured["data"] = kwargs.get("data")

    client = MiWiFiClient(host, password="foco2021")
    with aioresponses() as m:
        m.get(f"{base}/web", body=c.LOGIN_HTML)
        m.post(
            re.compile(rf"{re.escape(base)}/api/xqsystem/login.*"),
            payload=c.LOGIN_OK,
        )
        m.post(
            f"{base}/;stok=TESTTOKEN/api/xqnetwork/set_mac_filter",
            payload={"code": 0},
            callback=_capture,
        )
        ok = await client.async_block_device("AA:BB:CC:DD:EE:FF")
    assert ok is True
    assert captured["data"] == {"mac": "AA:BB:CC:DD:EE:FF", "wan": "0"}
    await client.async_close()


async def test_unblock_device_posts_wan_one(host, base):
    from tests import conftest as c

    captured: dict = {}

    def _capture(url, **kwargs):
        captured["data"] = kwargs.get("data")

    client = MiWiFiClient(host, password="foco2021")
    with aioresponses() as m:
        m.get(f"{base}/web", body=c.LOGIN_HTML)
        m.post(
            re.compile(rf"{re.escape(base)}/api/xqsystem/login.*"),
            payload=c.LOGIN_OK,
        )
        m.post(
            f"{base}/;stok=TESTTOKEN/api/xqnetwork/set_mac_filter",
            payload={"code": 0},
            callback=_capture,
        )
        ok = await client.async_unblock_device("AA:BB:CC:DD:EE:FF")
    assert ok is True
    assert captured["data"] == {"mac": "AA:BB:CC:DD:EE:FF", "wan": "1"}
    await client.async_close()


async def test_get_clients_parses_devicelist(host, base):
    from tests import conftest as c

    client = MiWiFiClient(host, password="foco2021")
    with aioresponses() as m:
        m.get(f"{base}/web", body=c.LOGIN_HTML)
        m.post(
            re.compile(rf"{re.escape(base)}/api/xqsystem/login.*"),
            payload=c.LOGIN_OK,
        )
        m.get(f"{base}/;stok=TESTTOKEN/api/misystem/devicelist", payload=c.DEVICELIST)
        clients = await client.async_get_clients()
    assert len(clients) == 1
    assert clients[0].name == "homeassistant"
    assert clients[0].ip == "192.168.31.150"
    await client.async_close()


async def test_get_dhcp_reservations(host, base):
    from tests import conftest as c

    client = MiWiFiClient(host, password="foco2021")
    with aioresponses() as m:
        m.get(f"{base}/web", body=c.LOGIN_HTML)
        m.post(
            re.compile(rf"{re.escape(base)}/api/xqsystem/login.*"),
            payload=c.LOGIN_OK,
        )
        m.get(f"{base}/;stok=TESTTOKEN/api/xqnetwork/macbind_info", payload=c.MACBIND)
        res = await client.async_get_dhcp_reservations()
    assert res == [{"mac": "11:22:33:44:55:66", "ip": "192.168.31.150", "name": "ha"}]
    await client.async_close()


async def test_set_dhcp_reservation_sends_full_list(host, base):
    from tests import conftest as c

    captured: dict = {}

    def _capture(url, **kwargs):
        captured["data"] = kwargs.get("data")

    client = MiWiFiClient(host, password="foco2021")
    with aioresponses() as m:
        m.get(f"{base}/web", body=c.LOGIN_HTML)
        m.post(
            re.compile(rf"{re.escape(base)}/api/xqsystem/login.*"),
            payload=c.LOGIN_OK,
        )
        m.get(f"{base}/;stok=TESTTOKEN/api/xqnetwork/macbind_info", payload=c.MACBIND)
        m.post(
            f"{base}/;stok=TESTTOKEN/api/xqnetwork/mac_bind",
            payload={"code": 0},
            callback=_capture,
        )
        ok = await client.async_add_dhcp_reservation(
            "AA:BB:CC:DD:EE:FF", "192.168.31.77", "newdev"
        )
    assert ok is True

    # The POSTed body must be the FULL merged list: pre-existing + new.
    posted = json.loads(captured["data"]["data"])
    assert posted == [
        {"mac": "11:22:33:44:55:66", "ip": "192.168.31.150", "name": "ha"},
        {"mac": "AA:BB:CC:DD:EE:FF", "ip": "192.168.31.77", "name": "newdev"},
    ]
    await client.async_close()


async def test_request_relogins_and_retries_on_401(host, base):
    """A 401 on the first authenticated call triggers re-login then succeeds."""
    from tests import conftest as c

    login_calls = 0

    def _count_login(url, **kwargs):
        nonlocal login_calls
        login_calls += 1

    client = MiWiFiClient(host, password="foco2021")
    with aioresponses() as m:
        # aioresponses matches each registration once, in order.
        m.get(f"{base}/web", body=c.LOGIN_HTML)
        m.get(f"{base}/web", body=c.LOGIN_HTML)
        m.post(
            re.compile(rf"{re.escape(base)}/api/xqsystem/login.*"),
            payload=c.LOGIN_OK,
            callback=_count_login,
        )
        m.post(
            re.compile(rf"{re.escape(base)}/api/xqsystem/login.*"),
            payload=c.LOGIN_OK,
            callback=_count_login,
        )
        url = f"{base}/;stok=TESTTOKEN/api/misystem/newstatus"
        m.get(url, payload={"code": 401})
        m.get(url, payload=c.NEWSTATUS)
        result = await client.async_get_newstatus()
    assert result == c.NEWSTATUS
    assert login_calls == 2
    await client.async_close()


async def test_request_401_twice_does_not_recurse(host, base):
    """Two consecutive 401s return the 401 payload (bounded by _retry=False)."""
    from tests import conftest as c

    client = MiWiFiClient(host, password="foco2021")
    with aioresponses() as m:
        m.get(f"{base}/web", body=c.LOGIN_HTML)
        m.get(f"{base}/web", body=c.LOGIN_HTML)
        m.post(
            re.compile(rf"{re.escape(base)}/api/xqsystem/login.*"),
            payload=c.LOGIN_OK,
        )
        m.post(
            re.compile(rf"{re.escape(base)}/api/xqsystem/login.*"),
            payload=c.LOGIN_OK,
        )
        url = f"{base}/;stok=TESTTOKEN/api/misystem/newstatus"
        m.get(url, payload={"code": 401})
        m.get(url, payload={"code": 401})
        result = await client.async_get_newstatus()
    assert result == {"code": 401}
    await client.async_close()


async def test_login_non_json_raises_connection_error(host, base):
    """A captive-portal HTML login response raises MiWiFiConnectionError."""
    from tests import conftest as c

    client = MiWiFiClient(host, password="foco2021")
    with aioresponses() as m:
        m.get(f"{base}/web", body=c.LOGIN_HTML)
        m.post(
            re.compile(rf"{re.escape(base)}/api/xqsystem/login.*"),
            body="<html>captive portal</html>",
        )
        with pytest.raises(MiWiFiConnectionError):
            await client.async_login()
    await client.async_close()


async def test_closed_caller_session_raises(host):
    """A caller-supplied session that is closed must not be silently replaced."""
    session = aiohttp.ClientSession()
    await session.close()
    client = MiWiFiClient(host, password="foco2021", session=session)
    with pytest.raises(MiWiFiConnectionError, match="provided session is closed"):
        await client._ensure_session()


async def test_reboot_posts_reboot_endpoint(host, base):
    from tests import conftest as c

    client = MiWiFiClient(host, password="foco2021")
    with aioresponses() as m:
        m.get(f"{base}/web", body=c.LOGIN_HTML)
        m.post(
            re.compile(rf"{re.escape(base)}/api/xqsystem/login.*"),
            payload=c.LOGIN_OK,
        )
        m.get(f"{base}/;stok=TESTTOKEN/api/xqsystem/reboot", payload={"code": 0})
        ok = await client.async_reboot()
    assert ok is True
    await client.async_close()


async def test_set_wifi_enabled_toggles_radio(host, base):
    from tests import conftest as c

    client = MiWiFiClient(host, password="foco2021")
    with aioresponses() as m:
        m.get(f"{base}/web", body=c.LOGIN_HTML)
        m.post(
            re.compile(rf"{re.escape(base)}/api/xqsystem/login.*"),
            payload=c.LOGIN_OK,
        )
        m.post(f"{base}/;stok=TESTTOKEN/api/xqnetwork/wifi_down", payload={"code": 0})
        ok = await client.async_set_wifi_enabled("wl0", False)
    assert ok is True
    await client.async_close()


async def test_get_wifi_connect_devices(host, base):
    from tests import conftest as c

    client = MiWiFiClient(host, password="foco2021")
    with aioresponses() as m:
        m.get(f"{base}/web", body=c.LOGIN_HTML)
        m.post(
            re.compile(rf"{re.escape(base)}/api/xqsystem/login.*"),
            payload=c.LOGIN_OK,
        )
        m.get(f"{base}/;stok=TESTTOKEN/api/xqnetwork/wifi_connect_devices",
              payload=c.CONNECT_DEVS)
        data = await client.async_get_wifi_connect_devices()
    assert data["list"][0]["signal"] == 110
    await client.async_close()


async def test_get_clients_is_enriched(host, base):
    from tests import conftest as c

    client = MiWiFiClient(host, password="foco2021")
    with aioresponses() as m:
        m.get(f"{base}/web", body=c.LOGIN_HTML)
        m.post(
            re.compile(rf"{re.escape(base)}/api/xqsystem/login.*"),
            payload=c.LOGIN_OK,
        )
        tok = "TESTTOKEN"
        m.get(f"{base}/;stok={tok}/api/misystem/devicelist", payload=c.DEVICELIST)
        m.get(f"{base}/;stok={tok}/api/misystem/status", payload=c.STATUS_DEVS)
        m.get(f"{base}/;stok={tok}/api/xqnetwork/wifi_connect_devices",
              payload=c.CONNECT_DEVS)
        clients = await client.async_get_clients()
    ha = next(d for d in clients if d.mac == "B8:AE:ED:77:48:B7")
    assert ha.signal == 110
    assert ha.band == "5G"
    assert ha.download_speed == 7951
    assert ha.upload_total == 38238520331
    await client.async_close()


async def test_luci_request_passthrough(host, base):
    client = MiWiFiClient(host, password="foco2021")
    with aioresponses() as m:
        m.get(f"{base}/web", body="<html>key:'k'</html>")
        m.post(re.compile(rf"{re.escape(base)}/api/xqsystem/login.*"),
               payload={"token": "TESTTOKEN", "code": 0})
        m.get(f"{base}/;stok=TESTTOKEN/api/misystem/router_info",
              payload={"code": 0, "mode": 0})
        data = await client.async_luci_request("api/misystem/router_info")
    assert data["mode"] == 0
    await client.async_close()


async def test_luci_request_blocks_reboot(host):
    client = MiWiFiClient(host, password="foco2021")
    with pytest.raises(MiWiFiError):
        await client.async_luci_request("api/xqsystem/reboot")
    await client.async_close()


async def test_luci_request_blocks_set_led(host):
    client = MiWiFiClient(host, password="foco2021")
    with pytest.raises(MiWiFiError):
        await client.async_luci_request("api/misystem/set_led?on=0")
    await client.async_close()


async def test_get_available_channels(host, base):
    from tests import conftest as c

    client = MiWiFiClient(host, password="foco2021")
    with aioresponses() as m:
        m.get(f"{base}/web", body=c.LOGIN_HTML)
        m.post(re.compile(rf"{re.escape(base)}/api/xqsystem/login.*"),
               payload=c.LOGIN_OK)
        m.get(re.compile(
            rf"{re.escape(base)}/;stok=TESTTOKEN/api/xqnetwork/avaliable_channels.*"),
            payload=c.AVAIL_CH_24)
        chans = await client.async_get_available_channels(1)
    assert chans == ["0", "1", "6", "11"]
    await client.async_close()


async def test_get_init_info_and_qos(host, base):
    from tests import conftest as c

    client = MiWiFiClient(host, password="foco2021")
    with aioresponses() as m:
        m.get(f"{base}/web", body=c.LOGIN_HTML)
        m.post(re.compile(rf"{re.escape(base)}/api/xqsystem/login.*"),
               payload=c.LOGIN_OK)
        m.get(f"{base}/;stok=TESTTOKEN/api/xqsystem/init_info", payload=c.INIT_INFO)
        m.get(f"{base}/;stok=TESTTOKEN/api/misystem/qos_info", payload=c.QOS_INFO)
        info = await client.async_get_init_info()
        qos = await client.async_get_qos_info()
    assert info["countrycode"] == "CN"
    assert qos["status"]["on"] == 1
    await client.async_close()


def test_public_exports():
    import xiaomi_miwifi as pkg

    assert pkg.__version__ == "0.3.0"
    assert pkg.MiWiFiClient is not None
    assert pkg.MiWiFiStatus is not None
    assert pkg.MiWiFiConnectionError is not None
    assert pkg.MiWiFiAuthError is not None
    assert pkg.friendly_model("RM1800") == "Xiaomi Router AX1800"
