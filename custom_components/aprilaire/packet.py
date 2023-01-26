"""Functions for handling response data from the thermostat"""

from __future__ import annotations

import logging

from enum import Enum
from typing import Any

from .const import Action, FunctionalDomain, LOG_NAME
from .utils import decode_humidity, decode_temperature


class ValueType(Enum):
    """Parsable value types from data"""

    INTEGER = 1
    INTEGER_REQUIRED = 2
    TEMPERATURE = 3
    TEMPERATURE_REQUIRED = 4
    HUMIDITY = 5
    MAC_ADDRESS = 6


MAPPING = {
    Action.READ_RESPONSE: {
        FunctionalDomain.SETUP: {
            1: [
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                ("away_available", ValueType.INTEGER),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
            ]
        },
        FunctionalDomain.CONTROL: {
            1: [
                ("mode", ValueType.INTEGER_REQUIRED),
                ("fan_mode", ValueType.INTEGER_REQUIRED),
                ("heat_setpoint", ValueType.TEMPERATURE_REQUIRED),
                ("cool_setpoint", ValueType.TEMPERATURE_REQUIRED),
            ],
            7: [
                ("thermostat_modes", ValueType.INTEGER),
                ("air_cleaning_available", ValueType.INTEGER),
                ("ventilation_available", ValueType.INTEGER),
                ("dehumidification_available", ValueType.INTEGER),
                ("humidification_available", ValueType.INTEGER),
            ],
        },
        FunctionalDomain.SCHEDULING: {
            4: [
                ("hold", ValueType.INTEGER),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
                (None, None),
            ],
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
            6: [
                ("heating_equipment_status", ValueType.INTEGER),
                ("cooling_equipment_status", ValueType.INTEGER),
                ("progressive_recovery", ValueType.INTEGER),
                ("fan_status", ValueType.INTEGER),
            ],
            7: [
                ("dehumidification_status", ValueType.INTEGER),
                ("humidification_status", ValueType.INTEGER),
                ("ventilation_status", ValueType.INTEGER),
                ("air_cleaning_status", ValueType.INTEGER),
            ],
            8: [
                ("error", ValueType.INTEGER),
            ],
        },
        FunctionalDomain.IDENTIFICATION: {
            1: [
                ("hardware_revision", ValueType.INTEGER),
                ("firmware_major_revision", ValueType.INTEGER),
                ("firmware_minor_revision", ValueType.INTEGER),
                ("protocol_major_revision", ValueType.INTEGER),
                ("model_number", ValueType.INTEGER),
                ("gainspan_firmware_major_revision", ValueType.INTEGER),
                ("gainspan_firmware_minor_revision", ValueType.INTEGER),
            ],
            2: [
                ("mac_address", ValueType.MAC_ADDRESS),
            ],
        },
    }
}

MAPPING[Action.COS] = MAPPING[Action.READ_RESPONSE]
MAPPING[Action.WRITE] = MAPPING[Action.READ_RESPONSE]

_LOGGER = logging.getLogger(LOG_NAME)


def decode_packet(data: bytes) -> list[dict[str, Any]]:
    """Decode the response data from the thermostat"""

    (action, functional_domain, attribute) = decode_packet_header(data)

    if (
        action not in MAPPING
        or functional_domain not in MAPPING[action]
        or attribute not in MAPPING[action][functional_domain]
    ):
        _LOGGER.debug(
            "Unhandled command, action=%s, functional_domain=%s, attribute=%d, data=%s",
            str(action),
            str(functional_domain),
            attribute,
            data.hex(" ", 1),
        )

        return []

    _LOGGER.debug("Reading data=%s", data.hex(" ", 1))

    results: list[dict[str, Any]] = []

    current_result = {"event": (action, functional_domain, attribute)}

    i = 0

    while i < len(data):
        if i == 0:
            current_result["revision"] = data[i]
        elif i == 1:
            current_result["sequence"] = data[i]
        elif i == 2:
            current_result["count"] = data[2] << 2 | data[3]
            i += 1
        elif i == 4:
            if data[i] == "\06":
                break
            j = 0

            attribute_index = 0

            while j < current_result["count"]:
                if j < 3:
                    pass
                elif attribute_index >= len(
                    MAPPING[action][functional_domain][attribute]
                ):
                    pass
                else:
                    (attribute_name, value_type) = MAPPING[action][functional_domain][
                        attribute
                    ][attribute_index]

                    if attribute_name is None or value_type is None:
                        j += 1
                        attribute_index += 1
                        continue

                    data_value = data[i + j]

                    if value_type == ValueType.INTEGER:
                        current_result[attribute_name] = data_value
                    elif value_type == ValueType.INTEGER_REQUIRED:
                        if data_value is not None and data_value != 0:
                            current_result[attribute_name] = data_value
                    elif value_type == ValueType.HUMIDITY:
                        current_result[attribute_name] = decode_humidity(data_value)
                    elif value_type == ValueType.TEMPERATURE:
                        current_result[attribute_name] = decode_temperature(data_value)
                    elif value_type == ValueType.TEMPERATURE_REQUIRED:
                        if data_value is not None and data_value != 0:
                            current_result[attribute_name] = decode_temperature(
                                data_value
                            )
                    elif value_type == ValueType.MAC_ADDRESS:
                        mac_address_components = []

                        for _ in range(0, 6):
                            mac_address_components.append(f"{data[i + j]:x}")
                            j += 1

                        current_result[attribute_name] = ":".join(
                            mac_address_components
                        )

                    attribute_index += 1
                j += 1
            i += j
        else:
            results.extend(decode_packet(data[i:]))
            break

        i += 1

    results.insert(0, current_result)

    return results


def decode_packet_header(data):
    """Read the header from a packet"""
    try:
        action = Action(int(data[4]))
        functional_domain = FunctionalDomain(int(data[5]))
        attribute = int(data[6])
    except ValueError:
        return (Action.NONE, FunctionalDomain.NONE, 0)

    return (action, functional_domain, attribute)
