# Changelog

All notable changes to this project are documented here.

## [0.6.0] - 2026-06-02

### Added
- Read: `async_get_ipv6_status` (`api/xqnetwork/ipv6_status`), wired into `async_get_status` best-effort.
- `MiWiFiStatus.ipv6_on` derived from `info.ipv6_info.wanType` (False when `""`/`"off"`).

## [0.5.0] - 2026-06-02

### Added
- Reads: `async_get_bandwidth_history`, `async_get_pppoe_status`, `async_get_ddns`, `async_get_dmz`, `async_get_portforward`, `async_get_lan_dhcp`, `async_get_sys_time`.
- Write controls: `async_run_speed_test`, `async_add_port_forward`, `async_delete_port_forward`, `async_set_dmz`, `async_clear_dmz`, `async_set_ddns`, `async_set_dhcp`.
- `MiWiFiStatus`: speed-test results, WAN DNS, DDNS/DMZ state, port-forward count, DHCP config, timezone.

## [0.4.0] - 2026-06-02

### Added
- `async_get_available_channels`, `async_get_init_info`, `async_get_qos_info`.
- Write controls: `async_set_wifi_channel`, `async_set_wifi_txpwr` (read-modify-write over set_wifi), `async_set_qos`.
- `MiWiFiStatus.txpwr_24g`/`txpwr_5g`, `country_code`, `qos_on`.
- Full ~45-model `SUPPORTED_ROUTERS` table incl. RC06 and RD03.

## [0.3.0] - 2026-06-02

### Added
- `ClientDevice` enriched with `signal`, `band`, per-device `download_speed`/`upload_speed`/`download_total`/`upload_total` (merged from misystem/status + wifi_connect_devices).
- `MiWiFiStatus.mode`/`mode_name` (router operating mode) and `lan_ports`/`lan_ports_active` (Ethernet link state).
- `async_get_wifi_connect_devices`, `async_get_lan_info`, and generic read-only `async_luci_request(path)`.

## [0.2.0] - 2026-06-02

### Added
- Read methods: `async_get_wan_statistics`, `async_get_wifi_detail`,
  `async_get_macfilter` (longer timeout for this slow endpoint),
  `async_get_led`, `async_get_router_info`, `async_get_blocked_devices`.
- Write controls: `async_block_device` / `async_unblock_device`
  (set_mac_filter wan=0/1).
- `MiWiFiStatus` fields: `wan_download_total`, `wan_upload_total`,
  `wan_max_download`, `wan_max_upload`, `led_on`, `channel_24g`, `channel_5g`,
  `encryption_24g`, `encryption_5g`, `rom_changelog`, `rom_latest_version`.
- `MeshNode.online` flag.
- `parse_status` accepts optional `wan_stats`, `wifi_detail`, and `led` inputs;
  prefers WAN-statistics live speeds over summing per-client throughput.
- `async_get_status` now fetches wan_statistics, wifi_detail and led
  best-effort (a failing secondary endpoint no longer breaks the status).

## [0.1.0] - 2026-06-01

### Added
- Async `MiWiFiClient` with token login and request signing.
- Aggregated `MiWiFiStatus` (WAN, throughput, per-band client counts, firmware, mesh topology).
- `ClientDevice` and `MeshNode` models.
- Controls: reboot, per-radio enable/disable, DHCP reservation add/remove.
- Supported-router table (RM1800, RA82).
