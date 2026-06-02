"""Protocol constants for the Xiaomi MiWiFi LuCI HTTP API."""
from __future__ import annotations

DEFAULT_PORT = 80
HTTP_TIMEOUT = 12
HTTP_TIMEOUT_SLOW = 30  # for slow endpoints like wifi_macfilter_info

# Unauthenticated
PATH_WEB = "cgi-bin/luci/web"
PATH_LOGIN = "api/xqsystem/login"

# Authenticated (appended after ;stok=<token>/)
PATH_ROUTER_NAME = "api/xqsystem/router_name"
PATH_FAC_INFO = "api/xqsystem/fac_info"
PATH_NEWSTATUS = "api/misystem/newstatus"
PATH_STATUS = "api/misystem/status"
PATH_DEVICELIST = "api/misystem/devicelist"
PATH_WIFI_CONNECT_DEVICES = "api/xqnetwork/wifi_connect_devices"
PATH_LAN_INFO = "api/xqnetwork/lan_info"
PATH_WAN_INFO = "api/xqnetwork/wan_info"
PATH_TOPO_GRAPH = "api/misystem/topo_graph"
PATH_WIFI_DETAIL = "api/xqnetwork/wifi_detail_all"
PATH_CHECK_ROM = "api/xqsystem/check_rom_update"
PATH_MACBIND_INFO = "api/xqnetwork/macbind_info"
PATH_WAN_STATISTICS = "api/xqnetwork/wan_statistics"
PATH_MACFILTER_INFO = "api/xqnetwork/wifi_macfilter_info"
PATH_LED = "api/misystem/led"
PATH_ROUTER_INFO = "api/misystem/router_info"

# Write endpoints (exposed by the integration; never hit by tests live)
PATH_MAC_BIND = "api/xqnetwork/mac_bind"
PATH_MAC_UNBIND = "api/xqnetwork/mac_unbind"
PATH_REBOOT = "api/xqsystem/reboot"
PATH_WIFI_UP = "api/xqnetwork/wifi_up"
PATH_WIFI_DOWN = "api/xqnetwork/wifi_down"
PATH_SET_MAC_FILTER = "api/xqnetwork/set_mac_filter"

# Radio interface names (from wifi_detail_all: wl0=5G, wl1=2.4G on RM1800)
IFNAME_5G = "wl0"
IFNAME_24G = "wl1"
