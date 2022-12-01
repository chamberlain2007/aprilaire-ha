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

RECONNECT_INTERVAL = 10
SYNC_INTERVAL = 300

class _AprilaireClientProtocol(asyncio.Protocol):
    """Protocol for interacting with the thermostat over socket connection"""

    def __init__(self, data_received_callback: Callable[[dict[str, Any]], None], reconnect_action: Callable[[], None]) -> None:
        """Initialize the protocol"""
        self.data_received_callback = data_received_callback
        self.reconnect_action = reconnect_action

        self.transport: asyncio.Transport = None

        self.command_buffer: list[int] = []

    def _send_command(
        self,
        action: Action,
        functional_domain: FunctionalDomain,
        attribute: int,
        extra_payload: list[int] = None,
    ) -> None:
        """Send a command to the thermostat"""
        command_bytes = generate_command_bytes(
            action, functional_domain, attribute, extra_payload=extra_payload
        )

        _LOGGER.debug("Sending data, action=%s, functional_domain=%s, attribute=%d", str(action), str(functional_domain), attribute)

        if self.transport:
            self.transport.write(command_bytes)
        else:
            self.command_buffer.append(command_bytes)
    
    def _send_raw_command(self, command_bytes: list[int]):
        """Send raw command data to the thermostat"""
        if self.transport:
            self.transport.write(command_bytes)

    def connection_made(self, transport: asyncio.Transport):
        """Called when a connection has been made to the socket"""
        _LOGGER.info("Aprilaire connection made")

        self.transport = transport

        self.configure_cos()
        self.sync()

        for command_bytes in self.command_buffer:
            self._send_raw_command(command_bytes)
        
        self.command_buffer = []

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

    def read_sensors(self):
        """Send a request for updated sensor data"""
        self._send_command(
            Action.READ_REQUEST,
            FunctionalDomain.SENSORS,
            2
        )

    def read_control(self):
        """Send a request for updated control data"""
        self._send_command(
            Action.READ_REQUEST,
            FunctionalDomain.CONTROL,
            1
        )

    def update_mode(self, mode: int):
        """Send a request to update the mode"""
        self._send_command(
            Action.WRITE,
            FunctionalDomain.CONTROL,
            1,
            extra_payload=[mode, 0, 0, 0]
        )

    def update_setpoint(self, cool_setpoint: int, heat_setpoint: int):
        """Send a request to update the setpoint"""
        self._send_command(
            Action.WRITE,
            FunctionalDomain.CONTROL,
            1,
            extra_payload=[0, 0, heat_setpoint, cool_setpoint],
        )

    def sync(self):
        """Send a request to sync data"""
        self._send_command(
            Action.WRITE,
            FunctionalDomain.STATUS,
            2,
            extra_payload=[1],
        )

    def configure_cos(self):
        """Send a request to configure the COS settings"""
        self._send_command(
            Action.WRITE,
            FunctionalDomain.STATUS,
            1,
            extra_payload=[0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]
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

    async def _keep_alive(self):
        """Continuously make sync requests to keep connection alive"""
        while not self.stopped:
            await asyncio.sleep(SYNC_INTERVAL)
            
            if self.connected and not self.stopped:
                self.sync()

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
        asyncio.ensure_future(self._keep_alive())

    def stop_listen(self):
        """Stop listening to the socket"""

        self.stopped = True

        if self.protocol and self.protocol.transport:
            self.protocol.transport.close()

    def read_sensors(self):
        """Send a request for updated sensor data"""
        self.protocol.read_sensors()

    def read_control(self):
        """Send a request for updated control data"""
        self.protocol.read_control()

    def update_mode(self, mode: int):
        """Send a request to update the mode"""
        self.protocol.update_mode(mode)

    def update_setpoint(self, cool_setpoint: int, heat_setpoint: int):
        """Send a request to update the setpoint"""
        self.protocol.update_setpoint(cool_setpoint, heat_setpoint)

    def sync(self):
        """Send a request to sync data"""
        self.protocol.sync()