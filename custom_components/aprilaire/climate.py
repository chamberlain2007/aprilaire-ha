"""The Aprilaire climate component"""

from __future__ import annotations

import logging

from homeassistant.components.climate import (
    HVAC_MODES,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
    FAN_AUTO,
    FAN_ON,
)

from homeassistant.const import (
    TEMP_CELSIUS,
    PRECISION_WHOLE,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.climate import ClimateEntity

from . import AprilaireCoordinator
from .const import DOMAIN, LOG_NAME
from .entity import BaseAprilaireEntity
from .utils import encode_temperature

FAN_CIRCULATE = "Circulate"

HVAC_MODE_MAP = {
    1: HVACMode.OFF,
    2: HVACMode.HEAT,
    3: HVACMode.COOL,
    4: HVACMode.HEAT,
    5: HVACMode.AUTO,
}

FAN_MODE_MAP = {
    1: FAN_ON,
    2: FAN_AUTO,
    3: FAN_CIRCULATE,
}

_LOGGER = logging.getLogger(LOG_NAME)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add climates for passed config_entry in HA."""

    coordinator: AprilaireCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities([AprilaireClimate(coordinator)])


class AprilaireClimate(BaseAprilaireEntity, ClimateEntity):
    """Climate entity for Aprilaire"""

    @property
    def name(self):
        """Get name of entity"""
        
        return f"Aprilaire Thermostat"

    @property
    def temperature_unit(self):
        """Get temperature units"""
        return TEMP_CELSIUS

    @property
    def precision(self):
        """Get precision"""
        return PRECISION_WHOLE

    @property
    def supported_features(self):
        """Get supported features"""
        features = 0

        if "mode" not in self._coordinator.data:
            features = features | ClimateEntityFeature.TARGET_TEMPERATURE
        else:
            mode = self._coordinator.data["mode"]

            if mode == 5:
                features = features | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
            else:
                features = features | ClimateEntityFeature.TARGET_TEMPERATURE

        features = features | ClimateEntityFeature.FAN_MODE

        return features

    @property
    def current_temperature(self):
        """Get current temperature"""
        return (
            self._coordinator.data["indoor_temperature_controlling_sensor_value"]
            if "indoor_temperature_controlling_sensor_value" in self._coordinator.data
            else None
        )

    @property
    def target_temperature_low(self):
        """Get heat setpoint"""
        return self._coordinator.data["heat_setpoint"] if "heat_setpoint" in self._coordinator.data else None

    @property
    def target_temperature_high(self):
        """Get cool setpoint"""
        return self._coordinator.data["cool_setpoint"] if "cool_setpoint" in self._coordinator.data else None

    @property
    def target_temperature(self) -> float | None:
        hvac_mode = self.hvac_mode

        if hvac_mode == HVACMode.COOL:
            return self.target_temperature_high
        elif hvac_mode == HVACMode.HEAT:
            return self.target_temperature_low

        return None

    @property
    def current_humidity(self):
        """Get current humidity"""
        return (
            self._coordinator.data["indoor_humidity_controlling_sensor_value"]
            if "indoor_humidity_controlling_sensor_value" in self._coordinator.data
            else None
        )

    @property
    def hvac_mode(self) -> HVAC_MODES:
        """Get HVAC mode"""
        if "mode" not in self._coordinator.data:
            _LOGGER.warn("No mode found in coordinator data")
            return None

        mode = self._coordinator.data["mode"]

        if mode not in HVAC_MODE_MAP:
            _LOGGER.warn("Invalid mode %d found in coordinator data", mode)
            return None

        return HVAC_MODE_MAP[mode]

    @property
    def hvac_modes(self) -> list[HVAC_MODES]:
        """Get supported HVAC modes"""
        return [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.AUTO]

    @property
    def fan_mode(self):
        """Get fan mode"""
        if "fan_mode" not in self._coordinator.data:
            return None

        fan_mode = self._coordinator.data["fan_mode"]

        if fan_mode not in FAN_MODE_MAP:
            return None

        return FAN_MODE_MAP[fan_mode]

    @property
    def fan_modes(self):
        """Get supported fan modes"""
        return [FAN_AUTO, FAN_ON, FAN_CIRCULATE]

    @property
    def fan(self):
        return "on" if self._coordinator.data.get("fan_status", 0) == 1 else "off"

    @property
    def min_temp(self) -> float:
        return 10

    @property
    def max_temp(self) -> float:
        return 32

    @property
    def hvac_action(self) -> HVACAction | str | None:
        heating_equipment_status = self._coordinator.data.get("heating_equipment_status", 0)

        if heating_equipment_status > 0:
            return HVACAction.HEATING

        cooling_equipment_status = self._coordinator.data.get("cooling_equipment_status", 0)

        if cooling_equipment_status > 0:
            return HVACAction.COOLING

        return HVACAction.IDLE

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes."""
        return {
            "fan": self.fan,
        }

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the HVAC mode"""
        try:
            mode_value_index = list(HVAC_MODE_MAP.values()).index(hvac_mode)
        except ValueError:
            _LOGGER.error("Invalid HVAC mode %s", hvac_mode)
            return

        mode_value = list(HVAC_MODE_MAP.keys())[mode_value_index]

        await self._coordinator.client.update_mode(mode_value)

        await self._coordinator.client.read_control()

    async def async_set_temperature(self, **kwargs) -> None:
        """Set the temperature setpoints"""
        cool_setpoint = 0
        heat_setpoint = 0

        if "temperature" in kwargs:
            if self._coordinator.data["mode"] == 3:
                cool_setpoint = encode_temperature(kwargs.get("temperature"))
            else:
                heat_setpoint = encode_temperature(kwargs.get("temperature"))
        else:
            if "target_temp_low" in kwargs:
                heat_setpoint = encode_temperature(kwargs.get("target_temp_low"))
            if "target_temp_high" in kwargs:
                cool_setpoint = encode_temperature(kwargs.get("target_temp_high"))

        if cool_setpoint == 0 and heat_setpoint == 0:
            return

        await self._coordinator.client.update_setpoint(cool_setpoint, heat_setpoint)

        await self._coordinator.client.read_control()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set the fan mode."""

        try:
            fan_mode_value_index = list(FAN_MODE_MAP.values()).index(fan_mode)
        except ValueError:
            _LOGGER.error("Invalid fan mode %s", fan_mode)
            return

        fan_mode_value = list(FAN_MODE_MAP.keys())[fan_mode_value_index]

        await self._coordinator.client.update_fan_mode(fan_mode_value)

        await self._coordinator.client.read_control()