"""Tests for the Aprilaire integration setup."""

# pylint: disable=protected-access,redefined-outer-name

from collections.abc import Awaitable, Callable
from unittest.mock import AsyncMock, Mock, patch

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from pyaprilaire.client import AprilaireClient

from custom_components.aprilaire import async_setup_entry, async_unload_entry
from custom_components.aprilaire.const import DOMAIN
from custom_components.aprilaire.coordinator import AprilaireCoordinator


async def test_async_setup_entry(
    client: AprilaireClient,
    config_entry: ConfigEntry,
    unique_id: str,
    hass: HomeAssistant,
) -> None:
    """Test handling of setup with missing MAC address."""

    with patch(
        "pyaprilaire.client.AprilaireClient",
        return_value=client,
    ):
        setup_result = await async_setup_entry(hass, config_entry)

    assert setup_result is True

    client.start_listen.assert_called_once()

    assert isinstance(hass.data[DOMAIN][unique_id], AprilaireCoordinator)


async def test_async_setup_entry_ready(
    client: AprilaireClient,
    config_entry: ConfigEntry,
    hass: HomeAssistant,
) -> None:
    """Test setup entry with valid data."""

    # pylint: disable=unused-argument
    async def wait_for_ready(self, ready_callback: Callable[[bool], Awaitable[None]]):
        await ready_callback(True)

    with patch(
        "pyaprilaire.client.AprilaireClient",
        return_value=client,
    ), patch(
        "custom_components.aprilaire.coordinator.AprilaireCoordinator.wait_for_ready",
        new=wait_for_ready,
    ):
        setup_result = await async_setup_entry(hass, config_entry)

    assert setup_result is True


async def test_async_setup_entry_not_ready(
    client: AprilaireClient,
    config_entry: ConfigEntry,
    hass: HomeAssistant,
) -> None:
    """Test handling of setup when client is not ready."""

    # pylint: disable=unused-argument
    async def wait_for_ready(self, ready_callback: Callable[[bool], Awaitable[None]]):
        await ready_callback(False)

    with patch(
        "pyaprilaire.client.AprilaireClient",
        return_value=client,
    ), patch(
        "custom_components.aprilaire.coordinator.AprilaireCoordinator.wait_for_ready",
        new=wait_for_ready,
    ):
        setup_result = await async_setup_entry(hass, config_entry)

    assert setup_result is True

    client.stop_listen.assert_called_once()


async def test_unload_entry_ok(
    client: AprilaireClient,
    config_entry: ConfigEntry,
    hass: HomeAssistant,
) -> None:
    """Test unloading the config entry."""

    # pylint: disable=unused-argument
    async def wait_for_ready(self, ready_callback: Callable[[bool], Awaitable[None]]):
        await ready_callback(True)

    stop_listen_mock = Mock()

    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

    with patch(
        "pyaprilaire.client.AprilaireClient",
        return_value=client,
    ), patch(
        "custom_components.aprilaire.coordinator.AprilaireCoordinator.wait_for_ready",
        new=wait_for_ready,
    ), patch(
        "custom_components.aprilaire.coordinator.AprilaireCoordinator.stop_listen",
        new=stop_listen_mock,
    ):
        await async_setup_entry(hass, config_entry)

        unload_result = await async_unload_entry(hass, config_entry)

    hass.config_entries.async_unload_platforms.assert_called_once()

    assert unload_result is True

    stop_listen_mock.assert_called_once()


async def test_unload_entry_not_ok(
    client: AprilaireClient,
    config_entry: ConfigEntry,
    hass: HomeAssistant,
) -> None:
    """Test handling of unload failure."""

    # pylint: disable=unused-argument
    async def wait_for_ready(self, ready_callback: Callable[[bool], Awaitable[None]]):
        await ready_callback(True)

    with patch(
        "pyaprilaire.client.AprilaireClient",
        return_value=client,
    ), patch(
        "custom_components.aprilaire.coordinator.AprilaireCoordinator.wait_for_ready",
        new=wait_for_ready,
    ):
        await async_setup_entry(hass, config_entry)

    hass.config_entries.async_unload_platforms = AsyncMock(return_value=False)

    unload_result = await async_unload_entry(hass, config_entry)

    hass.config_entries.async_unload_platforms.assert_called_once()

    assert unload_result is False
