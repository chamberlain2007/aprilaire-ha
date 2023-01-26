"""Constants for the Aprilaire integration"""

from __future__ import annotations

from enum import IntEnum

DOMAIN = "aprilaire"
LOG_NAME = "custom_components.aprilaire"


class Action(IntEnum):
    """An action for commands"""

    NONE = 0
    WRITE = 1
    READ_REQUEST = 2
    READ_RESPONSE = 3
    COS = 5
    NACK = 6


class FunctionalDomain(IntEnum):
    """A functional domain for commands"""

    NONE = 0
    SETUP = 1
    CONTROL = 2
    SCHEDULING = 3
    ALERTS = 4
    SENSORS = 5
    LOCKOUT = 6
    STATUS = 7
    IDENTIFICATION = 8
    MESSAGING = 9
    DISPLAY = 10
    WEATHER = 13
    FIRMWARE_UPDATE = 14
    DEBUG_COMMANDS = 15
    NACK = 16


MODELS = {
    0: "8476W",
    1: "8810",
    2: "8620W",
    3: "8820",
    4: "8910W",
    5: "8830",
    6: "8920W",
    7: "8840",
}
