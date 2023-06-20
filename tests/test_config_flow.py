import logging
import unittest
from unittest.mock import AsyncMock, Mock, patch

import pyaprilaire.client
from homeassistant.config_entries import ConfigEntries, ConfigEntry
from homeassistant.core import EventBus, HomeAssistant
from homeassistant.data_entry_flow import AbortFlow
from homeassistant.util import uuid as uuid_util
from pyaprilaire.client import AprilaireClient
from pyaprilaire.const import FunctionalDomain

from custom_components.aprilaire.config_flow import STEP_USER_DATA_SCHEMA, ConfigFlow
from custom_components.aprilaire.const import LOG_NAME

_LOGGER = logging.getLogger(LOG_NAME)


class Test_Config_Flow(unittest.IsolatedAsyncioTestCase):
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

    async def test_user_input_step(self):
        show_form_mock = Mock()

        config_flow = ConfigFlow()
        config_flow.async_show_form = show_form_mock

        await config_flow.async_step_user(None)

        show_form_mock.assert_called_once_with(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA
        )

    async def test_unique_id_abort(self):
        show_form_mock = Mock()
        set_unique_id_mock = AsyncMock()
        abort_if_unique_id_configured_mock = Mock(
            side_effect=AbortFlow("already_configured")
        )

        config_flow = ConfigFlow()
        config_flow.async_show_form = show_form_mock
        config_flow.async_set_unique_id = set_unique_id_mock
        config_flow._abort_if_unique_id_configured = abort_if_unique_id_configured_mock

        await config_flow.async_step_user(
            {
                "host": "localhost",
                "port": 7000,
            }
        )

        show_form_mock.assert_called_once_with(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors={"base": "already_configured"},
        )

    async def test_unique_id_exception(self):
        show_form_mock = Mock()
        set_unique_id_mock = AsyncMock()
        abort_if_unique_id_configured_mock = Mock(side_effect=Exception("test"))

        config_flow = ConfigFlow()
        config_flow.async_show_form = show_form_mock
        config_flow.async_set_unique_id = set_unique_id_mock
        config_flow._abort_if_unique_id_configured = abort_if_unique_id_configured_mock

        with self.assertLogs(_LOGGER, level="ERROR"):
            await config_flow.async_step_user(
                {
                    "host": "localhost",
                    "port": 7000,
                }
            )

        show_form_mock.assert_called_once_with(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors={"base": "test"},
        )

    async def test_config_flow_invalid_data(self):
        show_form_mock = Mock()
        set_unique_id_mock = AsyncMock()
        abort_if_unique_id_configured_mock = Mock()

        config_flow = ConfigFlow()
        config_flow.async_show_form = show_form_mock
        config_flow.async_set_unique_id = set_unique_id_mock
        config_flow._abort_if_unique_id_configured = abort_if_unique_id_configured_mock

        client_mock = AsyncMock(AprilaireClient)

        with patch("pyaprilaire.client.AprilaireClient", return_value=client_mock):
            await config_flow.async_step_user(
                {
                    "host": "localhost",
                    "port": 7000,
                }
            )

        client_mock.start_listen.assert_called_once()
        client_mock.wait_for_response.assert_called_once_with(
            FunctionalDomain.IDENTIFICATION, 2, 30
        )
        client_mock.stop_listen.assert_called_once()

        show_form_mock.assert_called_once_with(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors={"base": "connection_failed"},
        )

    async def test_config_flow_data(self):
        show_form_mock = Mock()
        set_unique_id_mock = AsyncMock()
        abort_if_unique_id_configured_mock = Mock()
        create_entry_mock = Mock()
        sleep_mock = AsyncMock()

        config_flow = ConfigFlow()
        config_flow.async_show_form = show_form_mock
        config_flow.async_set_unique_id = set_unique_id_mock
        config_flow._abort_if_unique_id_configured = abort_if_unique_id_configured_mock
        config_flow.async_create_entry = create_entry_mock

        client_mock = AsyncMock(AprilaireClient)
        client_mock.wait_for_response = AsyncMock(return_value={"mac_address": "test"})

        with patch(
            "pyaprilaire.client.AprilaireClient", return_value=client_mock
        ), patch("asyncio.sleep", new=sleep_mock):
            await config_flow.async_step_user(
                {
                    "host": "localhost",
                    "port": 7000,
                }
            )

        client_mock.start_listen.assert_called_once()
        client_mock.wait_for_response.assert_called_once_with(
            FunctionalDomain.IDENTIFICATION, 2, 30
        )
        client_mock.stop_listen.assert_called_once()
        sleep_mock.assert_awaited_once()

        create_entry_mock.assert_called_once_with(
            title="Aprilaire",
            data={
                "host": "localhost",
                "port": 7000,
            },
        )
