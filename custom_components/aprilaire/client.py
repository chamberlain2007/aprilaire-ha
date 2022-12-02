"""Client for interfacing with the thermostat"""

from __future__ import annotations

import asyncio
import logging

from collections.abc import Callable
from typing import Any

from .const import Action, FunctionalDomain, LOG_NAME
from .packet import decode_packet
from .utils import generate_command_bytes

_LOGGER = logging.getLogger(LOG_NAME)

RECONNECT_INTERVAL = 60

class _AprilaireClientProtocol(asyncio.Protocol):
    """Protocol for interacting with the thermostat over socket connection"""

    def __init__(self, data_received_callback: Callable[[dict[str, Any]], None], reconnect_action: Callable[[], None]) -> None:
        """Initialize the protocol"""
        self.data_received_callback = data_received_callback
        self.reconnect_action = reconnect_action

        self.transport: asyncio.Transport = None

        self.command_queue = asyncio.Queue()

        self.sequence = 1

    async def _send_command(
        self,
        action: Action,
        functional_domain: FunctionalDomain,
        attribute: int,
        extra_payload: list[int] = None,
    ) -> None:

        """Send a command to the thermostat"""
        command_bytes = generate_command_bytes(
            self.sequence,
            action,
            functional_domain,
            attribute,
            extra_payload=extra_payload
        )
        _LOGGER.debug("Sending data, sequence=%d, action=%s, functional_domain=%s, attribute=%d", self.sequence, str(action), str(functional_domain), attribute)

        self.sequence = (self.sequence + 1) % 128

        await self.command_queue.put(command_bytes)

    def _empty_command_queue(self):
        try:
            for _ in range(self.command_queue.qsize()):
                self.command_queue.get_nowait()
                self.command_queue.task_done()
        except:
            pass

    async def _process_command_queue(self):
        while True:
            command_bytes = await self.command_queue.get()

            if not command_bytes:
                continue

            if not self.transport:
                break

            self.transport.write(command_bytes)

    def connection_made(self, transport: asyncio.Transport):
        """Called when a connection has been made to the socket"""
        _LOGGER.info("Aprilaire connection made")

        self.transport = transport
        self._empty_command_queue()

        asyncio.ensure_future(self._process_command_queue())

        asyncio.ensure_future(self.configure_cos())
        asyncio.ensure_future(self.sync())

    def data_received(self, data: bytes) -> None:
        """Called when data has been received from the socket"""
        _LOGGER.info("Aprilaire data received")

        decoded_data = decode_packet(data)

        if decoded_data:
            if "event" not in decoded_data:
                _LOGGER.warning("Event data missing")
                return

            (action, functional_domain, attribute) = decoded_data["event"]

            _LOGGER.debug("Received data, action=%s, functional_domain=%s, attribute=%d", action, functional_domain, attribute)

            if "error" in decoded_data:
                error = decoded_data["error"]

                if error != 0:
                    _LOGGER.error("Thermostat error: %d", error)
            else:
                decoded_data["available"] = True

            if self.data_received_callback:
                self.data_received_callback(decoded_data)

    def connection_lost(self, exc: Exception | None) -> None:
        """Called when the connection to the socket has been lost"""
        _LOGGER.info("Aprilaire connection lost")

        if self.data_received_callback:
            self.data_received_callback({"available": False})

        if self.reconnect_action:
            asyncio.ensure_future(self.reconnect_action())

    async def read_sensors(self):
        """Send a request for updated sensor data"""
        await self._send_command(
            Action.READ_REQUEST,
            FunctionalDomain.SENSORS,
            2
        )

    async def read_control(self):
        """Send a request for updated control data"""
        await self._send_command(
            Action.READ_REQUEST,
            FunctionalDomain.CONTROL,
            1
        )

    async def update_mode(self, mode: int):
        """Send a request to update the mode"""
        await self._send_command(
            Action.WRITE,
            FunctionalDomain.CONTROL,
            1,
            extra_payload=[
                mode, # Mode
                0, # Fan Mode (0 to not set)
                0, # Heat Setpoint (0 to not set)
                0, # Cool Setpoint (0 to not set)
            ]
        )

    async def update_fan_mode(self, fan_mode: int):
        """Send a request to update the fan mode"""
        await self._send_command(
            Action.WRITE,
            FunctionalDomain.CONTROL,
            1,
            extra_payload=[
                0, # Mode (0 to not set)
                fan_mode, # Fan Mode
                0, # Heat Setpoint (0 to not set)
                0, # Cool Setpoint (0 to not set)
            ]
        )

    async def update_setpoint(self, cool_setpoint: int, heat_setpoint: int):
        """Send a request to update the setpoint"""
        await self._send_command(
            Action.WRITE,
            FunctionalDomain.CONTROL,
            1,
            extra_payload=[
                0, # Mode
                0, # Fan
                heat_setpoint, # Heat Setpoint
                cool_setpoint, # Cool Setpoint
            ],
        )

    async def sync(self):
        """Send a request to sync data"""
        await self._send_command(
            Action.WRITE,
            FunctionalDomain.STATUS,
            2,
            extra_payload=[
                1, # Sync
            ],
        )

    async def configure_cos(self):
        """Send a request to configure the COS settings"""
        await self._send_command(
            Action.WRITE,
            FunctionalDomain.STATUS,
            1,
            extra_payload=[
                0, # Installer Thermostat Settings
                0, # Contractor Information
                0, # Air Cleaning Installer Variable
                0, # Humidity Control Installer Settings
                0, # Fresh Air Installer Settings
                1, # Thermostate Setpoint & Mode Settings
                0, # Dehumidification Setpoint
                0, # Humidification Setpoint
                0, # Fresh Air Setting
                0, # Air Cleaning Settings
                0, # Thermostat IAQ Available
                0, # Schedule Settings
                0, # Away Settings
                0, # Schedule Day
                0, # Schedule Hold
                0, # Heat Blast
                0, # Service Reminders Status
                0, # Alerts Status
                0, # Alerts Settings
                0, # Backlight Settings
                0, # Thermostat Location & Name
                0, # Reserved
                1, # Controlling Sensor Values
                0, # Over the air ODT update timeout
                0, # Thermostat Status
                0, # IAQ Status
                0, # Model & Revision
                0, # Support Module
                0, # Lockouts
            ]
        )

class AprilaireClient:
    """Client for sending/receiving data"""

    def __init__(
        self, host: str, port: int, data_received_callback: Callable[[dict[str, Any]], None]
    ) -> None:
        """Initialize client"""
        self.host = host
        self.port = port
        self.data_received_callback = data_received_callback

        self.connected = False
        self.stopped = True

        self.protocol: _AprilaireClientProtocol = None

    def start_listen(self):
        """Start listening to the socket"""

        async def _reconnect():
            self.connected = False

            while not self.stopped:
                try:
                    await asyncio.get_event_loop().create_connection(
                        lambda: self.protocol,
                        self.host,
                        self.port,
                    )

                    self.connected = True

                    break
                except Exception as e:
                    _LOGGER.error("Failed to connect to thermostat: %s", str(e))

                    await asyncio.sleep(RECONNECT_INTERVAL)

        self.stopped = False

        self.protocol = _AprilaireClientProtocol(self.data_received_callback, _reconnect)

        asyncio.ensure_future(_reconnect())

    def stop_listen(self):
        """Stop listening to the socket"""

        self.stopped = True

        if self.protocol and self.protocol.transport:
            self.protocol.transport.close()

    async def read_sensors(self):
        """Send a request for updated sensor data"""
        await self.protocol.read_sensors()

    async def read_control(self):
        """Send a request for updated control data"""
        await self.protocol.read_control()

    async def update_mode(self, mode: int):
        """Send a request to update the mode"""
        await self.protocol.update_mode(mode)

    async def update_fan_mode(self, fan_mode: int):
        """Send a request to update the fan mode"""
        await self.protocol.update_fan_mode(fan_mode)

    async def update_setpoint(self, cool_setpoint: int, heat_setpoint: int):
        """Send a request to update the setpoint"""
        await self.protocol.update_setpoint(cool_setpoint, heat_setpoint)

    async def sync(self):
        """Send a request to sync data"""
        await self.protocol.sync()