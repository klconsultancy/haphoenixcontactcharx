"""The config flow: the user step, DHCP discovery, the cap on Charging Points, reconfigure."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import SOURCE_DHCP, SOURCE_USER
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo
from modbus_connection.exceptions import (
    IllegalDataValueError,
    ModbusConnectionError,
    ModbusTimeoutError,
)

from custom_components.phoenixcontact_charx.const import DOMAIN

from .conftest import SYNTHETIC_MAC, make_entry

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from modbus_connection.mock import MockModbusUnit

USER_INPUT = {"host": "192.0.2.15", "port": 502}
DHCP = DhcpServiceInfo(ip="192.0.2.15", hostname="ev3000", macaddress="a8741d0012ab")


@pytest.fixture(autouse=True)
def no_setup() -> Iterator[AsyncMock]:
    """Keep a created entry from being set up."""
    with patch(
        "custom_components.phoenixcontact_charx.async_setup_entry", return_value=True
    ) as mock:
        yield mock


async def start(hass: HomeAssistant, user_input: dict[str, Any] | None = None) -> Any:  # noqa: ANN401
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    if user_input is None:
        return result
    return await hass.config_entries.flow.async_configure(result["flow_id"], user_input)


# -- the user step -----------------------------------------------------------------


async def test_the_form(hass: HomeAssistant) -> None:
    result = await start(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"


@pytest.mark.usefixtures("charx_unit", "temporary_unit")
async def test_a_controller_is_added(hass: HomeAssistant) -> None:
    result = await start(hass, USER_INPUT)

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "CHARX SEC-3100"
    # The MAC in 1.x's uppercase form, which existing entries and devices use.
    assert result["result"].unique_id == SYNTHETIC_MAC
    assert result["data"] == {
        "host": "192.0.2.15",
        "port": 502,
        "mac": SYNTHETIC_MAC,
        "num_charging_points": 2,
    }


@pytest.mark.usefixtures("charx_unit", "temporary_unit")
async def test_the_host_is_stripped(hass: HomeAssistant) -> None:
    result = await start(hass, {"host": "  192.0.2.15 ", "port": 502})

    assert result["data"]["host"] == "192.0.2.15"


async def test_a_controller_without_a_designation_is_titled_by_its_host(
    hass: HomeAssistant, charx_unit: MockModbusUnit, temporary_unit: object
) -> None:
    for address in range(100, 110):
        charx_unit.holding[address] = 0

    result = await start(hass, USER_INPUT)

    assert result["title"] == "CHARX @ 192.0.2.15"


@pytest.mark.parametrize(
    ("failure", "error"),
    [
        (ModbusConnectionError("refused"), "cannot_connect"),
        (ModbusTimeoutError("silent"), "cannot_connect"),
        (IllegalDataValueError(3), "modbus_error"),
    ],
)
async def test_a_controller_that_does_not_answer_shows_an_error(
    hass: HomeAssistant,
    charx_unit: MockModbusUnit,
    temporary_unit: object,
    failure: Exception,
    error: str,
) -> None:
    charx_unit.fail_requests(failure)

    result = await start(hass, USER_INPUT)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}


async def test_an_unreadable_identity_shows_an_error(
    hass: HomeAssistant, charx_unit: MockModbusUnit, temporary_unit: object
) -> None:
    # The count reads, the identity doesn't: no MAC to identify the controller by.
    charx_unit.fail_read(115, IllegalDataValueError(3))

    result = await start(hass, USER_INPUT)

    assert result["errors"] == {"base": "modbus_error"}


async def test_an_address_another_integration_holds_shows_an_error(
    hass: HomeAssistant,
) -> None:
    with patch(
        "custom_components.phoenixcontact_charx.config_flow.async_get_temporary_unit",
        side_effect=HomeAssistantError("in use"),
    ):
        result = await start(hass, USER_INPUT)

    assert result["errors"] == {"base": "connection_in_use"}


async def test_an_unexpected_error_shows_an_error(hass: HomeAssistant) -> None:
    with patch(
        "custom_components.phoenixcontact_charx.config_flow._validate_and_probe",
        side_effect=RuntimeError("boom"),
    ):
        result = await start(hass, USER_INPUT)

    assert result["errors"] == {"base": "unknown"}


@pytest.mark.usefixtures("charx_unit", "temporary_unit")
async def test_a_configured_controller_aborts_and_updates_its_host(hass: HomeAssistant) -> None:
    entry = make_entry()
    entry.add_to_hass(hass)

    result = await start(hass, {"host": "192.0.2.99", "port": 502})

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert entry.data["host"] == "192.0.2.99"


# -- the cap on Charging Points ----------------------------------------------------


async def test_more_than_twelve_charging_points_asks_to_confirm_the_cap(
    hass: HomeAssistant, charx_unit: MockModbusUnit, temporary_unit: object
) -> None:
    charx_unit.holding[114] = 13

    result = await start(hass, USER_INPUT)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "cap_confirm"
    assert result["description_placeholders"] == {"detected": "13", "cap": "12"}

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"]["num_charging_points"] == 12


# -- DHCP discovery ----------------------------------------------------------------


async def test_a_discovered_controller_is_confirmed_then_added(
    hass: HomeAssistant, charx_unit: MockModbusUnit, temporary_unit: object
) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=DHCP
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "dhcp_confirm"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == SYNTHETIC_MAC


async def test_a_discovered_controller_already_configured_updates_its_ip(
    hass: HomeAssistant,
) -> None:
    entry = make_entry()
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(ip="192.0.2.77", hostname="ev3000", macaddress="a8741d0012ab"),
    )

    assert result["type"] is FlowResultType.ABORT
    assert entry.data["host"] == "192.0.2.77"


async def test_a_discovered_controller_that_does_not_answer_shows_an_error(
    hass: HomeAssistant, charx_unit: MockModbusUnit, temporary_unit: object
) -> None:
    charx_unit.fail_requests(ModbusConnectionError("refused"))
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=DHCP
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["errors"] == {"base": "cannot_connect"}


# -- reconfigure -------------------------------------------------------------------


async def reconfigure(hass: HomeAssistant, user_input: dict[str, Any]) -> Any:  # noqa: ANN401
    entry = make_entry(num_charging_points=1)
    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)
    assert result["step_id"] == "reconfigure"
    return entry, await hass.config_entries.flow.async_configure(result["flow_id"], user_input)


@pytest.mark.usefixtures("charx_unit", "temporary_unit")
async def test_reconfigure_moves_the_entry_and_counts_again(hass: HomeAssistant) -> None:
    entry, result = await reconfigure(hass, {"host": "192.0.2.20", "port": 502})

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data["host"] == "192.0.2.20"
    assert entry.data["num_charging_points"] == 2


async def test_reconfigure_to_another_controller_shows_an_error(
    hass: HomeAssistant, charx_unit: MockModbusUnit, temporary_unit: object
) -> None:
    charx_unit.holding[117] = 0x9999  # another MAC

    _, result = await reconfigure(hass, {"host": "192.0.2.20", "port": 502})

    assert result["errors"] == {"base": "wrong_device"}


async def test_reconfigure_past_the_cap_confirms_it(
    hass: HomeAssistant, charx_unit: MockModbusUnit, temporary_unit: object
) -> None:
    charx_unit.holding[114] = 13
    entry, result = await reconfigure(hass, {"host": "192.0.2.20", "port": 502})
    assert result["step_id"] == "cap_confirm"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["reason"] == "reconfigure_successful"
    assert entry.data["num_charging_points"] == 12


async def test_a_step_reached_without_its_data_starts_over(hass: HomeAssistant) -> None:
    from custom_components.phoenixcontact_charx.config_flow import (  # noqa: PLC0415
        CharxConfigFlow,
    )

    flow = CharxConfigFlow()
    flow.hass = hass

    for step in (flow.async_step_cap_confirm, flow.async_step_dhcp_confirm):
        result = await step()
        assert result["step_id"] == "user"
