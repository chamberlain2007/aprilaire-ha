"""The Aprilaire integration"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant, Event
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers import device_registry as dr

from .client import AprilaireClient

from .const import FunctionalDomain, DOMAIN, LOG_NAME, MODELS

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

    async def ready_callback(ready: bool):
        if ready:
            hass.config_entries.async_setup_platforms(entry, PLATFORMS)

            async def _async_close(_: Event) -> None:
                coordinator.stop_listen()

            entry.async_on_unload(
                hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _async_close)
            )
        else:
            _LOGGER.error("Failed to wait for ready")

            coordinator.stop_listen()

    coordinator.wait_for_ready(ready_callback)

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
            RETRY_CONNECTION_INTERVAL,
        )

    def async_set_updated_data(self, data: Any) -> None:
        old_device_info = self.create_device_info(self.data)

        if self.data is not None:
            data = self.data | data

        super().async_set_updated_data(data)

        new_device_info = self.create_device_info(data)

        if (
            old_device_info is not None
            and new_device_info is not None
            and old_device_info != new_device_info
        ):
            device_registry = dr.async_get(self.hass)

            device = device_registry.async_get_device(old_device_info["identifiers"])

            new_device_info.pop("identifiers")

            device_registry.async_update_device(device_id=device.id, **new_device_info)

    def start_listen(self):
        """Start listening for data"""
        self.client.start_listen()

    def stop_listen(self):
        """Stop listening for data"""
        self.client.stop_listen()

    def wait_for_ready(self, ready_callback: Callable[[bool], Awaitable[None]]):
        """Makes requests needed for startup and waits for necessary data to be retrieved"""

        async def _run():
            if not self.data or "mac_address" not in self.data:
                data = await self.client.wait_for_response(
                    FunctionalDomain.IDENTIFICATION, 2, 30
                )

                if not data or "mac_address" not in data:
                    _LOGGER.error("Missing MAC address, cannot create unique ID")
                    await ready_callback(False)

                    return

            if not self.data or "name" not in self.data:
                await self.client.wait_for_response(
                    FunctionalDomain.IDENTIFICATION, 4, 30
                )

            if not self.data or "thermostat_modes" not in self.data:
                await self.client.wait_for_response(FunctionalDomain.CONTROL, 7, 30)

            if (
                not self.data
                or "indoor_temperature_controlling_sensor_status" not in self.data
            ):
                await self.client.wait_for_response(FunctionalDomain.SENSORS, 2, 30)

            await ready_callback(True)

        asyncio.ensure_future(_run())

    @property
    def device_name(self) -> str:
        """Get the name of the thermostat"""
        return self.create_device_name(self.data)

    def create_device_name(self, data: dict[str, Any]) -> str:
        """Create the name of the thermostat"""
        name = data.get("name")

        if name is None or len(name) == 0:
            return "Aprilaire"

        return name

    @property
    def device_info(self) -> DeviceInfo:
        """Get the device info for the thermostat"""
        return self.create_device_info(self.data)

    def create_device_info(self, data: dict[str, Any]) -> DeviceInfo:
        """Create the device info for the thermostat"""

        if "mac_address" not in data:
            return None

        device_info = DeviceInfo(
            identifiers={(DOMAIN, data["mac_address"])},
            name=self.create_device_name(data),
            manufacturer="Aprilaire",
        )

        model_number = data.get("model_number")
        if model_number is not None:
            device_info["model"] = (
                MODELS[model_number]
                if model_number in MODELS
                else f"Unknown ({model_number})"
            )

        hardware_revision = data.get("hardware_revision")
        if hardware_revision is not None:
            if hardware_revision > ord("A"):
                device_info["hw_version"] = f"Rev. {chr(hardware_revision)}"
            else:
                device_info["hw_version"] = hardware_revision

        firmware_major_revision = data.get("firmware_major_revision")
        firmware_minor_revision = data.get("firmware_minor_revision")
        if firmware_major_revision is not None:
            device_info["sw_version"] = (
                str(firmware_major_revision)
                if firmware_minor_revision is None
                else f"{firmware_major_revision}.{firmware_minor_revision:02}"
            )

        return device_info
