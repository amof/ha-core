"""Entity class for Renson ventilation unit."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import RensonCoordinator


class RensonHealthboxSensor(CoordinatorEntity[RensonCoordinator]):
    """Base class for a Renson Healthbox sensor."""

    def __init__(self, name: str, coordinator: RensonCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._attr_device_info = DeviceInfo(
            name=f"{coordinator.api.serial}",
            identifiers={
                (
                    DOMAIN,
                    coordinator.config_entry.entry_id
                    if coordinator.config_entry is not None
                    else coordinator.api.serial,
                )
            },
            manufacturer=MANUFACTURER,
            model=coordinator.api.description,
            hw_version=coordinator.api.warranty_number,
            sw_version=coordinator.api.firmware_version,
        )
        self._attr_unique_id = coordinator.api.serial + name
        self.api = coordinator.api
