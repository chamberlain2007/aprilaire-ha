"""Tests for the Aprilaire config flow."""

# pylint: disable=protected-access,redefined-outer-name

from unittest.mock import AsyncMock, Mock, patch

from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from pyaprilaire.client import AprilaireClient
from pyaprilaire.const import Attribute, FunctionalDomain

from custom_components.aprilaire.config_flow import STEP_USER_DATA_SCHEMA, ConfigFlow


async def test_user_input_step() -> None:
    """Test the user input step."""

    show_form_mock = Mock()

    config_flow = ConfigFlow()
    config_flow.async_show_form = show_form_mock

    await config_flow.async_step_user(None)

    show_form_mock.assert_called_once_with(
        step_id="user", data_schema=STEP_USER_DATA_SCHEMA
    )


async def test_config_flow_invalid_data(client: AprilaireClient) -> None:
    """Test that the flow is aborted with invalid data."""

    show_form_mock = Mock()
    set_unique_id_mock = AsyncMock()
    async_abort_entries_match_mock = Mock()

    config_flow = ConfigFlow()
    config_flow.async_show_form = show_form_mock
    config_flow.async_set_unique_id = set_unique_id_mock
    config_flow._async_abort_entries_match = async_abort_entries_match_mock

    with patch("pyaprilaire.client.AprilaireClient", return_value=client):
        await config_flow.async_step_user(
            {
                CONF_HOST: "localhost",
                CONF_PORT: 7000,
            }
        )

    client.start_listen.assert_called_once()
    client.wait_for_response.assert_called_once_with(
        FunctionalDomain.IDENTIFICATION, 2, 30
    )
    client.stop_listen.assert_called_once()

    async_abort_entries_match_mock.assert_called_once_with(
        {CONF_HOST: "localhost", CONF_PORT: 7000}
    )

    show_form_mock.assert_called_once_with(
        step_id="user",
        data_schema=STEP_USER_DATA_SCHEMA,
        errors={"base": "connection_failed"},
    )


async def test_config_flow_data(client: AprilaireClient, hass: HomeAssistant) -> None:
    """Test the config flow with valid data."""

    show_form_mock = Mock()
    set_unique_id_mock = AsyncMock()
    async_abort_entries_match_mock = Mock()
    create_entry_mock = Mock()

    config_flow = ConfigFlow()
    config_flow.hass = hass
    config_flow.async_show_form = show_form_mock
    config_flow.async_set_unique_id = set_unique_id_mock
    config_flow._async_abort_entries_match = async_abort_entries_match_mock
    config_flow.async_create_entry = create_entry_mock

    client.wait_for_response = AsyncMock(return_value={Attribute.MAC_ADDRESS: "test"})

    with patch("pyaprilaire.client.AprilaireClient", return_value=client):
        await config_flow.async_step_user(
            {
                CONF_HOST: "localhost",
                CONF_PORT: 7000,
            }
        )

    client.start_listen.assert_called_once()
    client.wait_for_response.assert_any_call(FunctionalDomain.IDENTIFICATION, 2, 30)
    client.wait_for_response.assert_any_call(FunctionalDomain.IDENTIFICATION, 4, 30)
    client.wait_for_response.assert_any_call(FunctionalDomain.CONTROL, 7, 30)
    client.wait_for_response.assert_any_call(FunctionalDomain.SENSORS, 2, 30)
    client.stop_listen.assert_called_once()

    async_abort_entries_match_mock.assert_called_once_with(
        {CONF_HOST: "localhost", CONF_PORT: 7000}
    )

    create_entry_mock.assert_called_once_with(
        title="Aprilaire",
        data={
            CONF_HOST: "localhost",
            CONF_PORT: 7000,
        },
    )
