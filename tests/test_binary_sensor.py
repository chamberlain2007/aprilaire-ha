import unittest
from unittest.mock import AsyncMock, Mock

from homeassistant.config_entries import ConfigEntries, ConfigEntry
from homeassistant.core import Config, EventBus, HomeAssistant
from homeassistant.util import uuid as uuid_util

from custom_components.aprilaire.binary_sensor import (
    AprilaireFanStatusSensor,
    async_setup_entry,
)
from custom_components.aprilaire.const import DOMAIN
from custom_components.aprilaire.coordinator import AprilaireCoordinator


class Test_Binary_Sensor(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.coordinator_mock = AsyncMock(AprilaireCoordinator)
        self.coordinator_mock.data = {}

        self.entry_id = uuid_util.random_uuid_hex()

        self.hass_mock = AsyncMock(HomeAssistant)
        self.hass_mock.data = {DOMAIN: {self.entry_id: self.coordinator_mock}}
        self.hass_mock.config_entries = AsyncMock(ConfigEntries)
        self.hass_mock.bus = AsyncMock(EventBus)
        self.hass_mock.config = Mock(Config)

        self.config_entry_mock = AsyncMock(ConfigEntry)
        self.config_entry_mock.data = {"host": "test123", "port": 123}
        self.config_entry_mock.entry_id = self.entry_id

    async def test_fan_status_sensor(self):
        self.coordinator_mock.data = {
            "fan_status": 0,
        }

        async_add_entities_mock = Mock()

        await async_setup_entry(
            self.hass_mock, self.config_entry_mock, async_add_entities_mock
        )

        sensors_list = async_add_entities_mock.call_args_list[0][0]

        self.assertEqual(len(sensors_list), 1)

        sensor = sensors_list[0][0]

        self.assertIsInstance(sensor, AprilaireFanStatusSensor)

        sensor._attr_available = True

        self.assertTrue(sensor.available)
        self.assertEqual(sensor.entity_name, "Fan")
        self.assertFalse(sensor.is_on)

        self.coordinator_mock.data = {
            "fan_status": 1,
        }

        self.assertTrue(sensor.is_on)
