"""Client for interfacing with the thermostat"""

from __future__ import annotations

import asyncio
import logging

from collections.abc import Callable
from typing import Any

from .const import Action, FunctionalDomain, LOG_NAME
from .crc import generate_crc
from .response import decode_response

_LOGGER = logging.getLogger(LOG_NAME)

RECONNECT_INTERVAL = 10
SYNC_INTERVAL = 120

class _AprilaireProtocol(asyncio.Protocol):
    """Protocol for interacting with the thermostat over socket connection"""

    def __init__(self, data_callback: Callable[[dict[str, Any]], None], reconnect_action: Callable[[], None]) -> None:
        """Initialize the protocol"""
        self.data_callback = data_callback
        self.reconnect_action = reconnect_action

        self.transport: asyncio.Transport = None

        self.command_buffer: list[int] = []


    def __generate_command_bytes(
        self,
        action: Action,
        functional_domain: FunctionalDomain,
        attribute: int,
        extra_payload: list[int] = None,
    ) -> list[int]:
        """Generate the data to send to the thermostat"""
        payload = [int(action), int(functional_domain), attribute]
        if extra_payload:
            payload.extend(extra_payload)
        result = [1, 0, 0, len(payload)]
        result.extend(payload)
        result.append(generate_crc(result))
        return bytes(result)

    async def __send_command(
        self,
        action: Action,
        functional_domain: FunctionalDomain,
        attribute: int,
        extra_payload: list[int] = None,
    ) -> None:
        """Send a command to the thermostat"""
        command_bytes = self.__generate_command_bytes(
            action, functional_domain, attribute, extra_payload=extra_payload
        )

        _LOGGER.debug("Sending data, action=%s, functional_domain=%s, attribute=%d", str(action), str(functional_domain), attribute)

        if self.transport:
            self.transport.write(command_bytes)
        else:
            self.command_buffer.append(command_bytes)
    
    async def __send_raw_command(self, command_bytes: list[int]):
        if self.transport:
            self.transport.write(command_bytes)

    async def read_sensors(self):
        """Send a request for updated sensor data"""
        await self.__send_command(Action.READ_REQUEST, FunctionalDomain.SENSORS, 2)

    async def read_control(self):
        """Send a request for updated control data"""
        await self.__send_command(Action.READ_REQUEST, FunctionalDomain.CONTROL, 1)

    async def update_mode(self, mode: int):
        """Send a request to update the mode"""
        await self.__send_command(
            Action.WRITE, FunctionalDomain.CONTROL, 1, extra_payload=[mode, 0, 0, 0]
        )

    async def update_setpoint(self, cool_setpoint: int, heat_setpoint: int):
        """Send a request to update the setpoint"""
        await self.__send_command(
            Action.WRITE,
            FunctionalDomain.CONTROL,
            1,
            extra_payload=[0, 0, heat_setpoint, cool_setpoint],
        )
    
    async def sync(self):
        await self.__send_command(
            Action.WRITE,
            FunctionalDomain.STATUS,
            2,
            extra_payload=[1],
        )
    
    async def configure_cos(self):
        await self.__send_command(
            Action.WRITE,
            FunctionalDomain.STATUS,
            1,
            extra_payload=[0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]
        )

    def connection_made(self, transport: asyncio.Transport):
        """Called when a connection has been made to the socket"""
        _LOGGER.info("Aprilaire connection made")
        self.transport = transport

        asyncio.ensure_future(self.configure_cos())
        asyncio.ensure_future(self.sync())

        for command_bytes in self.command_buffer:
            asyncio.ensure_future(self.__send_raw_command(command_bytes))
        
        self.command_buffer = []

    def data_received(self, data: bytes) -> None:
        """Called when data has been received from the socket"""
        _LOGGER.info("Aprilaire data received")

        parsed_data = decode_response(data)

        if parsed_data:
            (action, functional_domain, attribute) = parsed_data["event"]

            _LOGGER.debug("Received data, action=%s, functional_domain=%s, attribute=%d", action, functional_domain, attribute)

            if "error" in parsed_data:
                error = parsed_data["error"]

                if error != 0:
                    _LOGGER.error("Thermostat error: %d", error)

            if self.data_callback:
                self.data_callback(parsed_data)

    def connection_lost(self, exc: Exception | None) -> None:
        """Called when the connection to the socket has been lost"""
        _LOGGER.info("Aprilaire connection lost")

        if self.reconnect_action:
            asyncio.ensure_future(self.reconnect_action())


class AprilaireClient:
    """Client for sending/receiving data"""

    def __init__(
        self, host: str, port: int, data_callback: Callable[[dict[str, Any]], None]
    ) -> None:
        """Initialize client"""
        self.host = host
        self.port = port
        self.data_callback = data_callback

        self.connected = False
        self.protocol: _AprilaireProtocol = None

    async def read_sensors(self):
        """Send a request for updated sensor data"""
        await self.protocol.read_sensors()

    async def read_control(self):
        """Send a request for updated control data"""
        await self.protocol.read_control()

    async def update_mode(self, mode: int):
        """Send a request to update the mode"""
        await self.protocol.update_mode(mode)

    async def update_setpoint(self, cool_setpoint: int, heat_setpoint: int):
        """Send a request to update the setpoint"""
        await self.protocol.update_setpoint(cool_setpoint, heat_setpoint)
    
    async def sync(self):
        await self.protocol.sync()

    async def _keep_alive(self):
        while True:
            await asyncio.sleep(SYNC_INTERVAL)
            
            if self.connected:
                await self.sync()

    async def _start_listen_inner(self):
        """Start listening to the socket"""

        async def reconnect_action():
            self.connected = False

            while True:
                try:
                    await asyncio.get_event_loop().create_connection(
                        lambda: self.protocol,
                        self.host,
                        self.port,
                    )

                    self.connected = True

                    break
                except ConnectionRefusedError as e:
                    _LOGGER.error("Failed to connect to thermostat: %s", str(e))

                    await asyncio.sleep(RECONNECT_INTERVAL)
        
        self.protocol = _AprilaireProtocol(self.data_callback, reconnect_action)

        asyncio.ensure_future(reconnect_action())
        asyncio.ensure_future(self._keep_alive())

    async def start_listen(self):
        """Start listening to the socket"""
        asyncio.ensure_future(self._start_listen_inner())

    def stop_listen(self):
        """Stop listening to the socket"""

        if self.protocol and self.protocol.transport:
            self.protocol.transport.close()
