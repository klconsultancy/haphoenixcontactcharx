"""The base of every CHARX entity."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiophoenixcontactcharx import CharxError, charging_point_name
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from modbus_connection.exceptions import ModbusError

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import CharxCoordinator

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aiophoenixcontactcharx import ChargingPoint, Group


class CharxEntity(CoordinatorEntity[CharxCoordinator]):
    """An entity of the hub device, showing the Group.

    Its unique ID is ``{mac}_{suffix}``, as in 1.x.
    """

    _attr_has_entity_name = True
    # The part of the controller whose values the entity shows.
    _part = "group"

    def __init__(self, coordinator: CharxCoordinator, unique_suffix: str) -> None:
        """Show part of the hub, under ``unique_suffix``."""
        super().__init__(coordinator)
        mac = coordinator.device_id
        self._attr_unique_id = f"{mac}_{unique_suffix}"
        # The setup registers the hub and keeps its details current.
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, mac)})

    @property
    def _group(self) -> Group:
        return self.coordinator.controller.group

    @property
    def available(self) -> bool:
        """Unavailable while the entity's part fails to refresh."""
        return super().available and self._part not in self.coordinator.data.failed

    async def _write(self, write: Callable[[], Awaitable[Any]], what: str) -> None:
        """Run a library write and refresh; raise a ``HomeAssistantError`` if it fails.

        The library rejects a bad value (``TypeError``, ``ValueError``), a write the
        release mode doesn't allow, or one the controller doesn't apply (``CharxError``),
        and Modbus failures (``ModbusError``).
        """
        try:
            await write()
        except (CharxError, ModbusError, TypeError, ValueError) as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="write_failed",
                translation_placeholders={"what": what, "error": str(err)},
            ) from err
        # The library read the part back until the write landed, so its values are
        # current: show them now rather than after the (debounced) refresh.
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()


class CharxChargingPointEntity(CharxEntity):
    """An entity of one Charging Point's device.

    Its unique ID is ``{mac}_cp{n}_{suffix}``, as in 1.x.
    """

    def __init__(
        self, coordinator: CharxCoordinator, charging_point: int, unique_suffix: str
    ) -> None:
        """Show part of Charging Point ``charging_point``, under ``unique_suffix``."""
        super().__init__(coordinator, f"cp{charging_point}_{unique_suffix}")
        self._charging_point = charging_point
        self._part = charging_point_name(charging_point)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{coordinator.device_id}_cp{charging_point}")},
            name=f"Charging Point {charging_point}",
            manufacturer=MANUFACTURER,
            model=MODEL,
            via_device_id=coordinator.hub_device_id,
        )

    @property
    def _cp(self) -> ChargingPoint | None:
        """The Charging Point, looked up on every use: the library may replace it.

        ``None`` if the controller no longer reports it (fewer Charging Controllers than
        the entry had).
        """
        cp: ChargingPoint | None = getattr(self.coordinator.controller, self._part, None)
        return cp

    @property
    def available(self) -> bool:
        """Unavailable while the Charging Point fails to refresh or isn't reported."""
        return super().available and self._cp is not None

    def _require_cp(self) -> ChargingPoint:
        """The Charging Point, for a write; raise if the controller doesn't report it."""
        cp = self._cp
        if cp is None:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="charging_point_missing",
                translation_placeholders={"number": str(self._charging_point)},
            )
        return cp
