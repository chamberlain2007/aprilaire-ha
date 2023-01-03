from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass, StateType

from homeassistant.const import (
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    PERCENTAGE,
)

from . import AprilaireCoordinator
from .const import DOMAIN
from .entity import BaseAprilaireEntity

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add climates for passed config_entry in HA."""

    coordinator: AprilaireCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    if not await coordinator.wait_for_ready():
        return
    
    entities = [
        AprilaireIndoorHumidityControllingSensor(coordinator),
        AprilaireOutdoorHumidityControllingSensor(coordinator),
        AprilaireIndoorTemperatureControllingSensor(coordinator),
        AprilaireOutdoorTemperatureControllingSensor(coordinator),
    ]

    async_add_entities(entities)


class AprilaireIndoorHumidityControllingSensor(BaseAprilaireEntity, SensorEntity):
    @property
    def available(self):
        return super().available and self._data.get("indoor_humidity_controlling_sensor_status", None) == 0

    @property
    def name(self) -> str | None:
        return "Aprilaire Indoor Humidity Controlling Sensor"

    @property
    def device_class(self) -> str | None:
        return SensorDeviceClass.HUMIDITY
    
    @property
    def state_class(self) -> SensorStateClass | str | None:
        return SensorStateClass.MEASUREMENT
    
    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        return self._data["indoor_humidity_controlling_sensor_value"]

    @property
    def native_unit_of_measurement(self) -> str | None:
        return PERCENTAGE

class AprilaireOutdoorHumidityControllingSensor(BaseAprilaireEntity, SensorEntity):
    @property
    def available(self):
        return super().available and self._data.get("outdoor_humidity_controlling_sensor_status", None) == 0

    @property
    def name(self) -> str | None:
        return "Aprilaire Outdoor Humidity Controlling Sensor"

    @property
    def device_class(self) -> str | None:
        return SensorDeviceClass.HUMIDITY
    
    @property
    def state_class(self) -> SensorStateClass | str | None:
        return SensorStateClass.MEASUREMENT
    
    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        return self._data["outdoor_humidity_controlling_sensor_value"]

    @property
    def native_unit_of_measurement(self) -> str | None:
        return PERCENTAGE

class BaseAprilaireTemperatureSensor(SensorEntity):
    @property
    def device_class(self) -> str | None:
        return SensorDeviceClass.TEMPERATURE
    
    @property
    def state_class(self) -> SensorStateClass | str | None:
        return SensorStateClass.MEASUREMENT

    @property
    def safe_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement of the entity, after unit conversion. Uses custom logic for native unit of measurement."""
        # Highest priority, for registered entities: unit set by user, with fallback to unit suggested
        # by integration or secondary fallback to unit conversion rules
        if self._sensor_option_unit_of_measurement:
            return self._sensor_option_unit_of_measurement

        # Second priority, for non registered entities: unit suggested by integration
        if not self.registry_entry and self.suggested_unit_of_measurement:
            return self.suggested_unit_of_measurement

        # Third priority: Legacy temperature conversion, which applies
        # to both registered and non registered entities
        return self.hass.config.units.temperature_unit

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        unit_of_measurement = self.hass.config.units.temperature_unit

        sensor_value = self.get_native_value()

        if sensor_value is None:
            return None

        if unit_of_measurement == TEMP_FAHRENHEIT:
            return round(sensor_value * 9 / 5 + 32)
        
        return sensor_value

    @property
    def native_unit_of_measurement(self) -> str | None:
        unit_of_measurement = self.safe_unit_of_measurement

        if unit_of_measurement == TEMP_FAHRENHEIT:
            return TEMP_FAHRENHEIT

        return TEMP_CELSIUS

    def get_native_value(self):
        return None

class AprilaireIndoorTemperatureControllingSensor(
    BaseAprilaireEntity,
    BaseAprilaireTemperatureSensor,
    SensorEntity):
    @property
    def available(self):
        return super().available and self._data.get("indoor_temperature_controlling_sensor_status", None) == 0

    @property
    def name(self) -> str | None:
        return "Aprilaire Indoor Temperature Controlling Sensor"

    def get_native_value(self):
        return self._data.get("indoor_temperature_controlling_sensor_value")

class AprilaireOutdoorTemperatureControllingSensor(
    BaseAprilaireEntity,
    BaseAprilaireTemperatureSensor,
    SensorEntity):
    @property
    def available(self):
        return super().available and self._data.get("outdoor_temperature_controlling_sensor_status", None) == 0

    @property
    def name(self) -> str | None:
        return "Aprilaire Outdoor Temperature Controlling Sensor"

    def get_native_value(self):
        return self._data.get("outdoor_temperature_controlling_sensor_value")