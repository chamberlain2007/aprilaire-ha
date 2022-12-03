from __future__ import annotations

import logging

from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import AprilaireCoordinator
from .const import DOMAIN, LOG_NAME

_LOGGER = logging.getLogger(LOG_NAME)

class BaseAprilaireEntity(CoordinatorEntity, Entity):
    def __init__(self, coordinator: AprilaireCoordinator) -> None:
        """Initialize the entity"""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._data = coordinator.data
        self._available = False

        _LOGGER.debug("Current data: %s", self._data)

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        _LOGGER.debug(self._coordinator.data)

        for key in self._coordinator.data:
            self._data[key] = self._coordinator.data[key]

        _LOGGER.debug("Current data: %s", self._data)

        if "available" in self._data:
            self._available = self._data["available"]

        self.async_write_ha_state()

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers = {(DOMAIN, self._data['mac_address'])},
            name = "Aprilaire Thermostat",
        )

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
        return self.name