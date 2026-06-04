"""Shared fixtures for haphoenixcontactcharx tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from aiophoenixcontactcharx import CharxData, DeviceInfo
from aiophoenixcontactcharx.models import (
    ChargingPointConfig,
    ChargingPointControl,
    ChargingPointData,
    ChargingPointStatus,
    ModemRegistration,
    ModemSignalQuality,
    ReleaseMode,
)

from custom_components.phoenixcontact_charx.const import DOMAIN


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Allow custom integrations to load in the test HA instance."""
    yield


# ---------------------------------------------------------------------------
# Fake data builders
# ---------------------------------------------------------------------------

def fake_device_info(**overrides) -> DeviceInfo:
    defaults = dict(
        designation="CHARX SEC-3000",
        software_version="1.9.0",
        mac_eth0="AA:BB:CC:DD:EE:FF",
        mac_eth1="AA:BB:CC:DD:EE:00",
        ip_eth0="192.168.1.100",
        ip_eth1="192.168.2.100",
        num_controllers=1,
        modem_registration=ModemRegistration.REGISTERED,
        modem_signal_quality=ModemSignalQuality.GOOD,
        num_non_critical_error=0,
        num_status_ef=0,
        num_status_a=1,
        num_status_bcd=0,
        num_charging=0,
        group_active_power_mw=0,
        group_reactive_power_mvar=0,
        group_apparent_power_mva=0,
        group_current_l1_ma=0,
        group_current_l2_ma=0,
        group_current_l3_ma=0,
        availability=True,
        dynamic_max_current_a=32,
    )
    defaults.update(overrides)
    return DeviceInfo(**defaults)


def fake_cp_data(
    charging_point: int = 1,
    vehicle_status: str = "A1",
    **status_overrides,
) -> ChargingPointData:
    status_defaults = dict(
        charging_point=charging_point,
        voltage_l1_mv=230_000,
        voltage_l2_mv=230_000,
        voltage_l3_mv=230_000,
        current_l1_ma=0,
        current_l2_ma=0,
        current_l3_ma=0,
        active_power_mw=0,
        reactive_power_mvar=0,
        apparent_power_mva=0,
        energy_active_wh=12_345_000,
        session_energy_wh=0,
        connection_time_s=0,
        charging_duration_s=0,
        error_code=0,
        setpoint_a=0,
        cable_capacity_a=32,
        vehicle_status=vehicle_status,
    )
    status_defaults.update(status_overrides)
    return ChargingPointData(
        charging_point=charging_point,
        config=ChargingPointConfig(
            charging_point=charging_point,
            max_current_cfg_a=32,
            release_mode=ReleaseMode.MODBUS,
        ),
        status=ChargingPointStatus(**status_defaults),
        control=ChargingPointControl(
            charging_point=charging_point,
            charging_release=False,
            max_current_a=16,
            available=True,
        ),
    )


def fake_charx_data(num_points: int = 1, **device_overrides) -> CharxData:
    return CharxData(
        device_info=fake_device_info(**device_overrides),
        charging_points=[fake_cp_data(cp) for cp in range(1, num_points + 1)],
    )


# ---------------------------------------------------------------------------
# Shared mock client fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_coordinator():
    """Patch only the coordinator's CharxClient (does not touch config_flow probing)."""
    with patch(
        "custom_components.phoenixcontact_charx.coordinator.CharxClient"
    ) as mock_cls:
        instance = mock_cls.return_value
        instance.fetch_data = AsyncMock(return_value=fake_charx_data())
        instance.disconnect = AsyncMock()
        instance.set_charging_release = AsyncMock()
        instance.set_max_current = AsyncMock()
        instance.set_availability = AsyncMock()
        instance.set_dynamic_max_current = AsyncMock()
        yield instance


@pytest.fixture
def mock_client():
    """Patch CharxClient in both config_flow and coordinator."""
    with patch(
        "custom_components.phoenixcontact_charx.config_flow._validate_and_probe",
        AsyncMock(return_value={
            "title": "CHARX SEC-3000",
            "mac": "AA:BB:CC:DD:EE:FF",
            "num_charging_points": 1,
        }),
    ), patch(
        "custom_components.phoenixcontact_charx.coordinator.CharxClient"
    ) as mock_cls:
        instance = mock_cls.return_value
        instance.fetch_data = AsyncMock(return_value=fake_charx_data())
        instance.disconnect = AsyncMock()
        instance.set_charging_release = AsyncMock()
        instance.set_max_current = AsyncMock()
        instance.set_availability = AsyncMock()
        instance.set_dynamic_max_current = AsyncMock()
        yield instance


# ---------------------------------------------------------------------------
# Pre-configured config entry fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def config_entry(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "host": "192.168.1.100",
            "port": 502,
            "mac": "AA:BB:CC:DD:EE:FF",
            "num_charging_points": 1,
        },
        unique_id="AA:BB:CC:DD:EE:FF",
        title="CHARX SEC-3000",
    )
    entry.add_to_hass(hass)
    return entry
