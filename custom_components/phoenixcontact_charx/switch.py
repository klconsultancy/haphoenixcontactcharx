"""Switch platform for Phoenix Contact CHARX integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from aiophoenixcontactcharx import ReleaseMode
from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity

from .entity import CharxChargingPointEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import CharxConfigEntry, CharxCoordinator

_LOGGER = logging.getLogger(__name__)


class CharxModbusReleaseSwitch(CharxChargingPointEntity, SwitchEntity):
    """A switch the controller only takes in release mode Modbus.

    In any other release mode (OCPP, for one) it is unavailable rather than a switch
    that does nothing.
    """

    _attr_device_class = SwitchDeviceClass.SWITCH
    _field: str

    @property
    def available(self) -> bool:
        """Unavailable outside release mode Modbus."""
        cp = self._cp
        return (
            super().available and cp is not None and cp.release_mode is ReleaseMode.MODBUS
        )

    @property
    def is_on(self) -> bool | None:
        """The register's state."""
        cp = self._cp
        return None if cp is None else getattr(cp, self._field)


class CharxChargingReleaseSwitch(CharxModbusReleaseSwitch):
    """Release charging for a connected vehicle, or withdraw the release."""

    _attr_translation_key = "charging_release"
    _field = "charging_release"

    def __init__(self, coordinator: CharxCoordinator, charging_point: int) -> None:
        """Control the charging release of Charging Point ``charging_point``."""
        super().__init__(coordinator, charging_point, "charging_release")

    async def async_turn_on(self, **kwargs: Any) -> None:  # noqa: ARG002
        """Release charging."""
        await self._write(lambda: self._require_cp().set_charging_release(True), self.entity_id)

    async def async_turn_off(self, **kwargs: Any) -> None:  # noqa: ARG002
        """Withdraw the charging release."""
        await self._write(lambda: self._require_cp().set_charging_release(False), self.entity_id)


class CharxAvailabilitySwitch(CharxModbusReleaseSwitch):
    """Put the Charging Point in service, or into status F."""

    _attr_translation_key = "availability"
    _field = "available"

    def __init__(self, coordinator: CharxCoordinator, charging_point: int) -> None:
        """Control the availability of Charging Point ``charging_point``."""
        super().__init__(coordinator, charging_point, "availability")

    async def async_turn_on(self, **kwargs: Any) -> None:  # noqa: ARG002
        """Put the Charging Point in service."""
        await self._write(lambda: self._require_cp().set_available(True), self.entity_id)

    async def async_turn_off(self, **kwargs: Any) -> None:  # noqa: ARG002
        """Put the Charging Point into status F."""
        await self._write(lambda: self._require_cp().set_available(False), self.entity_id)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: CharxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the release and availability switches of every Charging Point."""
    coordinator = entry.runtime_data
    entities: list[SwitchEntity] = []
    for cp in coordinator.controller.charging_points:
        if cp.release_mode is not ReleaseMode.MODBUS:
            mode = "unread" if cp.release_mode is None else cp.release_mode.name
            _LOGGER.info(
                "%s: Charging Point %d is in release mode %s, so its charging release and "
                "availability switches are unavailable; they need release mode MODBUS",
                entry.title,
                cp.number,
                mode,
            )
        entities.append(CharxChargingReleaseSwitch(coordinator, cp.number))
        entities.append(CharxAvailabilitySwitch(coordinator, cp.number))
    async_add_entities(entities)
