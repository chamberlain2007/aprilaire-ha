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

from pyaprilaire.client import AprilaireClient

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
        self.client_mock = AsyncMock(AprilaireClient)

        self.coordinator_mock = AsyncMock(AprilaireCoordinator)
        self.coordinator_mock.data = {}
        self.coordinator_mock.client = self.client_mock

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

    def test_current_humidity(self):
        self.assertIsNone(self.climate.current_humidity)

        self.coordinator_mock.data = {
            "indoor_humidity_controlling_sensor_value": 20,
        }

        self.assertEqual(self.climate.current_humidity, 20)

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

    def test_hvac_mode(self):
        self.assertIsNone(self.climate.hvac_mode)

        self.coordinator_mock.data = {
            "mode": 0,
        }

        self.assertIsNone(self.climate.hvac_mode)

        self.coordinator_mock.data = {
            "mode": 1,
        }

        self.assertEqual(self.climate.hvac_mode, HVACMode.OFF)

        self.coordinator_mock.data = {
            "mode": 2,
        }

        self.assertEqual(self.climate.hvac_mode, HVACMode.HEAT)

        self.coordinator_mock.data = {
            "mode": 3,
        }

        self.assertEqual(self.climate.hvac_mode, HVACMode.COOL)

        self.coordinator_mock.data = {
            "mode": 4,
        }

        self.assertEqual(self.climate.hvac_mode, HVACMode.HEAT)

        self.coordinator_mock.data = {
            "mode": 5,
        }

        self.assertEqual(self.climate.hvac_mode, HVACMode.AUTO)

    def test_hvac_modes(self):
        self.assertEqual(self.climate.hvac_modes, [])

        self.coordinator_mock.data = {
            "thermostat_modes": 0,
        }

        self.assertEqual(self.climate.hvac_modes, [])

        self.coordinator_mock.data = {
            "thermostat_modes": 1,
        }

        self.assertEqual(self.climate.hvac_modes, [HVACMode.OFF, HVACMode.HEAT])

        self.coordinator_mock.data = {
            "thermostat_modes": 2,
        }

        self.assertEqual(self.climate.hvac_modes, [HVACMode.OFF, HVACMode.COOL])

        self.coordinator_mock.data = {
            "thermostat_modes": 3,
        }

        self.assertEqual(
            self.climate.hvac_modes, [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL]
        )

        self.coordinator_mock.data = {
            "thermostat_modes": 4,
        }

        self.assertEqual(
            self.climate.hvac_modes, [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL]
        )

        self.coordinator_mock.data = {
            "thermostat_modes": 5,
        }

        self.assertEqual(
            self.climate.hvac_modes,
            [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.AUTO],
        )

        self.coordinator_mock.data = {
            "thermostat_modes": 6,
        }

        self.assertEqual(
            self.climate.hvac_modes,
            [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.AUTO],
        )

    def test_hvac_action(self):
        self.assertEqual(self.climate.hvac_action, HVACAction.IDLE)

        self.coordinator_mock.data = {
            "heating_equipment_status": 0,
            "cooling_equipment_status": 0,
        }

        self.assertEqual(self.climate.hvac_action, HVACAction.IDLE)

        self.coordinator_mock.data = {
            "heating_equipment_status": 1,
            "cooling_equipment_status": 0,
        }

        self.assertEqual(self.climate.hvac_action, HVACAction.HEATING)

        self.coordinator_mock.data = {
            "heating_equipment_status": 1,
            "cooling_equipment_status": 1,
        }

        self.assertEqual(self.climate.hvac_action, HVACAction.HEATING)

        self.coordinator_mock.data = {
            "heating_equipment_status": 0,
            "cooling_equipment_status": 1,
        }

        self.assertEqual(self.climate.hvac_action, HVACAction.COOLING)

    def test_preset_modes(self):
        self.assertEqual(self.climate.preset_modes, [PRESET_NONE, PRESET_VACATION])

        self.coordinator_mock.data = {
            "away_available": 1,
        }

        self.assertEqual(
            self.climate.preset_modes, [PRESET_NONE, PRESET_VACATION, PRESET_AWAY]
        )

        self.coordinator_mock.data = {
            "hold": 1,
        }

        self.assertEqual(
            self.climate.preset_modes,
            [PRESET_NONE, PRESET_VACATION, PRESET_TEMPORARY_HOLD],
        )

        self.coordinator_mock.data = {
            "hold": 2,
        }

        self.assertEqual(
            self.climate.preset_modes,
            [PRESET_NONE, PRESET_VACATION, PRESET_PERMANENT_HOLD],
        )

        self.coordinator_mock.data = {
            "hold": 1,
            "away_available": 1,
        }

        self.assertEqual(
            self.climate.preset_modes,
            [PRESET_NONE, PRESET_VACATION, PRESET_AWAY, PRESET_TEMPORARY_HOLD],
        )

        self.coordinator_mock.data = {
            "hold": 2,
            "away_available": 1,
        }

        self.assertEqual(
            self.climate.preset_modes,
            [PRESET_NONE, PRESET_VACATION, PRESET_AWAY, PRESET_PERMANENT_HOLD],
        )

    def test_preset_mode(self):
        self.assertEqual(self.climate.preset_mode, PRESET_NONE)

        self.coordinator_mock.data = {
            "hold": 0,
        }

        self.assertEqual(self.climate.preset_mode, PRESET_NONE)

        self.coordinator_mock.data = {
            "hold": 1,
        }

        self.assertEqual(self.climate.preset_mode, PRESET_TEMPORARY_HOLD)

        self.coordinator_mock.data = {
            "hold": 2,
        }

        self.assertEqual(self.climate.preset_mode, PRESET_PERMANENT_HOLD)

        self.coordinator_mock.data = {
            "hold": 3,
        }

        self.assertEqual(self.climate.preset_mode, PRESET_AWAY)

        self.coordinator_mock.data = {
            "hold": 4,
        }

        self.assertEqual(self.climate.preset_mode, PRESET_VACATION)

    def test_climate_extra_state_attributes(self):
        self.coordinator_mock.data = {
            "fan_status": 0,
        }

        self.assertEqual(self.climate.extra_state_attributes, {"fan": "off"})

        self.coordinator_mock.data = {
            "fan_status": 1,
        }

        self.assertEqual(self.climate.extra_state_attributes, {"fan": "on"})

    async def test_set_hvac_mode(self):
        await self.climate.async_set_hvac_mode(HVACMode.OFF)

        self.client_mock.update_mode.assert_called_once_with(1)
        self.client_mock.read_control.assert_called_once()
        self.client_mock.reset_mock()

        await self.climate.async_set_hvac_mode(HVACMode.HEAT)

        self.client_mock.update_mode.assert_called_once_with(2)
        self.client_mock.read_control.assert_called_once()
        self.client_mock.reset_mock()

        await self.climate.async_set_hvac_mode(HVACMode.COOL)

        self.client_mock.update_mode.assert_called_once_with(3)
        self.client_mock.read_control.assert_called_once()
        self.client_mock.reset_mock()

        await self.climate.async_set_hvac_mode(HVACMode.AUTO)

        self.client_mock.update_mode.assert_called_once_with(5)
        self.client_mock.read_control.assert_called_once()
        self.client_mock.reset_mock()

        await self.climate.async_set_hvac_mode(HVACMode.HEAT_COOL)

        self.client_mock.update_mode.assert_not_called()
        self.client_mock.read_control.assert_not_called()
        self.client_mock.reset_mock()

        await self.climate.async_set_hvac_mode(HVACMode.DRY)

        self.client_mock.update_mode.assert_not_called()
        self.client_mock.read_control.assert_not_called()
        self.client_mock.reset_mock()

        await self.climate.async_set_hvac_mode(HVACMode.FAN_ONLY)

        self.client_mock.update_mode.assert_not_called()
        self.client_mock.read_control.assert_not_called()
        self.client_mock.reset_mock()

    async def test_set_temperature(self):
        self.coordinator_mock.data = {
            "mode": 1,
        }

        await self.climate.async_set_temperature(temperature=20)

        self.client_mock.update_setpoint.assert_called_once_with(0, 20)
        self.client_mock.read_control.assert_called_once()
        self.client_mock.reset_mock()

        self.coordinator_mock.data = {
            "mode": 3,
        }

        await self.climate.async_set_temperature(temperature=20)

        self.client_mock.update_setpoint.assert_called_once_with(20, 0)
        self.client_mock.read_control.assert_called_once()
        self.client_mock.reset_mock()

        await self.climate.async_set_temperature(target_temp_low=20)

        self.client_mock.update_setpoint.assert_called_once_with(0, 20)
        self.client_mock.read_control.assert_called_once()
        self.client_mock.reset_mock()

        await self.climate.async_set_temperature(target_temp_high=20)

        self.client_mock.update_setpoint.assert_called_once_with(20, 0)
        self.client_mock.read_control.assert_called_once()
        self.client_mock.reset_mock()

        await self.climate.async_set_temperature(
            target_temp_low=20, target_temp_high=30
        )

        self.client_mock.update_setpoint.assert_called_once_with(30, 20)
        self.client_mock.read_control.assert_called_once()
        self.client_mock.reset_mock()

        await self.climate.async_set_temperature()

        self.client_mock.update_setpoint.assert_not_called()
        self.client_mock.read_control.assert_not_called()
        self.client_mock.reset_mock()

    async def test_set_fan_mode(self):
        await self.climate.async_set_fan_mode(FAN_ON)

        self.client_mock.update_fan_mode.assert_called_once_with(1)
        self.client_mock.read_control.assert_called_once()
        self.client_mock.reset_mock()

        await self.climate.async_set_fan_mode(FAN_AUTO)

        self.client_mock.update_fan_mode.assert_called_once_with(2)
        self.client_mock.read_control.assert_called_once()
        self.client_mock.reset_mock()

        await self.climate.async_set_fan_mode(FAN_CIRCULATE)

        self.client_mock.update_fan_mode.assert_called_once_with(3)
        self.client_mock.read_control.assert_called_once()
        self.client_mock.reset_mock()

        await self.climate.async_set_fan_mode("")

        self.client_mock.update_fan_mode.assert_not_called()
        self.client_mock.read_control.assert_not_called()
        self.client_mock.reset_mock()

    async def test_set_preset_mode(self):
        await self.climate.async_set_preset_mode(PRESET_AWAY)

        self.client_mock.set_hold.assert_called_once_with(3)
        self.client_mock.read_scheduling.assert_called_once()
        self.client_mock.reset_mock()

        await self.climate.async_set_preset_mode(PRESET_VACATION)

        self.client_mock.set_hold.assert_called_once_with(4)
        self.client_mock.read_scheduling.assert_called_once()
        self.client_mock.reset_mock()

        await self.climate.async_set_preset_mode(PRESET_NONE)

        self.client_mock.set_hold.assert_called_once_with(0)
        self.client_mock.read_scheduling.assert_called_once()
        self.client_mock.reset_mock()

        await self.climate.async_set_preset_mode(PRESET_TEMPORARY_HOLD)

        self.client_mock.set_hold.assert_not_called()
        self.client_mock.read_scheduling.assert_not_called()
        self.client_mock.reset_mock()

        await self.climate.async_set_preset_mode(PRESET_PERMANENT_HOLD)

        self.client_mock.set_hold.assert_not_called()
        self.client_mock.read_scheduling.assert_not_called()
        self.client_mock.reset_mock()

        await self.climate.async_set_preset_mode("")

        self.client_mock.set_hold.assert_not_called()
        self.client_mock.read_scheduling.assert_not_called()
        self.client_mock.reset_mock()
