from __future__ import annotations

import logging

from typing import Any

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
        self._available = False

        self._update_available()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        _LOGGER.debug("Current data: %s", self._coordinator.data)

        self._update_available()

        self.async_write_ha_state()

    def _update_available(self):
        connected: bool = self._coordinator.data.get("connected", None) or self._coordinator.data.get("reconnecting", None)
        stopped: bool = self._coordinator.data.get("stopped", None)

        if stopped:
            self._available = False
        elif not connected:
            self._available = False
        else:
            self._available = "mac_address" in self._coordinator.data

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers = {(DOMAIN, self._coordinator.data['mac_address'])},
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