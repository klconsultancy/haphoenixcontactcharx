# haphoenixcontactcharx

> Home Assistant custom integration for **Phoenix Contact CHARX SEC** EV AC charging controllers.

---

## What this does

Integrates CHARX SEC-3xxx EV charging controllers into Home Assistant via Modbus/TCP (local polling, no cloud). Exposes:

- **Per charging point**: vehicle status, per-phase voltage/current/power, total energy, session energy, error code, connection time — plus controls for charging release, availability, and max current
- **Group level**: total active power, per-phase group current, active session count, dynamic max current for load management
- Supports up to **12 charging points** per controller group (auto-detected at setup)

Powered by [`aiophoenixcontactcharx`](https://github.com/klconsultancy/aiophoenixcontactcharx), over Home Assistant's own Modbus connection handling (the `modbus` integration). Requires Home Assistant 2026.10 or later.

---

## Installation

### Via HACS (recommended)

1. Open HACS → Integrations → ⋮ → Custom repositories
2. Add `https://github.com/klconsultancy/haphoenixcontactcharx` as category **Integration**
3. Install **Phoenix Contact CHARX**
4. Restart Home Assistant
5. Go to Settings → Integrations → Add Integration → search **Phoenix Contact CHARX**

### Manual

1. Copy `custom_components/phoenixcontact_charx/` into your HA `config/custom_components/` directory
2. Restart Home Assistant
3. Go to Settings → Integrations → Add Integration → search **Phoenix Contact CHARX**

---

## Configuration

The config flow asks for:

| Field | Default | Description |
|---|---|---|
| IP Address | — | IP of the CHARX ETH0 interface |
| Modbus TCP Port | 502 | Leave as 502 unless changed in WBM |

At setup the integration connects, reads the device designation, MAC address, and auto-detects the number of charging controllers.

### Prerequisites on the CHARX controller

Before adding the integration, configure these in the CHARX **Web-Based Management (WBM)**:

1. **Enable Modbus server**: WBM → System Control → Status → Modbus Server: Enable
2. **Open port 502**: WBM → Network → Port Sharing → Modbus TCP (502): Enable
3. **Set release mode** *(only required for the charging release and availability switches)*: WBM → Charging Stations → Charge Point → Configuration → Release Mode: **Modbus**

---

## Entities

### Per charging point (`Charging Point N`)

| Entity | Type | Description |
|---|---|---|
| Vehicle Status | Sensor (enum) | IEC 61851-1 state: A1 / B1 / C2 / E0 … |
| Voltage L1/L2/L3 | Sensor | Phase voltages [V] |
| Current L1/L2/L3 | Sensor | Phase currents [A] |
| Active Power | Sensor | [W] |
| Reactive Power | Sensor | [VAR] |
| Apparent Power | Sensor | [VA] |
| Total Energy | Sensor | Lifetime energy counter [kWh] |
| Session Energy | Sensor | Energy in current session [kWh] |
| Current Setpoint | Sensor | Active PWM current command [A] |
| Max Current | Sensor | Configured maximum [A] |
| Connection Time | Sensor | Time connected [s] |
| Error Code | Sensor | 32-bit error bitmask (hex) |
| Connected | Binary sensor | Vehicle physically connected |
| Charging | Binary sensor | Energy transfer active (C2) |
| Error | Binary sensor | Status E or F |
| Charging Release | Switch | Enable/disable charging (Modbus release mode required) |
| Available | Switch | Set availability / status F (Modbus release mode required) |
| Max Current | Number | 6–80 A slider |

### Group (`CHARX SEC`)

| Entity | Type | Description |
|---|---|---|
| Group Active Power | Sensor | Sum of all charging points [W] |
| Group Current L1/L2/L3 | Sensor | Aggregated phase currents [A] |
| Active Charging Sessions | Sensor | Count of points in C2 |
| Connected Vehicles | Sensor | Count of points in B/C/D |
| Dynamic Max Current | Sensor + Number | Load management target [A] |

---

## Troubleshooting

**Integration fails to set up**
- Verify port 502 is open: `nc -zv <IP> 502` from another device on the same LAN
- Verify Modbus server is running: WBM → System Control → Status
- Check HA logs: search for `phoenixcontact_charx`

**Charging release and availability switches are unavailable**
- They need the charging point's release mode set to **Modbus** in WBM. In any other mode (OCPP, Permanent, Whitelist) the controller ignores them, so the integration shows them as unavailable rather than as switches that do nothing; the log says which release mode the charging point is in.
- With an OCPP backend that authorizes the sessions, limit the charging current with **Dynamic Max Current** instead: it works in every release mode.

**Sensors show "unavailable"**
- The controller may be temporarily unreachable. Check the ERR LED and WBM dashboard.
- One charging point can be unavailable while the others work: each part of the controller is read on its own, and the log names the part that failed.
- A register the controller refuses reads as "unknown" rather than taking its charging point down; the integration tries it again an hour later.
- If the controller is in a client/server group, only connect HA to the **server** (highest-level CHARX SEC-3xxx).

## Recovery

If the integration fails to load after a restart:

1. Open `home-assistant.log` and search for `phoenixcontact_charx`
2. Common causes: `ImportError` (library not installed), "Another integration already uses this controller" (another integration connects to the same address with different Modbus settings), or the device being unreachable at startup (the integration retries; check the network)
3. Remove and re-add the integration via Settings → Integrations if config entry data is corrupted

---

*Not affiliated with Phoenix Contact GmbH & Co. KG.*
