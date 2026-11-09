"""Phoenix Contact CHARX SEC EV charging controller integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aiophoenixcontactcharx import CharxController
from homeassistant.components.modbus import async_get_unit
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.exceptions import ConfigEntryError, HomeAssistantError
from homeassistant.helpers import device_registry as dr
from modbus_connection import ModbusTcpParams

from .const import DOMAIN, MANUFACTURER, UNIT_ID
from .coordinator import CharxConfigEntry, CharxCoordinator

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

__all__ = ["CharxConfigEntry"]

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: CharxConfigEntry) -> bool:
    """Set up a Charging Controller from a config entry."""
    try:
        unit = async_get_unit(
            hass,
            entry,
            ModbusTcpParams(host=entry.data[CONF_HOST], port=entry.data[CONF_PORT]),
            UNIT_ID,
        )
    except HomeAssistantError as err:
        # Another integration holds the address with other link settings; retrying won't.
        raise ConfigEntryError(
            translation_domain=DOMAIN, translation_key="connection_in_use"
        ) from err

    coordinator = CharxCoordinator(hass, entry, CharxController(unit))
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    # Register the hub first, so the Charging Point devices can point at it with
    # via_device_id even when the platforms set up concurrently.
    info = coordinator.controller.device_info
    name = info.designation or "CHARX SEC"
    hub = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, coordinator.device_id)},
        name=name,
        manufacturer=MANUFACTURER,
        model=name,
        sw_version=info.software_version,
        configuration_url=f"http://{entry.data[CONF_HOST]}",
    )
    coordinator.hub_device_id = hub.id

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: CharxConfigEntry) -> bool:
    """Unload a config entry; the modbus integration closes the connection."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
