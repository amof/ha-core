"""The Renson integration."""

from __future__ import annotations

from pyhealthbox3.healthbox3 import Healthbox3

from homeassistant.const import CONF_API_KEY, CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .coordinator import RensonHealthboxConfigEntry, RensonHealthboxCoordinator

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
]


async def async_setup_entry(
    hass: HomeAssistant, entry: RensonHealthboxConfigEntry
) -> bool:
    """Set up Renson Healthbox from a config entry."""

    client = Healthbox3(
        host=entry.data[CONF_HOST],
        api_key=entry.data.get(CONF_API_KEY, None),
        session=async_get_clientsession(hass),
    )

    coordinator = RensonHealthboxCoordinator(hass, entry, client)

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: RensonHealthboxConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
