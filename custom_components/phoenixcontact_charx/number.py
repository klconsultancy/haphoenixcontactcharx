"""Number platform for Phoenix Contact CHARX integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.const import UnitOfElectricCurrent

from .const import MAX_CURRENT_A, MIN_CURRENT_A
from .entity import CharxChargingPointEntity, CharxEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import CharxConfigEntry, CharxCoordinator


class CharxMaxCurrentNumber(CharxChargingPointEntity, NumberEntity):
    """The maximum charging current of one Charging Point (x301)."""

    _attr_translation_key = "max_current"
    _attr_device_class = NumberDeviceClass.CURRENT
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = MIN_CURRENT_A
    _attr_native_max_value = MAX_CURRENT_A
    _attr_native_step = 1.0

    def __init__(self, coordinator: CharxCoordinator, charging_point: int) -> None:
        """Control the maximum current of Charging Point ``charging_point``."""
        super().__init__(coordinator, charging_point, "max_current_number")

    @property
    def native_value(self) -> float | None:
        """The current maximum, in A."""
        cp = self._cp
        value = None if cp is None else cp.max_current
        return None if value is None else float(value)

    async def async_set_native_value(self, value: float) -> None:
        """Set the maximum current; the library rejects one outside 6-80 A."""
        await self._write(lambda: self._require_cp().set_max_current(int(value)), self.entity_id)


class CharxDynamicMaxCurrentNumber(CharxEntity, NumberEntity):
    """The Group's Dynamic Max Current (load management, 167).

    It works in every release mode, so it limits the charging current next to an OCPP
    backend too. Unknown while no limit is set.
    """

    _attr_translation_key = "dynamic_max_current_number"
    _attr_device_class = NumberDeviceClass.CURRENT
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0.0
    _attr_native_max_value = float(MAX_CURRENT_A)
    _attr_native_step = 1.0

    def __init__(self, coordinator: CharxCoordinator) -> None:
        """Control the Group's Dynamic Max Current."""
        super().__init__(coordinator, "dynamic_max_current_number")

    @property
    def native_value(self) -> float | None:
        """The limit, in A; ``None`` while none is set."""
        value = self._group.dynamic_max_current
        return None if value is None else float(value)

    async def async_set_native_value(self, value: float) -> None:
        """Set the limit."""
        await self._write(lambda: self._group.set_dynamic_max_current(int(value)), self.entity_id)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: CharxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the Group's Dynamic Max Current and the maximum current of every point."""
    coordinator = entry.runtime_data
    entities: list[NumberEntity] = [CharxDynamicMaxCurrentNumber(coordinator)]
    entities.extend(
        CharxMaxCurrentNumber(coordinator, cp.number)
        for cp in coordinator.controller.charging_points
    )
    async_add_entities(entities)
