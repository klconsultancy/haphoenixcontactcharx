"""The sensors, binary sensors, switches and numbers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from modbus_connection.exceptions import IllegalDataValueError, ModbusConnectionError

from custom_components.phoenixcontact_charx.const import DOMAIN

from .conftest import REAL_MAC, SYNTHETIC_MAC

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, State
    from modbus_connection.mock import MockModbusUnit, WriteEvent
    from pytest_homeassistant_custom_component.common import MockConfigEntry


async def set_up(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


def entity_id(hass: HomeAssistant, platform: str, suffix: str, mac: str = SYNTHETIC_MAC) -> str:
    """The entity ID of the entity with unique ID ``{mac}_{suffix}``."""
    found = er.async_get(hass).async_get_entity_id(platform, DOMAIN, f"{mac}_{suffix}")
    assert found is not None, suffix
    return found


def state(hass: HomeAssistant, platform: str, suffix: str, mac: str = SYNTHETIC_MAC) -> State:
    found = hass.states.get(entity_id(hass, platform, suffix, mac))
    assert found is not None
    return found


def writes(unit: MockModbusUnit) -> list[WriteEvent]:
    events: list[WriteEvent] = []
    unit.on_write(events.append)
    return events


async def refresh(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()


# -- sensors -----------------------------------------------------------------------


@pytest.mark.usefixtures("charx_unit", "unit")
async def test_the_group_sensors(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    await set_up(hass, config_entry)

    assert float(state(hass, "sensor", "group_active_power").state) == pytest.approx(7398.0)
    # -1: a configured Charging Point's phase rotation is unknown.
    assert state(hass, "sensor", "group_current_l1").state == STATE_UNKNOWN
    assert state(hass, "sensor", "num_charging").state == "1"
    assert state(hass, "sensor", "num_connected").state == "1"
    assert state(hass, "sensor", "dynamic_max_current").state == "32"


@pytest.mark.usefixtures("charx_unit", "unit")
async def test_the_charging_point_sensors(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    await set_up(hass, config_entry)

    assert state(hass, "sensor", "cp1_vehicle_status").state == "c2"
    assert float(state(hass, "sensor", "cp1_voltage_l1").state) == pytest.approx(230.1)
    assert float(state(hass, "sensor", "cp1_current_l1").state) == pytest.approx(10.7)
    assert float(state(hass, "sensor", "cp1_active_power").state) == pytest.approx(7398.0)
    assert float(state(hass, "sensor", "cp1_reactive_power").state) == pytest.approx(-40.0)
    assert float(state(hass, "sensor", "cp1_total_energy").state) == pytest.approx(10450.504)
    assert float(state(hass, "sensor", "cp1_session_energy").state) == pytest.approx(3.212)
    assert state(hass, "sensor", "cp1_current_setpoint").state == "16"
    assert state(hass, "sensor", "cp1_max_current").state == "16"
    assert state(hass, "sensor", "cp1_connection_time").state == "1830"
    assert state(hass, "sensor", "cp1_error_code").state == "0x00000000"
    assert state(hass, "sensor", "cp2_error_code").state == "0x00000040"
    assert state(hass, "sensor", "cp2_current_l1").state == STATE_UNKNOWN


@pytest.mark.usefixtures("charx_unit", "unit")
async def test_the_state_classes_stay(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    await set_up(hass, config_entry)

    assert state(hass, "sensor", "cp1_total_energy").attributes["state_class"] == "total_increasing"
    assert state(hass, "sensor", "cp1_session_energy").attributes["state_class"] == "total"


async def test_a_lifetime_energy_of_zero_is_unknown(
    hass: HomeAssistant, config_entry: MockConfigEntry, charx_unit: MockModbusUnit, unit: object
) -> None:
    # A meter that is starting after a reconnect reports 0 (#38).
    for address in range(1250, 1254):
        charx_unit.holding[address] = 0

    await set_up(hass, config_entry)

    assert state(hass, "sensor", "cp1_total_energy").state == STATE_UNKNOWN


@pytest.mark.parametrize(("code", "option"), [(b"D1", "d1"), (b"D2", "d2"), (b"F0", "f0")])
async def test_every_vehicle_status_is_an_option(  # noqa: PLR0913
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    charx_unit: MockModbusUnit,
    unit: object,
    code: bytes,
    option: str,
) -> None:
    charx_unit.holding[1299] = int.from_bytes(code, "big")

    await set_up(hass, config_entry)

    sensor = state(hass, "sensor", "cp1_vehicle_status")
    assert sensor.state == option
    assert option in sensor.attributes["options"]


@pytest.mark.usefixtures("real_unit", "unit")
async def test_the_real_controller(hass: HomeAssistant, real_entry: MockConfigEntry) -> None:
    await set_up(hass, real_entry)

    assert state(hass, "sensor", "cp1_vehicle_status", REAL_MAC).state == "a1"
    assert float(state(hass, "sensor", "cp1_total_energy", REAL_MAC).state) == pytest.approx(
        10562.978
    )
    # 65535: no dynamic limit set.
    assert state(hass, "sensor", "dynamic_max_current", REAL_MAC).state == STATE_UNKNOWN
    assert state(hass, "number", "dynamic_max_current_number", REAL_MAC).state == STATE_UNKNOWN


# -- binary sensors ----------------------------------------------------------------


@pytest.mark.usefixtures("charx_unit", "unit")
async def test_the_binary_sensors(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    await set_up(hass, config_entry)

    assert state(hass, "binary_sensor", "cp1_connected").state == STATE_ON
    assert state(hass, "binary_sensor", "cp1_charging").state == STATE_ON
    assert state(hass, "binary_sensor", "cp1_error").state == STATE_OFF
    assert state(hass, "binary_sensor", "cp2_connected").state == STATE_OFF
    assert state(hass, "binary_sensor", "cp2_charging").state == STATE_OFF


async def test_an_unread_vehicle_status_is_unknown(
    hass: HomeAssistant, config_entry: MockConfigEntry, charx_unit: MockModbusUnit, unit: object
) -> None:
    charx_unit.holding[1299] = 0  # no characters

    await set_up(hass, config_entry)

    assert state(hass, "sensor", "cp1_vehicle_status").state == STATE_UNKNOWN
    assert state(hass, "binary_sensor", "cp1_connected").state == STATE_UNKNOWN


# -- availability ------------------------------------------------------------------


async def test_a_failing_charging_point_makes_only_its_entities_unavailable(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    charx_unit: MockModbusUnit,
    unit: object,
    caplog: pytest.LogCaptureFixture,
) -> None:
    await set_up(hass, config_entry)
    charx_unit.fail_read(2232, IllegalDataValueError(3))

    with caplog.at_level(logging.WARNING):
        await refresh(hass, config_entry)

    assert state(hass, "sensor", "cp2_vehicle_status").state == STATE_UNAVAILABLE
    assert state(hass, "binary_sensor", "cp2_connected").state == STATE_UNAVAILABLE
    assert state(hass, "number", "cp2_max_current_number").state == STATE_UNAVAILABLE
    assert state(hass, "sensor", "cp1_vehicle_status").state == "c2"
    assert float(state(hass, "sensor", "group_active_power").state) == pytest.approx(7398.0)
    assert "charging_point_2 failed to refresh" in caplog.text


async def test_a_charging_point_that_answers_again_is_available_again(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    charx_unit: MockModbusUnit,
    unit: object,
    caplog: pytest.LogCaptureFixture,
) -> None:
    await set_up(hass, config_entry)
    charx_unit.fail_read(2232, IllegalDataValueError(3))
    await refresh(hass, config_entry)
    charx_unit.fail_read(2232, None)

    with caplog.at_level(logging.INFO):
        await refresh(hass, config_entry)

    assert state(hass, "sensor", "cp2_vehicle_status").state == "a1"
    assert "charging_point_2 is available again" in caplog.text


async def test_a_failing_group_makes_the_hub_entities_unavailable(
    hass: HomeAssistant, config_entry: MockConfigEntry, charx_unit: MockModbusUnit, unit: object
) -> None:
    await set_up(hass, config_entry)
    charx_unit.fail_read(152, IllegalDataValueError(3))

    await refresh(hass, config_entry)

    assert state(hass, "sensor", "group_active_power").state == STATE_UNAVAILABLE
    assert state(hass, "number", "dynamic_max_current_number").state == STATE_UNAVAILABLE
    assert state(hass, "sensor", "cp1_vehicle_status").state == "c2"


async def test_a_lost_connection_makes_everything_unavailable(
    hass: HomeAssistant, config_entry: MockConfigEntry, charx_unit: MockModbusUnit, unit: object
) -> None:
    await set_up(hass, config_entry)
    charx_unit.fail_requests(ModbusConnectionError("gone"))

    await refresh(hass, config_entry)

    assert state(hass, "sensor", "group_active_power").state == STATE_UNAVAILABLE
    assert state(hass, "sensor", "cp1_vehicle_status").state == STATE_UNAVAILABLE


async def test_every_part_failing_makes_everything_unavailable(
    hass: HomeAssistant, config_entry: MockConfigEntry, charx_unit: MockModbusUnit, unit: object
) -> None:
    await set_up(hass, config_entry)
    for address in (100, 152, 1232, 2232):
        charx_unit.fail_read(address, IllegalDataValueError(3))

    await refresh(hass, config_entry)

    assert not config_entry.runtime_data.last_update_success
    assert state(hass, "sensor", "cp1_vehicle_status").state == STATE_UNAVAILABLE


# -- switches ----------------------------------------------------------------------


@pytest.mark.usefixtures("unit")
async def test_the_switches_in_release_mode_modbus(
    hass: HomeAssistant, config_entry: MockConfigEntry, charx_unit: MockModbusUnit
) -> None:
    # The synthetic Charging Points are in release mode Modbus.
    await set_up(hass, config_entry)
    events = writes(charx_unit)

    assert state(hass, "switch", "cp1_charging_release").state == STATE_ON
    assert state(hass, "switch", "cp1_availability").state == STATE_ON
    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": entity_id(hass, "switch", "cp1_charging_release")},
        blocking=True,
    )
    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": entity_id(hass, "switch", "cp1_availability")},
        blocking=True,
    )

    assert [(e.address, e.values, e.function_code) for e in events] == [
        (1300, [0], 0x10),
        (1304, [0], 0x10),
    ]
    assert state(hass, "switch", "cp1_charging_release").state == STATE_OFF
    assert state(hass, "switch", "cp1_availability").state == STATE_OFF


@pytest.mark.usefixtures("unit")
async def test_the_switches_are_unavailable_in_release_mode_ocpp(
    hass: HomeAssistant,
    real_entry: MockConfigEntry,
    real_unit: MockModbusUnit,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.INFO):
        await set_up(hass, real_entry)

    assert state(hass, "switch", "cp1_charging_release", REAL_MAC).state == STATE_UNAVAILABLE
    assert state(hass, "switch", "cp1_availability", REAL_MAC).state == STATE_UNAVAILABLE
    assert "Charging Point 1 is in release mode OCPP" in caplog.text
    # The rest of the Charging Point is available.
    assert state(hass, "sensor", "cp1_vehicle_status", REAL_MAC).state == "a1"


async def test_a_failed_switch_write_raises(
    hass: HomeAssistant, config_entry: MockConfigEntry, charx_unit: MockModbusUnit, unit: object
) -> None:
    await set_up(hass, config_entry)
    charx_unit.fail_write(1300, IllegalDataValueError(3))

    with pytest.raises(HomeAssistantError, match="Writing switch.*failed"):
        await hass.services.async_call(
            "switch",
            "turn_off",
            {"entity_id": entity_id(hass, "switch", "cp1_charging_release")},
            blocking=True,
        )


# -- numbers -----------------------------------------------------------------------


@pytest.mark.usefixtures("unit")
async def test_the_max_current(
    hass: HomeAssistant, config_entry: MockConfigEntry, charx_unit: MockModbusUnit
) -> None:
    await set_up(hass, config_entry)
    events = writes(charx_unit)
    number = entity_id(hass, "number", "cp1_max_current_number")
    assert float(state(hass, "number", "cp1_max_current_number").state) == 16

    await hass.services.async_call(
        "number", "set_value", {"entity_id": number, "value": 10}, blocking=True
    )

    assert [(e.address, e.values, e.function_code) for e in events] == [(1301, [10], 0x10)]
    assert float(state(hass, "number", "cp1_max_current_number").state) == 10


@pytest.mark.usefixtures("unit")
async def test_the_dynamic_max_current_in_release_mode_ocpp(
    hass: HomeAssistant, real_entry: MockConfigEntry, real_unit: MockModbusUnit
) -> None:
    # Load management works next to an OCPP backend (as tested on the real controller).
    await set_up(hass, real_entry)
    events = writes(real_unit)

    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": entity_id(hass, "number", "dynamic_max_current_number", REAL_MAC), "value": 16},
        blocking=True,
    )

    assert [(e.address, e.values, e.function_code) for e in events] == [(167, [16], 0x10)]
    assert float(state(hass, "number", "dynamic_max_current_number", REAL_MAC).state) == 16


async def test_a_failed_number_write_raises(
    hass: HomeAssistant, config_entry: MockConfigEntry, charx_unit: MockModbusUnit, unit: object
) -> None:
    await set_up(hass, config_entry)
    charx_unit.fail_write(167, ModbusConnectionError("gone"))

    with pytest.raises(HomeAssistantError, match="gone"):
        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": entity_id(hass, "number", "dynamic_max_current_number"), "value": 20},
            blocking=True,
        )


# -- a Charging Point the controller no longer reports -----------------------------


async def test_a_charging_point_the_controller_no_longer_reports_is_unavailable(
    hass: HomeAssistant, charx_unit: MockModbusUnit, unit: object
) -> None:
    # An entry of three points; the controller now counts two. The registry still has
    # point 3's entities from before, which must not break setup.
    from .conftest import make_entry  # noqa: PLC0415

    entry = make_entry(num_charging_points=3)
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    registry.async_get_or_create(
        "sensor", DOMAIN, f"{SYNTHETIC_MAC}_cp3_vehicle_status", config_entry=entry
    )

    await set_up(hass, entry)

    stale = hass.states.get(entity_id(hass, "sensor", "cp3_vehicle_status"))
    assert stale is None or stale.state == STATE_UNAVAILABLE
    assert state(hass, "sensor", "cp2_vehicle_status").state == "a1"


@pytest.mark.usefixtures("unit")
async def test_the_switches_turn_on(
    hass: HomeAssistant, config_entry: MockConfigEntry, charx_unit: MockModbusUnit
) -> None:
    charx_unit.holding[1300] = 0
    charx_unit.holding[1304] = 0
    await set_up(hass, config_entry)
    events = writes(charx_unit)

    for suffix in ("cp1_charging_release", "cp1_availability"):
        await hass.services.async_call(
            "switch", "turn_on", {"entity_id": entity_id(hass, "switch", suffix)}, blocking=True
        )

    assert [(e.address, e.values) for e in events] == [(1300, [1]), (1304, [1])]


async def test_a_write_to_a_charging_point_the_controller_dropped_raises(
    hass: HomeAssistant, config_entry: MockConfigEntry, charx_unit: MockModbusUnit, unit: object
) -> None:
    # Home Assistant calls no service on the entity then, since it is unavailable; the
    # guard covers a direct call.
    await set_up(hass, config_entry)
    delattr(config_entry.runtime_data.controller, "charging_point_1")
    number = hass.data["entity_components"]["number"].get_entity(
        entity_id(hass, "number", "cp1_max_current_number")
    )

    with pytest.raises(HomeAssistantError, match="doesn't report Charging Point 1"):
        await number.async_set_native_value(10)
