"""Tests for the Aprilaire sensors."""

# pylint: disable=protected-access,redefined-outer-name

from unittest.mock import Mock

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, TEMP_CELSIUS, TEMP_FAHRENHEIT
from homeassistant.core import HomeAssistant
from homeassistant.util.unit_system import METRIC_SYSTEM, US_CUSTOMARY_SYSTEM

from custom_components.aprilaire.coordinator import AprilaireCoordinator
from custom_components.aprilaire.sensor import (
    AprilaireAirCleaningStatusSensor,
    AprilaireDehumidificationStatusSensor,
    AprilaireHumidificationStatusSensor,
    AprilaireIndoorHumidityControllingSensor,
    AprilaireIndoorTemperatureControllingSensor,
    AprilaireOutdoorHumidityControllingSensor,
    AprilaireOutdoorTemperatureControllingSensor,
    AprilaireVentilationStatusSensor,
    BaseAprilaireTemperatureSensor,
    async_setup_entry,
)


async def test_no_sensors_without_data(config_entry: ConfigEntry, hass: HomeAssistant):
    """Test that there are no sensors when there is no data."""

    async_add_entities_mock = Mock()

    await async_setup_entry(hass, config_entry, async_add_entities_mock)

    async_add_entities_mock.assert_called_once_with([])


def test_temperature_sensor_unit_of_measurement_sensor_option(
    coordinator: AprilaireCoordinator,
    hass: HomeAssistant,
):
    """Test the base temperature sensor's unit of measurement."""

    base_sensor = BaseAprilaireTemperatureSensor(coordinator)
    base_sensor.hass = hass

    base_sensor._sensor_option_unit_of_measurement = TEMP_CELSIUS
    assert base_sensor.unit_of_measurement == TEMP_CELSIUS

    base_sensor._sensor_option_unit_of_measurement = TEMP_FAHRENHEIT
    assert base_sensor.unit_of_measurement == TEMP_FAHRENHEIT


def test_base_temperature_sensor_value(
    coordinator: AprilaireCoordinator,
    hass: HomeAssistant,
):
    """Test the base temperature sensor's value"""
    base_sensor = BaseAprilaireTemperatureSensor(coordinator)
    base_sensor.hass = hass
    hass.config.units = METRIC_SYSTEM

    assert base_sensor.native_value is None


def test_base_temperature_sensor_display_precision(
    coordinator: AprilaireCoordinator,
    hass: HomeAssistant,
):
    """Test the base temperature sensor's display precision."""

    base_sensor = BaseAprilaireTemperatureSensor(coordinator)
    base_sensor.hass = hass

    hass.config.units = METRIC_SYSTEM
    assert base_sensor.suggested_display_precision == 1

    hass.config.units = US_CUSTOMARY_SYSTEM
    assert base_sensor.suggested_display_precision == 0


async def test_indoor_humidity_controlling_sensor(
    config_entry: ConfigEntry,
    coordinator: AprilaireCoordinator,
    hass: HomeAssistant,
):
    """Test the indoor humidity controlling sensor."""

    test_value = 50

    coordinator.data = {
        "indoor_humidity_controlling_sensor_status": 0,
        "indoor_humidity_controlling_sensor_value": test_value,
    }

    async_add_entities_mock = Mock()

    await async_setup_entry(hass, config_entry, async_add_entities_mock)

    sensors_list = async_add_entities_mock.call_args_list[0][0]

    assert len(sensors_list) == 1

    sensor = sensors_list[0][0]

    assert isinstance(sensor, AprilaireIndoorHumidityControllingSensor)

    sensor._attr_available = True

    assert sensor.device_class == SensorDeviceClass.HUMIDITY
    assert sensor.state_class == SensorStateClass.MEASUREMENT
    assert sensor.native_unit_of_measurement == PERCENTAGE
    assert sensor.available is True
    assert sensor.native_value == test_value
    assert sensor.entity_name == "Indoor Humidity Controlling Sensor"
    assert sensor.extra_state_attributes["status"] == 0
    assert sensor.extra_state_attributes["raw_sensor_value"] == test_value


async def test_outdoor_humidity_controlling_sensor(
    config_entry: ConfigEntry,
    coordinator: AprilaireCoordinator,
    hass: HomeAssistant,
):
    """Test the outdoor humidity controlling sensor."""

    test_value = 50

    coordinator.data = {
        "outdoor_humidity_controlling_sensor_status": 0,
        "outdoor_humidity_controlling_sensor_value": test_value,
    }

    async_add_entities_mock = Mock()

    await async_setup_entry(hass, config_entry, async_add_entities_mock)

    sensors_list = async_add_entities_mock.call_args_list[0][0]

    assert len(sensors_list) == 1

    sensor = sensors_list[0][0]

    assert isinstance(sensor, AprilaireOutdoorHumidityControllingSensor)

    sensor._attr_available = True

    assert sensor.device_class == SensorDeviceClass.HUMIDITY
    assert sensor.state_class == SensorStateClass.MEASUREMENT
    assert sensor.native_unit_of_measurement == PERCENTAGE
    assert sensor.available is True
    assert sensor.native_value == test_value
    assert sensor.entity_name == "Outdoor Humidity Controlling Sensor"
    assert sensor.extra_state_attributes["status"] == 0
    assert sensor.extra_state_attributes["raw_sensor_value"] == test_value


async def test_indoor_temperature_controlling_sensor(
    config_entry: ConfigEntry,
    coordinator: AprilaireCoordinator,
    hass: HomeAssistant,
):
    """Test the indoor temperature controlling sensor."""

    test_value = 25

    coordinator.data = {
        "indoor_temperature_controlling_sensor_status": 0,
        "indoor_temperature_controlling_sensor_value": test_value,
    }

    async_add_entities_mock = Mock()

    await async_setup_entry(hass, config_entry, async_add_entities_mock)

    sensors_list = async_add_entities_mock.call_args_list[0][0]

    assert len(sensors_list) == 1

    sensor = sensors_list[0][0]
    sensor.hass = hass

    assert isinstance(sensor, AprilaireIndoorTemperatureControllingSensor)

    sensor._attr_available = True

    assert sensor.device_class == SensorDeviceClass.TEMPERATURE
    assert sensor.state_class == SensorStateClass.MEASUREMENT
    assert sensor.native_unit_of_measurement == TEMP_CELSIUS
    assert sensor.available is True
    assert sensor.native_value == test_value
    assert sensor.entity_name == "Indoor Temperature Controlling Sensor"
    assert sensor.extra_state_attributes["status"] == 0
    assert sensor.extra_state_attributes["raw_sensor_value"] == test_value


async def test_outdoor_temperature_controlling_sensor(
    config_entry: ConfigEntry,
    coordinator: AprilaireCoordinator,
    hass: HomeAssistant,
):
    """Test the outdoor temperature controlling sensor."""

    test_value = 25

    coordinator.data = {
        "outdoor_temperature_controlling_sensor_status": 0,
        "outdoor_temperature_controlling_sensor_value": test_value,
    }

    async_add_entities_mock = Mock()

    await async_setup_entry(hass, config_entry, async_add_entities_mock)

    sensors_list = async_add_entities_mock.call_args_list[0][0]

    assert len(sensors_list) == 1

    sensor = sensors_list[0][0]
    sensor.hass = hass

    assert isinstance(sensor, AprilaireOutdoorTemperatureControllingSensor)

    sensor._attr_available = True

    assert sensor.device_class == SensorDeviceClass.TEMPERATURE
    assert sensor.state_class == SensorStateClass.MEASUREMENT
    assert sensor.native_unit_of_measurement == TEMP_CELSIUS
    assert sensor.available is True
    assert sensor.native_value == test_value
    assert sensor.entity_name == "Outdoor Temperature Controlling Sensor"
    assert sensor.extra_state_attributes["status"] == 0
    assert sensor.extra_state_attributes["raw_sensor_value"] == test_value


def test_indoor_temperature_controlling_sensor_fahrenheit(
    coordinator: AprilaireCoordinator,
    hass: HomeAssistant,
):
    """Test the indoor temperature controlling sensor in fahrenheit."""

    test_value = 25

    coordinator.data = {
        "indoor_temperature_controlling_sensor_status": 0,
        "indoor_temperature_controlling_sensor_value": test_value,
    }

    sensor = AprilaireIndoorTemperatureControllingSensor(coordinator)
    sensor._attr_available = True
    sensor._sensor_option_unit_of_measurement = TEMP_FAHRENHEIT
    sensor.hass = hass

    assert sensor.device_class == SensorDeviceClass.TEMPERATURE
    assert sensor.state_class == SensorStateClass.MEASUREMENT
    assert sensor.unit_of_measurement == TEMP_FAHRENHEIT
    assert sensor.available is True
    assert sensor.native_value == 25
    assert sensor.entity_name == "Indoor Temperature Controlling Sensor"
    assert sensor.extra_state_attributes["status"] == 0
    assert sensor.extra_state_attributes["raw_sensor_value"] == test_value


def test_outdoor_temperature_controlling_sensor_fahrenheit(
    coordinator: AprilaireCoordinator, hass: HomeAssistant
):
    """Test the outdoor temperature controlling sensor in fahrenheit."""

    test_value = 25

    coordinator.data = {
        "outdoor_temperature_controlling_sensor_status": 0,
        "outdoor_temperature_controlling_sensor_value": test_value,
    }

    sensor = AprilaireOutdoorTemperatureControllingSensor(coordinator)
    sensor._attr_available = True
    sensor._sensor_option_unit_of_measurement = TEMP_FAHRENHEIT
    sensor.hass = hass

    assert sensor.device_class == SensorDeviceClass.TEMPERATURE
    assert sensor.state_class == SensorStateClass.MEASUREMENT
    assert sensor.unit_of_measurement == TEMP_FAHRENHEIT
    assert sensor.available is True
    assert sensor.native_value == 25
    assert sensor.entity_name == "Outdoor Temperature Controlling Sensor"
    assert sensor.extra_state_attributes["status"] == 0
    assert sensor.extra_state_attributes["raw_sensor_value"] == test_value


async def test_dehumidification_available(
    config_entry: ConfigEntry, coordinator: AprilaireCoordinator, hass: HomeAssistant
):
    """Test the dehumidification status sensor."""

    coordinator.data = {
        "dehumidification_available": 1,
    }

    async_add_entities_mock = Mock()

    await async_setup_entry(hass, config_entry, async_add_entities_mock)

    sensors_list = async_add_entities_mock.call_args_list[0][0]

    assert len(sensors_list) == 1

    sensor = sensors_list[0][0]

    assert isinstance(sensor, AprilaireDehumidificationStatusSensor)


def test_dehumidification_status_sensor_0(
    coordinator: AprilaireCoordinator,
):
    """Test the dehumidification status sensor with status 0."""

    coordinator.data = {
        "dehumidification_status": 0,
    }

    sensor = AprilaireDehumidificationStatusSensor(coordinator)
    sensor._attr_available = True

    assert sensor.available is True
    assert sensor.entity_name == "Dehumidification Status"
    assert sensor.native_value == "Idle"


def test_dehumidification_status_sensor_1(
    coordinator: AprilaireCoordinator,
):
    """Test the dehumidification status sensor with status 1."""

    coordinator.data = {
        "dehumidification_status": 1,
    }

    sensor = AprilaireDehumidificationStatusSensor(coordinator)
    sensor._attr_available = True

    assert sensor.available is True
    assert sensor.entity_name == "Dehumidification Status"
    assert sensor.native_value == "Idle"


def test_dehumidification_status_sensor_2(
    coordinator: AprilaireCoordinator,
):
    """Test the dehumidification status sensor with status 2."""

    coordinator.data = {
        "dehumidification_status": 2,
    }

    sensor = AprilaireDehumidificationStatusSensor(coordinator)
    sensor._attr_available = True

    assert sensor.available is True
    assert sensor.entity_name == "Dehumidification Status"
    assert sensor.native_value == "On"


def test_dehumidification_status_sensor_3(
    coordinator: AprilaireCoordinator,
):
    """Test the dehumidification status sensor with status 3."""

    coordinator.data = {
        "dehumidification_status": 3,
    }

    sensor = AprilaireDehumidificationStatusSensor(coordinator)
    sensor._attr_available = True

    assert sensor.available is True
    assert sensor.entity_name == "Dehumidification Status"
    assert sensor.native_value == "On"


def test_dehumidification_status_sensor_4(
    coordinator: AprilaireCoordinator,
):
    """Test the dehumidification status sensor with status 4."""

    coordinator.data = {
        "dehumidification_status": 4,
    }

    sensor = AprilaireDehumidificationStatusSensor(coordinator)
    sensor._attr_available = True

    assert sensor.available is True
    assert sensor.entity_name == "Dehumidification Status"
    assert sensor.native_value == "Off"


def test_dehumidification_status_sensor_5(
    coordinator: AprilaireCoordinator,
):
    """Test the dehumidification status sensor with status 5."""

    coordinator.data = {
        "dehumidification_status": 5,
    }

    sensor = AprilaireDehumidificationStatusSensor(coordinator)
    sensor._attr_available = True

    assert sensor.available is True
    assert sensor.entity_name == "Dehumidification Status"
    assert sensor.native_value is None


async def test_humidification_available(
    config_entry: ConfigEntry, coordinator: AprilaireCoordinator, hass: HomeAssistant
):
    """Test the humidification status sensor."""

    coordinator.data = {
        "humidification_available": 1,
    }

    async_add_entities_mock = Mock()

    await async_setup_entry(hass, config_entry, async_add_entities_mock)

    sensors_list = async_add_entities_mock.call_args_list[0][0]

    assert len(sensors_list) == 1

    sensor = sensors_list[0][0]

    assert isinstance(sensor, AprilaireHumidificationStatusSensor)


def test_humidification_status_sensor_0(
    coordinator: AprilaireCoordinator,
):
    """Test the humidification status sensor with status 0."""

    coordinator.data = {
        "humidification_status": 0,
    }

    sensor = AprilaireHumidificationStatusSensor(coordinator)
    sensor._attr_available = True

    assert sensor.available is True
    assert sensor.entity_name == "Humidification Status"
    assert sensor.native_value == "Idle"


def test_humidification_status_sensor_1(
    coordinator: AprilaireCoordinator,
):
    """Test the humidification status sensor with status 1."""

    coordinator.data = {
        "humidification_status": 1,
    }

    sensor = AprilaireHumidificationStatusSensor(coordinator)
    sensor._attr_available = True

    assert sensor.available is True
    assert sensor.entity_name == "Humidification Status"
    assert sensor.native_value == "Idle"


def test_humidification_status_sensor_2(
    coordinator: AprilaireCoordinator,
):
    """Test the humidification status sensor with status 2."""

    coordinator.data = {
        "humidification_status": 2,
    }

    sensor = AprilaireHumidificationStatusSensor(coordinator)
    sensor._attr_available = True

    assert sensor.available is True
    assert sensor.entity_name == "Humidification Status"
    assert sensor.native_value == "On"


def test_humidification_status_sensor_3(
    coordinator: AprilaireCoordinator,
):
    """Test the humidification status sensor with status 3."""

    coordinator.data = {
        "humidification_status": 3,
    }

    sensor = AprilaireHumidificationStatusSensor(coordinator)
    sensor._attr_available = True

    assert sensor.available is True
    assert sensor.entity_name == "Humidification Status"
    assert sensor.native_value == "Off"


def test_humidification_status_sensor_4(
    coordinator: AprilaireCoordinator,
):
    """Test the humidification status sensor with status 4."""

    coordinator.data = {
        "humidification_status": 4,
    }

    sensor = AprilaireHumidificationStatusSensor(coordinator)
    sensor._attr_available = True

    assert sensor.available is True
    assert sensor.entity_name == "Humidification Status"
    assert sensor.native_value is None


async def test_ventilation_available(
    config_entry: ConfigEntry, coordinator: AprilaireCoordinator, hass: HomeAssistant
):
    """Test the ventilation status sensor."""

    coordinator.data = {
        "ventilation_available": 1,
    }

    async_add_entities_mock = Mock()

    await async_setup_entry(hass, config_entry, async_add_entities_mock)

    sensors_list = async_add_entities_mock.call_args_list[0][0]

    assert len(sensors_list) == 1

    sensor = sensors_list[0][0]

    assert isinstance(sensor, AprilaireVentilationStatusSensor)


def test_ventilation_status_sensor_0(
    coordinator: AprilaireCoordinator,
):
    """Test the ventilation status sensor with status 0."""

    coordinator.data = {
        "ventilation_status": 0,
    }

    sensor = AprilaireVentilationStatusSensor(coordinator)
    sensor._attr_available = True

    assert sensor.available is True
    assert sensor.entity_name == "Ventilation Status"
    assert sensor.native_value == "Idle"


def test_ventilation_status_sensor_1(
    coordinator: AprilaireCoordinator,
):
    """Test the ventilation status sensor with status 1."""

    coordinator.data = {
        "ventilation_status": 1,
    }

    sensor = AprilaireVentilationStatusSensor(coordinator)
    sensor._attr_available = True

    assert sensor.available is True
    assert sensor.entity_name == "Ventilation Status"
    assert sensor.native_value == "Idle"


def test_ventilation_status_sensor_2(
    coordinator: AprilaireCoordinator,
):
    """Test the ventilation status sensor with status 2."""

    coordinator.data = {
        "ventilation_status": 2,
    }

    sensor = AprilaireVentilationStatusSensor(coordinator)
    sensor._attr_available = True

    assert sensor.available is True
    assert sensor.entity_name == "Ventilation Status"
    assert sensor.native_value == "On"


def test_ventilation_status_sensor_3(
    coordinator: AprilaireCoordinator,
):
    """Test the ventilation status sensor with status 3."""

    coordinator.data = {
        "ventilation_status": 3,
    }

    sensor = AprilaireVentilationStatusSensor(coordinator)
    sensor._attr_available = True

    assert sensor.available is True
    assert sensor.entity_name == "Ventilation Status"
    assert sensor.native_value == "Idle"


def test_ventilation_status_sensor_4(
    coordinator: AprilaireCoordinator,
):
    """Test the ventilation status sensor with status 4."""

    coordinator.data = {
        "ventilation_status": 4,
    }

    sensor = AprilaireVentilationStatusSensor(coordinator)
    sensor._attr_available = True

    assert sensor.available is True
    assert sensor.entity_name == "Ventilation Status"
    assert sensor.native_value == "Idle"


def test_ventilation_status_sensor_5(
    coordinator: AprilaireCoordinator,
):
    """Test the ventilation status sensor with status 5."""

    coordinator.data = {
        "ventilation_status": 5,
    }

    sensor = AprilaireVentilationStatusSensor(coordinator)
    sensor._attr_available = True

    assert sensor.available is True
    assert sensor.entity_name == "Ventilation Status"
    assert sensor.native_value == "Idle"


def test_ventilation_status_sensor_6(
    coordinator: AprilaireCoordinator,
):
    """Test the ventilation status sensor with status 6."""

    coordinator.data = {
        "ventilation_status": 6,
    }

    sensor = AprilaireVentilationStatusSensor(coordinator)
    sensor._attr_available = True

    assert sensor.available is True
    assert sensor.entity_name == "Ventilation Status"
    assert sensor.native_value == "Off"


def test_ventilation_status_sensor_7(
    coordinator: AprilaireCoordinator,
):
    """Test the ventilation status sensor with status 7."""

    coordinator.data = {
        "ventilation_status": 7,
    }

    sensor = AprilaireVentilationStatusSensor(coordinator)
    sensor._attr_available = True

    assert sensor.available is True
    assert sensor.entity_name == "Ventilation Status"
    assert sensor.native_value is None


async def test_air_cleaning_available(
    config_entry: ConfigEntry,
    coordinator: AprilaireCoordinator,
    hass: HomeAssistant,
):
    """Test the air cleaning status sensor."""

    coordinator.data = {
        "air_cleaning_available": 1,
    }

    async_add_entities_mock = Mock()

    await async_setup_entry(hass, config_entry, async_add_entities_mock)

    sensors_list = async_add_entities_mock.call_args_list[0][0]

    assert len(sensors_list) == 1

    sensor = sensors_list[0][0]

    assert isinstance(sensor, AprilaireAirCleaningStatusSensor)


def test_air_cleaning_status_sensor_0(
    coordinator: AprilaireCoordinator,
):
    """Test the air cleaning status sensor with status 0."""

    coordinator.data = {
        "air_cleaning_status": 0,
    }

    sensor = AprilaireAirCleaningStatusSensor(coordinator)
    sensor._attr_available = True

    assert sensor.available is True
    assert sensor.entity_name == "Air Cleaning Status"
    assert sensor.native_value == "Idle"


def test_air_cleaning_status_sensor_1(
    coordinator: AprilaireCoordinator,
):
    """Test the air cleaning status sensor with status 1."""

    coordinator.data = {
        "air_cleaning_status": 1,
    }

    sensor = AprilaireAirCleaningStatusSensor(coordinator)
    sensor._attr_available = True

    assert sensor.available is True
    assert sensor.entity_name == "Air Cleaning Status"
    assert sensor.native_value == "Idle"


def test_air_cleaning_status_sensor_2(
    coordinator: AprilaireCoordinator,
):
    """Test the air cleaning status sensor with status 2."""

    coordinator.data = {
        "air_cleaning_status": 2,
    }

    sensor = AprilaireAirCleaningStatusSensor(coordinator)
    sensor._attr_available = True

    assert sensor.available is True
    assert sensor.entity_name == "Air Cleaning Status"
    assert sensor.native_value == "On"


def test_air_cleaning_status_sensor_3(
    coordinator: AprilaireCoordinator,
):
    """Test the air cleaning status sensor with status 3."""

    coordinator.data = {
        "air_cleaning_status": 3,
    }

    sensor = AprilaireAirCleaningStatusSensor(coordinator)
    sensor._attr_available = True

    assert sensor.available is True
    assert sensor.entity_name == "Air Cleaning Status"
    assert sensor.native_value == "Off"


def test_air_cleaning_status_sensor_4(
    coordinator: AprilaireCoordinator,
):
    """Test the air cleaning status sensor with status 4."""

    coordinator.data = {
        "air_cleaning_status": 4,
    }

    sensor = AprilaireAirCleaningStatusSensor(coordinator)
    sensor._attr_available = True

    assert sensor.available is True
    assert sensor.entity_name == "Air Cleaning Status"
    assert sensor.native_value is None
