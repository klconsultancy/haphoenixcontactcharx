"""Pure value helpers for the entities, free of Home Assistant imports."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiophoenixcontactcharx import ErrorCode, VehicleStatus


def nullable_round(value: float | None, ndigits: int) -> float | None:
    """Round ``value``; ``None`` stays ``None`` (a value the controller can't give)."""
    return None if value is None else round(value, ndigits)


def vehicle_status_key(status: VehicleStatus | None) -> str | None:
    """Return the vehicle status as a lowercase enum option (``"c2"``)."""
    return None if status is None else status.value.lower()


def error_code_hex(code: ErrorCode | None) -> str | None:
    """Return the error code as 8 hexadecimal digits (``"0x00000040"``)."""
    return None if code is None else f"0x{int(code):08X}"
