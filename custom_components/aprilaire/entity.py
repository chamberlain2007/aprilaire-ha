"""Base functionality for Aprilaire entities"""

from __future__ import annotations

import logging

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import LOG_NAME
from .coordinator import AprilaireCoordinator


class BaseAprilaireEntity(CoordinatorEntity, Entity):
    """Base for Aprilaire entities"""

    def __init__(self, coordinator: AprilaireCoordinator) -> None:
        """Initialize the entity"""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._available = False

        self._update_available()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        self._coordinator.logger.debug("Current data: %s", self._coordinator.data)

        self._update_available()

        self.async_write_ha_state()

    def _update_available(self):
        connected: bool = self._coordinator.data.get(
            "connected", None
        ) or self._coordinator.data.get("reconnecting", None)

        stopped: bool = self._coordinator.data.get("stopped", None)

        if stopped:
            self._available = False
        elif not connected:
            self._available = False
        else:
            self._available = (
                self._coordinator.data.get("mac_address", None) is not None
            )

    @property
    def device_info(self):
        return self._coordinator.device_info

    @property
    def should_poll(self):
        """Do not need to poll"""
        return False

    @property
    def available(self):
        """Get entity availability"""
        return self._available

    @property
    def unique_id(self):
        return slugify(
            self._coordinator.data["mac_address"].replace(":", "_")
            + "_"
            + self.entity_name
        )

    @property
    def name(self) -> str | None:
        return f"{self._coordinator.device_name} {self.entity_name}"

    @property
    def entity_name(self) -> str | None:
        """Name of the entity"""
        return None

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes."""
        return {
            "device_name": self._coordinator.device_name,
            "device_location": self._coordinator.data.get("location"),
        }
