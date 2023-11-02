"""Tests for the Aprilaire coordinator."""

# pylint: disable=protected-access,redefined-outer-name

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceRegistry
from pyaprilaire.client import AprilaireClient
from pyaprilaire.const import FunctionalDomain

from custom_components.aprilaire.const import DOMAIN
from custom_components.aprilaire.coordinator import AprilaireCoordinator


@pytest.fixture
def coordinator(client: AprilaireClient, hass: HomeAssistant) -> AprilaireCoordinator:
    """Return a mock coordinator."""
    with patch(
        "pyaprilaire.client.AprilaireClient",
        return_value=client,
    ):
        return AprilaireCoordinator(hass, "", 0)


async def test_start_listen(coordinator: AprilaireCoordinator) -> None:
    """Test that the coordinator starts the client listening."""

    await coordinator.start_listen()

    assert coordinator.client.start_listen.call_count == 1


def test_stop_listen(coordinator: AprilaireCoordinator) -> None:
    """Test that the coordinator stops the client listening."""

    coordinator.stop_listen()

    assert coordinator.client.stop_listen.call_count == 1


def test_set_updated_data(coordinator: AprilaireCoordinator) -> None:
    """Test updating the coordinator data."""

    test_data = {"testKey": "testValue"}

    coordinator.async_set_updated_data(test_data)

    assert coordinator.data == test_data


def test_device_name_default(coordinator: AprilaireCoordinator) -> None:
    """Test the default device name."""
    assert coordinator.device_name == "Aprilaire"


def test_device_name(coordinator: AprilaireCoordinator) -> None:
    """Test the device name when provided to the coordinator."""

    test_device_name = "Test Device Name"

    coordinator.async_set_updated_data({"name": test_device_name})

    assert coordinator.device_name == test_device_name


def test_device_info(coordinator: AprilaireCoordinator) -> None:
    """Test the device info."""

    test_mac_address = "1:2:3:4:5:6"
    test_device_name = "Test Device Name"
    test_model_number = 0
    test_hardware_revision = ord("B")
    test_firmware_major_revision = 1
    test_firmware_minor_revision = 5

    coordinator.async_set_updated_data(
        {
            "mac_address": test_mac_address,
            "name": test_device_name,
            "model_number": test_model_number,
            "hardware_revision": test_hardware_revision,
            "firmware_major_revision": test_firmware_major_revision,
            "firmware_minor_revision": test_firmware_minor_revision,
        }
    )

    device_info = coordinator.device_info

    assert device_info["identifiers"] == {(DOMAIN, test_mac_address)}
    assert device_info["name"] == test_device_name
    assert device_info["model"] == "8476W"
    assert device_info["hw_version"] == "Rev. B"
    assert (
        device_info["sw_version"]
        == f"{test_firmware_major_revision}.{test_firmware_minor_revision:02}"
    )


def test_no_hw_version(coordinator: AprilaireCoordinator) -> None:
    """Test the hardware version for revision A."""
    assert coordinator.get_hw_version({}) == "Unknown"


def test_hw_version_a(coordinator: AprilaireCoordinator) -> None:
    """Test the hardware version for revision A."""
    assert coordinator.get_hw_version({"hardware_revision": 1}) == "1"


def test_hw_version_b(coordinator: AprilaireCoordinator) -> None:
    """Test the hardware version for revision B."""
    assert coordinator.get_hw_version({"hardware_revision": ord("B")}) == "Rev. B"


def test_updated_device(
    coordinator: AprilaireCoordinator, device_registry: DeviceRegistry
) -> None:
    """Test updating the device info."""

    test_mac_address = "1:2:3:4:5:6"
    test_device_name = "Test Device Name"
    test_model_number = 0
    test_hardware_revision = ord("B")
    test_firmware_major_revision = 1
    test_firmware_minor_revision = 5

    test_new_mac_address = "1:2:3:4:5:7"
    test_new_device_name = "Test Device Name 2"
    test_new_model_number = 1
    test_new_hardware_revision = ord("C")
    test_new_firmware_major_revision = 2
    test_new_firmware_minor_revision = 6

    coordinator.async_set_updated_data(
        {
            "mac_address": test_mac_address,
            "name": test_device_name,
            "model_number": test_model_number,
            "hardware_revision": test_hardware_revision,
            "firmware_major_revision": test_firmware_major_revision,
            "firmware_minor_revision": test_firmware_minor_revision,
        }
    )

    coordinator.async_set_updated_data(
        {
            "mac_address": test_new_mac_address,
            "name": test_new_device_name,
            "model_number": test_new_model_number,
            "hardware_revision": test_new_hardware_revision,
            "firmware_major_revision": test_new_firmware_major_revision,
            "firmware_minor_revision": test_new_firmware_minor_revision,
        }
    )

    assert device_registry.async_update_device.call_count == 1

    new_device_info = device_registry.async_update_device.call_args[1]

    assert new_device_info == new_device_info | {
        "name": test_new_device_name,
        "manufacturer": "Aprilaire",
        "model": "8810",
        "hw_version": "Rev. C",
        "sw_version": "2.06",
    }


async def test_wait_for_ready_mac_fail(
    coordinator: AprilaireCoordinator,
) -> None:
    """Test the handling of a missing MAC address."""

    ready_callback_mock = AsyncMock()

    await coordinator.wait_for_ready(ready_callback_mock)

    assert ready_callback_mock.call_count == 1
    assert ready_callback_mock.call_args[0][0] is False


async def test_wait_for_ready(coordinator: AprilaireCoordinator) -> None:
    """Test waiting for the client to be ready."""

    ready_callback_mock = AsyncMock()

    wait_for_response_mock = AsyncMock()
    wait_for_response_mock.return_value = {"mac_address": "1:2:3:4:5:6"}

    coordinator.client.wait_for_response = wait_for_response_mock

    await coordinator.wait_for_ready(ready_callback_mock)

    wait_for_response_mock.assert_any_call(FunctionalDomain.IDENTIFICATION, 2, 30)
    wait_for_response_mock.assert_any_call(FunctionalDomain.IDENTIFICATION, 4, 30)
    wait_for_response_mock.assert_any_call(FunctionalDomain.CONTROL, 7, 30)
    wait_for_response_mock.assert_any_call(FunctionalDomain.SENSORS, 2, 30)
