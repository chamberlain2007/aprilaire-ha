# pylint: skip-file

import logging
from unittest.mock import AsyncMock, Mock, PropertyMock, patch

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
from homeassistant.config_entries import ConfigEntries, ConfigEntry
from homeassistant.core import Config, EventBus, HomeAssistant
from homeassistant.util import uuid as uuid_util
from homeassistant.util.unit_system import METRIC_SYSTEM, US_CUSTOMARY_SYSTEM
from pyaprilaire.client import AprilaireClient
from pyaprilaire.const import Attribute

from custom_components.aprilaire.climate import (
    FAN_CIRCULATE,
    PRESET_PERMANENT_HOLD,
    PRESET_TEMPORARY_HOLD,
    PRESET_VACATION,
    AprilaireClimate,
    ExtendedClimateEntityFeature,
    async_setup_entry,
)
from custom_components.aprilaire.const import DOMAIN
from custom_components.aprilaire.coordinator import AprilaireCoordinator


@pytest.fixture
def logger():
    logger = logging.getLogger()
    logger.propagate = False

    return logger


@pytest.fixture
def client() -> AprilaireClient:
    return AsyncMock(AprilaireClient)


@pytest.fixture
def coordinator(
    client: AprilaireClient, logger: logging.Logger
) -> AprilaireCoordinator:
    coordinator_mock = AsyncMock(AprilaireCoordinator)
    coordinator_mock.data = {}
    coordinator_mock.client = client
    coordinator_mock.logger = logger

    return coordinator_mock


@pytest.fixture
def entry_id() -> str:
    return uuid_util.random_uuid_hex()


@pytest.fixture
def hass(coordinator: AprilaireCoordinator, entry_id: str) -> HomeAssistant:
    hass_mock = AsyncMock(HomeAssistant)
    hass_mock.data = {DOMAIN: {entry_id: coordinator}}
    hass_mock.config_entries = AsyncMock(ConfigEntries)
    hass_mock.bus = AsyncMock(EventBus)
    hass_mock.config = Mock(Config)
    hass_mock.config.units = METRIC_SYSTEM

    return hass_mock


@pytest.fixture
def config_entry(entry_id: str) -> ConfigEntry:
    config_entry_mock = AsyncMock(ConfigEntry)
    config_entry_mock.data = {"host": "test123", "port": 123}
    config_entry_mock.entry_id = entry_id

    return config_entry_mock


@pytest.fixture
async def climate(config_entry: ConfigEntry, hass: HomeAssistant) -> AprilaireClimate:
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


def test_climate_entity_name(climate: AprilaireClimate):
    assert climate.entity_name == "Thermostat"


def test_climate_min_temp(climate: AprilaireClimate):
    assert climate.min_temp == DEFAULT_MIN_TEMP


def test_climate_max_temp(climate: AprilaireClimate):
    assert climate.max_temp == DEFAULT_MAX_TEMP


def test_climate_fan_modes(climate: AprilaireClimate):
    assert climate.fan_modes == [FAN_AUTO, FAN_ON, FAN_CIRCULATE]


def test_climate_fan_mode(climate: AprilaireClimate, coordinator: AprilaireCoordinator):
    assert climate.fan_mode is None

    coordinator.data = {
        "fan_mode": 0,
    }

    assert climate.fan_mode is None

    coordinator.data = {
        "fan_mode": 1,
    }

    assert climate.fan_mode == FAN_ON

    coordinator.data = {
        "fan_mode": 2,
    }

    assert climate.fan_mode == FAN_AUTO

    coordinator.data = {
        "fan_mode": 3,
    }

    assert climate.fan_mode == FAN_CIRCULATE


def test_supported_features_no_mode(climate: AprilaireClimate):
    assert (
        climate.supported_features
        == ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.FAN_MODE,
    )


def test_supported_features_mode_5(
    climate: AprilaireClimate, coordinator: AprilaireCoordinator
):
    coordinator.data = {
        "mode": 5,
    }

    assert (
        climate.supported_features
        == ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.FAN_MODE,
    )


def test_supported_features_mode_4(
    climate: AprilaireClimate, coordinator: AprilaireCoordinator
):
    coordinator.data = {
        "mode": 4,
    }

    assert (
        climate.supported_features
        == ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.FAN_MODE,
    )


def test_supported_features_humidification_available(
    climate: AprilaireClimate, coordinator: AprilaireCoordinator
):
    coordinator.data = {
        "humidification_available": 2,
    }

    assert (
        climate.supported_features
        == ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TARGET_HUMIDITY
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.FAN_MODE,
    )


def test_supported_features_dehumidification_available(
    climate: AprilaireClimate, coordinator: AprilaireCoordinator
):
    coordinator.data = {
        "dehumidification_available": 1,
    }

    assert (
        climate.supported_features
        == ClimateEntityFeature.TARGET_TEMPERATURE
        | ExtendedClimateEntityFeature.TARGET_DEHUMIDITY
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.FAN_MODE,
    )


def test_supported_features_air_cleaning_available(
    climate: AprilaireClimate, coordinator: AprilaireCoordinator
):
    coordinator.data = {
        "air_cleaning_available": 1,
    }

    assert (
        climate.supported_features
        == ClimateEntityFeature.TARGET_TEMPERATURE
        | ExtendedClimateEntityFeature.AIR_CLEANING
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.FAN_MODE,
    )


def test_supported_features_ventilation_available(
    climate: AprilaireClimate, coordinator: AprilaireCoordinator
):
    coordinator.data = {
        "ventilation_available": 1,
    }

    assert (
        climate.supported_features
        == ClimateEntityFeature.TARGET_TEMPERATURE
        | ExtendedClimateEntityFeature.FRESH_AIR
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.FAN_MODE,
    )


def test_current_temperature(
    climate: AprilaireClimate, coordinator: AprilaireCoordinator
):
    assert climate.current_temperature is None

    coordinator.data = {
        "indoor_temperature_controlling_sensor_value": 20,
    }

    assert climate.current_temperature == 20


def test_corrected_current_temperature(
    climate: AprilaireClimate, coordinator: AprilaireCoordinator
):
    climate.hass.config.units = US_CUSTOMARY_SYSTEM

    coordinator.data = {
        "indoor_temperature_controlling_sensor_value": 22.5,
    }

    assert climate.current_temperature > 22.5


def test_current_humidity(climate: AprilaireClimate, coordinator: AprilaireCoordinator):
    assert climate.current_humidity is None

    coordinator.data = {
        "indoor_humidity_controlling_sensor_value": 20,
    }

    assert climate.current_humidity == 20


def test_target_temperature_low(
    climate: AprilaireClimate, coordinator: AprilaireCoordinator
):
    assert climate.target_temperature_low is None

    coordinator.data = {
        "heat_setpoint": 20,
    }

    assert climate.target_temperature_low == 20


def test_target_temperature_high(
    climate: AprilaireClimate, coordinator: AprilaireCoordinator
):
    assert climate.target_temperature_high is None

    coordinator.data = {
        "cool_setpoint": 20,
    }

    assert climate.target_temperature_high == 20


def test_target_temperature(climate: AprilaireClimate):
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
    climate.hass.config.units = METRIC_SYSTEM
    assert climate.target_temperature_step == 0.5

    climate.hass.config.units = US_CUSTOMARY_SYSTEM
    assert climate.target_temperature_step == 1


def test_precision(climate: AprilaireClimate):
    climate.hass.config.units = METRIC_SYSTEM
    assert climate.precision == 0.5

    climate.hass.config.units = US_CUSTOMARY_SYSTEM
    assert climate.precision == 1


def test_hvac_mode(climate: AprilaireClimate, coordinator: AprilaireCoordinator):
    assert climate.hvac_mode is None

    coordinator.data = {
        "mode": 0,
    }

    assert climate.hvac_mode is None

    coordinator.data = {
        "mode": 1,
    }

    assert climate.hvac_mode == HVACMode.OFF

    coordinator.data = {
        "mode": 2,
    }

    assert climate.hvac_mode == HVACMode.HEAT

    coordinator.data = {
        "mode": 3,
    }

    assert climate.hvac_mode == HVACMode.COOL

    coordinator.data = {
        "mode": 4,
    }

    assert climate.hvac_mode == HVACMode.HEAT

    coordinator.data = {
        "mode": 5,
    }

    assert climate.hvac_mode == HVACMode.AUTO


def test_hvac_modes(climate: AprilaireClimate, coordinator: AprilaireCoordinator):
    assert climate.hvac_modes == []

    coordinator.data = {
        "thermostat_modes": 0,
    }

    assert climate.hvac_modes == []

    coordinator.data = {
        "thermostat_modes": 1,
    }

    assert climate.hvac_modes, [HVACMode.OFF == HVACMode.HEAT]

    coordinator.data = {
        "thermostat_modes": 2,
    }

    assert climate.hvac_modes, [HVACMode.OFF == HVACMode.COOL]

    coordinator.data = {
        "thermostat_modes": 3,
    }

    assert climate.hvac_modes, [HVACMode.OFF, HVACMode.HEAT == HVACMode.COOL]

    coordinator.data = {
        "thermostat_modes": 4,
    }

    assert climate.hvac_modes, [HVACMode.OFF, HVACMode.HEAT == HVACMode.COOL]

    coordinator.data = {
        "thermostat_modes": 5,
    }

    assert (
        climate.hvac_modes
        == [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.AUTO],
    )

    coordinator.data = {
        "thermostat_modes": 6,
    }

    assert (
        climate.hvac_modes
        == [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.AUTO],
    )


def test_hvac_action(climate: AprilaireClimate, coordinator: AprilaireCoordinator):
    assert climate.hvac_action == HVACAction.IDLE

    coordinator.data = {
        "heating_equipment_status": 0,
        "cooling_equipment_status": 0,
    }

    assert climate.hvac_action == HVACAction.IDLE

    coordinator.data = {
        "heating_equipment_status": 1,
        "cooling_equipment_status": 0,
    }

    assert climate.hvac_action == HVACAction.HEATING

    coordinator.data = {
        "heating_equipment_status": 1,
        "cooling_equipment_status": 1,
    }

    assert climate.hvac_action == HVACAction.HEATING

    coordinator.data = {
        "heating_equipment_status": 0,
        "cooling_equipment_status": 1,
    }

    assert climate.hvac_action == HVACAction.COOLING


def test_preset_modes(climate: AprilaireClimate, coordinator: AprilaireCoordinator):
    assert climate.preset_modes, [PRESET_NONE == PRESET_VACATION]

    coordinator.data = {
        "away_available": 1,
    }

    assert climate.preset_modes, [PRESET_NONE, PRESET_VACATION == PRESET_AWAY]

    coordinator.data = {
        "hold": 1,
    }

    assert (
        climate.preset_modes == [PRESET_NONE, PRESET_VACATION, PRESET_TEMPORARY_HOLD],
    )

    coordinator.data = {
        "hold": 2,
    }

    assert (
        climate.preset_modes == [PRESET_NONE, PRESET_VACATION, PRESET_PERMANENT_HOLD],
    )

    coordinator.data = {
        "hold": 1,
        "away_available": 1,
    }

    assert (
        climate.preset_modes
        == [PRESET_NONE, PRESET_VACATION, PRESET_AWAY, PRESET_TEMPORARY_HOLD],
    )

    coordinator.data = {
        "hold": 2,
        "away_available": 1,
    }

    assert (
        climate.preset_modes
        == [PRESET_NONE, PRESET_VACATION, PRESET_AWAY, PRESET_PERMANENT_HOLD],
    )


def test_preset_mode(climate: AprilaireClimate, coordinator: AprilaireCoordinator):
    assert climate.preset_mode == PRESET_NONE

    coordinator.data = {
        "hold": 0,
    }

    assert climate.preset_mode == PRESET_NONE

    coordinator.data = {
        "hold": 1,
    }

    assert climate.preset_mode == PRESET_TEMPORARY_HOLD

    coordinator.data = {
        "hold": 2,
    }

    assert climate.preset_mode == PRESET_PERMANENT_HOLD

    coordinator.data = {
        "hold": 3,
    }

    assert climate.preset_mode == PRESET_AWAY

    coordinator.data = {
        "hold": 4,
    }

    assert climate.preset_mode == PRESET_VACATION


def test_climate_target_humidity(
    climate: AprilaireClimate, coordinator: AprilaireCoordinator
):
    assert climate.target_humidity is None

    coordinator.data = {
        "humidification_setpoint": 10,
    }

    assert climate.target_humidity == 10


def test_climate_min_humidity(climate: AprilaireClimate):
    assert climate.min_humidity == 10


def test_climate_max_humidity(climate: AprilaireClimate):
    assert climate.max_humidity == 50


def test_climate_extra_state_attributes(
    climate: AprilaireClimate, coordinator: AprilaireCoordinator
):
    coordinator.data = {
        "fan_status": 0,
    }

    assert climate.extra_state_attributes.get("fan_status") == "off"

    coordinator.data = {
        "fan_status": 1,
    }

    assert climate.extra_state_attributes.get("fan_status") == "on"


async def test_set_hvac_mode(
    client: AprilaireClient,
    climate: AprilaireClimate,
):
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
    coordinator.data = {
        "mode": 1,
    }

    await climate.async_set_temperature(temperature=20)

    client.update_setpoint.assert_called_once_with(0, 20)
    client.read_control.assert_called_once()
    client.reset_mock()

    coordinator.data = {
        "mode": 3,
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
    coordinator.data["humidification_available"] = 2

    await climate.async_set_humidity(30)

    client.set_humidification_setpoint.assert_called_with(30)


async def test_set_dehumidity(
    client: AprilaireClient,
    climate: AprilaireClimate,
    coordinator: AprilaireCoordinator,
):
    with pytest.raises(ValueError):
        await climate.async_set_dehumidity(30)

    coordinator.data["dehumidification_available"] = 1

    await climate.async_set_dehumidity(30)

    client.set_dehumidification_setpoint.assert_called_with(30)


async def test_trigger_air_cleaning_event(
    client: AprilaireClient,
    climate: AprilaireClimate,
    coordinator: AprilaireCoordinator,
):
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
    with pytest.raises(ValueError):
        await climate.async_cancel_air_cleaning_event()

    coordinator.data[Attribute.AIR_CLEANING_AVAILABLE] = 1
    coordinator.data[Attribute.AIR_CLEANING_MODE] = 2

    await climate.async_cancel_air_cleaning_event()

    client.set_air_cleaning.assert_called_with(2, 0)
    assert coordinator.data[Attribute.AIR_CLEANING_MODE] == 2


async def test_trigger_fresh_air_event(
    client: AprilaireClient,
    climate: AprilaireClimate,
    coordinator: AprilaireCoordinator,
):
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
    with pytest.raises(ValueError):
        await climate.async_cancel_fresh_air_event()

    coordinator.data[Attribute.VENTILATION_AVAILABLE] = 1
    coordinator.data[Attribute.FRESH_AIR_MODE] = 2

    await climate.async_cancel_fresh_air_event()

    client.set_fresh_air.assert_called_with(2, 0)
    assert coordinator.data[Attribute.FRESH_AIR_MODE] == 2
