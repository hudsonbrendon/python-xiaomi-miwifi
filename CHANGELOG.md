# Changelog

All notable changes to this project are documented here.

## [0.1.0] - 2026-06-01

### Added
- Async `MiWiFiClient` with token login and request signing.
- Aggregated `MiWiFiStatus` (WAN, throughput, per-band client counts, firmware, mesh topology).
- `ClientDevice` and `MeshNode` models.
- Controls: reboot, per-radio enable/disable, DHCP reservation add/remove.
- Supported-router table (RM1800, RA82).
