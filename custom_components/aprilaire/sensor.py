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

    entities = [
    ]

    if coordinator.data.get("indoor_humidity_controlling_sensor_status") != 3:
        entities.append(AprilaireIndoorHumidityControllingSensor(coordinator))

    if coordinator.data.get("outdoor_humidity_controlling_sensor_status") != 3:
        entities.append(AprilaireOutdoorHumidityControllingSensor(coordinator))

    if coordinator.data.get("indoor_temperature_controlling_sensor_status") != 3:
        entities.append(AprilaireIndoorTemperatureControllingSensor(coordinator))

    if coordinator.data.get("outdoor_temperature_controlling_sensor_status") != 3:
        entities.append(AprilaireOutdoorTemperatureControllingSensor(coordinator))

    if coordinator.data.get('dehumidification_available') == 1:
        entities.append(AprilaireDehumidificationStatusSensor(coordinator))

    if coordinator.data.get('humidification_available') == 1:
        entities.append(AprilaireHumidificationStatusSensor(coordinator))

    if coordinator.data.get('ventilation_available') == 1:
        entities.append(AprilaireVentilationStatusSensor(coordinator))

    if coordinator.data.get('air_cleaning_available') == 1:
        entities.append(AprilaireAirCleaningStatusSensor(coordinator))

    async_add_entities(entities)


class AprilaireIndoorHumidityControllingSensor(BaseAprilaireEntity, SensorEntity):
    @property
    def available(self):
        return super().available and self._coordinator.data.get("indoor_humidity_controlling_sensor_status", None) == 0

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
        return self._coordinator.data["indoor_humidity_controlling_sensor_value"]

    @property
    def native_unit_of_measurement(self) -> str | None:
        return PERCENTAGE

class AprilaireOutdoorHumidityControllingSensor(BaseAprilaireEntity, SensorEntity):
    @property
    def available(self):
        return super().available and self._coordinator.data.get("outdoor_humidity_controlling_sensor_status", None) == 0

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
        return self._coordinator.data["outdoor_humidity_controlling_sensor_value"]

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
        return super().available and self._coordinator.data.get("indoor_temperature_controlling_sensor_status", None) == 0

    @property
    def name(self) -> str | None:
        return "Aprilaire Indoor Temperature Controlling Sensor"

    def get_native_value(self):
        return self._coordinator.data.get("indoor_temperature_controlling_sensor_value")

class AprilaireOutdoorTemperatureControllingSensor(
    BaseAprilaireEntity,
    BaseAprilaireTemperatureSensor,
    SensorEntity):
    @property
    def available(self):
        return super().available and self._coordinator.data.get("outdoor_temperature_controlling_sensor_status", None) == 0

    @property
    def name(self) -> str | None:
        return "Aprilaire Outdoor Temperature Controlling Sensor"

    def get_native_value(self):
        return self._coordinator.data.get("outdoor_temperature_controlling_sensor_value")

class AprilaireDehumidificationStatusSensor(BaseAprilaireEntity, SensorEntity):
    @property
    def available(self):
        return super().available and "dehumidification_status" in self._coordinator.data

    @property
    def name(self) -> str | None:
        return "Aprilaire Dehumidification Status"

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        dehumidification_status = self._coordinator.data.get("dehumidification_status")

        dehumidification_status_map = {
            0: "Idle",
            1: "Idle",
            2: "On",
            3: "On",
            4: "Off",
        }

        return dehumidification_status_map.get(dehumidification_status)

class AprilaireHumidificationStatusSensor(BaseAprilaireEntity, SensorEntity):
    @property
    def available(self):
        return super().available and "humidification_status" in self._coordinator.data

    @property
    def name(self) -> str | None:
        return "Aprilaire Humidification Status"

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        humidification_status = self._coordinator.data.get("humidification_status")

        humidification_status_map = {
            0: "Idle",
            1: "Idle",
            2: "On",
            3: "Off",
        }

        return humidification_status_map.get(humidification_status)

class AprilaireVentilationStatusSensor(BaseAprilaireEntity, SensorEntity):
    @property
    def available(self):
        return super().available and "ventilation_status" in self._coordinator.data

    @property
    def name(self) -> str | None:
        return "Aprilaire Ventilation Status"

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        ventilation_status = self._coordinator.data.get("ventilation_status")

        ventilation_status_map = {
            0: "Idle",
            1: "Idle",
            2: "On",
            3: "Idle",
            4: "Idle",
            5: "Idle",
            6: "Off",
        }

        return ventilation_status_map.get(ventilation_status)

class AprilaireAirCleaningStatusSensor(BaseAprilaireEntity, SensorEntity):
    @property
    def available(self):
        return super().available and "air_cleaning_status" in self._coordinator.data

    @property
    def name(self) -> str | None:
        return "Aprilaire Air Cleaning Status"

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        air_cleaning_status = self._coordinator.data.get("air_cleaning_status")

        air_cleaning_status_map = {
            0: "Idle",
            1: "Idle",
            2: "On",
            3: "Off",
        }

        return air_cleaning_status_map.get(air_cleaning_status)