"""Utilities for the Aprilaire integration"""

from __future__ import annotations

import math
from typing import Any

from .crc import generate_crc
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


def generate_command_bytes(
    sequence: int,
    action: Action,
    functional_domain: FunctionalDomain,
    attribute: int,
    extra_payload: list[int] = None,
) -> list[int]:
    """Generate the data to send to the thermostat"""
    payload = [int(action), int(functional_domain), attribute]
    if extra_payload:
        payload.extend(extra_payload)
    (payload_length_high, payload_length_low) = _encode_int_value(len(payload))
    result = [1, sequence, payload_length_high, payload_length_low]
    result.extend(payload)
    result.append(generate_crc(result))
    return bytes(result)


def pad_list(lst: list[Any], length: int, pad: Any = 0):
    """Pad a list to a minimum length"""
    return lst + [pad] * (length - len(lst))


def _encode_int_value(value: int):
    return ((value >> 8) & 0xFF, value & 0xFF)
