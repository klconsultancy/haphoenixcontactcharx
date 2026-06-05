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

from .const import CONF_MAC, CONF_NUM_CHARGING_POINTS, DEFAULT_POLL_TIMEOUT, DEFAULT_SCAN_INTERVAL, DOMAIN

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

    @property
    def device_id(self) -> str:
        return self.config_entry.data.get(CONF_MAC, self.config_entry.data[CONF_HOST])

    @property
    def charging_point_indices(self) -> range:
        return range(1, self.num_charging_points + 1)

    async def _async_update_data(self) -> CharxData:
        try:
            async with asyncio.timeout(DEFAULT_POLL_TIMEOUT):
                return await self.client.fetch_data(self.num_charging_points)
        except CharxConnectionError as err:
            raise UpdateFailed(f"Cannot reach CHARX controller: {err}") from err
        except CharxModbusError as err:
            raise UpdateFailed(f"Modbus error from CHARX controller: {err}") from err
        except TimeoutError as err:
            raise UpdateFailed(f"Timeout polling CHARX controller after {DEFAULT_POLL_TIMEOUT}s") from err
