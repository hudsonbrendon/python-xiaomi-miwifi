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
CONNECT_DEVS = {"code": 0, "list": [
    {"mac": "B8:AE:ED:77:48:B7", "wifiIndex": 2, "signal": 110}]}
LAN_INFO = {"code": 0, "info": {"mac": "9C:9D:7E:46:DA:7C", "uptime": 153742},
            "linkList": [0, 1, 0]}
ROUTER_INFO = {"code": 0, "name": "GW", "mac": "28:D1:27:9F:4C:14",
               "hardware": "RM1800", "mode": 0}
STATUS_DEVS = {"code": 0, "dev": [
    {"mac": "B8:AE:ED:77:48:B7", "downspeed": "7951", "upspeed": "147874",
     "download": "45258676102", "upload": "38238520331"}]}
AVAIL_CH_24 = {"code": 0, "list": [
    {"c": "0", "b": ["20", "40"]}, {"c": "1", "b": ["20", "40"]},
    {"c": "6", "b": ["20", "40"]}, {"c": "11", "b": ["20", "40"]}]}
AVAIL_CH_5 = {"code": 0, "list": [
    {"c": "0", "b": ["20", "40", "80"]}, {"c": "36", "b": ["20", "40", "80"]},
    {"c": "149", "b": ["20", "40", "80"]}]}
INIT_INFO = {"code": 0, "countrycode": "CN", "model": "xiaomi.router.rm1800",
             "id": "27450/X", "hardware": "RM1800", "romversion": "1.0.394"}
QOS_INFO = {"code": 0, "status": {"on": 1, "mode": 0}}
WIFI_DETAIL_TX = {"code": 0, "info": [
    {"ifname": "wl1", "ssid": "CASA_2G", "password": "p", "encryption": "mixed-psk",
     "channelInfo": {"channel": 6, "bandwidth": "0"}, "channel": "0",
     "txpwr": "max", "hidden": "0", "ax": "0", "txbf": "3"},
    {"ifname": "wl0", "ssid": "CASA_5G", "password": "p", "encryption": "mixed-psk",
     "channelInfo": {"channel": 36, "bandwidth": "0"}, "channel": "0",
     "txpwr": "mid", "hidden": "0", "ax": "0", "txbf": "3"}]}


BANDWIDTH_HISTORY = {"code": 0, "download": 865.28, "upload": 1553.92,
                     "bandwidth": 6.76, "bandwidth2": 12.14}
PPPOE = {"code": 0, "proto": "dhcp", "dns": ["1.1.1.1", "8.8.8.8"],
         "gw": "100.107.32.1"}
DDNS = {"code": 0, "on": 0, "list": []}
DMZ = {"code": 0, "status": 0, "lanip": "192.168.31.1"}
PORTFORWARD = {"code": 0, "status": 0, "list": []}
LAN_DHCP = {"code": 0, "info": {"leasetimeNum": "720", "limit": "250",
            "start": "5", "leasetime": "720m"}}
SYS_TIME = {"code": 0, "role": "whc_cap",
            "time": {"timezone": "CST-8", "year": 2026}}


@pytest.fixture
def host():
    return "192.168.31.1"


@pytest.fixture
def base(host):
    return f"http://{host}/cgi-bin/luci"
