# Changelog

All notable changes to this project are documented here.

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
