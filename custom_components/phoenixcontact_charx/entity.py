"""Base entity class for Phoenix Contact CHARX integration."""

from __future__ import annotations

import logging
from collections.abc import Coroutine
from typing import Any

from homeassistant.const import CONF_HOST
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from aiophoenixcontactcharx import CharxError, ChargingPointData

from .const import DOMAIN
from .coordinator import CharxCoordinator

_LOGGER = logging.getLogger(__name__)


class CharxEntity(CoordinatorEntity[CharxCoordinator]):
    """Base class providing device_info and unique_id construction."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: CharxCoordinator, unique_suffix: str) -> None:
        super().__init__(coordinator)
        mac = coordinator.device_id
        self._attr_unique_id = f"{mac}_{unique_suffix}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, mac)},
            name=coordinator.data.device_info.designation or "CHARX SEC",
            manufacturer="Phoenix Contact",
            model=coordinator.data.device_info.designation or "CHARX SEC",
            sw_version=coordinator.data.device_info.software_version,
            configuration_url=f"http://{coordinator.config_entry.data[CONF_HOST]}",
        )

    async def _write_command(
        self, coro: Coroutine[Any, Any, Any], error_msg: str
    ) -> None:
        try:
            await coro
        except CharxError as err:
            message = f"{error_msg}: {err}"
            _LOGGER.error(message)
            raise HomeAssistantError(message) from err
        await self.coordinator.async_request_refresh()


class CharxChargingPointEntity(CharxEntity):
    """Base entity linked to a specific charging point sub-device."""

    def __init__(
        self,
        coordinator: CharxCoordinator,
        charging_point: int,
        unique_suffix: str,
    ) -> None:
        super().__init__(coordinator, f"cp{charging_point}_{unique_suffix}")
        mac = coordinator.device_id
        cp_id = f"{mac}_cp{charging_point}"
        self._charging_point = charging_point
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, cp_id)},
            name=f"Charging Point {charging_point}",
            manufacturer="Phoenix Contact",
            model="CHARX SEC",
            via_device=(DOMAIN, mac),
        )

    @property
    def _cp_data(self) -> ChargingPointData | None:
        return next(
            (cp for cp in self.coordinator.data.charging_points
             if cp.charging_point == self._charging_point),
            None,
        )
