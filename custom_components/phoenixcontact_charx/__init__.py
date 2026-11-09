"""Phoenix Contact CHARX SEC EV charging controller integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aiophoenixcontactcharx import CharxController
from homeassistant.components.modbus import async_get_unit
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import callback
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.typing import UNDEFINED
from modbus_connection import ModbusTcpParams

from .const import CONF_NUM_CHARGING_POINTS, DOMAIN, MANUFACTURER, MODEL, UNIT_ID
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
    if not coordinator.controller.charging_points and entry.data.get(CONF_NUM_CHARGING_POINTS):
        # The controller counted no Charging Controllers (register 114 read 0, as while it
        # starts). The library counts once per setup, so try a fresh one rather than set
        # up without the Charging Points this entry has.
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN, translation_key="no_charging_points"
        )
    entry.runtime_data = coordinator

    # Register the hub first, so the Charging Point devices can point at it with
    # via_device_id even when the platforms set up concurrently.
    registry = dr.async_get(hass)
    identifier = (DOMAIN, coordinator.device_id)
    known = registry.async_get_device_by_identifier(identifier, entry.entry_id)
    # An unread identity keeps a known hub's name; a new hub starts generic.
    fallback = UNDEFINED if known is not None else "CHARX SEC"
    hub = registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={identifier},
        name=coordinator.controller.device_info.designation or fallback,
        manufacturer=MANUFACTURER,
        model=MODEL,
        configuration_url=f"http://{entry.data[CONF_HOST]}",
    )
    coordinator.hub_device_id = hub.id
    _async_update_hub(hass, coordinator)
    entry.async_on_unload(
        coordinator.async_add_listener(lambda: _async_update_hub(hass, coordinator))
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


@callback
def _async_update_hub(hass: HomeAssistant, coordinator: CharxCoordinator) -> None:
    """Keep the hub device's name and firmware version current, once the identity reads.

    A read that missed the identity leaves what the registry holds. A name the user set
    (``name_by_user``) always wins over this one.
    """
    if "device_info" in coordinator.data.failed:
        return
    info = coordinator.controller.device_info
    dr.async_get(hass).async_update_device(
        coordinator.hub_device_id,
        name=info.designation or UNDEFINED,
        sw_version=info.software_version or UNDEFINED,
    )


async def async_unload_entry(hass: HomeAssistant, entry: CharxConfigEntry) -> bool:
    """Unload a config entry; the modbus integration closes the connection."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
