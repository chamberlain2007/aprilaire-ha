"""The Aprilaire integration"""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant, Event

from .const import DOMAIN, LOG_NAME
from .coordinator import AprilaireCoordinator

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.CLIMATE, Platform.SENSOR]

_LOGGER = logging.getLogger(LOG_NAME)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup Aprilaire from config entry"""

    config = entry.data

    host = config.get("host")

    if host is None or len(host) == 0:
        _LOGGER.error("Invalid host %s", host)
        return False

    port = config.get("port")
    if port is None or port <= 0:
        _LOGGER.error("Invalid port %s", port)
        return False

    coordinator = AprilaireCoordinator(hass, host, port)
    await coordinator.start_listen()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    async def ready_callback(ready: bool):
        if ready:
            await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

            async def _async_close(_: Event) -> None:
                coordinator.stop_listen()  # pragma: no cover

            entry.async_on_unload(
                hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _async_close)
            )
        else:
            _LOGGER.error("Failed to wait for ready")

            coordinator.stop_listen()

    await coordinator.wait_for_ready(ready_callback)

    return True
