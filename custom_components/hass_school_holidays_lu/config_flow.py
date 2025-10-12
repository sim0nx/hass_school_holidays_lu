"""Config flow for hass_school_holidays_lu integration."""

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_URL

_LOGGER = logging.getLogger(__name__)

# Constants (MUST match calendar.py)
CONF_LANGUAGE = "language"
SUPPORTED_LANGUAGES = ["EN", "FR", "DE", "LB"]
STATIC_URL = "https://example.com/events.json"

# Schema to present to the user
DATA_SCHEMA = vol.Schema(
    {
        # Use vol.In for a dropdown selection of supported languages, defaulting to English
        vol.Required(CONF_LANGUAGE, default="EN"): vol.In(SUPPORTED_LANGUAGES),
    }
)


class HASSURLCalendarConfigFlow(
    config_entries.ConfigFlow, domain="hass_school_holidays_lu"
):
    """Handle a config flow for the school holidays URL calendar."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step to configure language."""

        # Check if a config entry already exists. This integration only supports one instance.
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        errors = {}

        if user_input is not None:
            selected_lang = user_input[CONF_LANGUAGE]

            # Create the config entry with the selected language and the static URL
            return self.async_create_entry(
                title=f"School Holidays LU ({selected_lang})",
                data={CONF_URL: STATIC_URL, CONF_LANGUAGE: selected_lang},
            )

        # Show the form to the user
        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_import(self, import_config):
        """Handle configuration from YAML. Not supported for this flow."""
        return self.async_abort(reason="not_supported")
