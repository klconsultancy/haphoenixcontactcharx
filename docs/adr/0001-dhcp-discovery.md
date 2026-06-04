# ADR 0001 — DHCP discovery via OUI + hostname filter

**Status:** Accepted

## Context

CHARX SEC-3xxx devices announce themselves on the network. Home Assistant supports automatic device discovery via DHCP, Zeroconf (mDNS), and SSDP. We want HA to prompt the user when a CHARX device appears, instead of requiring manual host entry.

CHARX advertises only `_sftp-ssh._tcp` via mDNS — a generic SSH service shared with non-CHARX devices. That service type cannot be used for typed discovery without false positives.

DHCP is viable: Phoenix Contact owns the entire OUI block `A8:74:1D` (MA-L, 16M addresses, confirmed via IEEE registry). The factory DHCP hostname for all CHARX SEC-3xxx models is `ev3000`; multiple units on the same network receive suffixed names (`ev3000-2`, `ev3000-3`).

## Decision

Use DHCP discovery with two filters: `macaddress: "A8741D*"` and `hostname: "ev3000*"`.

Both filters are required together. OUI alone matches all Phoenix Contact hardware (PLCs, sensors, power supplies). Hostname alone is user-configurable and unreliable. Combined, they identify CHARX devices at factory defaults with no known false positives.

Hostname filter is best-effort: a user who renames their device will not see auto-discovery. Manual add always works as a fallback.

## Consequences

- New CHARX devices at factory hostname settings appear in the HA integration discovery UI automatically.
- Users who change the hostname from `ev3000` must add the integration manually.
- If Phoenix Contact ships a non-CHARX product with hostname `ev3000*` on the same OUI, false positives become possible. No such product is known at the time of this decision.
