"""Utilities for the Aprilaire integration"""

from __future__ import annotations

import math

from .const import Action, FunctionalDomain


def encode_temperature(temperature: float) -> int:
    """Encode a temperature value for sending to the thermostat"""
    is_negative = temperature < 0
    is_fraction = temperature % 1 >= 0.5

    return (
        math.floor(temperature)
        + (64 if is_fraction else 0)
        + (128 if is_negative else 0)
    )


def decode_temperature(raw_value: int) -> float:
    """Decode a temperature value from the thermostat"""
    temperature_value = float(int(raw_value & 63))

    raw_value = raw_value >> 6
    has_fraction = bool(raw_value & 1)
    if has_fraction:
        temperature_value += 0.5

    raw_value = raw_value >> 1
    is_positive = raw_value & 1 == 0
    if not is_positive:
        temperature_value = -temperature_value

    return temperature_value


def decode_humidity(raw_value: int) -> int:
    """Decode a humidity value from the thermostat"""
    if raw_value == 0 or raw_value >= 100:
        return None
    return raw_value


def read_packet_header(data):
    """Read the header from a packet"""
    action = Action(int(data[4]))
    functional_domain = FunctionalDomain(int(data[5]))
    attribute = int(data[6])

    return (action, functional_domain, attribute)
