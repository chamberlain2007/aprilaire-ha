# pylint: skip-file

import logging
from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.helpers.entity import DeviceInfo

from custom_components.aprilaire.coordinator import AprilaireCoordinator
from custom_components.aprilaire.entity import BaseAprilaireEntity


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


async def test_available_on_init(coordinator: AprilaireCoordinator):
    update_available_mock = Mock()
    with patch(
        "custom_components.aprilaire.entity.BaseAprilaireEntity._update_available",
        new=update_available_mock,
    ):
        entity = BaseAprilaireEntity(coordinator)
    update_available_mock.assert_called_once()


async def test_handle_coordinator_update(coordinator: AprilaireCoordinator):
    update_available_mock = Mock()
    async_write_ha_state_mock = Mock()

    with patch(
        "custom_components.aprilaire.entity.BaseAprilaireEntity._update_available",
        new=update_available_mock,
    ), patch(
        "homeassistant.helpers.entity.Entity.async_write_ha_state",
        new=async_write_ha_state_mock,
    ):
        entity = BaseAprilaireEntity(coordinator)
        entity._handle_coordinator_update()

    assert update_available_mock.call_count == 2

    async_write_ha_state_mock.assert_called_once()


async def test_update_available_stopped(coordinator: AprilaireCoordinator):
    entity = BaseAprilaireEntity(coordinator)

    coordinator.data["stopped"] = True
    entity._update_available()

    assert entity._attr_available is False
    assert entity.available is False


async def test_update_available_no_mac(coordinator: AprilaireCoordinator):
    entity = BaseAprilaireEntity(coordinator)

    coordinator.data["connected"] = True
    coordinator.data["stopped"] = False
    coordinator.data["mac_address"] = None
    entity._update_available()

    assert entity._attr_available is False
    assert entity.available is False


async def test_update_available_connected_not_stopped(
    coordinator: AprilaireCoordinator,
):
    entity = BaseAprilaireEntity(coordinator)

    coordinator.data["connected"] = True
    coordinator.data["stopped"] = False
    coordinator.data["mac_address"] = "1:2:3:4:5:6"
    entity._update_available()

    assert entity._attr_available is True
    assert entity.available is True


async def test_update_available_reconnecting_not_stopped(
    coordinator: AprilaireCoordinator,
):
    entity = BaseAprilaireEntity(coordinator)

    coordinator.data["connected"] = False
    coordinator.data["reconnecting"] = True
    coordinator.data["stopped"] = False
    coordinator.data["mac_address"] = "1:2:3:4:5:6"
    entity._update_available()

    assert entity._attr_available is True
    assert entity.available is True


def test_should_poll(coordinator: AprilaireCoordinator):
    entity = BaseAprilaireEntity(coordinator)

    assert entity.should_poll is False


def test_unique_id(coordinator: AprilaireCoordinator):
    entity = BaseAprilaireEntity(coordinator)

    coordinator.data["mac_address"] = "1:2:3:4:5:6"

    with patch(
        "custom_components.aprilaire.entity.BaseAprilaireEntity.entity_name",
        new="Test Entity",
    ):
        assert entity.unique_id == "1_2_3_4_5_6_test_entity"


def test_name(coordinator: AprilaireCoordinator):
    entity = BaseAprilaireEntity(coordinator)
    coordinator.device_name = "Aprilaire"

    with patch(
        "custom_components.aprilaire.entity.BaseAprilaireEntity.entity_name",
        new="Test Entity",
    ):
        assert entity.name == "Aprilaire Test Entity"


def test_extra_state_attributes(coordinator: AprilaireCoordinator):
    entity = BaseAprilaireEntity(coordinator)
    coordinator.device_name = "Aprilaire"
    coordinator.data["location"] = "Test Location"

    assert entity.extra_state_attributes == {
        "device_name": "Aprilaire",
        "device_location": "Test Location",
    }


def test_device_info(coordinator: AprilaireCoordinator):
    coordinator.device_info = DeviceInfo()

    entity = BaseAprilaireEntity(coordinator)
    device_info = entity.device_info

    assert device_info == coordinator.device_info
