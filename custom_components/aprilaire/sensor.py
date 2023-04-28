"""The Aprilaire sensor component"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import UNDEFINED

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
    StateType,
)

from homeassistant.const import (
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    PERCENTAGE,
)

from pyaprilaire.const import Attribute

from .const import DOMAIN
from .coordinator import AprilaireCoordinator
from .entity import BaseAprilaireEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add climates for passed config_entry in HA."""

    coordinator: AprilaireCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []

    if (
        coordinator.data.get(Attribute.INDOOR_HUMIDITY_CONTROLLING_SENSOR_STATUS, 3)
        != 3
    ):
        entities.append(AprilaireIndoorHumidityControllingSensor(coordinator))

    if (
        coordinator.data.get(Attribute.OUTDOOR_HUMIDITY_CONTROLLING_SENSOR_STATUS, 3)
        != 3
    ):
        entities.append(AprilaireOutdoorHumidityControllingSensor(coordinator))

    if (
        coordinator.data.get(Attribute.INDOOR_TEMPERATURE_CONTROLLING_SENSOR_STATUS, 3)
        != 3
    ):
        entities.append(AprilaireIndoorTemperatureControllingSensor(coordinator))

    if (
        coordinator.data.get(Attribute.OUTDOOR_TEMPERATURE_CONTROLLING_SENSOR_STATUS, 3)
        != 3
    ):
        entities.append(AprilaireOutdoorTemperatureControllingSensor(coordinator))

    if coordinator.data.get(Attribute.DEHUMIDIFICATION_AVAILABLE) == 1:
        entities.append(AprilaireDehumidificationStatusSensor(coordinator))

    if (
        coordinator.data.get(Attribute.HUMIDIFICATION_AVAILABLE) == 1
        or coordinator.data.get(Attribute.HUMIDIFICATION_AVAILABLE) == 2
    ):
        entities.append(AprilaireHumidificationStatusSensor(coordinator))

    if coordinator.data.get(Attribute.VENTILATION_AVAILABLE) == 1:
        entities.append(AprilaireVentilationStatusSensor(coordinator))

    if coordinator.data.get(Attribute.AIR_CLEANING_AVAILABLE) == 1:
        entities.append(AprilaireAirCleaningStatusSensor(coordinator))

    async_add_entities(entities)


class BaseAprilaireHumiditySensor(SensorEntity):
    """Base for Aprilaire humidity sensors"""

    @property
    def device_class(self) -> str | None:
        return SensorDeviceClass.HUMIDITY

    @property
    def state_class(self) -> SensorStateClass | str | None:
        return SensorStateClass.MEASUREMENT

    @property
    def native_unit_of_measurement(self) -> str | None:
        return PERCENTAGE


class AprilaireIndoorHumidityControllingSensor(
    BaseAprilaireEntity, BaseAprilaireHumiditySensor, SensorEntity
):
    """Sensor for indoor humidity"""

    @property
    def available(self):
        return (
            super().available
            and self._coordinator.data.get(
                Attribute.INDOOR_HUMIDITY_CONTROLLING_SENSOR_STATUS
            )
            == 0
        )

    @property
    def entity_name(self) -> str | None:
        return "Indoor Humidity Controlling Sensor"

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        return self._coordinator.data.get(
            Attribute.INDOOR_HUMIDITY_CONTROLLING_SENSOR_VALUE
        )

    @property
    def extra_state_attributes(self):
        return super().extra_state_attributes | {
            "status": self._coordinator.data.get(
                Attribute.INDOOR_HUMIDITY_CONTROLLING_SENSOR_STATUS
            ),
            "raw_sensor_value": self._coordinator.data.get(
                Attribute.INDOOR_HUMIDITY_CONTROLLING_SENSOR_VALUE
            ),
        }


class AprilaireOutdoorHumidityControllingSensor(
    BaseAprilaireEntity, BaseAprilaireHumiditySensor, SensorEntity
):
    """Sensor for outdoor humidity"""

    @property
    def available(self):
        return (
            super().available
            and self._coordinator.data.get(
                Attribute.OUTDOOR_HUMIDITY_CONTROLLING_SENSOR_STATUS
            )
            == 0
        )

    @property
    def entity_name(self) -> str | None:
        return "Outdoor Humidity Controlling Sensor"

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        return self._coordinator.data.get(
            Attribute.OUTDOOR_HUMIDITY_CONTROLLING_SENSOR_VALUE
        )

    @property
    def extra_state_attributes(self):
        return super().extra_state_attributes | {
            "status": self._coordinator.data.get(
                Attribute.OUTDOOR_HUMIDITY_CONTROLLING_SENSOR_STATUS
            ),
            "raw_sensor_value": self._coordinator.data.get(
                Attribute.OUTDOOR_HUMIDITY_CONTROLLING_SENSOR_VALUE
            ),
        }


class BaseAprilaireTemperatureSensor(BaseAprilaireEntity, SensorEntity):
    """Base for Aprilaire temperature sensors"""

    @property
    def device_class(self) -> str | None:
        return SensorDeviceClass.TEMPERATURE

    @property
    def state_class(self) -> SensorStateClass | str | None:
        return SensorStateClass.MEASUREMENT

    @property
    def safe_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement of the entity, after unit conversion.
        Uses custom logic for native unit of measurement."""

        # Highest priority, for registered entities: unit set by user, with fallback
        # by integration or secondary fallback to unit conversion rules
        if self._sensor_option_unit_of_measurement != UNDEFINED:
            return self._sensor_option_unit_of_measurement

        # Second priority, for non registered entities: unit suggested by integration
        if not self.registry_entry and self.suggested_unit_of_measurement:
            return self.suggested_unit_of_measurement

        # Third priority: Legacy temperature conversion, which applies
        # to both registered and non registered entities
        return self.hass.config.units.temperature_unit

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        unit_of_measurement = self.safe_unit_of_measurement

        sensor_value = self.get_native_value()  # pylint: disable=assignment-from-none

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

    def get_native_value(self) -> float:
        """Get the native value (implemented in derived classes)"""
        return None

    @property
    def extra_state_attributes(self):
        return super().extra_state_attributes | {
            "safe_unit_of_measurement": self.safe_unit_of_measurement,
            "native_unit_of_measurement": self.native_unit_of_measurement,
        }


class AprilaireIndoorTemperatureControllingSensor(
    BaseAprilaireTemperatureSensor, SensorEntity
):
    """Sensor for indoor temperature"""

    @property
    def available(self):
        return (
            super().available
            and self._coordinator.data.get(
                Attribute.INDOOR_TEMPERATURE_CONTROLLING_SENSOR_STATUS
            )
            == 0
        )

    @property
    def entity_name(self) -> str | None:
        return "Indoor Temperature Controlling Sensor"

    def get_native_value(self):
        return self._coordinator.data.get(
            Attribute.INDOOR_TEMPERATURE_CONTROLLING_SENSOR_VALUE
        )

    @property
    def extra_state_attributes(self):
        return super().extra_state_attributes | {
            "status": self._coordinator.data.get(
                Attribute.INDOOR_TEMPERATURE_CONTROLLING_SENSOR_STATUS
            ),
            "raw_sensor_value": self._coordinator.data.get(
                Attribute.INDOOR_TEMPERATURE_CONTROLLING_SENSOR_VALUE
            ),
        }


class AprilaireOutdoorTemperatureControllingSensor(
    BaseAprilaireTemperatureSensor, SensorEntity
):
    """Sensor for outdoor temperature"""

    @property
    def available(self):
        return (
            super().available
            and self._coordinator.data.get(
                Attribute.OUTDOOR_TEMPERATURE_CONTROLLING_SENSOR_STATUS
            )
            == 0
        )

    @property
    def entity_name(self) -> str | None:
        return "Outdoor Temperature Controlling Sensor"

    def get_native_value(self):
        return self._coordinator.data.get(
            Attribute.OUTDOOR_TEMPERATURE_CONTROLLING_SENSOR_VALUE
        )

    @property
    def extra_state_attributes(self):
        return super().extra_state_attributes | {
            "status": self._coordinator.data.get(
                Attribute.OUTDOOR_TEMPERATURE_CONTROLLING_SENSOR_STATUS
            ),
            "raw_sensor_value": self._coordinator.data.get(
                Attribute.OUTDOOR_TEMPERATURE_CONTROLLING_SENSOR_VALUE
            ),
        }


class AprilaireDehumidificationStatusSensor(BaseAprilaireEntity, SensorEntity):
    """Sensor representing the current dehumidification status"""

    @property
    def available(self):
        return (
            super().available
            and Attribute.DEHUMIDIFICATION_STATUS in self._coordinator.data
        )

    @property
    def entity_name(self) -> str | None:
        return "Dehumidification Status"

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        dehumidification_status = self._coordinator.data.get(
            Attribute.DEHUMIDIFICATION_STATUS
        )

        dehumidification_status_map = {
            0: "Idle",
            1: "Idle",
            2: "On",
            3: "On",
            4: "Off",
        }

        return dehumidification_status_map.get(dehumidification_status)


class AprilaireHumidificationStatusSensor(BaseAprilaireEntity, SensorEntity):
    """Sensor representing the current humidification status"""

    @property
    def available(self):
        return (
            super().available
            and Attribute.HUMIDIFICATION_STATUS in self._coordinator.data
        )

    @property
    def entity_name(self) -> str | None:
        return "Humidification Status"

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        humidification_status = self._coordinator.data.get(
            Attribute.HUMIDIFICATION_STATUS
        )

        humidification_status_map = {
            0: "Idle",
            1: "Idle",
            2: "On",
            3: "Off",
        }

        return humidification_status_map.get(humidification_status)


class AprilaireVentilationStatusSensor(BaseAprilaireEntity, SensorEntity):
    """Sensor representing the current ventilation status"""

    @property
    def available(self):
        return (
            super().available and Attribute.VENTILATION_STATUS in self._coordinator.data
        )

    @property
    def entity_name(self) -> str | None:
        return "Ventilation Status"

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        ventilation_status = self._coordinator.data.get(Attribute.VENTILATION_STATUS)

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
    """Sensor representing the current air cleaning status"""

    @property
    def available(self):
        return (
            super().available
            and Attribute.AIR_CLEANING_STATUS in self._coordinator.data
        )

    @property
    def entity_name(self) -> str | None:
        return "Air Cleaning Status"

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        air_cleaning_status = self._coordinator.data.get(Attribute.AIR_CLEANING_STATUS)

        air_cleaning_status_map = {
            0: "Idle",
            1: "Idle",
            2: "On",
            3: "Off",
        }

        return air_cleaning_status_map.get(air_cleaning_status)
