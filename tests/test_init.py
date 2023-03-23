from custom_components.aprilaire.coordinator import AprilaireCoordinator
from custom_components.aprilaire.const import DOMAIN, LOG_NAME
from custom_components.aprilaire import async_setup_entry

import pyaprilaire.client

from homeassistant.config_entries import ConfigEntry, ConfigEntries
from homeassistant.core import HomeAssistant, EventBus
from homeassistant.util import uuid as uuid_util

from collections.abc import Awaitable, Callable

import logging

import unittest
from unittest.mock import patch, AsyncMock, Mock

_LOGGER = logging.getLogger(LOG_NAME)


class Test_Init(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.hass_mock = AsyncMock(HomeAssistant)
        self.hass_mock.data = {}
        self.hass_mock.config_entries = AsyncMock(ConfigEntries)
        self.hass_mock.bus = AsyncMock(EventBus)

        self.entry_id = uuid_util.random_uuid_hex()

        self.config_entry_mock = AsyncMock(ConfigEntry)
        self.config_entry_mock.data = {"host": "test123", "port": 123}
        self.config_entry_mock.entry_id = self.entry_id

        self.client_mock = AsyncMock(pyaprilaire.client.AprilaireClient)

    async def test_async_setup_entry(self):
        with patch(
            "pyaprilaire.client.AprilaireClient",
            return_value=self.client_mock,
        ):
            setup_result = await async_setup_entry(
                self.hass_mock, self.config_entry_mock
            )

        self.assertTrue(setup_result)

        self.client_mock.start_listen.assert_called_once()

        self.assertIsInstance(
            self.hass_mock.data[DOMAIN][self.entry_id], AprilaireCoordinator
        )

    async def test_async_setup_entry_ready(self):
        async def wait_for_ready(
            self, ready_callback: Callable[[bool], Awaitable[None]]
        ):
            await ready_callback(True)

        with patch(
            "pyaprilaire.client.AprilaireClient",
            return_value=self.client_mock,
        ), patch(
            "custom_components.aprilaire.coordinator.AprilaireCoordinator.wait_for_ready",
            new=wait_for_ready,
        ):
            setup_result = await async_setup_entry(
                self.hass_mock, self.config_entry_mock
            )

        self.assertTrue(setup_result)

    async def test_async_setup_entry_not_ready(self):
        async def wait_for_ready(
            self, ready_callback: Callable[[bool], Awaitable[None]]
        ):
            await ready_callback(False)

        with patch(
            "pyaprilaire.client.AprilaireClient",
            return_value=self.client_mock,
        ), patch(
            "custom_components.aprilaire.coordinator.AprilaireCoordinator.wait_for_ready",
            new=wait_for_ready,
        ), self.assertLogs(
            _LOGGER
        ) as cm:
            setup_result = await async_setup_entry(
                self.hass_mock, self.config_entry_mock
            )

        self.assertTrue(setup_result)
        self.assertEqual(
            cm.output, ["ERROR:custom_components.aprilaire:Failed to wait for ready"]
        )
        self.client_mock.stop_listen.assert_called_once()

    async def test_invalid_host(self):
        config_entry_mock = AsyncMock()
        config_entry_mock.data = {}

        with (
            patch(
                "pyaprilaire.client.AprilaireClient",
                return_value=self.client_mock,
            ),
            self.assertLogs(_LOGGER) as cm,
        ):
            setup_result = await async_setup_entry(self.hass_mock, config_entry_mock)

        self.assertFalse(setup_result)
        self.client_mock.start_listen.assert_not_called()
        self.assertEqual(
            cm.output, ["ERROR:custom_components.aprilaire:Invalid host None"]
        )

    async def test_invalid_port(self):
        config_entry_mock = AsyncMock()
        config_entry_mock.data = {"host": "test123"}

        with (
            patch(
                "pyaprilaire.client.AprilaireClient",
                return_value=self.client_mock,
            ),
            self.assertLogs(_LOGGER) as cm,
        ):
            setup_result = await async_setup_entry(self.hass_mock, config_entry_mock)

        self.assertFalse(setup_result)
        self.client_mock.start_listen.assert_not_called()
        self.assertEqual(
            cm.output, ["ERROR:custom_components.aprilaire:Invalid port None"]
        )
