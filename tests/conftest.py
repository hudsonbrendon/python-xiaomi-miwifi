import pytest

LOGIN_HTML = (
    "<html><script>var deviceId = 'AA:BB';"
    " var o = { key:'abcdef0123', other:1 };</script></html>"
)

LOGIN_OK = {"token": "TESTTOKEN", "code": 0}

NEWSTATUS = {
    "code": 0, "count": 90, "re_count": 2, "cap_count": 0,
    "hardware": {"mac": "28:D1:27:9F:4C:14", "platform": "RM1800",
                 "version": "1.0.394", "sn": "SN1"},
    "2g": {"ssid": "CASA_396_2G", "online_sta_count": 69},
    "5g": {"ssid": "CASA_396_5G", "online_sta_count": 15},
}
WAN = {"code": 0, "info": {"uptime": 90861, "link": 1,
       "details": {"wanType": "dhcp"}, "gateWay": "100.107.32.1",
       "dns": ["1.1.1.1"], "ipv4": [{"ip": "100.107.54.94"}]}}
STATUS = {"code": 0, "dev": [
    {"mac": "AA", "upspeed": "100", "downspeed": "200"},
    {"mac": "BB", "upspeed": "50", "downspeed": "25"}]}
TOPO = {"code": 0, "graph": {"name": "GW", "ip": "192.168.31.1",
        "hardware": "RM1800", "ssid": "s", "mode": 0, "leafs": [
            {"name": "L1", "ip": "192.168.31.215", "hardware": "RM1800",
             "ssid": "s", "mode": 8}]}}
ROM = {"code": 0, "needUpdate": 0, "version": "1.0.394"}
DEVICELIST = {"code": 0, "mac": "GW", "list": [
    {"name": "homeassistant", "mac": "B8:AE:ED:77:48:B7", "online": 1,
     "parent": "", "isap": 0, "ip": [{"ip": "192.168.31.150"}]}]}
MACBIND = {"code": 0, "list": [
    {"mac": "11:22:33:44:55:66", "ip": "192.168.31.150", "name": "ha"}]}
WAN_STATS = {"code": 0, "statistics": {
    "download": "123456789", "upload": "987654321",
    "maxdownloadspeed": "5000000", "maxuploadspeed": "1000000"},
    "downspeed": "400", "upspeed": "120"}
WIFI_DETAIL = {"code": 0, "info": [
    {"ifname": "wl0", "ssid": "CASA_396_5G", "encryption": "psk2",
     "channelInfo": {"channel": 36}, "channel": 36, "status": 1, "hidden": 0},
    {"ifname": "wl1", "ssid": "CASA_396_2G", "encryption": "mixed-psk",
     "channelInfo": {"channel": 6}, "channel": 6, "status": 1, "hidden": 0}]}
LED = {"code": 0, "status": 1}
MACFILTER = {"code": 0, "flist": [
    {"mac": "AA:BB:CC:DD:EE:FF", "name": "blocked-dev"}]}


@pytest.fixture
def host():
    return "192.168.31.1"


@pytest.fixture
def base(host):
    return f"http://{host}/cgi-bin/luci"
