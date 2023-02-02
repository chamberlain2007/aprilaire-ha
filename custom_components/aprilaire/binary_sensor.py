"""The Aprilaire binary sensor component"""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.binary_sensor import BinarySensorEntity

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
        AprilaireFanStatusSensor(coordinator),
    ]

    async_add_entities(entities)


class AprilaireFanStatusSensor(BaseAprilaireEntity, BinarySensorEntity):
    """Sensor representing the fan status"""

    @property
    def available(self):
        return super().available and "fan_status" in self._coordinator.data

    @property
    def entity_name(self) -> str | None:
        return "Fan"

    @property
    def is_on(self) -> bool | None:
        return self._coordinator.data.get("fan_status", 0) == 1
