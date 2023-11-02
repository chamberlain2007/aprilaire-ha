"""Tests for the Aprilaire binary sensors."""

# pylint: disable=protected-access,redefined-outer-name

from unittest.mock import Mock, patch

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from pyaprilaire.const import Attribute

from custom_components.aprilaire.binary_sensor import (
    AprilaireFanStatusSensor,
    async_setup_entry,
)
from custom_components.aprilaire.coordinator import AprilaireCoordinator


@pytest.fixture
async def fan_status_sensor(
    config_entry: ConfigEntry, coordinator: AprilaireCoordinator, hass: HomeAssistant
) -> AprilaireFanStatusSensor:
    """Get a fan status sensor instance."""

    coordinator.data = {
        Attribute.FAN_STATUS: 0,
    }

    async_add_entities_mock = Mock()
    async_get_current_platform_mock = Mock()

    with patch(
        "homeassistant.helpers.entity_platform.async_get_current_platform",
        new=async_get_current_platform_mock,
    ):
        await async_setup_entry(hass, config_entry, async_add_entities_mock)

    binary_sensors_list = async_add_entities_mock.call_args_list[0][0]

    binary_sensor = binary_sensors_list[0][0]
    binary_sensor._attr_available = True
    binary_sensor.hass = hass

    return binary_sensor


async def test_fan_status_sensor(
    fan_status_sensor: AprilaireFanStatusSensor, coordinator: AprilaireCoordinator
):
    """Test that a fan status sensor is created."""

    assert fan_status_sensor is not None

    assert isinstance(fan_status_sensor, AprilaireFanStatusSensor)

    assert fan_status_sensor.available is True
    assert fan_status_sensor.entity_name == "Fan"
    assert fan_status_sensor.is_on is False

    coordinator.data = {
        Attribute.FAN_STATUS: 1,
    }

    assert fan_status_sensor.is_on is True
