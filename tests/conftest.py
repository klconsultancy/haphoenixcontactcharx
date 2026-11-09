"""Shared fixtures: a mock Modbus unit that answers like a CHARX controller."""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.phoenixcontact_charx.const import DOMAIN

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

    from modbus_connection.mock import MockModbusUnit

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict[str, Any]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


# Copied from the library's tests/fixtures. Synthetic: two Charging Points, 1 charging
# in release mode Modbus, 2 idle with an unknown phase rotation and an RFID reader error.
SYNTHETIC = _load("synthetic-sec3100.json")
# A real controller, anonymized: firmware 1.7.3, one Charging Point in OCPP release mode.
REAL = _load("sec3xxx-1.7.3.json")

SYNTHETIC_MAC = "A8:74:1D:00:12:AB"
REAL_MAC = "A8:74:1D:00:00:01"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Allow custom integrations to load in the test HA instance."""


@pytest.fixture
def charx_unit(mock_modbus_unit: MockModbusUnit) -> MockModbusUnit:
    """A mock unit that answers like the synthetic two-point controller."""
    mock_modbus_unit.load_raw(SYNTHETIC["registers"])
    return mock_modbus_unit


@pytest.fixture
def real_unit(mock_modbus_unit: MockModbusUnit) -> MockModbusUnit:
    """A mock unit that answers like the real controller (OCPP release mode)."""
    mock_modbus_unit.load_raw(REAL["registers"])
    return mock_modbus_unit


@pytest.fixture
def unit(mock_modbus_unit: MockModbusUnit) -> Iterator[MockModbusUnit]:
    """Serve the mock unit to the entry's setup in place of the modbus integration's."""
    with patch(
        "custom_components.phoenixcontact_charx.async_get_unit", return_value=mock_modbus_unit
    ):
        yield mock_modbus_unit


@pytest.fixture
def temporary_unit(mock_modbus_unit: MockModbusUnit) -> Iterator[Any]:
    """Serve the mock unit to the config flow's probe."""

    @asynccontextmanager
    async def get_temporary_unit(*_: Any) -> AsyncIterator[MockModbusUnit]:  # noqa: ANN401
        yield mock_modbus_unit

    with patch(
        "custom_components.phoenixcontact_charx.config_flow.async_get_temporary_unit",
        side_effect=get_temporary_unit,
    ) as mock:
        yield mock


def make_entry(mac: str = SYNTHETIC_MAC, num_charging_points: int = 2) -> MockConfigEntry:
    """A config entry as 1.x and 2.0 create it."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "host": "192.0.2.15",
            "port": 502,
            "mac": mac,
            "num_charging_points": num_charging_points,
        },
        unique_id=mac,
        title="CHARX SEC-3100",
    )


@pytest.fixture
def config_entry(hass: Any) -> MockConfigEntry:  # noqa: ANN401
    """The synthetic controller's entry, added to Home Assistant."""
    entry = make_entry()
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def real_entry(hass: Any) -> MockConfigEntry:  # noqa: ANN401
    """The real controller's entry, added to Home Assistant."""
    entry = make_entry(REAL_MAC, num_charging_points=1)
    entry.add_to_hass(hass)
    return entry
