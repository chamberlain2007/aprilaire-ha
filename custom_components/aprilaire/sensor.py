"""The Aprilaire sensor component"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Mapping

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
    StateType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import UNDEFINED
from pyaprilaire.const import Attribute

from .const import DOMAIN
from .coordinator import AprilaireCoordinator
from .entity import BaseAprilaireEntity
from .util import correct_temperature_value

DEHUMIDIFICATION_STATUS_MAP = {
    0: "Idle",
    1: "Idle",
    2: "On",
    3: "On",
    4: "Off",
}

HUMIDIFICATION_STATUS_MAP = {
    0: "Idle",
    1: "Idle",
    2: "On",
    3: "Off",
}

VENTILATION_STATUS_MAP = {
    0: "Idle",
    1: "Idle",
    2: "On",
    3: "Idle",
    4: "Idle",
    5: "Idle",
    6: "Off",
}

AIR_CLEANING_STATUS_MAP = {
    0: "Idle",
    1: "Idle",
    2: "On",
    3: "Off",
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add sensors for passed config_entry in HA."""

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

    if coordinator.data.get(Attribute.HUMIDIFICATION_AVAILABLE) in [1, 2]:
        entities.append(AprilaireHumidificationStatusSensor(coordinator))

    if coordinator.data.get(Attribute.VENTILATION_AVAILABLE) == 1:
        entities.append(AprilaireVentilationStatusSensor(coordinator))

    if coordinator.data.get(Attribute.AIR_CLEANING_AVAILABLE) == 1:
        entities.append(AprilaireAirCleaningStatusSensor(coordinator))

    async_add_entities(entities)


class BaseAprilaireHumiditySensor(SensorEntity):
    """Base for Aprilaire humidity sensors"""

    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE


class AprilaireIndoorHumidityControllingSensor(
    BaseAprilaireEntity, BaseAprilaireHumiditySensor, SensorEntity
):
    """Sensor for indoor humidity"""

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            super().available
            and self._coordinator.data.get(
                Attribute.INDOOR_HUMIDITY_CONTROLLING_SENSOR_STATUS
            )
            == 0
        )

    @property
    def entity_name(self) -> str | None:
        """Return the entity name"""
        return "Indoor Humidity Controlling Sensor"

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Return the value reported by the sensor."""
        return self._coordinator.data.get(
            Attribute.INDOOR_HUMIDITY_CONTROLLING_SENSOR_VALUE
        )

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return entity specific state attributes."""

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
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            super().available
            and self._coordinator.data.get(
                Attribute.OUTDOOR_HUMIDITY_CONTROLLING_SENSOR_STATUS
            )
            == 0
        )

    @property
    def entity_name(self) -> str | None:
        """Return the entity name"""
        return "Outdoor Humidity Controlling Sensor"

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Return the value reported by the sensor."""
        return self._coordinator.data.get(
            Attribute.OUTDOOR_HUMIDITY_CONTROLLING_SENSOR_VALUE
        )

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""

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

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def suggested_display_precision(self) -> int | None:
        """Return the suggested number of decimal digits for display."""
        if self.unit_of_measurement == UnitOfTemperature.CELSIUS:
            return 1
        else:
            return 0


class AprilaireIndoorTemperatureControllingSensor(
    BaseAprilaireTemperatureSensor, SensorEntity
):
    """Sensor for indoor temperature"""

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            super().available
            and self._coordinator.data.get(
                Attribute.INDOOR_TEMPERATURE_CONTROLLING_SENSOR_STATUS
            )
            == 0
        )

    @property
    def entity_name(self) -> str | None:
        """Return the entity name"""
        return "Indoor Temperature Controlling Sensor"

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Return the value reported by the sensor."""
        return correct_temperature_value(
            self.hass.config.units.temperature_unit,
            self._coordinator.data.get(
                Attribute.INDOOR_TEMPERATURE_CONTROLLING_SENSOR_VALUE
            ),
        )

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""

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
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            super().available
            and self._coordinator.data.get(
                Attribute.OUTDOOR_TEMPERATURE_CONTROLLING_SENSOR_STATUS
            )
            == 0
        )

    @property
    def entity_name(self) -> str | None:
        """Return the entity name"""
        return "Outdoor Temperature Controlling Sensor"

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Return the value reported by the sensor."""
        return correct_temperature_value(
            self.hass.config.units.temperature_unit,
            self._coordinator.data.get(
                Attribute.OUTDOOR_TEMPERATURE_CONTROLLING_SENSOR_VALUE
            ),
        )

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""

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
        """Return True if entity is available."""
        return (
            super().available
            and Attribute.DEHUMIDIFICATION_STATUS in self._coordinator.data
        )

    @property
    def entity_name(self) -> str | None:
        """Return the entity name"""
        return "Dehumidification Status"

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Return the value reported by the sensor."""

        dehumidification_status = self._coordinator.data.get(
            Attribute.DEHUMIDIFICATION_STATUS
        )

        if dehumidification_status_value := DEHUMIDIFICATION_STATUS_MAP.get(
            dehumidification_status
        ):
            return dehumidification_status_value

        return None


class AprilaireHumidificationStatusSensor(BaseAprilaireEntity, SensorEntity):
    """Sensor representing the current humidification status"""

    @property
    def available(self):
        """Return True if entity is available."""
        return (
            super().available
            and Attribute.HUMIDIFICATION_STATUS in self._coordinator.data
        )

    @property
    def entity_name(self) -> str | None:
        """Return the entity name"""
        return "Humidification Status"

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Return the value reported by the sensor."""

        humidification_status = self._coordinator.data.get(
            Attribute.HUMIDIFICATION_STATUS
        )

        if humidification_status_value := HUMIDIFICATION_STATUS_MAP.get(
            humidification_status
        ):
            return humidification_status_value

        return None


class AprilaireVentilationStatusSensor(BaseAprilaireEntity, SensorEntity):
    """Sensor representing the current ventilation status"""

    @property
    def available(self):
        """Return True if entity is available."""
        return (
            super().available and Attribute.VENTILATION_STATUS in self._coordinator.data
        )

    @property
    def entity_name(self) -> str | None:
        """Return the entity name"""
        return "Ventilation Status"

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Return the value reported by the sensor."""

        ventilation_status = self._coordinator.data.get(Attribute.VENTILATION_STATUS)

        if ventilation_status_value := VENTILATION_STATUS_MAP.get(ventilation_status):
            return ventilation_status_value

        return None


class AprilaireAirCleaningStatusSensor(BaseAprilaireEntity, SensorEntity):
    """Sensor representing the current air cleaning status"""

    @property
    def available(self):
        """Return True if entity is available."""
        return (
            super().available
            and Attribute.AIR_CLEANING_STATUS in self._coordinator.data
        )

    @property
    def entity_name(self) -> str | None:
        """Return the entity name"""
        return "Air Cleaning Status"

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Return the value reported by the sensor."""

        air_cleaning_status = self._coordinator.data.get(Attribute.AIR_CLEANING_STATUS)

        if air_cleaning_status_value := AIR_CLEANING_STATUS_MAP.get(
            air_cleaning_status
        ):
            return air_cleaning_status_value

        return None
