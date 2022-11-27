"""Functions for handling response data from the thermostat"""

from __future__ import annotations

import logging

from enum import Enum
from typing import Any

from .const import Action, FunctionalDomain, DOMAIN
from .utils import decode_humidity, decode_temperature, read_packet_header


class ValueType(Enum):
    """Parsable value types from data"""

    INTEGER = 1
    TEMPERATURE = 2
    HUMIDITY = 3


MAPPING = {
    Action.READ_RESPONSE: {
        FunctionalDomain.CONTROL: {
            1: [
                ("mode", ValueType.INTEGER),
                ("fan_mode", ValueType.INTEGER),
                ("heat_setpoint", ValueType.TEMPERATURE),
                ("cool_setpoint", ValueType.TEMPERATURE),
            ]
        },
        FunctionalDomain.SENSORS: {
            1: [
                ("built_in_temperature_sensor_status", ValueType.INTEGER),
                ("built_in_temperature_sensor_value", ValueType.TEMPERATURE),
                ("wired_remote_temperature_sensor_status", ValueType.INTEGER),
                ("wired_remote_temperature_sensor_value", ValueType.TEMPERATURE),
                ("wired_outdoor_temperature_sensor_status", ValueType.INTEGER),
                ("wired_outdoor_temperature_sensor_value", ValueType.TEMPERATURE),
                ("built_in_humidity_sensor_status", ValueType.INTEGER),
                ("built_in_humidity_sensor_value", ValueType.HUMIDITY),
                ("rat_sensor_status", ValueType.INTEGER),
                ("rat_sensor_value", ValueType.TEMPERATURE),
                ("lat_sensor_status", ValueType.INTEGER),
                ("lat_sensor_value", ValueType.TEMPERATURE),
                ("wireless_outdoor_temperature_sensor_status", ValueType.INTEGER),
                ("wireless_outdoor_temperature_sensor_value", ValueType.TEMPERATURE),
                ("wireless_outdoor_humidity_sensor_status", ValueType.INTEGER),
                ("wireless_outdoor_humidity_sensor_value", ValueType.HUMIDITY),
            ],
            2: [
                ("indoor_temperature_controlling_sensor_status", ValueType.INTEGER),
                ("indoor_temperature_controlling_sensor_value", ValueType.TEMPERATURE),
                ("outdoor_temperature_controlling_sensor_status", ValueType.INTEGER),
                ("outdoor_temperature_controlling_sensor_value", ValueType.TEMPERATURE),
                ("indoor_humidity_controlling_sensor_status", ValueType.INTEGER),
                ("indoor_humidity_controlling_sensor_value", ValueType.HUMIDITY),
                ("outdoor_humidity_controlling_sensor_status", ValueType.INTEGER),
                ("outdoor_humidity_controlling_sensor_value", ValueType.HUMIDITY),
            ],
        },
        FunctionalDomain.STATUS: {
            2: [
                ("synced", ValueType.INTEGER),
            ],
        },
    }
}

MAPPING[Action.COS] = MAPPING[Action.READ_RESPONSE]

_LOGGER = logging.getLogger(DOMAIN)


def decode_response(data: bytes) -> dict[str, Any]:
    """Decode the response data from the thermostat"""

    (action, functional_domain, attribute) = read_packet_header(data)

    if (
        action not in MAPPING
        or functional_domain not in MAPPING[action]
        or attribute not in MAPPING[action][functional_domain]
    ):
        _LOGGER.warn(
            "Unhandled command, action=%s, functional_domain=%s, attribute=%d", str(action), str(functional_domain), attribute
        )

        return None

    result: dict[str, Any] = {"event": (action, functional_domain, attribute)}

    i = 0

    while i < len(data):
        if i == 0:
            result["revision"] = data[i]
        elif i == 1:
            result["sequence"] = data[i]
        elif i == 2:
            result["count"] = data[2] << 2 | data[3]
            i += 1
        elif i == 4:
            if data[i] == "\06":
                break
            j = 0
            while j < result["count"]:
                if j < 3:
                    pass
                else:
                    (attribute_name, value_type) = MAPPING[action][functional_domain][
                        attribute
                    ][j - 3]

                    if value_type == ValueType.INTEGER:
                        result[attribute_name] = data[i + j]
                    elif value_type == ValueType.HUMIDITY:
                        result[attribute_name] = decode_humidity(data[i + j])
                    elif value_type == ValueType.TEMPERATURE:
                        result[attribute_name] = decode_temperature(data[i + j])
                j += 1
            i += j
        else:
            print(f"Extra {data[i]}")

        i += 1

    return result
