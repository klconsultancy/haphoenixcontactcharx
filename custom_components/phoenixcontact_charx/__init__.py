"""Phoenix Contact CHARX SEC EV charging controller integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN
from .coordinator import CharxCoordinator

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.SWITCH,
]

type CharxConfigEntry = ConfigEntry[CharxCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: CharxConfigEntry) -> bool:
    coordinator = CharxCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    # Pre-register the hub device so that charging point entities can reference
    # it via via_device even when platforms are set up concurrently.
    mac = entry.data.get("mac", entry.data[CONF_HOST])
    dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, mac)},
        name="CHARX",
        manufacturer="Phoenix Contact",
        model=coordinator.data.device_info.designation or "CHARX SEC",
        sw_version=coordinator.data.device_info.software_version,
        configuration_url=f"http://{entry.data[CONF_HOST]}",
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: CharxConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.client.disconnect()
    return unloaded
