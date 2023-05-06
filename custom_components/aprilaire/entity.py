"""Base functionality for Aprilaire entities"""

from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .coordinator import AprilaireCoordinator


class BaseAprilaireEntity(CoordinatorEntity):
    """Base for Aprilaire entities"""

    _attr_available = False

    def __init__(self, coordinator: AprilaireCoordinator) -> None:
        """Initialize the entity"""
        super().__init__(coordinator)
        self._coordinator = coordinator

        self._update_available()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        self._coordinator.logger.debug("Current data: %s", self._coordinator.data)

        self._update_available()

        self.async_write_ha_state()

    def _update_available(self):
        """Update the entity availability"""

        connected: bool = self._coordinator.data.get(
            "connected", None
        ) or self._coordinator.data.get("reconnecting", None)

        stopped: bool = self._coordinator.data.get("stopped", None)

        if stopped:
            self._attr_available = False
        elif not connected:
            self._attr_available = False
        else:
            self._attr_available = (
                self._coordinator.data.get("mac_address", None) is not None
            )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._attr_available

    @property
    def should_poll(self) -> bool:
        """Do not need to poll"""
        return False

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        return slugify(
            self._coordinator.data["mac_address"].replace(":", "_")
            + "_"
            + self.entity_name
        )

    @property
    def name(self) -> str | None:
        """Return the name of the entity."""
        return f"{self._coordinator.device_name} {self.entity_name}"

    @property
    def entity_name(self) -> str | None:
        """Return the name of the derived entity."""
        return None

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return device specific attributes."""

        return self._coordinator.device_info

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes."""
        return {
            "device_name": self._coordinator.device_name,
            "device_location": self._coordinator.data.get("location"),
        }
