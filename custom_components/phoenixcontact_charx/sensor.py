"""Sensor platform for Phoenix Contact CHARX integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

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

from .entity import CharxChargingPointEntity, CharxEntity
from .values import error_code_hex, nullable_round, vehicle_status_key

if TYPE_CHECKING:
    from aiophoenixcontactcharx import ChargingPoint, Group
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import CharxConfigEntry, CharxCoordinator


# ---------------------------------------------------------------------------
# Group-level sensor descriptions
# ---------------------------------------------------------------------------

@dataclass(frozen=True, kw_only=True)
class CharxGroupSensorDescription(SensorEntityDescription):
    value_fn: Callable[[Group], Any] = lambda _: None


GROUP_SENSORS: tuple[CharxGroupSensorDescription, ...] = (
    CharxGroupSensorDescription(
        key="group_active_power",
        translation_key="group_active_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=0,
        value_fn=lambda g: nullable_round(g.active_power, 1),
    ),
    CharxGroupSensorDescription(
        key="group_current_l1",
        translation_key="group_current_l1",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=2,
        value_fn=lambda g: nullable_round(g.current_l1, 2),
    ),
    CharxGroupSensorDescription(
        key="group_current_l2",
        translation_key="group_current_l2",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=2,
        value_fn=lambda g: nullable_round(g.current_l2, 2),
    ),
    CharxGroupSensorDescription(
        key="group_current_l3",
        translation_key="group_current_l3",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=2,
        value_fn=lambda g: nullable_round(g.current_l3, 2),
    ),
    CharxGroupSensorDescription(
        key="num_charging",
        translation_key="num_charging",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda g: g.charging,
    ),
    CharxGroupSensorDescription(
        key="num_connected",
        translation_key="num_connected",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda g: g.status_b_c_or_d,
    ),
    CharxGroupSensorDescription(
        key="dynamic_max_current",
        translation_key="dynamic_max_current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        value_fn=lambda g: g.dynamic_max_current,
    ),
)


# ---------------------------------------------------------------------------
# Per-charging-point sensor descriptions
# ---------------------------------------------------------------------------

@dataclass(frozen=True, kw_only=True)
class CharxCpSensorDescription(SensorEntityDescription):
    value_fn: Callable[[ChargingPoint], Any] = lambda _: None


CP_SENSORS: tuple[CharxCpSensorDescription, ...] = (
    CharxCpSensorDescription(
        key="vehicle_status",
        translation_key="vehicle_status",
        device_class=SensorDeviceClass.ENUM,
        options=["a1", "a2", "b1", "b2", "c1", "c2", "d1", "d2", "e0", "f0", "in"],
        value_fn=lambda cp: vehicle_status_key(cp.vehicle_status),
    ),
    CharxCpSensorDescription(
        key="voltage_l1",
        translation_key="voltage_l1",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=1,
        value_fn=lambda cp: nullable_round(cp.voltage_l1, 1),
    ),
    CharxCpSensorDescription(
        key="voltage_l2",
        translation_key="voltage_l2",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=1,
        value_fn=lambda cp: nullable_round(cp.voltage_l2, 1),
    ),
    CharxCpSensorDescription(
        key="voltage_l3",
        translation_key="voltage_l3",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=1,
        value_fn=lambda cp: nullable_round(cp.voltage_l3, 1),
    ),
    CharxCpSensorDescription(
        key="current_l1",
        translation_key="current_l1",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=2,
        value_fn=lambda cp: nullable_round(cp.current_l1, 2),
    ),
    CharxCpSensorDescription(
        key="current_l2",
        translation_key="current_l2",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=2,
        value_fn=lambda cp: nullable_round(cp.current_l2, 2),
    ),
    CharxCpSensorDescription(
        key="current_l3",
        translation_key="current_l3",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=2,
        value_fn=lambda cp: nullable_round(cp.current_l3, 2),
    ),
    CharxCpSensorDescription(
        key="active_power",
        translation_key="active_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=0,
        value_fn=lambda cp: nullable_round(cp.active_power, 1),
    ),
    CharxCpSensorDescription(
        key="reactive_power",
        translation_key="reactive_power",
        device_class=SensorDeviceClass.REACTIVE_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="var",
        suggested_display_precision=0,
        value_fn=lambda cp: nullable_round(cp.reactive_power, 1),
    ),
    CharxCpSensorDescription(
        key="apparent_power",
        translation_key="apparent_power",
        device_class=SensorDeviceClass.APPARENT_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="VA",
        suggested_display_precision=0,
        value_fn=lambda cp: nullable_round(cp.apparent_power, 1),
    ),
    CharxCpSensorDescription(
        key="total_energy",
        translation_key="total_energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=3,
        # The library reads a lifetime energy of 0 as None (#38).
        value_fn=lambda cp: nullable_round(cp.active_energy, 3),
    ),
    CharxCpSensorDescription(
        key="session_energy",
        translation_key="session_energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=3,
        value_fn=lambda cp: nullable_round(cp.session_energy, 3),
    ),
    CharxCpSensorDescription(
        key="current_setpoint",
        translation_key="current_setpoint",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        value_fn=lambda cp: cp.charging_current,
    ),
    CharxCpSensorDescription(
        key="max_current",
        translation_key="max_current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        value_fn=lambda cp: cp.max_current,
    ),
    CharxCpSensorDescription(
        key="connection_time",
        translation_key="connection_time",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        value_fn=lambda cp: cp.connection_time,
    ),
    CharxCpSensorDescription(
        key="error_code",
        translation_key="error_code",
        value_fn=lambda cp: error_code_hex(cp.error_code),
    ),
)


# ---------------------------------------------------------------------------
# Entity classes
# ---------------------------------------------------------------------------


class CharxGroupSensor(CharxEntity, SensorEntity):
    """A sensor of the Group, on the hub device."""

    entity_description: CharxGroupSensorDescription

    def __init__(
        self, coordinator: CharxCoordinator, description: CharxGroupSensorDescription
    ) -> None:
        """Show ``description`` of the Group."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:  # noqa: ANN401
        """The Group's value."""
        return self.entity_description.value_fn(self._group)


class CharxCpSensor(CharxChargingPointEntity, SensorEntity):
    """A sensor of one Charging Point."""

    entity_description: CharxCpSensorDescription

    def __init__(
        self,
        coordinator: CharxCoordinator,
        charging_point: int,
        description: CharxCpSensorDescription,
    ) -> None:
        """Show ``description`` of Charging Point ``charging_point``."""
        super().__init__(coordinator, charging_point, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:  # noqa: ANN401
        """The Charging Point's value; ``None`` while it isn't reported."""
        cp = self._cp
        return None if cp is None else self.entity_description.value_fn(cp)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: CharxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the Group's sensors and those of every Charging Point."""
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = [
        CharxGroupSensor(coordinator, description) for description in GROUP_SENSORS
    ]
    for cp in coordinator.controller.charging_points:
        entities.extend(
            CharxCpSensor(coordinator, cp.number, description) for description in CP_SENSORS
        )
    async_add_entities(entities)
