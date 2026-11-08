"""Pure value-extraction helpers for HA entity display logic.

These functions are intentionally free of HA imports so they can be
unit-tested without spinning up a HomeAssistant instance.
"""

from __future__ import annotations

from aiophoenixcontactcharx import ChargingPointData


def nullable_round(value: float | None, ndigits: int) -> float | None:
    """Round value; return None when value is None (phase rotation unknown)."""
    return None if value is None else round(value, ndigits)


def meter_reading_kwh(cp: ChargingPointData) -> float | None:
    """Return the lifetime energy meter reading in kWh, or None if not yet read.

    Right after a (re)connect the controller can report 0 Wh while its meter
    is still initialising. Publishing that 0 on a TOTAL_INCREASING sensor makes
    the recorder see a meter reset followed by the full lifetime value as new
    consumption (issue #38). A real lifetime counter is never 0 once in use,
    so treat 0 as "unknown" instead.
    """
    if not cp.status.energy_active_wh:
        return None
    return round(cp.status.energy_active_kwh, 3)


def vehicle_status_key(cp: ChargingPointData) -> str | None:
    """Return Vehicle Status as a lowercase HA enum key (e.g. 'c2')."""
    return cp.status.vehicle_status.lower() if cp.status.vehicle_status else None


def error_code_hex(cp: ChargingPointData) -> str:
    """Return Error Code as an 8-digit hex string (e.g. '0x00000001')."""
    return f"0x{cp.status.error_code:08X}"
