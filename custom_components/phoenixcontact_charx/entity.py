"""Base entity class for Phoenix Contact CHARX integration."""

from __future__ import annotations

from homeassistant.const import CONF_HOST
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CharxCoordinator


class CharxEntity(CoordinatorEntity[CharxCoordinator]):
    """Base class providing device_info and unique_id construction."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: CharxCoordinator, unique_suffix: str) -> None:
        super().__init__(coordinator)
        mac = coordinator.config_entry.data.get("mac", coordinator.config_entry.data[CONF_HOST])
        self._attr_unique_id = f"{mac}_{unique_suffix}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, mac)},
            name="CHARX",
            manufacturer="Phoenix Contact",
            model=coordinator.data.device_info.designation or "CHARX SEC",
            sw_version=coordinator.data.device_info.software_version,
            configuration_url=f"http://{coordinator.config_entry.data[CONF_HOST]}",
        )


class CharxChargingPointEntity(CharxEntity):
    """Base entity linked to a specific charging point sub-device."""

    def __init__(
        self,
        coordinator: CharxCoordinator,
        charging_point: int,
        unique_suffix: str,
    ) -> None:
        super().__init__(coordinator, f"cp{charging_point}_{unique_suffix}")
        mac = coordinator.config_entry.data.get("mac", coordinator.config_entry.data[CONF_HOST])
        cp_id = f"{mac}_cp{charging_point}"
        self._charging_point = charging_point
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, cp_id)},
            name=f"Charging Point {charging_point}",
            manufacturer="Phoenix Contact",
            model="CHARX SEC",
            via_device=(DOMAIN, mac),
        )
