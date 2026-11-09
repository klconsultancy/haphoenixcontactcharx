"""Setting up and unloading an entry, its devices, and the unique IDs of 1.0.x."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from modbus_connection.exceptions import ModbusConnectionError

from custom_components.phoenixcontact_charx.const import DOMAIN

from .conftest import FIXTURES, REAL_MAC, SYNTHETIC_MAC

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from modbus_connection.mock import MockModbusUnit
    from pytest_homeassistant_custom_component.common import MockConfigEntry

UNIQUE_IDS_1_0 = json.loads((FIXTURES / "unique_ids_1.0.json").read_text(encoding="utf-8"))
# Entities 2.0 adds; they don't exist in 1.0.x, so no history depends on their IDs.
NEW_IN_2_0 = {("button", "clear_dynamic_max_current")}


def new_in_2_0(mac: str) -> set[tuple[str, str]]:
    return {(platform, f"{mac}_{key}") for platform, key in NEW_IN_2_0}


def unique_ids_1_0(mac: str, charging_points: int) -> set[tuple[str, str]]:
    """The (platform, unique ID) pairs 1.0.x creates for ``charging_points`` points."""
    pairs = {
        (platform, f"{mac}_{key}")
        for platform, keys in UNIQUE_IDS_1_0["hub"].items()
        for key in keys
    }
    pairs |= {
        (platform, f"{mac}_cp{n}_{key}")
        for n in range(1, charging_points + 1)
        for platform, keys in UNIQUE_IDS_1_0["charging_point"].items()
        for key in keys
    }
    return pairs


async def set_up(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


def registered(hass: HomeAssistant, entry: MockConfigEntry) -> set[tuple[str, str]]:
    return {
        (e.domain, e.unique_id)
        for e in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    }


@pytest.mark.usefixtures("charx_unit", "unit")
async def test_the_unique_ids_are_those_of_1_0(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    # Two Charging Points: 7 + 1 hub entities, 16 + 3 + 2 + 1 per point.
    await set_up(hass, config_entry)

    assert registered(hass, config_entry) == unique_ids_1_0(SYNTHETIC_MAC, 2) | new_in_2_0(
        SYNTHETIC_MAC
    )


@pytest.mark.usefixtures("real_unit", "unit")
async def test_the_unique_ids_of_the_real_controller_are_those_of_1_0(
    hass: HomeAssistant, real_entry: MockConfigEntry
) -> None:
    await set_up(hass, real_entry)

    assert registered(hass, real_entry) == unique_ids_1_0(REAL_MAC, 1) | new_in_2_0(REAL_MAC)


@pytest.mark.usefixtures("charx_unit", "unit")
async def test_an_existing_entity_keeps_its_entity_id(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    # An entity 1.x registered keeps its entity ID, and with it its history.
    registry = er.async_get(hass)
    registry.async_get_or_create(
        "sensor",
        DOMAIN,
        f"{SYNTHETIC_MAC}_cp1_total_energy",
        config_entry=config_entry,
        suggested_object_id="oprit_veton_one_total_energy",
    )

    await set_up(hass, config_entry)

    entity_id = registry.async_get_entity_id("sensor", DOMAIN, f"{SYNTHETIC_MAC}_cp1_total_energy")
    assert entity_id == "sensor.oprit_veton_one_total_energy"
    state = hass.states.get(entity_id)
    assert state is not None
    assert float(state.state) == pytest.approx(10450.504)


@pytest.mark.usefixtures("charx_unit", "unit")
async def test_the_charging_points_hang_under_the_hub(
    hass: HomeAssistant, config_entry: MockConfigEntry, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.WARNING):
        await set_up(hass, config_entry)

    registry = dr.async_get(hass)
    hub = registry.async_get_device_by_identifier((DOMAIN, SYNTHETIC_MAC), config_entry.entry_id)
    assert hub is not None
    assert hub.name == "CHARX SEC-3100"
    assert hub.sw_version == "1.7.3"
    for n in (1, 2):
        point = registry.async_get_device_by_identifier(
            (DOMAIN, f"{SYNTHETIC_MAC}_cp{n}"), config_entry.entry_id
        )
        assert point is not None
        assert point.name == f"Charging Point {n}"
        assert point.via_device_id == hub.id
    assert "deprecated `via_device` parameter" not in caplog.text


@pytest.mark.usefixtures("charx_unit", "unit")
async def test_setup_and_unload(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    await set_up(hass, config_entry)
    assert config_entry.state is ConfigEntryState.LOADED

    assert await hass.config_entries.async_unload(config_entry.entry_id)

    assert config_entry.state is ConfigEntryState.NOT_LOADED


async def test_a_controller_that_does_not_answer_retries_setup(
    hass: HomeAssistant, config_entry: MockConfigEntry, unit: MockModbusUnit
) -> None:
    unit.fail_requests(ModbusConnectionError("gone"))

    await hass.config_entries.async_setup(config_entry.entry_id)

    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_an_address_another_integration_holds_fails_setup(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    with patch(
        "custom_components.phoenixcontact_charx.async_get_unit",
        side_effect=HomeAssistantError("in use"),
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)

    assert config_entry.state is ConfigEntryState.SETUP_ERROR
    assert config_entry.reason is not None
    assert "Another integration already uses this controller" in config_entry.reason


async def test_no_charging_points_at_first_retries_setup(
    hass: HomeAssistant, config_entry: MockConfigEntry, charx_unit: MockModbusUnit, unit: object
) -> None:
    # Register 114 reads 0 while the controller starts; the entry expects two points.
    charx_unit.holding[114] = 0
    await hass.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.SETUP_RETRY

    charx_unit.holding[114] = 2
    await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED
    assert ("sensor", f"{SYNTHETIC_MAC}_cp2_vehicle_status") in registered(hass, config_entry)


def hub(hass: HomeAssistant, entry: MockConfigEntry) -> dr.DeviceEntry:
    device = dr.async_get(hass).async_get_device_by_identifier(
        (DOMAIN, SYNTHETIC_MAC), entry.entry_id
    )
    assert device is not None
    return device


@pytest.mark.usefixtures("charx_unit", "unit")
async def test_the_model_is_the_family_not_the_designation(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    await set_up(hass, config_entry)

    assert hub(hass, config_entry).model == "CHARX SEC"
    assert hub(hass, config_entry).name == "CHARX SEC-3100"


async def test_the_firmware_version_follows_once_the_identity_reads(
    hass: HomeAssistant, config_entry: MockConfigEntry, charx_unit: MockModbusUnit, unit: object
) -> None:
    from modbus_connection.exceptions import IllegalDataValueError  # noqa: PLC0415

    charx_unit.fail_read(100, IllegalDataValueError(3))
    await set_up(hass, config_entry)
    assert hub(hass, config_entry).sw_version is None

    charx_unit.fail_read(100, None)
    await config_entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    assert hub(hass, config_entry).sw_version == "1.7.3"


async def test_a_missed_identity_keeps_the_known_firmware_version(
    hass: HomeAssistant, config_entry: MockConfigEntry, charx_unit: MockModbusUnit, unit: object
) -> None:
    from modbus_connection.exceptions import IllegalDataValueError  # noqa: PLC0415

    await set_up(hass, config_entry)
    charx_unit.fail_read(100, IllegalDataValueError(3))

    await config_entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    assert hub(hass, config_entry).sw_version == "1.7.3"


async def test_an_unread_identity_keeps_a_known_hubs_name(
    hass: HomeAssistant, config_entry: MockConfigEntry, charx_unit: MockModbusUnit, unit: object
) -> None:
    from modbus_connection.exceptions import IllegalDataValueError  # noqa: PLC0415

    registry = dr.async_get(hass)
    registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, SYNTHETIC_MAC)},
        name="CHARX SEC-3100",
    )
    charx_unit.fail_read(100, IllegalDataValueError(3))

    await set_up(hass, config_entry)

    assert hub(hass, config_entry).name == "CHARX SEC-3100"


async def test_an_unread_identity_names_a_new_hub_generically_until_it_reads(
    hass: HomeAssistant, config_entry: MockConfigEntry, charx_unit: MockModbusUnit, unit: object
) -> None:
    from modbus_connection.exceptions import IllegalDataValueError  # noqa: PLC0415

    charx_unit.fail_read(100, IllegalDataValueError(3))
    await set_up(hass, config_entry)
    assert hub(hass, config_entry).name == "CHARX SEC"

    charx_unit.fail_read(100, None)
    await config_entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    assert hub(hass, config_entry).name == "CHARX SEC-3100"
