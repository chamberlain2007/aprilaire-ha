"""Constants for the Aprilaire integration"""

from __future__ import annotations

from enum import IntEnum

DOMAIN = "aprilaire"


class Action(IntEnum):
    """An action for commands"""

    WRITE = 1
    READ_REQUEST = 2
    READ_RESPONSE = 3
    COS = 5
    NACK = 6


class FunctionalDomain(IntEnum):
    """A functional domain for commands"""

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
