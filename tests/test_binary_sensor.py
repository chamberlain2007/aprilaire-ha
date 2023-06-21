# pylint: skip-file

import logging
from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.config_entries import ConfigEntries, ConfigEntry
from homeassistant.core import Config, EventBus, HomeAssistant
from homeassistant.util import uuid as uuid_util

from custom_components.aprilaire.binary_sensor import (
    AprilaireFanStatusSensor,
    async_setup_entry,
)
from custom_components.aprilaire.const import DOMAIN
from custom_components.aprilaire.coordinator import AprilaireCoordinator


@pytest.fixture
def logger():
    logger = logging.getLogger()
    logger.propagate = False

    return logger


@pytest.fixture
def coordinator(logger: logging.Logger) -> AprilaireCoordinator:
    coordinator_mock = AsyncMock(AprilaireCoordinator)
    coordinator_mock.data = {}
    coordinator_mock.logger = logger

    return coordinator_mock


@pytest.fixture
def entry_id() -> str:
    return uuid_util.random_uuid_hex()


@pytest.fixture
def hass(coordinator: AprilaireCoordinator, entry_id: str) -> HomeAssistant:
    hass_mock = AsyncMock(HomeAssistant)
    hass_mock.data = {DOMAIN: {entry_id: coordinator}}
    hass_mock.config_entries = AsyncMock(ConfigEntries)
    hass_mock.bus = AsyncMock(EventBus)
    hass_mock.config = Mock(Config)

    return hass_mock


@pytest.fixture
def config_entry(entry_id: str) -> ConfigEntry:
    config_entry_mock = AsyncMock(ConfigEntry)
    config_entry_mock.data = {"host": "test123", "port": 123}
    config_entry_mock.entry_id = entry_id

    return config_entry_mock


async def test_fan_status_sensor(
    config_entry: ConfigEntry, coordinator: AprilaireCoordinator, hass: HomeAssistant
):
    coordinator.data = {
        "fan_status": 0,
    }

    async_add_entities_mock = Mock()

    await async_setup_entry(hass, config_entry, async_add_entities_mock)

    sensors_list = async_add_entities_mock.call_args_list[0][0]

    assert len(sensors_list) == 1

    sensor = sensors_list[0][0]

    assert isinstance(sensor, AprilaireFanStatusSensor)

    sensor._attr_available = True

    assert sensor.available is True
    assert sensor.entity_name == "Fan"
    assert sensor.is_on is False

    coordinator.data = {
        "fan_status": 1,
    }

    assert sensor.is_on is True
