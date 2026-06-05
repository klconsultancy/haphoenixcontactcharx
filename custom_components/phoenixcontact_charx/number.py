"""Number platform for Phoenix Contact CHARX integration."""

from __future__ import annotations

import logging

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.const import UnitOfElectricCurrent
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import CharxConfigEntry
from .const import MAX_CURRENT_A, MIN_CURRENT_A
from .coordinator import CharxCoordinator
from .entity import CharxChargingPointEntity, CharxEntity

_LOGGER = logging.getLogger(__name__)


class CharxMaxCurrentNumber(CharxChargingPointEntity, NumberEntity):
    """Number entity to set the maximum charging current for one charging point."""

    _attr_translation_key = "max_current"
    _attr_device_class = NumberDeviceClass.CURRENT
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = MIN_CURRENT_A
    _attr_native_max_value = MAX_CURRENT_A
    _attr_native_step = 1.0

    def __init__(self, coordinator: CharxCoordinator, charging_point: int) -> None:
        super().__init__(coordinator, charging_point, "max_current_number")

    @property
    def native_value(self) -> float | None:
        cp_data = self._cp_data
        return float(cp_data.control.max_current_a) if cp_data else None

    async def async_set_native_value(self, value: float) -> None:
        current = int(value)
        try:
            await self._write_command(
                self.coordinator.client.set_max_current(self._charging_point, current),
                f"Failed to set max current on CP{self._charging_point}",
            )
        except ValueError as err:
            message = f"Invalid max current value {current}: {err}"
            _LOGGER.error(message)
            raise HomeAssistantError(message) from err


class CharxDynamicMaxCurrentNumber(CharxEntity, NumberEntity):
    """Number entity for the group-level dynamic maximum current (load management)."""

    _attr_translation_key = "dynamic_max_current_number"
    _attr_device_class = NumberDeviceClass.CURRENT
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0.0
    _attr_native_max_value = float(MAX_CURRENT_A)
    _attr_native_step = 1.0

    def __init__(self, coordinator: CharxCoordinator) -> None:
        super().__init__(coordinator, "dynamic_max_current_number")

    @property
    def native_value(self) -> float | None:
        value = self.coordinator.data.device_info.dynamic_max_current_a
        return float(value) if value is not None else None

    async def async_set_native_value(self, value: float) -> None:
        current = int(value)
        await self._write_command(
            self.coordinator.client.set_dynamic_max_current(current),
            "Failed to set dynamic max current on CP group",
        )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CharxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[NumberEntity] = [CharxDynamicMaxCurrentNumber(coordinator)]
    for cp in coordinator.charging_point_indices:
        entities.append(CharxMaxCurrentNumber(coordinator, cp))
    async_add_entities(entities)
