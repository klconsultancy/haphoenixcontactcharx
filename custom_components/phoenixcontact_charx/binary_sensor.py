"""Binary sensor platform for Phoenix Contact CHARX integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from aiophoenixcontactcharx import ChargingPointData

from . import CharxConfigEntry
from .entity import CharxChargingPointEntity


@dataclass(frozen=True, kw_only=True)
class CharxBinarySensorDescription(BinarySensorEntityDescription):
    value_fn: Callable[[ChargingPointData], bool] = lambda _: False


CP_BINARY_SENSORS: tuple[CharxBinarySensorDescription, ...] = (
    CharxBinarySensorDescription(
        key="connected",
        translation_key="connected",
        device_class=BinarySensorDeviceClass.PLUG,
        value_fn=lambda cp: cp.is_connected,
    ),
    CharxBinarySensorDescription(
        key="charging",
        translation_key="charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        value_fn=lambda cp: cp.is_charging,
    ),
    CharxBinarySensorDescription(
        key="error",
        translation_key="error",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda cp: cp.has_error,
    ),
)


class CharxCpBinarySensor(CharxChargingPointEntity, BinarySensorEntity):
    """Binary sensor for a per-charging-point boolean state."""

    entity_description: CharxBinarySensorDescription

    def __init__(
        self,
        coordinator: Any,
        charging_point: int,
        description: CharxBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator, charging_point, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        cp_data = self._cp_data
        if cp_data is None:
            return None
        return self.entity_description.value_fn(cp_data)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CharxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[BinarySensorEntity] = []
    for cp in range(1, coordinator.num_charging_points + 1):
        for description in CP_BINARY_SENSORS:
            entities.append(CharxCpBinarySensor(coordinator, cp, description))
    async_add_entities(entities)
