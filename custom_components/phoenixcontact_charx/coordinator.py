"""DataUpdateCoordinator for the Phoenix Contact CHARX integration."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from aiophoenixcontactcharx import CharxClient, CharxConnectionError, CharxData, CharxModbusError

from .const import CONF_NUM_CHARGING_POINTS, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class CharxCoordinator(DataUpdateCoordinator[CharxData]):
    """Coordinator that polls a CHARX controller on a fixed interval."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        self.client = CharxClient(
            host=config_entry.data[CONF_HOST],
            port=config_entry.data[CONF_PORT],
        )
        self.num_charging_points: int = config_entry.data[CONF_NUM_CHARGING_POINTS]
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
            config_entry=config_entry,
        )

    async def _async_update_data(self) -> CharxData:
        try:
            async with asyncio.timeout(30):
                return await self.client.fetch_data(self.num_charging_points)
        except CharxConnectionError as err:
            raise UpdateFailed(f"Cannot reach CHARX controller: {err}") from err
        except CharxModbusError as err:
            raise UpdateFailed(f"Modbus error from CHARX controller: {err}") from err
