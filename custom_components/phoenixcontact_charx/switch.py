"""Switch platform for Phoenix Contact CHARX integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import CharxConfigEntry
from .coordinator import CharxCoordinator
from .entity import CharxChargingPointEntity


class CharxChargingReleaseSwitch(CharxChargingPointEntity, SwitchEntity):
    """Switch to enable/disable charging release for one charging point.

    Requires the charging point release mode to be set to Modbus in WBM.
    """

    _attr_translation_key = "charging_release"
    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, coordinator: CharxCoordinator, charging_point: int) -> None:
        super().__init__(coordinator, charging_point, "charging_release")

    @property
    def is_on(self) -> bool | None:
        cp_data = self._cp_data
        return cp_data.control.charging_release if cp_data else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._write_command(
            self.coordinator.client.set_charging_release(self._charging_point, True),
            f"Failed to enable charging release on CP{self._charging_point}",
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._write_command(
            self.coordinator.client.set_charging_release(self._charging_point, False),
            f"Failed to disable charging release on CP{self._charging_point}",
        )


class CharxAvailabilitySwitch(CharxChargingPointEntity, SwitchEntity):
    """Switch to set a charging point available or to status F (unavailable).

    Requires the charging point release mode to be set to Modbus in WBM.
    """

    _attr_translation_key = "availability"
    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, coordinator: CharxCoordinator, charging_point: int) -> None:
        super().__init__(coordinator, charging_point, "availability")

    @property
    def is_on(self) -> bool | None:
        cp_data = self._cp_data
        return cp_data.control.available if cp_data else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._write_command(
            self.coordinator.client.set_availability(self._charging_point, True),
            f"Failed to set CP{self._charging_point} available",
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._write_command(
            self.coordinator.client.set_availability(self._charging_point, False),
            f"Failed to set CP{self._charging_point} to status F",
        )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CharxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[SwitchEntity] = []
    for cp in coordinator.charging_point_indices:
        entities.append(CharxChargingReleaseSwitch(coordinator, cp))
        entities.append(CharxAvailabilitySwitch(coordinator, cp))
    async_add_entities(entities)
