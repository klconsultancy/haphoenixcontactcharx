"""Sensor platform for Phoenix Contact CHARX integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from aiophoenixcontactcharx import CharxData, ChargingPointData, DeviceInfo

from . import CharxConfigEntry
from .entity import CharxChargingPointEntity, CharxEntity


# ---------------------------------------------------------------------------
# Global (group-level) sensor descriptions
# ---------------------------------------------------------------------------

@dataclass(frozen=True, kw_only=True)
class CharxGlobalSensorDescription(SensorEntityDescription):
    value_fn: Callable[[DeviceInfo], Any] = lambda _: None


GROUP_SENSORS: tuple[CharxGlobalSensorDescription, ...] = (
    CharxGlobalSensorDescription(
        key="group_active_power",
        translation_key="group_active_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=0,
        value_fn=lambda d: round(d.group_active_power_w, 1),
    ),
    CharxGlobalSensorDescription(
        key="group_current_l1",
        translation_key="group_current_l1",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=2,
        value_fn=lambda d: round(d.group_current_l1_a, 2) if d.group_current_l1_a is not None else None,
    ),
    CharxGlobalSensorDescription(
        key="group_current_l2",
        translation_key="group_current_l2",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=2,
        value_fn=lambda d: round(d.group_current_l2_a, 2) if d.group_current_l2_a is not None else None,
    ),
    CharxGlobalSensorDescription(
        key="group_current_l3",
        translation_key="group_current_l3",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=2,
        value_fn=lambda d: round(d.group_current_l3_a, 2) if d.group_current_l3_a is not None else None,
    ),
    CharxGlobalSensorDescription(
        key="num_charging",
        translation_key="num_charging",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.num_charging,
    ),
    CharxGlobalSensorDescription(
        key="num_connected",
        translation_key="num_connected",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.num_status_bcd,
    ),
    CharxGlobalSensorDescription(
        key="dynamic_max_current",
        translation_key="dynamic_max_current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        value_fn=lambda d: d.dynamic_max_current_a,
    ),
)


# ---------------------------------------------------------------------------
# Per-charging-point sensor descriptions
# ---------------------------------------------------------------------------

@dataclass(frozen=True, kw_only=True)
class CharxCpSensorDescription(SensorEntityDescription):
    value_fn: Callable[[ChargingPointData], Any] = lambda _: None


CP_SENSORS: tuple[CharxCpSensorDescription, ...] = (
    CharxCpSensorDescription(
        key="vehicle_status",
        translation_key="vehicle_status",
        device_class=SensorDeviceClass.ENUM,
        options=["a1", "a2", "b1", "b2", "c1", "c2", "e0", "f0", "in"],
        value_fn=lambda cp: cp.status.vehicle_status.lower() if cp.status.vehicle_status else None,
    ),
    CharxCpSensorDescription(
        key="voltage_l1",
        translation_key="voltage_l1",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=1,
        value_fn=lambda cp: round(cp.status.voltage_l1_v, 1),
    ),
    CharxCpSensorDescription(
        key="voltage_l2",
        translation_key="voltage_l2",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=1,
        value_fn=lambda cp: round(cp.status.voltage_l2_v, 1),
    ),
    CharxCpSensorDescription(
        key="voltage_l3",
        translation_key="voltage_l3",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=1,
        value_fn=lambda cp: round(cp.status.voltage_l3_v, 1),
    ),
    CharxCpSensorDescription(
        key="current_l1",
        translation_key="current_l1",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=2,
        value_fn=lambda cp: round(cp.status.current_l1_a, 2) if cp.status.current_l1_a is not None else None,
    ),
    CharxCpSensorDescription(
        key="current_l2",
        translation_key="current_l2",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=2,
        value_fn=lambda cp: round(cp.status.current_l2_a, 2) if cp.status.current_l2_a is not None else None,
    ),
    CharxCpSensorDescription(
        key="current_l3",
        translation_key="current_l3",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=2,
        value_fn=lambda cp: round(cp.status.current_l3_a, 2) if cp.status.current_l3_a is not None else None,
    ),
    CharxCpSensorDescription(
        key="active_power",
        translation_key="active_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=0,
        value_fn=lambda cp: round(cp.status.active_power_w, 1),
    ),
    CharxCpSensorDescription(
        key="reactive_power",
        translation_key="reactive_power",
        device_class=SensorDeviceClass.REACTIVE_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="var",
        suggested_display_precision=0,
        value_fn=lambda cp: round(cp.status.reactive_power_var, 1),
    ),
    CharxCpSensorDescription(
        key="apparent_power",
        translation_key="apparent_power",
        device_class=SensorDeviceClass.APPARENT_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="VA",
        suggested_display_precision=0,
        value_fn=lambda cp: round(cp.status.apparent_power_va, 1),
    ),
    CharxCpSensorDescription(
        key="total_energy",
        translation_key="total_energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=3,
        value_fn=lambda cp: round(cp.status.energy_active_kwh, 3),
    ),
    CharxCpSensorDescription(
        key="session_energy",
        translation_key="session_energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=3,
        value_fn=lambda cp: round(cp.status.session_energy_kwh, 3),
    ),
    CharxCpSensorDescription(
        key="current_setpoint",
        translation_key="current_setpoint",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        value_fn=lambda cp: cp.status.setpoint_a,
    ),
    CharxCpSensorDescription(
        key="max_current",
        translation_key="max_current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        value_fn=lambda cp: cp.control.max_current_a,
    ),
    CharxCpSensorDescription(
        key="connection_time",
        translation_key="connection_time",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        value_fn=lambda cp: cp.status.connection_time_s,
    ),
    CharxCpSensorDescription(
        key="error_code",
        translation_key="error_code",
        value_fn=lambda cp: f"0x{cp.status.error_code:08X}" if cp.status.error_code else "0x00000000",
    ),
)


# ---------------------------------------------------------------------------
# Entity classes
# ---------------------------------------------------------------------------

class CharxGlobalSensor(CharxEntity, SensorEntity):
    """Sensor for group-level data."""

    entity_description: CharxGlobalSensorDescription

    def __init__(
        self,
        coordinator: Any,
        description: CharxGlobalSensorDescription,
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data.device_info)


class CharxCpSensor(CharxChargingPointEntity, SensorEntity):
    """Sensor for per-charging-point data."""

    entity_description: CharxCpSensorDescription

    def __init__(
        self,
        coordinator: Any,
        charging_point: int,
        description: CharxCpSensorDescription,
    ) -> None:
        super().__init__(coordinator, charging_point, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        cp_data = next(
            (cp for cp in self.coordinator.data.charging_points
             if cp.charging_point == self._charging_point),
            None,
        )
        if cp_data is None:
            return None
        return self.entity_description.value_fn(cp_data)


# ---------------------------------------------------------------------------
# Platform setup
# ---------------------------------------------------------------------------

async def async_setup_entry(
    hass: HomeAssistant,
    entry: CharxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = []

    for description in GROUP_SENSORS:
        entities.append(CharxGlobalSensor(coordinator, description))

    for cp in range(1, coordinator.num_charging_points + 1):
        for description in CP_SENSORS:
            entities.append(CharxCpSensor(coordinator, cp, description))

    async_add_entities(entities)
