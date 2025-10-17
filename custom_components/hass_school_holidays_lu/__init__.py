"""The hass_school_holidays_lu custom calendar integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["calendar"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up School Holidays LU from a config entry."""
    # This will forward the setup request to the calendar.py platform file
    # which then runs async_setup_entry in that file.
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry for the School Holidays LU integration."""
    # This will forward the unload request to the calendar.py platform file
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "calendar")

    if unload_ok:
        _LOGGER.info("Integration hass_school_holidays_lu unloaded successfully.")

    return unload_ok
