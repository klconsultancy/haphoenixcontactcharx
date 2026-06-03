"""Tests for the Phoenix Contact CHARX config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.data_entry_flow import FlowResultType

from aiophoenixcontactcharx import CharxConnectionError, CharxModbusError

from custom_components.phoenixcontact_charx.const import DOMAIN


async def _init_flow(hass):
    return await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )


async def _submit(hass, flow_id, host="192.168.1.100", port=502):
    return await hass.config_entries.flow.async_configure(
        flow_id, {"host": host, "port": port}
    )


# ---------------------------------------------------------------------------
# Success path
# ---------------------------------------------------------------------------

async def test_form_shown(hass):
    result = await _init_flow(hass)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


async def test_successful_setup(hass, mock_client):
    with patch(
        "custom_components.phoenixcontact_charx.config_flow._validate_and_probe",
        AsyncMock(return_value={
            "title": "CHARX SEC-3000",
            "mac": "AA:BB:CC:DD:EE:FF",
            "num_charging_points": 2,
        }),
    ):
        result = await _init_flow(hass)
        result = await _submit(hass, result["flow_id"])
    await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "CHARX SEC-3000"
    assert result["data"]["host"] == "192.168.1.100"
    assert result["data"]["port"] == 502
    assert result["data"]["mac"] == "AA:BB:CC:DD:EE:FF"
    assert result["data"]["num_charging_points"] == 2


async def test_host_is_stripped(hass, mock_client):
    """Leading/trailing whitespace in the host field is stripped."""
    with patch(
        "custom_components.phoenixcontact_charx.config_flow._validate_and_probe",
        AsyncMock(return_value={
            "title": "CHARX",
            "mac": "00:11:22:33:44:55",
            "num_charging_points": 1,
        }),
    ) as mock_probe:
        result = await _init_flow(hass)
        await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "  192.168.1.1  ", "port": 502}
        )
    await hass.async_block_till_done()

    called_host = mock_probe.call_args[0][0]
    assert called_host == "192.168.1.1"


async def test_cap_warning_shown_when_cp_count_exceeds_max(hass, mock_client):
    """Device reporting >12 CPs triggers the cap_confirm warning step."""
    with patch(
        "custom_components.phoenixcontact_charx.config_flow._validate_and_probe",
        AsyncMock(return_value={
            "title": "CHARX",
            "mac": "00:11:22:33:44:55",
            "num_charging_points": 50,
        }),
    ):
        result = await _init_flow(hass)
        result = await _submit(hass, result["flow_id"])

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "cap_confirm"
    assert result["description_placeholders"]["detected"] == "50"
    assert result["description_placeholders"]["cap"] == "12"


async def test_num_charging_points_capped_at_12(hass, mock_client):
    """Confirming the cap warning creates the entry with MAX_CHARGING_POINTS."""
    with patch(
        "custom_components.phoenixcontact_charx.config_flow._validate_and_probe",
        AsyncMock(return_value={
            "title": "CHARX",
            "mac": "00:11:22:33:44:55",
            "num_charging_points": 50,
        }),
    ):
        result = await _init_flow(hass)
        result = await _submit(hass, result["flow_id"])
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"]["num_charging_points"] == 12


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------

async def test_cannot_connect_shows_error(hass):
    with patch(
        "custom_components.phoenixcontact_charx.config_flow._validate_and_probe",
        AsyncMock(side_effect=CharxConnectionError("timeout")),
    ):
        result = await _init_flow(hass)
        result = await _submit(hass, result["flow_id"])

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "cannot_connect"


async def test_modbus_error_shows_error(hass):
    with patch(
        "custom_components.phoenixcontact_charx.config_flow._validate_and_probe",
        AsyncMock(side_effect=CharxModbusError("exception response")),
    ):
        result = await _init_flow(hass)
        result = await _submit(hass, result["flow_id"])

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "modbus_error"


async def test_unknown_exception_shows_error(hass):
    with patch(
        "custom_components.phoenixcontact_charx.config_flow._validate_and_probe",
        AsyncMock(side_effect=RuntimeError("unexpected")),
    ):
        result = await _init_flow(hass)
        result = await _submit(hass, result["flow_id"])

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "unknown"


# ---------------------------------------------------------------------------
# Duplicate device
# ---------------------------------------------------------------------------

async def test_already_configured_aborts(hass, config_entry):
    """Second setup attempt for the same MAC is rejected."""
    with patch(
        "custom_components.phoenixcontact_charx.config_flow._validate_and_probe",
        AsyncMock(return_value={
            "title": "CHARX SEC-3000",
            "mac": "AA:BB:CC:DD:EE:FF",  # same MAC as config_entry fixture
            "num_charging_points": 1,
        }),
    ):
        result = await _init_flow(hass)
        result = await _submit(hass, result["flow_id"])

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


# ---------------------------------------------------------------------------
# Reconfigure flow
# ---------------------------------------------------------------------------

async def _init_reconfigure(hass, config_entry):
    return await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "reconfigure", "entry_id": config_entry.entry_id},
    )


async def test_reconfigure_form_shown(hass, config_entry):
    result = await _init_reconfigure(hass, config_entry)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "reconfigure"


async def test_reconfigure_updates_cp_count(hass, config_entry, mock_client):
    with patch(
        "custom_components.phoenixcontact_charx.config_flow._validate_and_probe",
        AsyncMock(return_value={
            "title": "CHARX SEC-3000",
            "mac": "AA:BB:CC:DD:EE:FF",
            "num_charging_points": 4,
        }),
    ):
        result = await _init_reconfigure(hass, config_entry)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "192.168.1.100", "port": 502}
        )
    await hass.async_block_till_done()

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert config_entry.data["num_charging_points"] == 4


async def test_reconfigure_shows_cap_warning_when_exceeded(hass, config_entry, mock_client):
    with patch(
        "custom_components.phoenixcontact_charx.config_flow._validate_and_probe",
        AsyncMock(return_value={
            "title": "CHARX SEC-3000",
            "mac": "AA:BB:CC:DD:EE:FF",
            "num_charging_points": 20,
        }),
    ):
        result = await _init_reconfigure(hass, config_entry)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "192.168.1.100", "port": 502}
        )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "cap_confirm"
    assert result["description_placeholders"]["detected"] == "20"


async def test_reconfigure_cap_confirm_caps_at_max(hass, config_entry, mock_client):
    with patch(
        "custom_components.phoenixcontact_charx.config_flow._validate_and_probe",
        AsyncMock(return_value={
            "title": "CHARX SEC-3000",
            "mac": "AA:BB:CC:DD:EE:FF",
            "num_charging_points": 20,
        }),
    ):
        result = await _init_reconfigure(hass, config_entry)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "192.168.1.100", "port": 502}
        )
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    await hass.async_block_till_done()

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert config_entry.data["num_charging_points"] == 12


async def test_reconfigure_connection_error_shows_error(hass, config_entry):
    with patch(
        "custom_components.phoenixcontact_charx.config_flow._validate_and_probe",
        AsyncMock(side_effect=CharxConnectionError("timeout")),
    ):
        result = await _init_reconfigure(hass, config_entry)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "192.168.1.100", "port": 502}
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "cannot_connect"
