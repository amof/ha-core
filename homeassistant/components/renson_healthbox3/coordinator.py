"""Define an object to manage fetching Renson Healthbox3 data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from pyhealthbox3.healthbox3 import Healthbox3
from pyhealthbox3.models import Healthbox3DataObject

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, LOGGER

type RensonHealthboxConfigEntry = ConfigEntry[RensonHealthboxCoordinator]


@dataclass
class RensonHealthboxData:
    """Class for Renson Healthbox data."""

    healthbox_data: Healthbox3DataObject


class RensonHealthboxCoordinator(DataUpdateCoordinator[RensonHealthboxData]):
    """Class to manage fetching RensonHealthbox data."""

    config_entry: RensonHealthboxConfigEntry
    _current_version: str

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: RensonHealthboxConfigEntry,
        client: Healthbox3,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            logger=LOGGER,
            config_entry=config_entry,
            name=f"Renson Healthbox {client.host}",
            update_interval=timedelta(minutes=1),
        )
        self.client = client
        assert self.config_entry.unique_id
        self.serial_number = self.config_entry.unique_id

    async def _async_setup(self) -> None:
        """Set up the coordinator."""
        await self.client.async_get_data()
        self._current_version = self.client.firmware_version

    async def _async_update_data(self) -> RensonHealthboxData:
        try:
            await self.client.async_get_data()
        except Exception as error:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="update_error",
                translation_placeholders={"error": str(error)},
            ) from error
        if self.client.firmware_version != self._current_version:
            device_registry = dr.async_get(self.hass)
            device_entry = device_registry.async_get_device(
                identifiers={(DOMAIN, self.serial_number)}
            )
            assert device_entry
            device_registry.async_update_device(
                device_entry.id,
                sw_version=self.client.firmware_version,
            )
            self._current_version = self.client.firmware_version
        return RensonHealthboxData(self.client)
