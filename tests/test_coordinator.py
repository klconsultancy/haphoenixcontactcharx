"""Tests for the CharxCoordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from aiophoenixcontactcharx import CharxConnectionError, CharxModbusError

from .conftest import fake_charx_data


async def test_coordinator_loads_entry(hass, config_entry, mock_client):
    mock_client.fetch_data = AsyncMock(return_value=fake_charx_data())
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator = config_entry.runtime_data
    assert coordinator.data is not None
    assert coordinator.data.device_info.designation == "CHARX SEC-3000"


async def test_coordinator_connection_error_raises_update_failed(
    hass, config_entry, mock_client
):
    mock_client.fetch_data = AsyncMock(
        side_effect=CharxConnectionError("device offline")
    )
    with pytest.raises(UpdateFailed, match="Cannot reach"):
        coordinator = config_entry.runtime_data if hasattr(config_entry, "runtime_data") else None
        if coordinator is None:
            from custom_components.phoenixcontact_charx.coordinator import CharxCoordinator
            coordinator = CharxCoordinator(hass, config_entry)
        await coordinator._async_update_data()


async def test_coordinator_modbus_error_raises_update_failed(
    hass, config_entry, mock_client
):
    mock_client.fetch_data = AsyncMock(
        side_effect=CharxModbusError("exception 0x02")
    )
    from custom_components.phoenixcontact_charx.coordinator import CharxCoordinator
    coordinator = CharxCoordinator(hass, config_entry)
    with pytest.raises(UpdateFailed, match="Modbus error"):
        await coordinator._async_update_data()


async def test_coordinator_disconnect_called_on_unload(hass, config_entry, mock_client):
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    mock_client.disconnect.assert_awaited()
