"""Sensor data of the Renson Healthbox ventilation unit."""

from collections.abc import Callable
from dataclasses import dataclass

from pyhealthbox3.models import Healthbox3DataObject

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    REVOLUTIONS_PER_MINUTE,
    UnitOfElectricPotential,
    UnitOfPower,
    UnitOfPressure,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import RensonHealthboxConfigEntry
from .coordinator import RensonHealthboxCoordinator
from .entity import RensonHealthboxEntity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class RensonHealthboxGlobalSensorEntityDescription(SensorEntityDescription):
    """Describes AirGradient measurement sensor entity."""

    value_fn: Callable[[Healthbox3DataObject], StateType]


RENSON_GLOBAL_SENSOR_TYPES: tuple[RensonHealthboxGlobalSensorEntityDescription, ...] = (
    RensonHealthboxGlobalSensorEntityDescription(
        key="global_aqi",
        translation_key="global_aqi",
        native_unit_of_measurement=None,
        icon="mdi:leaf",
        device_class=SensorDeviceClass.AQI,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda x: x.global_aqi,
        suggested_display_precision=2,
    ),
    RensonHealthboxGlobalSensorEntityDescription(
        key="error_count",
        translation_key="error_count",
        native_unit_of_measurement=None,
        icon="mdi:alert-outline",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda x: x.error_count,
        suggested_display_precision=0,
    ),
    RensonHealthboxGlobalSensorEntityDescription(
        key="wifi_status",
        translation_key="wifi_status",
        icon="mdi:wifi",
        value_fn=lambda x: x.wifi.status,
    ),
    RensonHealthboxGlobalSensorEntityDescription(
        key="wifi_internet_connection",
        translation_key="wifi_internet_connection",
        native_unit_of_measurement=None,
        icon="mdi:web",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda x: x.wifi.internet_connection,
    ),
    RensonHealthboxGlobalSensorEntityDescription(
        key="wifi_ssid",
        translation_key="wifi_ssid",
        icon="mdi:wifi-settings",
        value_fn=lambda x: x.wifi.ssid if x.wifi.ssid != "" else "Not Available",
    ),
    RensonHealthboxGlobalSensorEntityDescription(
        key="fan_voltage",
        translation_key="fan_voltage",
        icon="mdi:sine-wave",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda x: x.fan.voltage,
        suggested_display_precision=2,
    ),
    RensonHealthboxGlobalSensorEntityDescription(
        key="fan_pressure",
        translation_key="fan_pressure",
        icon="mdi:arrow-collapse-vertical",
        native_unit_of_measurement=UnitOfPressure.PA,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda x: x.fan.pressure,
        suggested_display_precision=2,
    ),
    RensonHealthboxGlobalSensorEntityDescription(
        key="fan_flow",
        translation_key="fan_flow",
        icon="mdi:wind-power",
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda x: x.fan.flow,
        suggested_display_precision=2,
    ),
    RensonHealthboxGlobalSensorEntityDescription(
        key="fan_power",
        translation_key="fan_power",
        icon="mdi:flash",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda x: x.fan.power,
        suggested_display_precision=2,
    ),
    RensonHealthboxGlobalSensorEntityDescription(
        key="fan_rpm",
        translation_key="fan_rpm",
        icon="mdi:fan",
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda x: x.fan.rpm,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RensonHealthboxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up AirGradient sensor entities based on a config entry."""

    coordinator = entry.runtime_data
    listener: Callable[[], None] | None = None
    not_setup: set[RensonHealthboxGlobalSensorEntityDescription] = set(
        RENSON_GLOBAL_SENSOR_TYPES
    )

    @callback
    def add_entities() -> None:
        """Add new entities based on the latest data."""
        nonlocal not_setup, listener
        sensor_descriptions = not_setup
        not_setup = set()
        sensors = []

        for description in sensor_descriptions:
            if description.value_fn(coordinator.data.healthbox_data) is None:
                not_setup.add(description)
            else:
                sensors.append(RensonHealthboxGlobalSensor(coordinator, description))

        if sensors:
            async_add_entities(sensors)
        if not_setup:
            if not listener:
                listener = coordinator.async_add_listener(add_entities)
        elif listener:
            listener()

    add_entities()


class RensonHealthboxSensor(RensonHealthboxEntity, SensorEntity):
    """Defines an Renson Healthbox sensor."""

    def __init__(
        self,
        coordinator: RensonHealthboxCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize airgradient sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.serial_number}-{description.key}"


class RensonHealthboxGlobalSensor(RensonHealthboxSensor):
    """Defines an Renson Healthbox sensor."""

    entity_description: RensonHealthboxGlobalSensorEntityDescription

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data.healthbox_data)
