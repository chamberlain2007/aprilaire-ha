"""The Aprilaire humidifier component."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.components.humidifier import (
    MODE_AUTO,
    HumidifierDeviceClass,
    HumidifierEntity,
    HumidifierEntityFeature,
    HumidifierAction
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from pyaprilaire.const import Attribute

from .const import (
    DOMAIN,
)
from .coordinator import AprilaireCoordinator
from .entity import BaseAprilaireEntity

MODE_MANUAL = "manual"
MODE_VACATION = "vacation"

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add humidifier and dehumdifier for passed config_entry in HA."""

    coordinator: AprilaireCoordinator = hass.data[DOMAIN][config_entry.unique_id]

    entities = []
    if coordinator.data.get(Attribute.DEHUMIDIFICATION_AVAILABLE) == 1:
        entities.append(AprilaireDehumidifier(coordinator))

    if coordinator.data.get(Attribute.HUMIDIFICATION_AVAILABLE) in [1, 2]:
        entities.append(AprilaireHumidifier(coordinator))

    async_add_entities(entities)

class AprilaireDehumidifier(BaseAprilaireEntity, HumidifierEntity):
    """Dehumidifier entity for Aprilaire."""

    _attr_supported_features = HumidifierEntityFeature.MODES
    _attr_device_class = HumidifierDeviceClass.DEHUMIDIFIER
    _attr_available_modes = [MODE_MANUAL]
    _attr_min_humidity = 10
    _attr_max_humidity = 50

    def __init__(self, coordinator: AprilaireCoordinator) -> None:
        self._last_target_humidity = None
        self._last_is_on = None

    @property
    def action(self) -> HumidifierAction | None:
        """Return the current action."""
        
        status = self.coordinator.data.get(
            Attribute.DEHUMIDIFICATION_STATUS
        )

        if status == 0 or status == 1:
            return HumidifierAction.IDLE
        
        if status == 2 or status == 3:
            return HumidifierAction.DRYING
        
        if status == 4:
            return HumidifierAction.OFF
        
        raise ValueError(f"Unsupported dehumidification status {status}")

    @property
    def target_humidity(self) -> int:
        """Return the target humidity."""
        setpoint = self.coordinator.data.get(Attribute.DEHUMIDIFICATION_SETPOINT)
        """Don't set last target humidity if off."""
        self._last_is_on = setpoint != 0
        self._last_target_humidity = setpoint if self._last_is_on else self._last_target_humidity
        return self._last_target_humidity

    @property
    def is_on(self) -> bool:
        """Return true if on."""
        return self.target_humidity != 0

    @property
    def mode(self) -> str | None:
        """Get dehumidifier mode."""

        mode = self.coordinator.data.get(Attribute.MODE)

        if mode == 4:
            return MODE_VACATION

        return MODE_MANUAL

    @property
    def current_humidity(self) -> int | None:
        """Get current humidity."""
        return self.coordinator.data.get(
            Attribute.INDOOR_HUMIDITY_CONTROLLING_SENSOR_VALUE
        )

    async def async_set_humidity(self, humidity: int) -> None:
        """Set the target dehumidification setpoint."""
        await self.coordinator.client.set_dehumidification_setpoint(humidity)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the dehumidifier."""
        await self.async_set_humidity(self._last_target_humidity)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the dehumidifier."""
        await self.async_set_humidity(0)

    async def async_set_mode(self, mode: str) -> None:
        """Set the mode of the thermostat."""
        await self.coordinator.client.read_scheduling()

class AprilaireHumidifier(BaseAprilaireEntity, HumidifierEntity):
    """Humidifier entity for Aprilaire."""

    _attr_supported_features = HumidifierEntityFeature.MODES
    _attr_device_class = HumidifierDeviceClass.HUMIDIFIER
    _attr_min_humidity = 10
    _attr_max_humidity = 50

    def __init__(self, coordinator: AprilaireCoordinator) -> None:
        self._last_target_humidity = None
        self._last_is_on = None

    @property
    def action(self) -> HumidifierAction | None:
        """Return the current action."""
        
        status = self.coordinator.data.get(
            Attribute.HUMIDIFICATION_STATUS
        )

        if status == 0 or status == 1:
            return HumidifierAction.IDLE
        
        if status == 2:
            return HumidifierAction.HUMIDIFYING
        
        if status == 3:
            return HumidifierAction.OFF
        
        raise ValueError(f"Unsupported humidification status {status}")

    @property
    def target_humidity(self) -> int:
        """Return the target humidity."""
        setpoint = self.coordinator.data.get(Attribute.HUMIDIFICATION_SETPOINT)
        """Don't set last target humidity if off."""
        self._last_is_on = setpoint != 0
        self._last_target_humidity = setpoint if self._last_is_on else self._last_target_humidity
        return self._last_target_humidity

    @property
    def is_on(self) -> bool:
        """Return true if on."""
        return self.target_humidity != 0

    @property
    def mode(self) -> str | None:
        """Get humdification mode."""

        available = self.coordinator.data.get(Attribute.HUMIDIFICATION_AVAILABLE)

        if (available == 1):
            return MODE_AUTO
        
        if (available == 2):
            return MODE_MANUAL

        raise ValueError(f"Unsupported humidification mode {available}")

    @property
    def available_modes(self) -> list[str] | None:
        """Returns available modes."""

        available = self.coordinator.data.get(Attribute.HUMIDIFICATION_AVAILABLE)

        if (available == 1):
            return [MODE_AUTO]
        
        if (available == 2):
            return [MODE_MANUAL]

        raise ValueError(f"Unsupported humidification mode {available}")

    @property
    def current_humidity(self) -> int | None:
        """Get current humidity."""
        return self.coordinator.data.get(
            Attribute.INDOOR_HUMIDITY_CONTROLLING_SENSOR_VALUE
        )

    async def async_set_humidity(self, humidity: int) -> None:
        """Set the target dehumidification setpoint."""
        await self.coordinator.client.set_humidification_setpoint(humidity)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the humidifier."""
        await self.async_set_humidity(self._last_target_humidity)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the humidifier."""
        await self.async_set_humidity(0)

    async def async_set_mode(self, mode: str) -> None:
        """Set the mode of the thermostat."""
        await self.coordinator.client.read_scheduling()

