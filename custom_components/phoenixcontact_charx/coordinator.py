"""The coordinator that reads the whole Charging Controller."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from modbus_connection.exceptions import ModbusError
from modbus_connection.model import UpdateReport

from .const import CONF_MAC, DEFAULT_SCAN_INTERVAL, DOMAIN

if TYPE_CHECKING:
    from aiophoenixcontactcharx import CharxController
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

type CharxConfigEntry = ConfigEntry[CharxCoordinator]


class CharxCoordinator(DataUpdateCoordinator[UpdateReport]):
    """Read the controller; the report names the parts that failed.

    A part is the controller's identity (``device_info``), its ``group`` or one
    Charging Point (``charging_point_N``). A failed part keeps its last values, and only
    its entities are unavailable.
    """

    config_entry: CharxConfigEntry
    hub_device_id: str

    def __init__(
        self, hass: HomeAssistant, entry: CharxConfigEntry, controller: CharxController
    ) -> None:
        """Poll ``controller`` for ``entry``."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.controller = controller
        self._failing: set[str] = set()

    @property
    def device_id(self) -> str:
        """The identifier of the hub device: the MAC address, or the host before 1.0."""
        return self.config_entry.data.get(CONF_MAC, self.config_entry.data[CONF_HOST])

    async def _async_update_data(self) -> UpdateReport:
        try:
            report = await self.controller.async_update()
        except ModbusError as err:
            # A dead link or a timeout; a failure within one part is in the report.
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="update_failed",
                translation_placeholders={"error": str(err)},
            ) from err
        if not report.updated:
            raise UpdateFailed(
                translation_domain=DOMAIN, translation_key="nothing_answered"
            ) from ExceptionGroup("every part failed", list(report.failed.values()))
        self._log_changes(report)
        return report

    def _log_changes(self, report: UpdateReport) -> None:
        """Log a part when it starts failing and when it answers again."""
        for name, error in report.failed.items():
            if name not in self._failing:
                _LOGGER.warning(
                    "%s: %s failed to refresh; its entities are unavailable: %s",
                    self.config_entry.title,
                    name,
                    error,
                )
        for name in self._failing - set(report.failed):
            _LOGGER.info("%s: %s is available again", self.config_entry.title, name)
        self._failing = set(report.failed)
