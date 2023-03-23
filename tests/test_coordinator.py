from custom_components.aprilaire.coordinator import AprilaireCoordinator
from custom_components.aprilaire.const import DOMAIN, LOG_NAME

import pyaprilaire.client
from pyaprilaire.const import FunctionalDomain

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceRegistry

import logging

import unittest
from unittest.mock import patch, AsyncMock, Mock

_LOGGER = logging.getLogger(LOG_NAME)


class Test_Coordinator(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.data_registry_mock = Mock(DeviceRegistry)

        self.hass_mock = Mock(HomeAssistant)
        self.hass_mock.data = {"device_registry": self.data_registry_mock}

        self.client_mock = AsyncMock(pyaprilaire.client.AprilaireClient)

        with patch(
            "pyaprilaire.client.AprilaireClient",
            return_value=self.client_mock,
        ):
            self.coordinator = AprilaireCoordinator(self.hass_mock, "", 0)

    async def test_start_listen(self):
        await self.coordinator.start_listen()

        self.assertEqual(self.coordinator.client.start_listen.call_count, 1)

    def test_stop_listen(self):
        self.coordinator.stop_listen()

        self.assertEqual(self.coordinator.client.stop_listen.call_count, 1)

    def test_set_updated_data(self):
        test_data = {"testKey": "testValue"}

        self.coordinator.async_set_updated_data(test_data)

        self.assertDictEqual(self.coordinator.data, test_data)

    def test_device_name_default(self):
        self.assertEqual(self.coordinator.device_name, "Aprilaire")

    def test_device_name(self):
        test_device_name = "Test Device Name"

        self.coordinator.async_set_updated_data({"name": test_device_name})

        self.assertEqual(self.coordinator.device_name, test_device_name)

    def test_device_info(self):
        test_mac_address = "1:2:3:4:5:6"
        test_device_name = "Test Device Name"
        test_model_number = 0
        test_hardware_revision = ord("B")
        test_firmware_major_revision = 1
        test_firmware_minor_revision = 5

        self.coordinator.async_set_updated_data(
            {
                "mac_address": test_mac_address,
                "name": test_device_name,
                "model_number": test_model_number,
                "hardware_revision": test_hardware_revision,
                "firmware_major_revision": test_firmware_major_revision,
                "firmware_minor_revision": test_firmware_minor_revision,
            }
        )

        device_info = self.coordinator.device_info

        self.assertEqual(device_info["identifiers"], {(DOMAIN, test_mac_address)})
        self.assertEqual(device_info["name"], test_device_name)
        self.assertEqual(device_info["model"], "8476W")
        self.assertEqual(device_info["hw_version"], "Rev. B")
        self.assertEqual(
            device_info["sw_version"],
            f"{test_firmware_major_revision}.{test_firmware_minor_revision:02}",
        )

    def test_hw_version_A(self):
        self.assertEqual(self.coordinator.get_hw_version({"hardware_revision": 1}), "1")

    def test_hw_version_B(self):
        self.assertEqual(
            self.coordinator.get_hw_version({"hardware_revision": ord("B")}), "Rev. B"
        )

    def test_updated_device(self):
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

        self.coordinator.async_set_updated_data(
            {
                "mac_address": test_mac_address,
                "name": test_device_name,
                "model_number": test_model_number,
                "hardware_revision": test_hardware_revision,
                "firmware_major_revision": test_firmware_major_revision,
                "firmware_minor_revision": test_firmware_minor_revision,
            }
        )

        self.coordinator.async_set_updated_data(
            {
                "mac_address": test_new_mac_address,
                "name": test_new_device_name,
                "model_number": test_new_model_number,
                "hardware_revision": test_new_hardware_revision,
                "firmware_major_revision": test_new_firmware_major_revision,
                "firmware_minor_revision": test_new_firmware_minor_revision,
            }
        )

        self.assertEqual(self.data_registry_mock.async_update_device.call_count, 1)

        new_device_info = self.data_registry_mock.async_update_device.call_args[1]

        self.assertDictEqual(
            new_device_info,
            new_device_info
            | {
                "name": test_new_device_name,
                "manufacturer": "Aprilaire",
                "model": "8810",
                "hw_version": "Rev. C",
                "sw_version": "2.06",
            },
        )

    async def test_wait_for_ready_mac_fail(self):
        ready_callback_mock = AsyncMock()

        with self.assertLogs(_LOGGER) as cm:
            await self.coordinator._wait_for_ready_run(ready_callback_mock)

        self.assertListEqual(
            cm.output,
            [
                "ERROR:custom_components.aprilaire:Missing MAC address, cannot create unique ID"
            ],
        )
        self.assertEqual(ready_callback_mock.call_count, 1)
        self.assertFalse(ready_callback_mock.call_args[0][0])

    async def test_wait_for_ready(self):
        ready_callback_mock = AsyncMock()

        wait_for_response_mock = AsyncMock()
        wait_for_response_mock.return_value = {"mac_address": "1:2:3:4:5:6"}

        self.coordinator.client.wait_for_response = wait_for_response_mock

        with self.assertNoLogs(_LOGGER):
            await self.coordinator._wait_for_ready_run(ready_callback_mock)

        wait_for_response_mock.assert_any_call(FunctionalDomain.IDENTIFICATION, 2, 30)
        wait_for_response_mock.assert_any_call(FunctionalDomain.IDENTIFICATION, 4, 30)
        wait_for_response_mock.assert_any_call(FunctionalDomain.CONTROL, 7, 30)
        wait_for_response_mock.assert_any_call(FunctionalDomain.SENSORS, 2, 30)

    async def test_wait_for_ready_wrapper(self):
        self.coordinator._wait_for_ready_run = AsyncMock()
        ready_callback_mock = AsyncMock()

        await self.coordinator.wait_for_ready(ready_callback_mock)

        self.coordinator._wait_for_ready_run.assert_called_once_with(
            ready_callback_mock
        )
