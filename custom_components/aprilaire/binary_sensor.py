"""The Aprilaire binary sensor component"""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from pyaprilaire.const import Attribute

from .const import DOMAIN
from .coordinator import AprilaireCoordinator
from .entity import BaseAprilaireEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add binary sensors for passed config_entry in HA."""

    coordinator: AprilaireCoordinator = hass.data[DOMAIN][config_entry.unique_id]

    entities = [
        AprilaireFanStatusSensor(coordinator),
    ]

    async_add_entities(entities)


class AprilaireFanStatusSensor(BaseAprilaireEntity, BinarySensorEntity):
    """Sensor representing the fan status"""

    @property
    def available(self):
        """Get entity availability"""
        return super().available and Attribute.FAN_STATUS in self.coordinator.data

    @property
    def entity_name(self) -> str | None:
        """Return the entity name"""
        return "Fan"

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return self.coordinator.data.get(Attribute.FAN_STATUS) == 1
