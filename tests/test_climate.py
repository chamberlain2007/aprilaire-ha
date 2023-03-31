from custom_components.aprilaire.coordinator import AprilaireCoordinator
from custom_components.aprilaire.const import DOMAIN
from custom_components.aprilaire.climate import (
    async_setup_entry,
    AprilaireClimate,
    FAN_CIRCULATE,
    PRESET_TEMPORARY_HOLD,
    PRESET_PERMANENT_HOLD,
    PRESET_VACATION,
)

from homeassistant.config_entries import ConfigEntry, ConfigEntries
from homeassistant.core import Config, HomeAssistant, EventBus
from homeassistant.util import uuid as uuid_util

from homeassistant.components.climate import (
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
    FAN_AUTO,
    FAN_ON,
    HVAC_MODES,
    PRESET_AWAY,
    PRESET_NONE,
)

from homeassistant.const import (
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    PERCENTAGE,
    PRECISION_WHOLE,
)

import unittest
from unittest.mock import AsyncMock, Mock, PropertyMock, patch


class Test_Climate(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
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

        async_add_entities_mock = Mock()

        await async_setup_entry(
            self.hass_mock, self.config_entry_mock, async_add_entities_mock
        )

        sensors_list = async_add_entities_mock.call_args_list[0][0]

        self.climate: AprilaireClimate = sensors_list[0][0]
        self.climate._available = True

    async def test_climate(self):
        self.assertTrue(self.climate.available)
        self.assertEqual(self.climate.entity_name, "Thermostat")
        self.assertEqual(self.climate.temperature_unit, TEMP_CELSIUS)
        self.assertEqual(self.climate.precision, PRECISION_WHOLE)

    def test_climate_min_temp(self):
        self.assertEqual(self.climate.min_temp, 10)

    def test_climate_max_temp(self):
        self.assertEqual(self.climate.max_temp, 32)

    def test_climate_fan_status(self):
        self.coordinator_mock.data = {
            "fan_status": 0,
        }

        self.assertEqual(self.climate.fan, "off")

        self.coordinator_mock.data = {
            "fan_status": 1,
        }

        self.assertEqual(self.climate.fan, "on")

    def test_climate_fan_modes(self):
        self.assertEqual(self.climate.fan_modes, [FAN_AUTO, FAN_ON, FAN_CIRCULATE])

    def test_climate_fan_mode(self):
        self.assertIsNone(self.climate.fan_mode)

        self.coordinator_mock.data = {
            "fan_mode": 0,
        }

        self.assertIsNone(self.climate.fan_mode)

        self.coordinator_mock.data = {
            "fan_mode": 1,
        }

        self.assertEqual(self.climate.fan_mode, FAN_ON)

        self.coordinator_mock.data = {
            "fan_mode": 2,
        }

        self.assertEqual(self.climate.fan_mode, FAN_AUTO)

        self.coordinator_mock.data = {
            "fan_mode": 3,
        }

        self.assertEqual(self.climate.fan_mode, FAN_CIRCULATE)

    def test_supported_features_no_mode(self):
        self.assertEqual(
            self.climate.supported_features,
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.PRESET_MODE
            | ClimateEntityFeature.FAN_MODE,
        )

    def test_supported_features_mode_5(self):
        self.coordinator_mock.data = {
            "mode": 5,
        }

        self.assertEqual(
            self.climate.supported_features,
            ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
            | ClimateEntityFeature.PRESET_MODE
            | ClimateEntityFeature.FAN_MODE,
        )

    def test_supported_features_mode_4(self):
        self.coordinator_mock.data = {
            "mode": 4,
        }

        self.assertEqual(
            self.climate.supported_features,
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.PRESET_MODE
            | ClimateEntityFeature.FAN_MODE,
        )

    def test_current_temperature(self):
        self.assertIsNone(self.climate.current_temperature)

        self.coordinator_mock.data = {
            "indoor_temperature_controlling_sensor_value": 20,
        }

        self.assertEqual(self.climate.current_temperature, 20)

    def test_target_temperature_low(self):
        self.assertIsNone(self.climate.target_temperature_low)

        self.coordinator_mock.data = {
            "heat_setpoint": 20,
        }

        self.assertEqual(self.climate.target_temperature_low, 20)

    def test_target_temperature_high(self):
        self.assertIsNone(self.climate.target_temperature_high)

        self.coordinator_mock.data = {
            "cool_setpoint": 20,
        }

        self.assertEqual(self.climate.target_temperature_high, 20)

    def test_target_temperature(self):
        target_temperature_low_mock = PropertyMock(return_value=20)
        target_temperature_high_mock = PropertyMock(return_value=25)
        hvac_mode_mock = PropertyMock(return_value=HVACMode.OFF)

        with (
            patch(
                "custom_components.aprilaire.climate.AprilaireClimate.target_temperature_low",
                new=target_temperature_low_mock,
            ),
            patch(
                "custom_components.aprilaire.climate.AprilaireClimate.target_temperature_high",
                new=target_temperature_high_mock,
            ),
            patch(
                "custom_components.aprilaire.climate.AprilaireClimate.hvac_mode",
                new=hvac_mode_mock,
            ),
        ):
            self.assertIsNone(self.climate.target_temperature)

            hvac_mode_mock.return_value = HVACMode.COOL

            self.assertEqual(self.climate.target_temperature, 25)

            hvac_mode_mock.return_value = HVACMode.HEAT

            self.assertEqual(self.climate.target_temperature, 20)
