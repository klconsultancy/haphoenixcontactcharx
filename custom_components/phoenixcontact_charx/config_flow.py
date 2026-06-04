"""Config flow for Phoenix Contact CHARX integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

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

    def __init__(self) -> None:
        super().__init__()
        self._host: str = ""
        self._port: int = DEFAULT_PORT
        self._probed: dict[str, Any] = {}
        self._is_reconfigure: bool = False
        self._discovered_hostname: str = ""

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    async def _probe_or_error(
        self, host: str, port: int, errors: dict[str, str]
    ) -> dict[str, Any] | None:
        """Probe the device; populate errors on failure and return None."""
        try:
            return await _validate_and_probe(host, port)
        except CharxConnectionError:
            errors["base"] = "cannot_connect"
        except CharxError:
            errors["base"] = "modbus_error"
        except Exception:
            _LOGGER.exception("Unexpected error probing %s:%d", host, port)
            errors["base"] = "unknown"
        return None

    async def _finish_new_entry(self, probed: dict[str, Any]) -> ConfigFlowResult:
        """Create the config entry, or route to cap_confirm when the limit is exceeded."""
        if probed["num_charging_points"] > MAX_CHARGING_POINTS:
            self._probed = probed
            return await self.async_step_cap_confirm()
        return self.async_create_entry(
            title=probed["title"],
            data={
                CONF_HOST: self._host,
                CONF_PORT: self._port,
                CONF_MAC: probed["mac"],
                CONF_NUM_CHARGING_POINTS: probed["num_charging_points"],
            },
        )

    # ------------------------------------------------------------------
    # Flow steps
    # ------------------------------------------------------------------

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input[CONF_PORT]
            probed = await self._probe_or_error(host, port, errors)
            if probed is not None:
                await self.async_set_unique_id(probed["mac"])
                self._abort_if_unique_id_configured(
                    updates={CONF_HOST: host, CONF_PORT: port}
                )
                self._host, self._port = host, port
                return await self._finish_new_entry(probed)

        return self.async_show_form(
            step_id="user",
            data_schema=_STEP_USER_SCHEMA,
            errors=errors,
        )

    async def async_step_cap_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if not self._probed:
            return await self.async_step_user()
        if user_input is not None:
            if self._is_reconfigure:
                entry = self._get_reconfigure_entry()
                return self.async_update_reload_and_abort(
                    entry,
                    data={
                        **entry.data,
                        CONF_HOST: self._host,
                        CONF_PORT: self._port,
                        CONF_NUM_CHARGING_POINTS: MAX_CHARGING_POINTS,
                    },
                )
            return self.async_create_entry(
                title=self._probed["title"],
                data={
                    CONF_HOST: self._host,
                    CONF_PORT: self._port,
                    CONF_MAC: self._probed["mac"],
                    CONF_NUM_CHARGING_POINTS: MAX_CHARGING_POINTS,
                },
            )
        return self.async_show_form(
            step_id="cap_confirm",
            data_schema=vol.Schema({}),
            description_placeholders={
                "detected": str(self._probed["num_charging_points"]),
                "cap": str(MAX_CHARGING_POINTS),
            },
        )

    async def async_step_dhcp(self, discovery_info: DhcpServiceInfo) -> ConfigFlowResult:
        # DhcpServiceInfo.macaddress is guaranteed lowercase-no-colons by HA's DHCP scanner.
        # Normalize to uppercase-with-colons to match info.mac_eth0 from the library.
        mac = ":".join(discovery_info.macaddress[i:i + 2].upper() for i in range(0, 12, 2))
        await self.async_set_unique_id(mac)
        self._abort_if_unique_id_configured(updates={CONF_HOST: discovery_info.ip})
        self._host = discovery_info.ip
        self._port = DEFAULT_PORT
        self._discovered_hostname = discovery_info.hostname
        return await self.async_step_dhcp_confirm()

    async def async_step_dhcp_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if not self._host:
            return await self.async_step_user()
        errors: dict[str, str] = {}
        if user_input is not None:
            probed = await self._probe_or_error(self._host, self._port, errors)
            if probed is not None:
                return await self._finish_new_entry(probed)
        return self.async_show_form(
            step_id="dhcp_confirm",
            data_schema=vol.Schema({}),
            description_placeholders={
                "host": self._host,
                "hostname": self._discovered_hostname or self._host,
            },
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input.get(CONF_PORT, entry.data.get(CONF_PORT, DEFAULT_PORT))
            probed = await self._probe_or_error(host, port, errors)
            if probed is not None:
                if probed["mac"] != entry.data[CONF_MAC]:
                    errors["base"] = "wrong_device"
                elif probed["num_charging_points"] > MAX_CHARGING_POINTS:
                    self._host, self._port = host, port
                    self._probed = probed
                    self._is_reconfigure = True
                    return await self.async_step_cap_confirm()
                else:
                    return self.async_update_reload_and_abort(
                        entry,
                        data={
                            **entry.data,
                            CONF_HOST: host,
                            CONF_PORT: port,
                            CONF_NUM_CHARGING_POINTS: probed["num_charging_points"],
                        },
                    )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=entry.data[CONF_HOST]): str,
                    vol.Optional(CONF_PORT, default=entry.data[CONF_PORT]): vol.All(
                        int, vol.Range(min=1, max=65535)
                    ),
                }
            ),
            errors=errors,
        )
