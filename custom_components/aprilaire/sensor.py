from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass, StateType

from homeassistant.const import (
    TEMP_CELSIUS,
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
        return self._data.get("indoor_humidity_controlling_sensor_status", None) == 0

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
        return self._data.get("outdoor_humidity_controlling_sensor_status", None) == 0

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

class AprilaireIndoorTemperatureControllingSensor(BaseAprilaireEntity, SensorEntity):
    @property
    def available(self):
        return self._data.get("indoor_temperature_controlling_sensor_status", None) == 0

    @property
    def name(self) -> str | None:
        return "Aprilaire Indoor Temperature Controlling Sensor"

    @property
    def device_class(self) -> str | None:
        return SensorDeviceClass.TEMPERATURE
    
    @property
    def state_class(self) -> SensorStateClass | str | None:
        return SensorStateClass.MEASUREMENT
    
    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        return self._data["indoor_temperature_controlling_sensor_value"]

    @property
    def native_unit_of_measurement(self) -> str | None:
        return TEMP_CELSIUS

class AprilaireOutdoorTemperatureControllingSensor(BaseAprilaireEntity, SensorEntity):
    @property
    def available(self):
        return self._data.get("outdoor_temperature_controlling_sensor_status", None) == 0

    @property
    def name(self) -> str | None:
        return "Aprilaire Outdoor Temperature Controlling Sensor"

    @property
    def device_class(self) -> str | None:
        return SensorDeviceClass.TEMPERATURE
    
    @property
    def state_class(self) -> SensorStateClass | str | None:
        return SensorStateClass.MEASUREMENT
    
    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        return self._data["outdoor_temperature_controlling_sensor_value"]

    @property
    def native_unit_of_measurement(self) -> str | None:
        return TEMP_CELSIUS