"""Binary sensor platform for Phoenix Contact CHARX integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)

from .entity import CharxChargingPointEntity

if TYPE_CHECKING:
    from aiophoenixcontactcharx import ChargingPoint
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import CharxConfigEntry, CharxCoordinator


@dataclass(frozen=True, kw_only=True)
class CharxBinarySensorDescription(BinarySensorEntityDescription):
    """A binary sensor derived from a Charging Point's state."""

    value_fn: Callable[[ChargingPoint], bool]


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
    """A binary sensor of one Charging Point."""

    entity_description: CharxBinarySensorDescription

    def __init__(
        self,
        coordinator: CharxCoordinator,
        charging_point: int,
        description: CharxBinarySensorDescription,
    ) -> None:
        """Show ``description`` of Charging Point ``charging_point``."""
        super().__init__(coordinator, charging_point, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """The state; ``None`` while the vehicle status is unread."""
        cp = self._cp
        if cp is None or cp.vehicle_status is None:
            return None
        return self.entity_description.value_fn(cp)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: CharxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the binary sensors of every Charging Point."""
    coordinator = entry.runtime_data
    async_add_entities(
        CharxCpBinarySensor(coordinator, cp.number, description)
        for cp in coordinator.controller.charging_points
        for description in CP_BINARY_SENSORS
    )
