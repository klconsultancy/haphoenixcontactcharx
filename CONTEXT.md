# Domain language — Phoenix Contact CHARX SEC integration

## Controller

The CHARX SEC device that the integration connects to. In EV load infrastructure terminology, the Controller is the hardware unit managing charging. In a standalone deployment this is a single CHARX SEC-3xxx unit. In a Client/Server Group it is the server unit, which aggregates data for all Charge Points across all networked units. There is one Controller per Home Assistant config entry.

## Group

The aggregate view of all Charge Points under one Controller. The Group owns controller-wide measurements (total active power, per-phase currents, active session count, connected vehicle count) and the load management budget (Dynamic Max Current). Load management operates on the Group. A Controller has exactly one Group.

## Session

The period from when a vehicle connects to a Charge Point (IEC 61851-1 status B or C) until it disconnects (returns to A1). A Session accumulates session energy and connection time, both of which reset to zero when the Session ends. A Session exists even when no energy is flowing (vehicle connected but not charging).

## Charging Release

A per-Charge-Point operational gate that permits or blocks energy flow. When off, the Charge Point will not charge even if a vehicle is connected and in state C. Requires Release Mode = Modbus on the Charge Point. Has no effect when Availability is off.

## Availability

The in-service state of a Charge Point. When off, the Charge Point enters IEC 61851-1 status F (fault/unavailable) and is non-operational — Charging Release is ignored. When on, the Charge Point is in normal service. Requires Release Mode = Modbus on the Charge Point. Availability is the coarser gate; it overrides Charging Release.

## Dynamic Max Current

The Group-level current budget in amperes. The Controller distributes this budget internally across active Charge Points — HA sets the ceiling, the Controller handles allocation. Exposed as both a readable sensor (current active value) and a writable number (command to the Controller). Both read and write the same Modbus register, so the sensor and number values converge immediately after a write.

## Load Management

The process by which the Controller distributes the Dynamic Max Current budget across Charge Points to stay within the available electrical capacity. Entirely internal to the Controller — the integration only sets the budget via Dynamic Max Current.

## Release Mode

A per-Charge-Point configuration in the WBM that determines who controls charging authorisation. Possible values: Modbus, OCPP, Permanent, Whitelist. The integration's Charging Release and Availability switches only have effect when Release Mode is set to Modbus. In any other mode, Modbus write commands are silently ignored by the Controller.

## Vehicle Status

The IEC 61851-1 state of a Charge Point, reported as a two-character code. Base letter: A = no vehicle, B = connected not charging, C = charging, E = error (no power), F = fault/unavailable.

Digit suffix semantics differ by base state:
- A/B states: `1` = supply present (EVSE ready), `2` = no supply available
- C states: `1` = charge request pending (vehicle asking, EVSE not yet delivering), `2` = actively charging
- E/F states: `0` = error or fault condition (no side distinction)

The `in` state is Phoenix Contact-specific and means the Charge Point is initialising. Full set of possible values: `a1 a2 b1 b2 c1 c2 e0 f0 in`.

## Current Setpoint

The per-Charge-Point current in amperes that the Controller has actively allocated to that Charge Point at this moment. Read-only. Distinct from Max Current (the writable upper cap configured for the Charge Point) and from Dynamic Max Current (the Group-level budget). Reflects the Controller's internal load management output for that Charge Point.

## Error Code

A Phoenix Contact-specific 32-bit fault register for a Charge Point, formatted as an 8-digit hex string (e.g. `0x00000000` = no fault). Each bit represents a specific fault condition. Read-only.

## Charge Point

One physical EV socket, managed by one CHARX SEC-3xxx hardware unit. Identified by a 1-based integer index within the Controller. Carries vehicle status, per-phase electrical measurements, session energy, and controls (charging release, availability, max current).

Each CHARX SEC-3xxx hardware unit corresponds to exactly one Charge Point. The terms "controller" (library) and "Charge Point" (integration, WBM) are 1:1 at the hardware level.
