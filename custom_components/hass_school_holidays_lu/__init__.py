"""The hass_school_holidays_lu custom calendar integration."""

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import HolidaysConfigEntry, HolidaysDataUpdateCoordinator

PLATFORMS = [Platform.CALENDAR]


async def async_setup_entry(hass: HomeAssistant, entry: HolidaysConfigEntry) -> bool:
    """Set up School Holidays LU from a config entry."""
    coordinator = HolidaysDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: HolidaysConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
