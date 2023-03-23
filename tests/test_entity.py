from custom_components.aprilaire.coordinator import AprilaireCoordinator
from custom_components.aprilaire.const import DOMAIN, LOG_NAME
from custom_components.aprilaire.entity import BaseAprilaireEntity

import pyaprilaire.client

from homeassistant.helpers.entity import DeviceInfo

from homeassistant.config_entries import ConfigEntry, ConfigEntries
from homeassistant.core import HomeAssistant, EventBus
from homeassistant.util import uuid as uuid_util

from collections.abc import Awaitable, Callable

import logging

import unittest
from unittest.mock import patch, AsyncMock, Mock

_LOGGER = logging.getLogger(LOG_NAME)


class Test_Entity(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.coordinator_mock = AsyncMock(AprilaireCoordinator)
        self.coordinator_mock.data = {}

    async def test_available_on_init(self):
        update_available_mock = Mock()
        with patch(
            "custom_components.aprilaire.entity.BaseAprilaireEntity._update_available",
            new=update_available_mock,
        ):
            entity = BaseAprilaireEntity(self.coordinator_mock)
        update_available_mock.assert_called_once()

    async def test_handle_coordinator_update(self):
        update_available_mock = Mock()
        async_write_ha_state_mock = Mock()

        with patch(
            "custom_components.aprilaire.entity.BaseAprilaireEntity._update_available",
            new=update_available_mock,
        ), patch(
            "homeassistant.helpers.entity.Entity.async_write_ha_state",
            new=async_write_ha_state_mock,
        ):
            entity = BaseAprilaireEntity(self.coordinator_mock)
            entity._handle_coordinator_update()

        self.assertEqual(update_available_mock.call_count, 2)
        async_write_ha_state_mock.assert_called_once()

    async def test_update_available_stopped(self):
        entity = BaseAprilaireEntity(self.coordinator_mock)

        self.coordinator_mock.data["stopped"] = True
        entity._update_available()

        self.assertFalse(entity._available)
        self.assertFalse(entity.available)

    async def test_update_available_no_mac(self):
        entity = BaseAprilaireEntity(self.coordinator_mock)

        self.coordinator_mock.data["connected"] = True
        self.coordinator_mock.data["stopped"] = False
        self.coordinator_mock.data["mac_address"] = None
        entity._update_available()

        self.assertFalse(entity._available)
        self.assertFalse(entity.available)

    async def test_update_available_connected_not_stopped(self):
        entity = BaseAprilaireEntity(self.coordinator_mock)

        self.coordinator_mock.data["connected"] = True
        self.coordinator_mock.data["stopped"] = False
        self.coordinator_mock.data["mac_address"] = "1:2:3:4:5:6"
        entity._update_available()

        self.assertTrue(entity._available)
        self.assertTrue(entity.available)

    async def test_update_available_reconnecting_not_stopped(self):
        entity = BaseAprilaireEntity(self.coordinator_mock)

        self.coordinator_mock.data["connected"] = False
        self.coordinator_mock.data["reconnecting"] = True
        self.coordinator_mock.data["stopped"] = False
        self.coordinator_mock.data["mac_address"] = "1:2:3:4:5:6"
        entity._update_available()

        self.assertTrue(entity._available)
        self.assertTrue(entity.available)

    def test_should_poll(self):
        entity = BaseAprilaireEntity(self.coordinator_mock)

        self.assertFalse(entity.should_poll)

    def test_unique_id(self):
        entity = BaseAprilaireEntity(self.coordinator_mock)

        self.coordinator_mock.data["mac_address"] = "1:2:3:4:5:6"

        with patch(
            "custom_components.aprilaire.entity.BaseAprilaireEntity.entity_name",
            new="Test Entity",
        ):
            self.assertEqual(entity.unique_id, "1_2_3_4_5_6_test_entity")

    def test_name(self):
        entity = BaseAprilaireEntity(self.coordinator_mock)
        self.coordinator_mock.device_name = "Aprilaire"

        with patch(
            "custom_components.aprilaire.entity.BaseAprilaireEntity.entity_name",
            new="Test Entity",
        ):
            self.assertEqual(entity.name, "Aprilaire Test Entity")

    def test_base_entity_name(self):
        entity = BaseAprilaireEntity(self.coordinator_mock)
        self.assertIsNone(entity.entity_name)

    def test_extra_state_attributes(self):
        entity = BaseAprilaireEntity(self.coordinator_mock)
        self.coordinator_mock.device_name = "Aprilaire"
        self.coordinator_mock.data["location"] = "Test Location"

        self.assertDictEqual(
            entity.extra_state_attributes,
            {"device_name": "Aprilaire", "device_location": "Test Location"},
        )

    def test_device_info(self):
        self.coordinator_mock.device_info = DeviceInfo()

        entity = BaseAprilaireEntity(self.coordinator_mock)
        device_info = entity.device_info

        self.assertEqual(device_info, self.coordinator_mock.device_info)
