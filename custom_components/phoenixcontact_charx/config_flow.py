"""Config flow for Phoenix Contact CHARX integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT

from aiophoenixcontactcharx import CharxClient, CharxConnectionError, CharxError

from .const import (
    CONF_MAC,
    CONF_NUM_CHARGING_POINTS,
    DEFAULT_NUM_CHARGING_POINTS,
    DEFAULT_PORT,
    DOMAIN,
    MAX_CHARGING_POINTS,
)

_LOGGER = logging.getLogger(__name__)

_STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): vol.All(int, vol.Range(min=1, max=65535)),
    }
)


async def _validate_and_probe(host: str, port: int) -> dict[str, Any]:
    """Connect to the device, read basic info, and return data for the config entry."""
    async with CharxClient(host, port) as client:
        info = await client.get_device_info()
    return {
        "title": info.designation.strip() or f"CHARX @ {host}",
        "mac": info.mac_eth0,
        "num_charging_points": max(1, info.num_controllers),
    }


class CharxConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Phoenix Contact CHARX."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input[CONF_PORT]
            try:
                probed = await _validate_and_probe(host, port)
            except CharxConnectionError:
                errors["base"] = "cannot_connect"
            except CharxError:
                errors["base"] = "modbus_error"
            except Exception:
                _LOGGER.exception("Unexpected error probing %s:%d", host, port)
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(probed["mac"])
                self._abort_if_unique_id_configured(
                    updates={CONF_HOST: host, CONF_PORT: port}
                )
                return self.async_create_entry(
                    title=probed["title"],
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                        CONF_MAC: probed["mac"],
                        CONF_NUM_CHARGING_POINTS: min(
                            probed["num_charging_points"], MAX_CHARGING_POINTS
                        ),
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_STEP_USER_SCHEMA,
            errors=errors,
        )
