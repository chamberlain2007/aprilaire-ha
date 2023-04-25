"""The Aprilaire climate component"""

from __future__ import annotations

import logging

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
    PRECISION_WHOLE,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_platform, service
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.climate import ClimateEntity

from enum import IntFlag

import voluptuous as vol

from .const import DOMAIN, LOG_NAME
from .coordinator import AprilaireCoordinator
from .entity import BaseAprilaireEntity

FAN_CIRCULATE = "Circulate"

PRESET_TEMPORARY_HOLD = "Temporary"
PRESET_PERMANENT_HOLD = "Permanent"
PRESET_VACATION = "Vacation"

SERVICE_SET_DEHUMIDITY = "set_dehumidity"
SERVICE_TRIGGER_AIR_CLEANING_EVENT = "trigger_air_cleaning_event"
SERVICE_CANCEL_AIR_CLEANING_EVENT = "cancel_air_cleaning_event"
SERVICE_TRIGGER_FRESH_AIR_EVENT = "trigger_fresh_air_event"
SERVICE_CANCEL_FRESH_AIR_EVENT = "cancel_fresh_air_event"

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


class ExtendedClimateEntityFeature(IntFlag):
    """Supported features of the Aprilaire climate entity."""

    TARGET_DEHUMIDITY = 2 << 10
    FRESH_AIR = 2 << 11
    AIR_CLEANING = 2 << 12


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add climates for passed config_entry in HA."""

    coordinator: AprilaireCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities([AprilaireClimate(coordinator)])

    platform = entity_platform.async_get_current_platform()

    platform.async_register_entity_service(
        SERVICE_SET_DEHUMIDITY,
        {vol.Required("dehumidity"): vol.Coerce(int)},
        "async_set_dehumidity",
        [ExtendedClimateEntityFeature.TARGET_DEHUMIDITY],
    )

    platform.async_register_entity_service(
        SERVICE_TRIGGER_AIR_CLEANING_EVENT,
        {vol.Required("event"): vol.Coerce(str)},
        "async_trigger_air_cleaning_event",
        [ExtendedClimateEntityFeature.AIR_CLEANING],
    )

    platform.async_register_entity_service(
        SERVICE_CANCEL_AIR_CLEANING_EVENT,
        {},
        "async_cancel_air_cleaning_event",
        [ExtendedClimateEntityFeature.AIR_CLEANING],
    )

    platform.async_register_entity_service(
        SERVICE_TRIGGER_FRESH_AIR_EVENT,
        {vol.Required("event"): vol.Coerce(str)},
        "async_trigger_fresh_air_event",
        [ExtendedClimateEntityFeature.FRESH_AIR],
    )

    platform.async_register_entity_service(
        SERVICE_CANCEL_FRESH_AIR_EVENT,
        {},
        "async_cancel_fresh_air_event",
        [ExtendedClimateEntityFeature.FRESH_AIR],
    )


class AprilaireClimate(BaseAprilaireEntity, ClimateEntity):
    """Climate entity for Aprilaire"""

    @property
    def entity_name(self):
        """Get name of entity"""

        return "Thermostat"

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

        if self._coordinator.data.get("humidification_available") == 2:
            features = features | ClimateEntityFeature.TARGET_HUMIDITY

        if self._coordinator.data.get("dehumidification_available") == 1:
            features = features | ExtendedClimateEntityFeature.TARGET_DEHUMIDITY

        if self._coordinator.data.get("air_cleaning_available") == 1:
            features = features | ExtendedClimateEntityFeature.AIR_CLEANING

        if self._coordinator.data.get("ventilation_available") == 1:
            features = features | ExtendedClimateEntityFeature.FRESH_AIR

        features = features | ClimateEntityFeature.PRESET_MODE

        features = features | ClimateEntityFeature.FAN_MODE

        return features

    @property
    def current_temperature(self):
        """Get current temperature"""
        return self._coordinator.data.get("indoor_temperature_controlling_sensor_value")

    @property
    def current_humidity(self):
        """Get current humidity"""
        return self._coordinator.data.get("indoor_humidity_controlling_sensor_value")

    @property
    def target_temperature_low(self):
        """Get heat setpoint"""
        return self._coordinator.data.get("heat_setpoint")

    @property
    def target_temperature_high(self):
        """Get cool setpoint"""
        return self._coordinator.data.get("cool_setpoint")

    @property
    def target_temperature(self) -> float | None:
        """Get the target temperature"""

        hvac_mode = self.hvac_mode

        if hvac_mode == HVACMode.COOL:
            return self.target_temperature_high
        if hvac_mode == HVACMode.HEAT:
            return self.target_temperature_low

        return None

    @property
    def target_humidity(self) -> int:
        """Get current target humidity"""
        return self._coordinator.data.get("humidification_setpoint")

    @property
    def hvac_mode(self) -> HVAC_MODES:
        """Get HVAC mode"""
        if "mode" not in self._coordinator.data:
            self._coordinator.logger.warning("No mode found in coordinator data")
            return None

        mode = self._coordinator.data["mode"]

        if mode not in HVAC_MODE_MAP:
            self._coordinator.logger.warning(
                "Invalid mode %d found in coordinator data", mode
            )
            return None

        return HVAC_MODE_MAP[mode]

    @property
    def hvac_modes(self) -> list[HVAC_MODES]:
        """Get supported HVAC modes"""

        thermostat_modes = self._coordinator.data.get("thermostat_modes")

        thermostat_modes_map = {
            1: [HVACMode.OFF, HVACMode.HEAT],
            2: [HVACMode.OFF, HVACMode.COOL],
            3: [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL],
            4: [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL],
            5: [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.AUTO],
            6: [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.AUTO],
        }

        return thermostat_modes_map.get(thermostat_modes, [])

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
        """Get the fan status"""
        return "on" if self._coordinator.data.get("fan_status", 0) == 1 else "off"

    @property
    def min_temp(self) -> float:
        """Get the minimum temperature"""
        return 10

    @property
    def max_temp(self) -> float:
        """Get the maximum temperature"""
        return 32

    @property
    def hvac_action(self) -> HVACAction | str | None:
        """Get the current HVAC action"""

        heating_equipment_status = self._coordinator.data.get(
            "heating_equipment_status", 0
        )

        if heating_equipment_status > 0:
            return HVACAction.HEATING

        cooling_equipment_status = self._coordinator.data.get(
            "cooling_equipment_status", 0
        )

        if cooling_equipment_status > 0:
            return HVACAction.COOLING

        return HVACAction.IDLE

    @property
    def preset_modes(self) -> list[str] | None:
        presets = [PRESET_NONE, PRESET_VACATION]

        if self._coordinator.data.get("away_available") == 1:
            presets.append(PRESET_AWAY)

        hold: int = self._coordinator.data.get("hold")

        if hold == 1:
            presets.append(PRESET_TEMPORARY_HOLD)
        elif hold == 2:
            presets.append(PRESET_PERMANENT_HOLD)

        return presets

    @property
    def preset_mode(self) -> str | None:
        hold: int = self._coordinator.data.get("hold")

        if hold == 1:
            return PRESET_TEMPORARY_HOLD

        if hold == 2:
            return PRESET_PERMANENT_HOLD

        if hold == 3:
            return PRESET_AWAY

        if hold == 4:
            return PRESET_VACATION

        return PRESET_NONE

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes."""
        return {
            "fan": self.fan,
        }

    @property
    def min_humidity(self) -> int:
        """Get the minimum supported humidity (static per Aprilaire)"""
        return 10

    @property
    def max_humidity(self) -> int:
        """Get the maximum supported humidity (static per Aprilaire)"""
        return 50

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the HVAC mode"""
        try:
            mode_value_index = list(HVAC_MODE_MAP.values()).index(hvac_mode)
        except ValueError:
            self._coordinator.logger.error("Invalid HVAC mode %s", hvac_mode)
            return

        mode_value = list(HVAC_MODE_MAP.keys())[mode_value_index]

        await self._coordinator.client.update_mode(mode_value)

        await self._coordinator.client.read_control()

    async def async_set_temperature(self, **kwargs) -> None:
        """Set the temperature setpoints"""
        cool_setpoint = 0
        heat_setpoint = 0

        if "temperature" in kwargs:
            if self._coordinator.data.get("mode") == 3:
                cool_setpoint = kwargs.get("temperature")
            else:
                heat_setpoint = kwargs.get("temperature")
        else:
            if "target_temp_low" in kwargs:
                heat_setpoint = kwargs.get("target_temp_low")
            if "target_temp_high" in kwargs:
                cool_setpoint = kwargs.get("target_temp_high")

        if cool_setpoint == 0 and heat_setpoint == 0:
            return

        await self._coordinator.client.update_setpoint(cool_setpoint, heat_setpoint)

        await self._coordinator.client.read_control()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set the fan mode."""

        try:
            fan_mode_value_index = list(FAN_MODE_MAP.values()).index(fan_mode)
        except ValueError:
            self._coordinator.logger.error("Invalid fan mode %s", fan_mode)
            return

        fan_mode_value = list(FAN_MODE_MAP.keys())[fan_mode_value_index]

        await self._coordinator.client.update_fan_mode(fan_mode_value)

        await self._coordinator.client.read_control()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode."""

        if preset_mode == PRESET_AWAY:
            await self._coordinator.client.set_hold(3)
        elif preset_mode == PRESET_VACATION:
            await self._coordinator.client.set_hold(4)
        elif preset_mode == PRESET_NONE:
            await self._coordinator.client.set_hold(0)
        else:
            return

        await self._coordinator.client.read_scheduling()

    async def async_set_humidity(self, humidity: int) -> None:
        """Set the target humidification setpoint"""
        await self._coordinator.client.set_humidification_setpoint(humidity)

    async def async_set_dehumidity(self, dehumidity: int) -> None:
        """Set the target dehumidification setpoint"""
        await self._coordinator.client.set_dehumidification_setpoint(dehumidity)

    async def async_trigger_air_cleaning_event(self, event: str) -> None:
        """Triggers an air cleaning event of 3 or 24 hours"""
        current_air_cleaning_mode = self._coordinator.data.get("air_cleaning_mode", 0)

        if event == "3hour":
            await self._coordinator.client.set_air_cleaning(
                current_air_cleaning_mode, 3
            )
        elif event == "24hour":
            await self._coordinator.client.set_air_cleaning(
                current_air_cleaning_mode, 4
            )
        else:
            raise ValueError("Invalid event")

    async def async_cancel_air_cleaning_event(self) -> None:
        """Cancels an existing air cleaning event"""
        current_air_cleaning_mode = self._coordinator.data.get("air_cleaning_mode", 0)

        await self._coordinator.client.set_air_cleaning(current_air_cleaning_mode, 0)

    async def async_trigger_fresh_air_event(self, event: str) -> None:
        """Triggers a fresh air event of 3 or 24 hours"""
        current_fresh_air_mode = self._coordinator.data.get("fresh_air_mode", 0)

        if event == "3hour":
            await self._coordinator.client.set_fresh_air(current_fresh_air_mode, 2)
        elif event == "24hour":
            await self._coordinator.client.set_fresh_air(current_fresh_air_mode, 3)
        else:
            raise ValueError("Invalid event")

    async def async_cancel_fresh_air_event(self) -> None:
        """Cancels a existing fresh air event"""
        current_fresh_air_mode = self._coordinator.data.get("fresh_air_mode", 0)

        await self._coordinator.client.set_fresh_air(current_fresh_air_mode, 0)
