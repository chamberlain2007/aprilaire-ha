"""The Aprilaire integration"""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant, Event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from typing import Any

from .client import AprilaireClient

from .const import DOMAIN, LOG_NAME

PLATFORMS: list[Platform] = [Platform.CLIMATE]

_LOGGER = logging.getLogger(LOG_NAME)


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

        self.client = AprilaireClient(host, port, self.async_set_updated_data)

    def start_listen(self):
        """Start listening for data"""
        self.client.start_listen()

    def stop_listen(self):
        """Stop listening for data"""
        self.client.stop_listen()
