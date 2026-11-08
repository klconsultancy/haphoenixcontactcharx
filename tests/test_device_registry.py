"""Tests for hub/charging-point device parenting in the device registry."""

from __future__ import annotations

import logging

from homeassistant.helpers import device_registry as dr

from custom_components.phoenixcontact_charx.const import DOMAIN


async def test_setup_does_not_use_deprecated_via_device(
    hass, config_entry, mock_client, caplog
):
    """Charging point sub-devices must not trigger the via_device deprecation."""
    with caplog.at_level(logging.WARNING):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    assert not any(
        "deprecated `via_device` parameter" in record.message
        for record in caplog.records
    )


async def test_charging_point_device_is_parented_to_hub(
    hass, config_entry, mock_client
):
    """Charging point sub-device must be linked to the hub via via_device_id."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    registry = dr.async_get(hass)
    hub = registry.async_get_device_by_identifier(
        (DOMAIN, "AA:BB:CC:DD:EE:FF"), config_entry.entry_id
    )
    charging_point = registry.async_get_device_by_identifier(
        (DOMAIN, "AA:BB:CC:DD:EE:FF_cp1"), config_entry.entry_id
    )

    assert hub is not None
    assert charging_point is not None
    assert charging_point.via_device_id == hub.id
