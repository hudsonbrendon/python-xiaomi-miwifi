from xiaomi_miwifi.models import (
    ClientDevice,
    MiWiFiStatus,
    parse_status,
)

NEWSTATUS = {
    "code": 0,
    "count": 90,
    "re_count": 2,
    "cap_count": 0,
    "hardware": {
        "mac": "28:D1:27:9F:4C:14",
        "platform": "RM1800",
        "version": "1.0.394",
        "sn": "27450/F0PX56720",
    },
    "2g": {"ssid": "CASA_396_2G", "online_sta_count": 69},
    "5g": {"ssid": "CASA_396_5G", "online_sta_count": 15},
}
WAN = {
    "code": 0,
    "info": {
        "uptime": 90861,
        "link": 1,
        "details": {"wanType": "dhcp"},
        "gateWay": "100.107.32.1",
        "dns": ["1.1.1.1", "8.8.8.8"],
        "ipv4": [{"ip": "100.107.54.94", "mask": "255.255.224.0"}],
    },
}
STATUS = {
    "code": 0,
    "dev": [
        {"mac": "AA", "devname": "a", "upspeed": "100", "downspeed": "200",
         "online": "5"},
        {"mac": "BB", "devname": "b", "upspeed": "50", "downspeed": "25",
         "online": "5"},
    ],
}
TOPO = {
    "code": 0,
    "graph": {
        "name": "Xiaomi_4C14", "ip": "192.168.31.1", "hardware": "RM1800",
        "ssid": "CASA_396_2G", "mode": 0,
        "leafs": [
            {"name": "Xiaomi_C54C_3AB3", "ip": "192.168.31.215",
             "hardware": "RM1800", "ssid": "CASA_396_5G", "mode": 8},
            {"name": "ra82_miap9558", "ip": "192.168.31.156",
             "hardware": "RA82", "ssid": "CASA_396_2G", "mode": 8},
        ],
    },
}
ROM = {
    "code": 0, "needUpdate": 0, "version": "1.0.394",
    "changeLog": "Bug fixes and stability improvements.",
}
WAN_STATS = {
    "code": 0,
    "statistics": {
        "download": "123456789", "upload": "987654321",
        "maxdownloadspeed": "5000000", "maxuploadspeed": "1000000",
    },
    "downspeed": "400", "upspeed": "120",
}
WIFI_DETAIL = {
    "code": 0,
    "info": [
        {"ifname": "wl0", "ssid": "CASA_396_5G", "encryption": "psk2",
         "channelInfo": {"channel": 36}, "channel": 36},
        {"ifname": "wl1", "ssid": "CASA_396_2G", "encryption": "mixed-psk",
         "channelInfo": {"channel": 6}, "channel": 6},
    ],
}
LED = {"code": 0, "status": 1}


def test_parse_status_aggregates_all_sources():
    status = parse_status(
        newstatus=NEWSTATUS, wan=WAN, status=STATUS, topo=TOPO, rom=ROM
    )
    assert isinstance(status, MiWiFiStatus)
    assert status.online is True
    assert status.hardware == "RM1800"
    assert status.model == "Xiaomi Router AX1800"
    assert status.firmware_version == "1.0.394"
    assert status.serial == "27450/F0PX56720"
    assert status.mac == "28:D1:27:9F:4C:14"
    assert status.client_count == 90
    assert status.mesh_node_count == 2
    assert status.clients_24g == 69
    assert status.clients_5g == 15
    assert status.wan_ip == "100.107.54.94"
    assert status.wan_gateway == "100.107.32.1"
    assert status.wan_uptime == 90861
    assert status.wan_link is True
    assert status.wan_type == "dhcp"
    assert status.upload_speed == 150  # 100 + 50
    assert status.download_speed == 225  # 200 + 25
    assert status.update_available is False
    assert len(status.mesh_nodes) == 2
    assert status.mesh_nodes[0].name == "Xiaomi_C54C_3AB3"
    assert status.mesh_nodes[1].model == "Xiaomi Router AX3000T"


def test_parse_status_populates_v02_fields():
    status = parse_status(
        newstatus=NEWSTATUS, wan=WAN, status=STATUS, topo=TOPO, rom=ROM,
        wan_stats=WAN_STATS, wifi_detail=WIFI_DETAIL, led=LED,
    )
    # WAN cumulative totals + peak speeds from wan_statistics.
    assert status.wan_download_total == 123456789
    assert status.wan_upload_total == 987654321
    assert status.wan_max_download == 5000000
    assert status.wan_max_upload == 1000000
    # Live speeds preferred from wan_statistics (not the dev[] sum).
    assert status.download_speed == 400
    assert status.upload_speed == 120
    # Per-radio channels/encryption (wl1=2.4G, wl0=5G).
    assert status.channel_24g == 6
    assert status.channel_5g == 36
    assert status.encryption_24g == "mixed-psk"
    assert status.encryption_5g == "psk2"
    # LED status.
    assert status.led_on is True
    # ROM info.
    assert status.rom_latest_version == "1.0.394"
    assert status.rom_changelog == "Bug fixes and stability improvements."


def test_parse_status_falls_back_to_dev_sum_without_wan_stats():
    status = parse_status(
        newstatus=NEWSTATUS, wan=WAN, status=STATUS, topo=TOPO, rom=ROM
    )
    # No wan_stats -> sum dev[] throughput as before.
    assert status.upload_speed == 150
    assert status.download_speed == 225
    assert status.wan_download_total == 0
    assert status.led_on is False
    assert status.channel_24g == 0


def test_offline_status_factory():
    status = MiWiFiStatus(online=False)
    assert status.online is False
    assert status.client_count == 0
    assert status.mesh_nodes == []


def test_parse_status_handles_all_none_inputs():
    status = parse_status(
        newstatus=None, wan=None, status=None, topo=None, rom=None
    )
    assert isinstance(status, MiWiFiStatus)
    assert status.online is True
    assert status.hardware == ""
    assert status.firmware_version == ""
    assert status.client_count == 0
    assert status.mesh_node_count == 0
    assert status.clients_24g == 0
    assert status.clients_5g == 0
    assert status.wan_ip == ""
    assert status.upload_speed == 0
    assert status.download_speed == 0
    assert status.update_available is False
    assert status.mesh_nodes == []


def test_parse_status_handles_all_empty_dicts():
    status = parse_status(
        newstatus={}, wan={}, status={}, topo={}, rom={}
    )
    assert isinstance(status, MiWiFiStatus)
    assert status.online is True
    assert status.client_count == 0
    assert status.upload_speed == 0
    assert status.download_speed == 0
    assert status.update_available is False
    assert status.mesh_nodes == []


def test_parse_status_skips_non_dict_list_elements():
    status = parse_status(
        newstatus={},
        wan={},
        status={"dev": [None]},
        topo={"graph": {"leafs": [None]}},
        rom={},
    )
    assert isinstance(status, MiWiFiStatus)
    assert status.upload_speed == 0
    assert status.download_speed == 0
    assert status.mesh_nodes == []


def test_client_device_from_empty_entry():
    dev = ClientDevice.from_entry({})
    assert isinstance(dev, ClientDevice)
    assert dev.name == ""
    assert dev.mac == ""
    assert dev.ip == ""
    assert dev.online is False
    assert dev.parent == ""
    assert dev.is_router is False


def test_client_device_from_devicelist_entry():
    entry = {
        "name": "homeassistant", "mac": "B8:AE:ED:77:48:B7", "online": 1,
        "parent": "", "isap": 0,
        "ip": [{"ip": "192.168.31.150"}],
    }
    dev = ClientDevice.from_entry(entry)
    assert dev.name == "homeassistant"
    assert dev.mac == "B8:AE:ED:77:48:B7"
    assert dev.ip == "192.168.31.150"
    assert dev.online is True
    assert dev.is_router is False


def test_client_device_enrichment_defaults():
    dev = ClientDevice.from_entry(
        {"name": "tv", "mac": "AA:BB", "online": 1, "ip": [{"ip": "192.168.31.9"}]}
    )
    assert dev.signal == 0
    assert dev.band == ""
    assert dev.download_speed == 0
    assert dev.upload_speed == 0
    assert dev.download_total == 0
    assert dev.upload_total == 0


def test_merge_client_telemetry():
    from xiaomi_miwifi.models import merge_client_telemetry

    base = [
        ClientDevice.from_entry(
            {"name": "tv", "mac": "AA:BB:CC:DD:EE:01", "online": 1,
             "ip": [{"ip": "192.168.31.9"}]}
        )
    ]
    status_devs = [
        {"mac": "aa:bb:cc:dd:ee:01", "downspeed": "1000", "upspeed": "200",
         "download": "5000000", "upload": "900000"}
    ]
    connect_devs = [
        {"mac": "AA:BB:CC:DD:EE:01", "wifiIndex": 2, "signal": 110}
    ]
    merged = merge_client_telemetry(base, status_devs, connect_devs)
    d = merged[0]
    assert d.download_speed == 1000
    assert d.upload_speed == 200
    assert d.download_total == 5000000
    assert d.upload_total == 900000
    assert d.signal == 110
    assert d.band == "5G"


def test_merge_client_telemetry_tolerates_missing_and_bad():
    from xiaomi_miwifi.models import merge_client_telemetry

    base = [
        ClientDevice.from_entry(
            {"name": "x", "mac": "11:22", "online": 1, "ip": []}
        )
    ]
    # no matching telemetry, plus a junk non-dict element
    merged = merge_client_telemetry(base, [None, {}], [None])
    assert merged[0].signal == 0
    assert merged[0].band == ""
