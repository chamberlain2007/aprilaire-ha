"""The Aprilaire integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import Event, HomeAssistant

from .const import DOMAIN
from .coordinator import AprilaireCoordinator

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.CLIMATE, Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry for Aprilaire."""

    host = entry.data.get(CONF_HOST)
    port = entry.data.get(CONF_PORT)

    coordinator = AprilaireCoordinator(hass, host, port)  # type: ignore[arg-type]
    await coordinator.start_listen()

    hass.data.setdefault(DOMAIN, {})[entry.unique_id] = coordinator

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


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        coordinator: AprilaireCoordinator = hass.data[DOMAIN].pop(entry.unique_id)
        coordinator.stop_listen()

    return unload_ok
