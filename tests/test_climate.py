"""Tests for the Aprilaire climate entity."""

# pylint: disable=protected-access,redefined-outer-name

from unittest.mock import Mock, PropertyMock, patch

import pytest
from homeassistant.components.climate import (
    DEFAULT_MAX_TEMP,
    DEFAULT_MIN_TEMP,
    FAN_AUTO,
    FAN_ON,
    PRESET_AWAY,
    PRESET_NONE,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.util.unit_system import METRIC_SYSTEM, US_CUSTOMARY_SYSTEM
from pyaprilaire.client import AprilaireClient
from pyaprilaire.const import Attribute

from custom_components.aprilaire.climate import (
    FAN_CIRCULATE,
    PRESET_PERMANENT_HOLD,
    PRESET_TEMPORARY_HOLD,
    PRESET_VACATION,
    AprilaireClimate,
    async_setup_entry,
)
from custom_components.aprilaire.coordinator import AprilaireCoordinator


@pytest.fixture
async def climate(config_entry: ConfigEntry, hass: HomeAssistant) -> AprilaireClimate:
    """Get a climate entity."""

    async_add_entities_mock = Mock()
    async_get_current_platform_mock = Mock()

    with patch(
        "homeassistant.helpers.entity_platform.async_get_current_platform",
        new=async_get_current_platform_mock,
    ):
        await async_setup_entry(hass, config_entry, async_add_entities_mock)

    sensors_list = async_add_entities_mock.call_args_list[0][0]

    climate = sensors_list[0][0]
    climate._attr_available = True
    climate.hass = hass

    return climate


def test_climate_min_temp(climate: AprilaireClimate):
    """Test the climate entity minimum temperature."""
    assert climate.min_temp == DEFAULT_MIN_TEMP


def test_climate_max_temp(climate: AprilaireClimate):
    """Test the climate entity maximum temperature."""
    assert climate.max_temp == DEFAULT_MAX_TEMP


def test_climate_fan_modes(climate: AprilaireClimate):
    """Test the climate entity fan modes."""
    assert climate.fan_modes == [FAN_AUTO, FAN_ON, FAN_CIRCULATE]


def test_climate_fan_mode(climate: AprilaireClimate, coordinator: AprilaireCoordinator):
    """Test the climate current fan mode."""

    assert climate.fan_mode is None

    coordinator.data = {
        Attribute.FAN_MODE: 0,
    }

    assert climate.fan_mode is None

    coordinator.data = {
        Attribute.FAN_MODE: 1,
    }

    assert climate.fan_mode == FAN_ON

    coordinator.data = {
        Attribute.FAN_MODE: 2,
    }

    assert climate.fan_mode == FAN_AUTO

    coordinator.data = {
        Attribute.FAN_MODE: 3,
    }

    assert climate.fan_mode == FAN_CIRCULATE


def test_supported_features_no_mode(climate: AprilaireClimate):
    """Test the climate entity supported features when there is no mode set."""

    assert (
        climate.supported_features
        == ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.FAN_MODE
    )


def test_supported_features_mode_4(
    climate: AprilaireClimate, coordinator: AprilaireCoordinator
):
    """Test the climate entity supported features when mode is 4."""

    coordinator.data = {
        Attribute.MODE: 4,
    }

    assert (
        climate.supported_features
        == ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.FAN_MODE
    )


def test_supported_features_mode_5(
    climate: AprilaireClimate, coordinator: AprilaireCoordinator
):
    """Test the climate entity supported features when mode is 5."""

    coordinator.data = {
        Attribute.MODE: 5,
    }

    assert (
        climate.supported_features
        == ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.FAN_MODE
    )


def test_supported_features_humidification_available(
    climate: AprilaireClimate, coordinator: AprilaireCoordinator
):
    """Test the climate entity supported features when humidification is available."""

    coordinator.data = {
        Attribute.HUMIDIFICATION_AVAILABLE: 2,
    }

    assert (
        climate.supported_features
        == ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TARGET_HUMIDITY
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.FAN_MODE
    )


def test_supported_features_dehumidification_available(
    climate: AprilaireClimate, coordinator: AprilaireCoordinator
):
    """Test the climate entity supported features when dehumidification is available."""

    coordinator.data = {
        Attribute.DEHUMIDIFICATION_AVAILABLE: 1,
    }

    assert (
        climate.supported_features
        == ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.FAN_MODE
    )


def test_supported_features_air_cleaning_available(
    climate: AprilaireClimate, coordinator: AprilaireCoordinator
):
    """Test the climate entity supported features when air cleaning is available."""

    coordinator.data = {
        Attribute.AIR_CLEANING_AVAILABLE: 1,
    }

    assert (
        climate.supported_features
        == ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.FAN_MODE
    )


def test_supported_features_ventilation_available(
    climate: AprilaireClimate, coordinator: AprilaireCoordinator
):
    """Test the climate entity supported features when ventilation is available."""

    coordinator.data = {
        Attribute.VENTILATION_AVAILABLE: 1,
    }

    assert (
        climate.supported_features
        == ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.FAN_MODE
    )


def test_current_temperature(
    climate: AprilaireClimate, coordinator: AprilaireCoordinator
):
    """Test the climate entity current temperature."""

    assert climate.current_temperature is None

    coordinator.data = {
        Attribute.INDOOR_TEMPERATURE_CONTROLLING_SENSOR_VALUE: 20,
    }

    assert climate.current_temperature == 20


def test_corrected_current_temperature(
    climate: AprilaireClimate, coordinator: AprilaireCoordinator
):
    """Test the climate entity current temperature when in fahrenheit."""

    climate.hass.config.units = US_CUSTOMARY_SYSTEM

    coordinator.data = {
        Attribute.INDOOR_TEMPERATURE_CONTROLLING_SENSOR_VALUE: 22.5,
    }

    assert climate.current_temperature > 22.5


def test_current_humidity(climate: AprilaireClimate, coordinator: AprilaireCoordinator):
    """Test the climate entity current humidity."""

    assert climate.current_humidity is None

    coordinator.data = {
        Attribute.INDOOR_HUMIDITY_CONTROLLING_SENSOR_VALUE: 20,
    }

    assert climate.current_humidity == 20


def test_target_temperature_low(
    climate: AprilaireClimate, coordinator: AprilaireCoordinator
):
    """Test the climate entity target low temperature."""

    assert climate.target_temperature_low is None

    coordinator.data = {
        Attribute.HEAT_SETPOINT: 20,
    }

    assert climate.target_temperature_low == 20


def test_target_temperature_high(
    climate: AprilaireClimate, coordinator: AprilaireCoordinator
):
    """Test the climate entity target high temperature."""

    assert climate.target_temperature_high is None

    coordinator.data = {
        Attribute.COOL_SETPOINT: 20,
    }

    assert climate.target_temperature_high == 20


def test_target_temperature(climate: AprilaireClimate):
    """Test the climate entity target temperature."""

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
        assert climate.target_temperature is None

        hvac_mode_mock.return_value = HVACMode.COOL

        assert climate.target_temperature == 25

        hvac_mode_mock.return_value = HVACMode.HEAT

        assert climate.target_temperature == 20


def test_target_temperature_step(climate: AprilaireClimate):
    """Test the climate entity target temperature step."""

    climate.hass.config.units = METRIC_SYSTEM
    assert climate.target_temperature_step == 0.5

    climate.hass.config.units = US_CUSTOMARY_SYSTEM
    assert climate.target_temperature_step == 1


def test_precision(climate: AprilaireClimate):
    """Test the climate entity precision."""

    climate.hass.config.units = METRIC_SYSTEM
    assert climate.precision == 0.5

    climate.hass.config.units = US_CUSTOMARY_SYSTEM
    assert climate.precision == 1


def test_hvac_mode(climate: AprilaireClimate, coordinator: AprilaireCoordinator):
    """Test the climate entity HVAC mode."""

    assert climate.hvac_mode is None

    coordinator.data = {
        Attribute.MODE: 0,
    }

    assert climate.hvac_mode is None

    coordinator.data = {
        Attribute.MODE: 1,
    }

    assert climate.hvac_mode == HVACMode.OFF

    coordinator.data = {
        Attribute.MODE: 2,
    }

    assert climate.hvac_mode == HVACMode.HEAT

    coordinator.data = {
        Attribute.MODE: 3,
    }

    assert climate.hvac_mode == HVACMode.COOL

    coordinator.data = {
        Attribute.MODE: 4,
    }

    assert climate.hvac_mode == HVACMode.HEAT

    coordinator.data = {
        Attribute.MODE: 5,
    }

    assert climate.hvac_mode == HVACMode.AUTO


def test_hvac_modes(climate: AprilaireClimate, coordinator: AprilaireCoordinator):
    """Test the climate entity HVAC modes."""

    assert climate.hvac_modes == []

    coordinator.data = {
        Attribute.THERMOSTAT_MODES: 0,
    }

    assert climate.hvac_modes == []

    coordinator.data = {
        Attribute.THERMOSTAT_MODES: 1,
    }

    assert climate.hvac_modes, [HVACMode.OFF == HVACMode.HEAT]

    coordinator.data = {
        Attribute.THERMOSTAT_MODES: 2,
    }

    assert climate.hvac_modes, [HVACMode.OFF == HVACMode.COOL]

    coordinator.data = {
        Attribute.THERMOSTAT_MODES: 3,
    }

    assert climate.hvac_modes, [HVACMode.OFF, HVACMode.HEAT == HVACMode.COOL]

    coordinator.data = {
        Attribute.THERMOSTAT_MODES: 4,
    }

    assert climate.hvac_modes, [HVACMode.OFF, HVACMode.HEAT == HVACMode.COOL]

    coordinator.data = {
        Attribute.THERMOSTAT_MODES: 5,
    }

    assert climate.hvac_modes == [
        HVACMode.OFF,
        HVACMode.HEAT,
        HVACMode.COOL,
        HVACMode.AUTO,
    ]

    coordinator.data = {
        Attribute.THERMOSTAT_MODES: 6,
    }

    assert climate.hvac_modes == [
        HVACMode.OFF,
        HVACMode.HEAT,
        HVACMode.COOL,
        HVACMode.AUTO,
    ]


def test_hvac_action(climate: AprilaireClimate, coordinator: AprilaireCoordinator):
    """Test the climate entity HVAC action."""

    assert climate.hvac_action == HVACAction.IDLE

    coordinator.data = {
        Attribute.HEATING_EQUIPMENT_STATUS: 0,
        Attribute.COOLING_EQUIPMENT_STATUS: 0,
    }

    assert climate.hvac_action == HVACAction.IDLE

    coordinator.data = {
        Attribute.HEATING_EQUIPMENT_STATUS: 1,
        Attribute.COOLING_EQUIPMENT_STATUS: 0,
    }

    assert climate.hvac_action == HVACAction.HEATING

    coordinator.data = {
        Attribute.HEATING_EQUIPMENT_STATUS: 1,
        Attribute.COOLING_EQUIPMENT_STATUS: 1,
    }

    assert climate.hvac_action == HVACAction.HEATING

    coordinator.data = {
        Attribute.HEATING_EQUIPMENT_STATUS: 0,
        Attribute.COOLING_EQUIPMENT_STATUS: 1,
    }

    assert climate.hvac_action == HVACAction.COOLING


def test_preset_modes(climate: AprilaireClimate, coordinator: AprilaireCoordinator):
    """Test the climate entity preset modes."""

    assert climate.preset_modes, [PRESET_NONE == PRESET_VACATION]

    coordinator.data = {
        Attribute.AWAY_AVAILABLE: 1,
    }

    assert climate.preset_modes, [PRESET_NONE, PRESET_VACATION == PRESET_AWAY]

    coordinator.data = {
        Attribute.HOLD: 1,
    }

    assert climate.preset_modes == [PRESET_NONE, PRESET_VACATION, PRESET_TEMPORARY_HOLD]

    coordinator.data = {
        Attribute.HOLD: 2,
    }

    assert climate.preset_modes == [PRESET_NONE, PRESET_VACATION, PRESET_PERMANENT_HOLD]

    coordinator.data = {
        Attribute.HOLD: 1,
        Attribute.AWAY_AVAILABLE: 1,
    }

    assert climate.preset_modes == [
        PRESET_NONE,
        PRESET_VACATION,
        PRESET_AWAY,
        PRESET_TEMPORARY_HOLD,
    ]

    coordinator.data = {
        Attribute.HOLD: 2,
        Attribute.AWAY_AVAILABLE: 1,
    }

    assert climate.preset_modes == [
        PRESET_NONE,
        PRESET_VACATION,
        PRESET_AWAY,
        PRESET_PERMANENT_HOLD,
    ]


def test_preset_mode(climate: AprilaireClimate, coordinator: AprilaireCoordinator):
    """Test the climate entity current preset mode."""

    assert climate.preset_mode == PRESET_NONE

    coordinator.data = {
        Attribute.HOLD: 0,
    }

    assert climate.preset_mode == PRESET_NONE

    coordinator.data = {
        Attribute.HOLD: 1,
    }

    assert climate.preset_mode == PRESET_TEMPORARY_HOLD

    coordinator.data = {
        Attribute.HOLD: 2,
    }

    assert climate.preset_mode == PRESET_PERMANENT_HOLD

    coordinator.data = {
        Attribute.HOLD: 3,
    }

    assert climate.preset_mode == PRESET_AWAY

    coordinator.data = {
        Attribute.HOLD: 4,
    }

    assert climate.preset_mode == PRESET_VACATION


def test_climate_target_humidity(
    climate: AprilaireClimate, coordinator: AprilaireCoordinator
):
    """Test the climate entity target humidity."""

    assert climate.target_humidity is None

    coordinator.data = {
        Attribute.HUMIDIFICATION_SETPOINT: 10,
    }

    assert climate.target_humidity == 10


def test_climate_min_humidity(climate: AprilaireClimate):
    """Test the climate entity minimum humidity."""

    assert climate.min_humidity == 10


def test_climate_max_humidity(climate: AprilaireClimate):
    """Test the climate entity maximum humidity."""

    assert climate.max_humidity == 50


def test_climate_extra_state_attributes(
    climate: AprilaireClimate, coordinator: AprilaireCoordinator
):
    """Test the climate entity extra state attributes."""

    coordinator.data = {
        Attribute.FAN_STATUS: 0,
    }

    assert climate.extra_state_attributes.get(Attribute.FAN_STATUS) == "off"

    coordinator.data = {
        Attribute.FAN_STATUS: 1,
    }

    assert climate.extra_state_attributes.get(Attribute.FAN_STATUS) == "on"


async def test_set_hvac_mode(
    client: AprilaireClient,
    climate: AprilaireClimate,
):
    """Test setting the climate entity HVAC mode."""

    await climate.async_set_hvac_mode(HVACMode.OFF)

    client.update_mode.assert_called_once_with(1)
    client.read_control.assert_called_once()
    client.reset_mock()

    await climate.async_set_hvac_mode(HVACMode.HEAT)

    client.update_mode.assert_called_once_with(2)
    client.read_control.assert_called_once()
    client.reset_mock()

    await climate.async_set_hvac_mode(HVACMode.COOL)

    client.update_mode.assert_called_once_with(3)
    client.read_control.assert_called_once()
    client.reset_mock()

    await climate.async_set_hvac_mode(HVACMode.AUTO)

    client.update_mode.assert_called_once_with(5)
    client.read_control.assert_called_once()
    client.reset_mock()

    with pytest.raises(ValueError):
        await climate.async_set_hvac_mode(HVACMode.HEAT_COOL)

    client.update_mode.assert_not_called()
    client.read_control.assert_not_called()
    client.reset_mock()

    with pytest.raises(ValueError):
        await climate.async_set_hvac_mode(HVACMode.DRY)

    client.update_mode.assert_not_called()
    client.read_control.assert_not_called()
    client.reset_mock()

    with pytest.raises(ValueError):
        await climate.async_set_hvac_mode(HVACMode.FAN_ONLY)

    client.update_mode.assert_not_called()
    client.read_control.assert_not_called()
    client.reset_mock()


async def test_set_temperature(
    client: AprilaireClient,
    climate: AprilaireClimate,
    coordinator: AprilaireCoordinator,
):
    """Test setting the climate entity temperature."""

    coordinator.data = {
        Attribute.MODE: 1,
    }

    await climate.async_set_temperature(temperature=20)

    client.update_setpoint.assert_called_once_with(0, 20)
    client.read_control.assert_called_once()
    client.reset_mock()

    coordinator.data = {
        Attribute.MODE: 3,
    }

    await climate.async_set_temperature(temperature=20)

    client.update_setpoint.assert_called_once_with(20, 0)
    client.read_control.assert_called_once()
    client.reset_mock()

    await climate.async_set_temperature(target_temp_low=20)

    client.update_setpoint.assert_called_once_with(0, 20)
    client.read_control.assert_called_once()
    client.reset_mock()

    await climate.async_set_temperature(target_temp_high=20)

    client.update_setpoint.assert_called_once_with(20, 0)
    client.read_control.assert_called_once()
    client.reset_mock()

    await climate.async_set_temperature(target_temp_low=20, target_temp_high=30)

    client.update_setpoint.assert_called_once_with(30, 20)
    client.read_control.assert_called_once()
    client.reset_mock()

    await climate.async_set_temperature()

    client.update_setpoint.assert_not_called()
    client.read_control.assert_not_called()
    client.reset_mock()


async def test_set_fan_mode(
    client: AprilaireClient,
    climate: AprilaireClimate,
):
    """Test setting the climate entity fan mode."""

    await climate.async_set_fan_mode(FAN_ON)

    client.update_fan_mode.assert_called_once_with(1)
    client.read_control.assert_called_once()
    client.reset_mock()

    await climate.async_set_fan_mode(FAN_AUTO)

    client.update_fan_mode.assert_called_once_with(2)
    client.read_control.assert_called_once()
    client.reset_mock()

    await climate.async_set_fan_mode(FAN_CIRCULATE)

    client.update_fan_mode.assert_called_once_with(3)
    client.read_control.assert_called_once()
    client.reset_mock()

    with pytest.raises(ValueError):
        await climate.async_set_fan_mode("")

    client.update_fan_mode.assert_not_called()
    client.read_control.assert_not_called()
    client.reset_mock()


async def test_set_preset_mode(
    client: AprilaireClient,
    climate: AprilaireClimate,
):
    """Test setting the climate entity preset mode."""

    await climate.async_set_preset_mode(PRESET_AWAY)

    client.set_hold.assert_called_once_with(3)
    client.read_scheduling.assert_called_once()
    client.reset_mock()

    await climate.async_set_preset_mode(PRESET_VACATION)

    client.set_hold.assert_called_once_with(4)
    client.read_scheduling.assert_called_once()
    client.reset_mock()

    await climate.async_set_preset_mode(PRESET_NONE)

    client.set_hold.assert_called_once_with(0)
    client.read_scheduling.assert_called_once()
    client.reset_mock()

    with pytest.raises(ValueError):
        await climate.async_set_preset_mode(PRESET_TEMPORARY_HOLD)

    client.set_hold.assert_not_called()
    client.read_scheduling.assert_not_called()
    client.reset_mock()

    with pytest.raises(ValueError):
        await climate.async_set_preset_mode(PRESET_PERMANENT_HOLD)

    client.set_hold.assert_not_called()
    client.read_scheduling.assert_not_called()
    client.reset_mock()

    with pytest.raises(ValueError):
        await climate.async_set_preset_mode("")

    client.set_hold.assert_not_called()
    client.read_scheduling.assert_not_called()
    client.reset_mock()


async def test_set_humidity(
    client: AprilaireClient,
    climate: AprilaireClimate,
    coordinator: AprilaireCoordinator,
):
    """Test setting the climate entity humidity."""

    coordinator.data[Attribute.HUMIDIFICATION_AVAILABLE] = 2

    await climate.async_set_humidity(30)

    client.set_humidification_setpoint.assert_called_with(30)


async def test_set_dehumidity(
    client: AprilaireClient,
    climate: AprilaireClimate,
    coordinator: AprilaireCoordinator,
):
    """Test setting the climate entity dehumidity."""

    with pytest.raises(ValueError):
        await climate.async_set_dehumidity(30)

    coordinator.data[Attribute.DEHUMIDIFICATION_AVAILABLE] = 1

    await climate.async_set_dehumidity(30)

    client.set_dehumidification_setpoint.assert_called_with(30)


async def test_trigger_air_cleaning_event(
    client: AprilaireClient,
    climate: AprilaireClimate,
    coordinator: AprilaireCoordinator,
):
    """Test triggering a climate entity air cleaning event."""

    with pytest.raises(ValueError):
        await climate.async_trigger_air_cleaning_event("3hour")

    coordinator.data[Attribute.AIR_CLEANING_AVAILABLE] = 1
    coordinator.data[Attribute.AIR_CLEANING_MODE] = 1

    await climate.async_trigger_air_cleaning_event("3hour")

    client.set_air_cleaning.assert_called_with(1, 3)
    assert coordinator.data[Attribute.AIR_CLEANING_MODE] == 1
    client.reset_mock()

    await climate.async_trigger_air_cleaning_event("24hour")

    client.set_air_cleaning.assert_called_with(1, 4)
    assert coordinator.data[Attribute.AIR_CLEANING_MODE] == 1
    client.reset_mock()

    with pytest.raises(ValueError):
        await climate.async_trigger_air_cleaning_event("bad")

    client.set_air_cleaning.assert_not_called()
    assert coordinator.data[Attribute.AIR_CLEANING_MODE] == 1
    client.reset_mock()


async def test_cancel_air_cleaning_event(
    client: AprilaireClient,
    climate: AprilaireClimate,
    coordinator: AprilaireCoordinator,
):
    """Test cancelling a climate entity air cleaning event."""

    with pytest.raises(ValueError):
        await climate.async_cancel_air_cleaning_event()

    coordinator.data[Attribute.AIR_CLEANING_AVAILABLE] = 1
    coordinator.data[Attribute.AIR_CLEANING_MODE] = 2

    await climate.async_cancel_air_cleaning_event()

    client.set_air_cleaning.assert_called_with(2, 0)
    assert coordinator.data[Attribute.AIR_CLEANING_MODE] == 2


async def test_set_air_cleaning_mode(
    client: AprilaireClient,
    climate: AprilaireClimate,
    coordinator: AprilaireCoordinator,
):
    """Test setting a climate entity air cleaning mode."""

    with pytest.raises(ValueError):
        await climate.async_set_air_cleaning_mode(0)

    with pytest.raises(ValueError):
        await climate.async_set_air_cleaning_mode(-1)

    with pytest.raises(ValueError):
        await climate.async_set_air_cleaning_mode(3)

    coordinator.data[Attribute.AIR_CLEANING_AVAILABLE] = 1
    coordinator.data[Attribute.AIR_CLEANING_EVENT] = 1

    await climate.async_set_air_cleaning_mode(0)
    client.set_air_cleaning.assert_called_with(0, 1)

    await climate.async_set_air_cleaning_mode(1)
    client.set_air_cleaning.assert_called_with(1, 1)

    await climate.async_set_air_cleaning_mode(2)
    client.set_air_cleaning.assert_called_with(2, 1)


async def test_toggle_air_cleaning_mode(
    client: AprilaireClient,
    climate: AprilaireClimate,
    coordinator: AprilaireCoordinator,
):
    """Test toggline a climate entity fresh air mode."""

    with pytest.raises(ValueError):
        await climate.async_toggle_air_cleaning_mode(0)

    with pytest.raises(ValueError):
        await climate.async_toggle_air_cleaning_mode(-1)

    with pytest.raises(ValueError):
        await climate.async_toggle_air_cleaning_mode(3)

    coordinator.data[Attribute.AIR_CLEANING_AVAILABLE] = 1
    coordinator.data[Attribute.AIR_CLEANING_EVENT] = 1
    coordinator.data[Attribute.AIR_CLEANING_MODE] = 0

    await climate.async_toggle_air_cleaning_mode(1)
    client.set_air_cleaning.assert_called_with(1, 1)

    coordinator.data[Attribute.AIR_CLEANING_MODE] = 1

    await climate.async_toggle_air_cleaning_mode(1)
    client.set_air_cleaning.assert_called_with(0, 1)


async def test_trigger_fresh_air_event(
    client: AprilaireClient,
    climate: AprilaireClimate,
    coordinator: AprilaireCoordinator,
):
    """Test triggering a climate entity fresh air event."""

    with pytest.raises(ValueError):
        await climate.async_trigger_fresh_air_event("3hour")

    coordinator.data[Attribute.VENTILATION_AVAILABLE] = 1
    coordinator.data[Attribute.FRESH_AIR_MODE] = 2

    await climate.async_trigger_fresh_air_event("3hour")
    client.set_fresh_air.assert_called_with(2, 2)
    assert coordinator.data[Attribute.FRESH_AIR_MODE] == 2

    client.reset_mock()

    await climate.async_trigger_fresh_air_event("24hour")

    client.set_fresh_air.assert_called_with(2, 3)
    assert coordinator.data[Attribute.FRESH_AIR_MODE] == 2
    client.reset_mock()

    with pytest.raises(ValueError):
        await climate.async_trigger_fresh_air_event("bad")

    client.set_fresh_air.assert_not_called()
    assert coordinator.data[Attribute.FRESH_AIR_MODE] == 2
    client.reset_mock()


async def test_cancel_fresh_air_event(
    client: AprilaireClient,
    climate: AprilaireClimate,
    coordinator: AprilaireCoordinator,
):
    """Test cancelling a climate entity fresh air event."""

    with pytest.raises(ValueError):
        await climate.async_cancel_fresh_air_event()

    coordinator.data[Attribute.VENTILATION_AVAILABLE] = 1
    coordinator.data[Attribute.FRESH_AIR_MODE] = 2

    await climate.async_cancel_fresh_air_event()

    client.set_fresh_air.assert_called_with(2, 0)
    assert coordinator.data[Attribute.FRESH_AIR_MODE] == 2


async def test_set_fresh_air_mode(
    client: AprilaireClient,
    climate: AprilaireClimate,
    coordinator: AprilaireCoordinator,
):
    """Test setting a climate entity fresh air mode."""

    with pytest.raises(ValueError):
        await climate.async_set_fresh_air_mode(0)

    with pytest.raises(ValueError):
        await climate.async_set_fresh_air_mode(-1)

    with pytest.raises(ValueError):
        await climate.async_set_fresh_air_mode(2)

    coordinator.data[Attribute.VENTILATION_AVAILABLE] = 1
    coordinator.data[Attribute.FRESH_AIR_EVENT] = 1

    await climate.async_set_fresh_air_mode(0)
    client.set_fresh_air.assert_called_with(0, 1)

    await climate.async_set_fresh_air_mode(1)
    client.set_fresh_air.assert_called_with(1, 1)


async def test_toggle_fresh_air_mode(
    client: AprilaireClient,
    climate: AprilaireClimate,
    coordinator: AprilaireCoordinator,
):
    """Test toggline a climate entity fresh air mode."""

    with pytest.raises(ValueError):
        await climate.async_toggle_fresh_air_mode(0)

    with pytest.raises(ValueError):
        await climate.async_toggle_fresh_air_mode(-1)

    with pytest.raises(ValueError):
        await climate.async_toggle_fresh_air_mode(2)

    coordinator.data[Attribute.VENTILATION_AVAILABLE] = 1
    coordinator.data[Attribute.FRESH_AIR_EVENT] = 1
    coordinator.data[Attribute.FRESH_AIR_MODE] = 0

    await climate.async_toggle_fresh_air_mode(1)
    client.set_fresh_air.assert_called_with(1, 1)

    coordinator.data[Attribute.FRESH_AIR_MODE] = 1

    await climate.async_toggle_fresh_air_mode(1)
    client.set_fresh_air.assert_called_with(0, 1)
