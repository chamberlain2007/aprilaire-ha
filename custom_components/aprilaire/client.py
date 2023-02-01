"""Client for interfacing with the thermostat"""

from __future__ import annotations

import asyncio
import logging

from collections.abc import Callable
from typing import Any

from .const import Action, FunctionalDomain, LOG_NAME
from .packet import decode_packet
from .socket_client import SocketClient
from .utils import generate_command_bytes

_LOGGER = logging.getLogger(LOG_NAME)


class _AprilaireClientProtocol(asyncio.Protocol):
    """Protocol for interacting with the thermostat over socket connection"""

    def __init__(
        self,
        data_received_callback: Callable[[FunctionalDomain, int, dict[str, Any]], None],
        reconnect_action: Callable[[], None],
    ) -> None:
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
            extra_payload=extra_payload,
        )

        _LOGGER.debug(
            "Queuing data, sequence=%d, action=%s, functional_domain=%s, attribute=%d",
            self.sequence,
            str(action),
            str(functional_domain),
            attribute,
        )

        self.sequence = (self.sequence + 1) % 128

        await self.command_queue.put(command_bytes)

    def _empty_command_queue(self):
        try:
            for _ in range(self.command_queue.qsize()):
                self.command_queue.get_nowait()
                self.command_queue.task_done()
        except:  # pylint: disable=bare-except
            pass

    async def _process_command_queue(self):
        while True:
            command_bytes = await self.command_queue.get()

            if not command_bytes:
                continue

            if not self.transport:
                break

            _LOGGER.debug("Sending data %s", command_bytes.hex(" ", 1))

            self.transport.write(command_bytes)

    def connection_made(self, transport: asyncio.Transport):
        """Called when a connection has been made to the socket"""
        _LOGGER.info("Aprilaire connection made")

        self.transport = transport
        self._empty_command_queue()

        asyncio.ensure_future(self._process_command_queue())

        async def _update_status():
            await asyncio.sleep(2)

            await self.read_mac_address()
            await self.read_thermostat_status()
            await self.read_sensors()
            await self.configure_cos()
            await self.sync()

        asyncio.ensure_future(_update_status())

    def data_received(self, data: bytes) -> None:
        """Called when data has been received from the socket"""
        _LOGGER.info("Aprilaire data received")

        decoded_packets = decode_packet(data)

        for decoded_packet in decoded_packets:
            if "event" not in decoded_packet:
                _LOGGER.warning("Event data missing")
                return

            (action, functional_domain, attribute) = decoded_packet["event"]

            _LOGGER.debug(
                "Received data, action=%s, functional_domain=%s, attribute=%d",
                action,
                functional_domain,
                attribute,
            )

            if "error" in decoded_packet:
                error = decoded_packet["error"]

                if error != 0:
                    _LOGGER.error("Thermostat error: %d", error)

            if self.data_received_callback:
                asyncio.ensure_future(
                    self.data_received_callback(
                        functional_domain, attribute, decoded_packet
                    )
                )

    def connection_lost(self, exc: Exception | None) -> None:
        """Called when the connection to the socket has been lost"""
        _LOGGER.info("Aprilaire connection lost")

        if self.data_received_callback:
            asyncio.ensure_future(
                self.data_received_callback(
                    FunctionalDomain.NONE, 0, {"available": False}
                )
            )

        if self.reconnect_action:
            asyncio.ensure_future(self.reconnect_action())

    async def read_sensors(self):
        """Send a request for updated sensor data"""
        await self._send_command(Action.READ_REQUEST, FunctionalDomain.SENSORS, 2)

    async def read_control(self):
        """Send a request for updated control data"""
        await self._send_command(Action.READ_REQUEST, FunctionalDomain.CONTROL, 1)

    async def read_scheduling(self):
        """Send a request for updated scheduling data"""
        await self._send_command(Action.READ_REQUEST, FunctionalDomain.SCHEDULING, 4)

    async def update_mode(self, mode: int):
        """Send a request to update the mode"""
        await self._send_command(
            Action.WRITE,
            FunctionalDomain.CONTROL,
            1,
            extra_payload=[
                mode,  # Mode
                0,  # Fan Mode (0 to not set)
                0,  # Heat Setpoint (0 to not set)
                0,  # Cool Setpoint (0 to not set)
            ],
        )

    async def update_fan_mode(self, fan_mode: int):
        """Send a request to update the fan mode"""
        await self._send_command(
            Action.WRITE,
            FunctionalDomain.CONTROL,
            1,
            extra_payload=[
                0,  # Mode (0 to not set)
                fan_mode,  # Fan Mode
                0,  # Heat Setpoint (0 to not set)
                0,  # Cool Setpoint (0 to not set)
            ],
        )

    async def update_setpoint(self, cool_setpoint: int, heat_setpoint: int):
        """Send a request to update the setpoint"""
        await self._send_command(
            Action.WRITE,
            FunctionalDomain.CONTROL,
            1,
            extra_payload=[
                0,  # Mode
                0,  # Fan
                heat_setpoint,  # Heat Setpoint
                cool_setpoint,  # Cool Setpoint
            ],
        )

    async def set_hold(self, hold: int):
        """Send a request to set the hold status"""
        await self._send_command(
            Action.WRITE,
            FunctionalDomain.SCHEDULING,
            4,
            extra_payload=[
                hold,  # Hold
                0,  # Fan
                0,  # Heat Setpoint
                0,  # Cool Setpoint
                0,  # DEH Vacation
                0,  # End Minute
                0,  # End Hour
                0,  # End Date
                0,  # End Month
                0,  # End Year
            ],
        )

    async def sync(self):
        """Send a request to sync data"""
        await self._send_command(
            Action.WRITE,
            FunctionalDomain.STATUS,
            2,
            extra_payload=[
                1,  # Sync
            ],
        )

    async def configure_cos(self):
        """Send a request to configure the COS settings"""
        await self._send_command(
            Action.WRITE,
            FunctionalDomain.STATUS,
            1,
            extra_payload=[
                1,  # Installer Thermostat Settings
                0,  # Contractor Information
                0,  # Air Cleaning Installer Variable
                0,  # Humidity Control Installer Settings
                0,  # Fresh Air Installer Settings
                1,  # Thermostat Setpoint & Mode Settings
                0,  # Dehumidification Setpoint
                0,  # Humidification Setpoint
                0,  # Fresh Air Setting
                0,  # Air Cleaning Settings
                1,  # Thermostat IAQ Available
                0,  # Schedule Settings
                0,  # Away Settings
                0,  # Schedule Day
                1,  # Schedule Hold
                0,  # Heat Blast
                0,  # Service Reminders Status
                0,  # Alerts Status
                0,  # Alerts Settings
                0,  # Backlight Settings
                1,  # Thermostat Location & Name
                0,  # Reserved
                1,  # Controlling Sensor Values
                0,  # Over the air ODT update timeout
                1,  # Thermostat Status
                1,  # IAQ Status
                1,  # Model & Revision
                0,  # Support Module
                0,  # Lockouts
            ],
        )

    async def read_mac_address(self):
        """Send a request to get identification data (including MAC address)"""
        await self._send_command(
            Action.READ_REQUEST,
            FunctionalDomain.IDENTIFICATION,
            2,
        )

    async def read_thermostat_status(self):
        """Send a request for thermostat status"""
        await self._send_command(
            Action.READ_REQUEST,
            FunctionalDomain.CONTROL,
            7,
        )

    async def read_thermostat_name(self):
        """Send a reques for the thermostat name"""
        await self._send_command(
            Action.READ_REQUEST,
            FunctionalDomain.IDENTIFICATION,
            5,
        )


class AprilaireClient(SocketClient):
    """Client for sending/receiving data"""

    def __init__(
        self,
        host: str,
        port: int,
        data_received_callback: Callable[[dict[str, Any]], None],
        reconnect_interval: int = None,
        retry_connection_interval: int = None,
    ) -> None:
        super().__init__(
            host,
            port,
            data_received_callback,
            reconnect_interval,
            retry_connection_interval,
        )

        self.futures: dict[tuple[FunctionalDomain, int], list[asyncio.Future]] = {}

    def create_protocol(self):
        return _AprilaireClientProtocol(self.data_received, self._reconnect)

    async def data_received(
        self, functional_domain: FunctionalDomain, attribute: int, data: dict[str, Any]
    ):
        """Called when data is received from the thermostat"""
        self.data_received_callback(data)

        if not functional_domain or not attribute:
            return

        future_key = (functional_domain, attribute)

        futures_to_complete = self.futures.pop(future_key, [])

        for future in futures_to_complete:
            try:
                future.set_result(data)
            except asyncio.exceptions.InvalidStateError:
                pass

    def state_changed(self):
        """Send data indicating the state as changed"""
        data = {
            "connected": self.connected,
            "stopped": self.stopped,
            "reconnecting": self.reconnecting,
        }

        self.data_received_callback(data)

    async def wait_for_response(
        self, functional_domain: FunctionalDomain, attribute: int, timeout: int = None
    ):
        """Wait for a response for a particular request"""

        loop = asyncio.get_event_loop()
        future = loop.create_future()

        future_key = (functional_domain, attribute)

        if future_key not in self.futures:
            self.futures[future_key] = []

        self.futures[future_key].append(future)

        try:
            return await asyncio.wait_for(future, timeout)
        except asyncio.exceptions.TimeoutError:
            _LOGGER.error(
                "Hit timeout of %d waiting for %s, %d",
                timeout,
                int(functional_domain),
                attribute,
            )
            return None

    async def read_sensors(self):
        """Send a request for updated sensor data"""
        await self.protocol.read_sensors()

    async def read_control(self):
        """Send a request for updated control data"""
        await self.protocol.read_control()

    async def read_scheduling(self):
        """Send a request for updated scheduling data"""
        await self.protocol.read_scheduling()

    async def update_mode(self, mode: int):
        """Send a request to update the mode"""
        await self.protocol.update_mode(mode)

    async def update_fan_mode(self, fan_mode: int):
        """Send a request to update the fan mode"""
        await self.protocol.update_fan_mode(fan_mode)

    async def update_setpoint(self, cool_setpoint: int, heat_setpoint: int):
        """Send a request to update the setpoint"""
        await self.protocol.update_setpoint(cool_setpoint, heat_setpoint)

    async def set_hold(self, hold: int):
        """Send a request to update the away status"""
        await self.protocol.set_hold(hold)

    async def sync(self):
        """Send a request to sync data"""
        await self.protocol.sync()

    async def read_mac_address(self):
        """Send a request to read the MAC address"""
        await self.protocol.read_mac_address()

    async def read_thermostat_name(self):
        """Send a request to read the thermostat name"""
        await self.protocol.read_thermostat_name()
