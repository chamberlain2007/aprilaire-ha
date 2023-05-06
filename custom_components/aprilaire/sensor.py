"""The Aprilaire sensor component"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Mapping

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
    UnitOfTemperature,
)

from .const import DOMAIN
from .coordinator import AprilaireCoordinator
from .entity import BaseAprilaireEntity

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

    if coordinator.data.get("indoor_humidity_controlling_sensor_status", 3) != 3:
        entities.append(AprilaireIndoorHumidityControllingSensor(coordinator))

    if coordinator.data.get("outdoor_humidity_controlling_sensor_status", 3) != 3:
        entities.append(AprilaireOutdoorHumidityControllingSensor(coordinator))

    if coordinator.data.get("indoor_temperature_controlling_sensor_status", 3) != 3:
        entities.append(AprilaireIndoorTemperatureControllingSensor(coordinator))

    if coordinator.data.get("outdoor_temperature_controlling_sensor_status", 3) != 3:
        entities.append(AprilaireOutdoorTemperatureControllingSensor(coordinator))

    if coordinator.data.get("dehumidification_available") == 1:
        entities.append(AprilaireDehumidificationStatusSensor(coordinator))

    if (
        coordinator.data.get("humidification_available") == 1
        or coordinator.data.get("humidification_available") == 2
    ):
        entities.append(AprilaireHumidificationStatusSensor(coordinator))

    if coordinator.data.get("ventilation_available") == 1:
        entities.append(AprilaireVentilationStatusSensor(coordinator))

    if coordinator.data.get("air_cleaning_available") == 1:
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
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            super().available
            and self._coordinator.data.get("indoor_humidity_controlling_sensor_status")
            == 0
        )

    @property
    def entity_name(self) -> str | None:
        """Return the entity name"""
        return "Indoor Humidity Controlling Sensor"

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Return the value reported by the sensor."""
        return self._coordinator.data.get("indoor_humidity_controlling_sensor_value")

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return entity specific state attributes."""

        return super().extra_state_attributes | {
            "status": self._coordinator.data.get(
                "indoor_humidity_controlling_sensor_status"
            ),
            "raw_sensor_value": self._coordinator.data.get(
                "indoor_humidity_controlling_sensor_value"
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
            and self._coordinator.data.get("outdoor_humidity_controlling_sensor_status")
            == 0
        )

    @property
    def entity_name(self) -> str | None:
        """Return the entity name"""
        return "Outdoor Humidity Controlling Sensor"

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Return the value reported by the sensor."""
        return self._coordinator.data.get("outdoor_humidity_controlling_sensor_value")

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""

        return super().extra_state_attributes | {
            "status": self._coordinator.data.get(
                "outdoor_humidity_controlling_sensor_status"
            ),
            "raw_sensor_value": self._coordinator.data.get(
                "outdoor_humidity_controlling_sensor_value"
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
                "indoor_temperature_controlling_sensor_status"
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
        return self._coordinator.data.get("indoor_temperature_controlling_sensor_value")

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""

        return super().extra_state_attributes | {
            "status": self._coordinator.data.get(
                "indoor_temperature_controlling_sensor_status"
            ),
            "raw_sensor_value": self._coordinator.data.get(
                "indoor_temperature_controlling_sensor_value"
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
                "outdoor_temperature_controlling_sensor_status", None
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
        return self._coordinator.data.get(
            "outdoor_temperature_controlling_sensor_value"
        )

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""

        return super().extra_state_attributes | {
            "status": self._coordinator.data.get(
                "outdoor_temperature_controlling_sensor_status"
            ),
            "raw_sensor_value": self._coordinator.data.get(
                "outdoor_temperature_controlling_sensor_value"
            ),
        }


class AprilaireDehumidificationStatusSensor(BaseAprilaireEntity, SensorEntity):
    """Sensor representing the current dehumidification status"""

    @property
    def available(self):
        """Return True if entity is available."""
        return super().available and "dehumidification_status" in self._coordinator.data

    @property
    def entity_name(self) -> str | None:
        """Return the entity name"""
        return "Dehumidification Status"

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Return the value reported by the sensor."""

        dehumidification_status = self._coordinator.data.get("dehumidification_status")

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
        return super().available and "humidification_status" in self._coordinator.data

    @property
    def entity_name(self) -> str | None:
        """Return the entity name"""
        return "Humidification Status"

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Return the value reported by the sensor."""

        humidification_status = self._coordinator.data.get("humidification_status")

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
        return super().available and "ventilation_status" in self._coordinator.data

    @property
    def entity_name(self) -> str | None:
        """Return the entity name"""
        return "Ventilation Status"

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Return the value reported by the sensor."""

        ventilation_status = self._coordinator.data.get("ventilation_status")

        if ventilation_status_value := VENTILATION_STATUS_MAP.get(ventilation_status):
            return ventilation_status_value

        return None


class AprilaireAirCleaningStatusSensor(BaseAprilaireEntity, SensorEntity):
    """Sensor representing the current air cleaning status"""

    @property
    def available(self):
        """Return True if entity is available."""
        return super().available and "air_cleaning_status" in self._coordinator.data

    @property
    def entity_name(self) -> str | None:
        """Return the entity name"""
        return "Air Cleaning Status"

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Return the value reported by the sensor."""

        air_cleaning_status = self._coordinator.data.get("air_cleaning_status")

        if air_cleaning_status_value := AIR_CLEANING_STATUS_MAP.get(
            air_cleaning_status
        ):
            return air_cleaning_status_value

        return None
