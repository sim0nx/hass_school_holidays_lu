"""Config flow for the School Holidays LU integration."""

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import CONF_LANGUAGE, DOMAIN, SUPPORTED_LANGUAGES
from .coordinator import normalize_language

LANGUAGE_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=[
            SelectOptionDict(value=code, label=label)
            for code, label in SUPPORTED_LANGUAGES.items()
        ],
        mode=SelectSelectorMode.DROPDOWN,
    )
)


class SchoolHolidaysLuConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for School Holidays LU."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user pick the language of the event titles."""
        if user_input is not None:
            language = user_input[CONF_LANGUAGE]
            return self.async_create_entry(
                title=f"School Holidays LU ({language.upper()})",
                data={CONF_LANGUAGE: language},
            )

        default_language = normalize_language(self.hass.config.language)
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_LANGUAGE, default=default_language
                    ): LANGUAGE_SELECTOR,
                }
            ),
        )
