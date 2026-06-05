"""Pure value-extraction helpers for HA entity display logic.

These functions are intentionally free of HA imports so they can be
unit-tested without spinning up a HomeAssistant instance.
"""

from __future__ import annotations

from aiophoenixcontactcharx import ChargingPointData


def nullable_round(value: float | None, ndigits: int) -> float | None:
    """Round value; return None when value is None (phase rotation unknown)."""
    return None if value is None else round(value, ndigits)


def vehicle_status_key(cp: ChargingPointData) -> str | None:
    """Return Vehicle Status as a lowercase HA enum key (e.g. 'c2')."""
    return cp.status.vehicle_status.lower() if cp.status.vehicle_status else None


def error_code_hex(cp: ChargingPointData) -> str:
    """Return Error Code as an 8-digit hex string (e.g. '0x00000001')."""
    return f"0x{cp.status.error_code:08X}"
