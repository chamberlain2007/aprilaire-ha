"""The Aprilaire coordinator"""

from __future__ import annotations

import asyncio
import logging

from collections.abc import Awaitable, Callable
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers import device_registry as dr
import homeassistant.helpers.device_registry

import pyaprilaire.client
from pyaprilaire.client import AprilaireClient
from pyaprilaire.const import FunctionalDomain, MODELS

from .const import DOMAIN, LOG_NAME

RECONNECT_INTERVAL = 60 * 60
RETRY_CONNECTION_INTERVAL = 10

_LOGGER = logging.getLogger(LOG_NAME)


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

        self.client = pyaprilaire.client.AprilaireClient(
            host,
            port,
            self.async_set_updated_data,
            _LOGGER,
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
            device_registry = homeassistant.helpers.device_registry.async_get(self.hass)

            device = device_registry.async_get_device(old_device_info["identifiers"])

            if device is not None:
                new_device_info.pop("identifiers")

                device_registry.async_update_device(
                    device_id=device.id, **new_device_info
                )

    async def start_listen(self):
        """Start listening for data"""
        await self.client.start_listen()

    def stop_listen(self):
        """Stop listening for data"""
        self.client.stop_listen()

    async def _wait_for_ready_run(self, ready_callback: Callable[[bool], Awaitable[None]]):
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

    def wait_for_ready(self, ready_callback: Callable[[bool], Awaitable[None]]):
        """Makes requests needed for startup and waits for necessary data to be retrieved"""

        asyncio.ensure_future(self._wait_for_ready_run(ready_callback))

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

    def get_hw_version(self, data: dict[str, Any]) -> str:
        hardware_revision = data.get("hardware_revision")
        if hardware_revision is not None:
            if hardware_revision > ord("A"):
                return f"Rev. {chr(hardware_revision)}"
            else:
                return str(hardware_revision)

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

        device_info["hw_version"] = self.get_hw_version(data)

        firmware_major_revision = data.get("firmware_major_revision")
        firmware_minor_revision = data.get("firmware_minor_revision")
        if firmware_major_revision is not None:
            device_info["sw_version"] = (
                str(firmware_major_revision)
                if firmware_minor_revision is None
                else f"{firmware_major_revision}.{firmware_minor_revision:02}"
            )

        return device_info
