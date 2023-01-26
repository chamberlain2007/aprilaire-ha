"""Mock server for testing Aprilaire integration"""

from __future__ import annotations

import argparse
import asyncio
from asyncio import Queue
import logging

from .const import Action, FunctionalDomain, LOG_NAME
from .packet import decode_packet, decode_packet_header
from .utils import encode_temperature, generate_command_bytes

COS_FREQUENCY = 30
QUEUE_FREQUENCY = 0.5


class CustomFormatter(logging.Formatter):
    """Custom logging formatter"""

    green = "\x1b[32;20m"
    cyan = "\x1b[36;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    log_format = "%(asctime)s %(levelname)s [%(name)s] %(message)s"

    FORMATS = {
        logging.DEBUG: cyan + log_format + reset,
        logging.INFO: green + log_format + reset,
        logging.WARNING: yellow + log_format + reset,
        logging.ERROR: red + log_format + reset,
        logging.CRITICAL: bold_red + log_format + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


_LOGGER = logging.getLogger(LOG_NAME)
_LOGGER.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

ch.setFormatter(CustomFormatter())

_LOGGER.addHandler(ch)


class _AprilaireServerProtocol(asyncio.Protocol):
    def __init__(self):
        self.transport: asyncio.Transport = None

        self.mode = 5
        self.fan_mode = 2
        self.cool_setpoint = 25
        self.heat_setpoint = 20
        self.hold = 0

        self.queue = Queue()

        self.sequence = 1

    def _generate_thermostat_status_command_bytes(self):
        heating_equipment_status = {2: 2, 4: 7}.get(self.mode, 0)

        cooling_equipment_status = {3: 2, 5: 2}.get(self.mode, 0)

        fan_status = 1 if self.fan_mode == 1 or self.fan_mode == 2 else 0

        return generate_command_bytes(
            self.sequence + 127,
            Action.COS,
            FunctionalDomain.STATUS,
            6,
            [heating_equipment_status, cooling_equipment_status, 0, fan_status],
        )

    async def send_status(self):
        """Send the current status"""

        await self.queue.put(
            generate_command_bytes(
                self.sequence + 127,
                Action.READ_RESPONSE,
                FunctionalDomain.IDENTIFICATION,
                2,
                [1, 2, 3, 4, 5, 6],
            )
        )

        self.sequence = (self.sequence + 1) % 128

        await self.queue.put(
            generate_command_bytes(
                self.sequence + 127,
                Action.COS,
                FunctionalDomain.CONTROL,
                1,
                [
                    self.mode,
                    self.fan_mode,
                    encode_temperature(self.heat_setpoint),
                    encode_temperature(self.cool_setpoint),
                ],
            )
            + generate_command_bytes(
                self.sequence + 127,
                Action.COS,
                FunctionalDomain.SENSORS,
                2,
                [0, encode_temperature(25), 0, encode_temperature(20), 0, 50, 0, 40],
            )
            + generate_command_bytes(
                self.sequence + 127, Action.COS, FunctionalDomain.STATUS, 2, [1]
            )
            + generate_command_bytes(
                self.sequence + 127,
                Action.COS,
                FunctionalDomain.STATUS,
                7,
                [2, 2, 2, 2],
            )
            + generate_command_bytes(
                self.sequence + 127,
                Action.COS,
                FunctionalDomain.CONTROL,
                7,
                [6, 1, 1, 1],
            )
            + generate_command_bytes(
                self.sequence + 127,
                Action.COS,
                FunctionalDomain.SETUP,
                1,
                list([0] * 26) + [1] + list([0] * 17),
            )
            + generate_command_bytes(
                self.sequence + 127,
                Action.COS,
                FunctionalDomain.SCHEDULING,
                4,
                [self.hold] + list([0] * 9),
            )
            + generate_command_bytes(
                self.sequence + 127,
                Action.COS,
                FunctionalDomain.IDENTIFICATION,
                1,
                [66, 10, 2, 15, 1, 14, 3],
            )
            + self._generate_thermostat_status_command_bytes()
        )

        self.sequence = (self.sequence + 1) % 128

    async def cos_loop(self):
        """Send the current status (COS) periodically"""
        await asyncio.sleep(2)

        while self.transport:
            await self.send_status()
            await asyncio.sleep(COS_FREQUENCY)

    async def queue_loop(self):
        """Periodically send items from the queue"""
        while self.transport:
            command_bytes = await self.queue.get()

            if self.transport:
                _LOGGER.info("Sent data: %s", command_bytes.hex(" ", 1))

                self.transport.write(command_bytes)

            await asyncio.sleep(QUEUE_FREQUENCY)

    def connection_made(self, transport):
        _LOGGER.info("Connection made")

        self.transport = transport

        asyncio.ensure_future(self.cos_loop())
        asyncio.ensure_future(self.queue_loop())

    def data_received(self, data: bytes) -> None:
        _LOGGER.info("Received data: %s", data.hex(" ", 1))

        (action, functional_domain, attribute) = decode_packet_header(data)

        if action == Action.READ_REQUEST:
            if functional_domain == FunctionalDomain.SENSORS:
                if attribute == 2:
                    self.queue.put_nowait(
                        generate_command_bytes(
                            self.sequence + 127,
                            Action.READ_RESPONSE,
                            FunctionalDomain.SENSORS,
                            2,
                            [
                                0,
                                encode_temperature(22),
                                0,
                                encode_temperature(10),
                                0,
                                50,
                                0,
                                40,
                            ],
                        )
                    )

                    self.sequence = (self.sequence + 1) % 128
            elif functional_domain == FunctionalDomain.SCHEDULING:
                if attribute == 4:
                    self.queue.put_nowait(
                        generate_command_bytes(
                            self.sequence + 127,
                            Action.COS,
                            FunctionalDomain.SCHEDULING,
                            4,
                            [self.hold] + list([0] * 9),
                        )
                    )

                    self.sequence = (self.sequence + 1) % 128
        elif action == Action.WRITE:
            if functional_domain == FunctionalDomain.CONTROL:
                if attribute == 1:
                    decoded_packets = decode_packet(data)

                    for decoded_packet in decoded_packets:
                        if "mode" in decoded_packet:
                            new_mode = decoded_packet["mode"]

                            if new_mode != 0:
                                self.mode = new_mode
                                self.hold = 0

                        if "fan_mode" in decoded_packet:
                            new_fan_mode = decoded_packet["fan_mode"]

                            if new_fan_mode != 0:
                                self.fan_mode = new_fan_mode

                        if "heat_setpoint" in decoded_packet:
                            new_heat_setpoint = decoded_packet["heat_setpoint"]

                            if new_heat_setpoint != 0:
                                self.heat_setpoint = new_heat_setpoint
                                self.hold = 1

                        if "cool_setpoint" in decoded_packet:
                            new_cool_setpoint = decoded_packet["cool_setpoint"]

                            if new_cool_setpoint != 0:
                                self.cool_setpoint = new_cool_setpoint
                                self.hold = 1

                        self.queue.put_nowait(
                            generate_command_bytes(
                                self.sequence + 127,
                                Action.COS,
                                FunctionalDomain.CONTROL,
                                1,
                                [
                                    self.mode,
                                    self.fan_mode,
                                    encode_temperature(self.heat_setpoint),
                                    encode_temperature(self.cool_setpoint),
                                ],
                            )
                        )

                        self.sequence = (self.sequence + 1) % 128

                        self.queue.put_nowait(
                            self._generate_thermostat_status_command_bytes()
                        )

                        self.queue.put_nowait(
                            generate_command_bytes(
                                self.sequence + 127,
                                Action.COS,
                                FunctionalDomain.SCHEDULING,
                                4,
                                [self.hold] + list([0] * 9),
                            )
                        )

                        self.sequence = (self.sequence + 1) % 128
            elif functional_domain == FunctionalDomain.SCHEDULING:
                if attribute == 4:
                    decoded_packets = decode_packet(data)

                    for decoded_packet in decoded_packets:
                        if "hold" in decoded_packet:
                            self.hold = decoded_packet["hold"]

                    self.queue.put_nowait(
                        generate_command_bytes(
                            self.sequence + 127,
                            Action.COS,
                            FunctionalDomain.SCHEDULING,
                            4,
                            [self.hold] + list([0] * 9),
                        )
                    )

                    self.sequence = (self.sequence + 1) % 128
            elif functional_domain == FunctionalDomain.STATUS:
                if attribute == 2:
                    asyncio.ensure_future(self.send_status())

    def connection_lost(self, exc: Exception | None) -> None:
        _LOGGER.info("Connection lost")
        self.transport = None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-H", "--host", default="localhost")
    parser.add_argument("-p", "--port", default=7001)

    args = parser.parse_args()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    coro = loop.create_server(_AprilaireServerProtocol, args.host, args.port)

    server = loop.run_until_complete(coro)

    _LOGGER.info("Server listening on %s port %d", args.host, args.port)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.close()
        loop.close()
