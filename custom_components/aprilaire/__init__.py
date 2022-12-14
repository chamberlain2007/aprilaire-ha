"""The Aprilaire integration"""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant, Event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from typing import Any

from .client import AprilaireClient

from .const import FunctionalDomain, DOMAIN, LOG_NAME

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.CLIMATE, Platform.SENSOR]

_LOGGER = logging.getLogger(LOG_NAME)

RECONNECT_INTERVAL = 60 * 60
RETRY_CONNECTION_INTERVAL = 10

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup Aprilaire from config entry"""

    config = entry.data

    coordinator = AprilaireCoordinator(hass, config.get("host"), config.get("port"))
    coordinator.start_listen()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    async def _async_close(_: Event) -> None:
        coordinator.stop_listen()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _async_close)
    )

    return True


class AprilaireCoordinator(DataUpdateCoordinator):
    """Coordinator for interacting with the thermostat"""

    def __init__(self, hass: HomeAssistant, host: str, port: int) -> None:
        """Initialize the coordinator"""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
        )

        self.data: dict[str, Any] = {}

        self.client = AprilaireClient(
            host,
            port,
            self.async_set_updated_data,
            RECONNECT_INTERVAL,
            RETRY_CONNECTION_INTERVAL)

    def async_set_updated_data(self, data: _T) -> None:
        if self.data is not None:
            data = self.data | data

        super().async_set_updated_data(data)

    def start_listen(self):
        """Start listening for data"""
        self.client.start_listen()

    def stop_listen(self):
        """Stop listening for data"""
        self.client.stop_listen()

    async def wait_for_ready(self):
        if not self.data or "mac_address" not in self.data:
            data = await self.client.wait_for_response(FunctionalDomain.IDENTIFICATION, 2, 30)

            if not data or "mac_address" not in data:
                _LOGGER.error("Missing MAC address, cannot create unique ID")
                return False

        return True