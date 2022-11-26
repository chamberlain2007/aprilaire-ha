"""Client for interfacing with the thermostat"""

from __future__ import annotations

import asyncio
import logging

from collections.abc import Callable
from typing import Any

from .const import Action, FunctionalDomain
from .crc import generate_crc
from .response import decode_response

_LOGGER = logging.getLogger(__name__)

class _AprilaireProtocol(asyncio.Protocol):
    """Protocol for interacting with the thermostat over socket connection"""

    def __init__(self, data_callback: Callable[[dict[str, Any]], None]) -> None:
        """Initialize the protocol"""
        self.data_callback = data_callback
        self.transport: asyncio.Transport = None

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

    def connection_made(self, transport: asyncio.Transport):
        """Called when a connection has been made to the socket"""
        _LOGGER.info("Apprilaire connection made")
        self.transport = transport

        asyncio.ensure_future(self.read_sensors())
        asyncio.ensure_future(self.read_control())

    def data_received(self, data: bytes) -> None:
        """Called when data has been received from the socket"""
        _LOGGER.info("Aprilaire data received")

        parsed_data = decode_response(data)

        if parsed_data and self.data_callback:
            self.data_callback(parsed_data)

    def connection_lost(self, exc: Exception | None) -> None:
        """Called when the connection to the socket has been lost"""
        _LOGGER.error("Aprilaire connection lost")


class AprilaireClient:
    """Client for sending/receiving data"""

    def __init__(
        self, host: str, port: int, data_callback: Callable[[dict[str, Any]], None]
    ) -> None:
        """Initialize client"""
        self.host = host
        self.port = port
        self.data_callback = data_callback

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

    async def _start_listen_inner(self):
        """Start listening to the socket"""
        self.protocol = _AprilaireProtocol(self.data_callback)

        asyncio.ensure_future(
            asyncio.get_event_loop().create_connection(
                lambda: self.protocol,
                self.host,
                self.port,
            )
        )

    async def start_listen(self):
        """Start listening to the socket"""
        asyncio.ensure_future(self._start_listen_inner())

    def stop_listen(self):
        """Stop listening to the socket"""
        self.protocol.transport.close()
