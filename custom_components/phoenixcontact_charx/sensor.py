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
from .values import error_code_hex, nullable_round, vehicle_status_key


# ---------------------------------------------------------------------------
# Group-level sensor descriptions
# ---------------------------------------------------------------------------

@dataclass(frozen=True, kw_only=True)
class CharxGroupSensorDescription(SensorEntityDescription):
    value_fn: Callable[[DeviceInfo], Any] = lambda _: None


GROUP_SENSORS: tuple[CharxGroupSensorDescription, ...] = (
    CharxGroupSensorDescription(
        key="group_active_power",
        translation_key="group_active_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=0,
        value_fn=lambda d: round(d.group_active_power_w, 1),
    ),
    CharxGroupSensorDescription(
        key="group_current_l1",
        translation_key="group_current_l1",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=2,
        value_fn=lambda d: nullable_round(d.group_current_l1_a, 2),
    ),
    CharxGroupSensorDescription(
        key="group_current_l2",
        translation_key="group_current_l2",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=2,
        value_fn=lambda d: nullable_round(d.group_current_l2_a, 2),
    ),
    CharxGroupSensorDescription(
        key="group_current_l3",
        translation_key="group_current_l3",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=2,
        value_fn=lambda d: nullable_round(d.group_current_l3_a, 2),
    ),
    CharxGroupSensorDescription(
        key="num_charging",
        translation_key="num_charging",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.num_charging,
    ),
    CharxGroupSensorDescription(
        key="num_connected",
        translation_key="num_connected",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.num_status_bcd,
    ),
    CharxGroupSensorDescription(
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
        value_fn=vehicle_status_key,
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
        value_fn=lambda cp: nullable_round(cp.status.current_l1_a, 2),
    ),
    CharxCpSensorDescription(
        key="current_l2",
        translation_key="current_l2",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=2,
        value_fn=lambda cp: nullable_round(cp.status.current_l2_a, 2),
    ),
    CharxCpSensorDescription(
        key="current_l3",
        translation_key="current_l3",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=2,
        value_fn=lambda cp: nullable_round(cp.status.current_l3_a, 2),
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
        state_class=SensorStateClass.TOTAL,
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
        value_fn=error_code_hex,
    ),
)


# ---------------------------------------------------------------------------
# Entity classes
# ---------------------------------------------------------------------------

class CharxGroupSensor(CharxEntity, SensorEntity):
    """Sensor for group-level data."""

    entity_description: CharxGroupSensorDescription

    def __init__(
        self,
        coordinator: Any,
        description: CharxGroupSensorDescription,
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
        cp_data = self._cp_data
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
        entities.append(CharxGroupSensor(coordinator, description))

    for cp in coordinator.charging_point_indices:
        for description in CP_SENSORS:
            entities.append(CharxCpSensor(coordinator, cp, description))

    async_add_entities(entities)
