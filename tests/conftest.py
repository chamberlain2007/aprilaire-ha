"""Setup test fixtures for Aprilaire tests."""

# pylint: disable=redefined-outer-name

import logging
from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.config_entries import ConfigEntries, ConfigEntry
from homeassistant.core import Config, EventBus, HomeAssistant
from homeassistant.helpers.device_registry import DeviceRegistry
from homeassistant.util import uuid as uuid_util
from homeassistant.util.unit_system import METRIC_SYSTEM
from pyaprilaire.client import AprilaireClient

from custom_components.aprilaire.const import DOMAIN
from custom_components.aprilaire.coordinator import AprilaireCoordinator


@pytest.fixture
def logger():
    """Get a logger instance."""
    logger_instance = logging.getLogger()
    logger_instance.propagate = False

    return logger_instance


@pytest.fixture
def client() -> AprilaireClient:
    """Get a client instance."""
    client_mock = AsyncMock(AprilaireClient)
    client_mock.connected = True
    client_mock.stopped = False
    client_mock.reconnecting = True
    client_mock.auto_reconnecting = True

    return client_mock


@pytest.fixture
def coordinator(
    client: AprilaireClient, logger: logging.Logger
) -> AprilaireCoordinator:
    """Get a coordinator instance."""
    coordinator_mock = AsyncMock(AprilaireCoordinator)
    coordinator_mock.data = {"mac_address": "1:2:3:4:5:6"}
    coordinator_mock.client = client
    coordinator_mock.logger = logger

    return coordinator_mock


@pytest.fixture
def unique_id() -> str:
    """Get a unique ID."""
    return uuid_util.random_uuid_hex()


@pytest.fixture
def device_registry() -> DeviceRegistry:
    """Return a mock device registry."""
    return Mock(DeviceRegistry)


@pytest.fixture
def hass(
    coordinator: AprilaireCoordinator, device_registry: DeviceRegistry, unique_id: str
) -> HomeAssistant:
    """Get a HomeAssistant instance."""
    hass_mock = AsyncMock(HomeAssistant)
    hass_mock.data = {
        DOMAIN: {unique_id: coordinator},
        "device_registry": device_registry,
    }
    hass_mock.config_entries = AsyncMock(ConfigEntries)
    hass_mock.bus = AsyncMock(EventBus)
    hass_mock.config = Mock(Config)
    hass_mock.config.units = METRIC_SYSTEM

    return hass_mock


@pytest.fixture
def config_entry(unique_id: str) -> ConfigEntry:
    """Get a config entry instance."""
    config_entry_mock = AsyncMock(ConfigEntry)
    config_entry_mock.data = {"host": "test123", "port": 123}
    config_entry_mock.unique_id = unique_id

    return config_entry_mock
