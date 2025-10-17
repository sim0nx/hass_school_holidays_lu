"""Data update coordinator for the School Holidays LU Calendar integration."""

import logging
from typing import Any

import aiohttp.http_exceptions

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import const

_LOGGER = logging.getLogger(__name__)


class HolidaysDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch and store the school holidays data."""

    def __init__(self, hass: HomeAssistant, event_url: str):
        """Initialize the data update coordinator."""
        self.event_url = event_url

        super().__init__(
            hass,
            _LOGGER,
            name=const.DOMAIN,
            update_interval=const.SCAN_INTERVAL,
        )

    def get_localized_summary(
        self, localized_summary_data: dict, preferred_lang: str, fallback_lang="EN"
    ) -> str:
        """Picks the best summary string based on preferred language and fallback."""

        # 1. Try the preferred language
        if preferred_lang in localized_summary_data:
            return localized_summary_data[preferred_lang]

        # 2. Try the primary fallback (English 'EN')
        if fallback_lang in localized_summary_data:
            _LOGGER.debug(
                "Title missing for %s, falling back to %s.",
                preferred_lang,
                fallback_lang,
            )
            return localized_summary_data[fallback_lang]

        # 3. Try any available supported language as a last resort
        for lang in const.SUPPORTED_LANGUAGES:
            if lang in localized_summary_data:
                _LOGGER.warning(
                    "Title missing for %s and EN, using available language %s.",
                    preferred_lang,
                    lang,
                )
                return localized_summary_data[lang]

        # 4. Final fallback
        _LOGGER.error(
            "No valid summary found in any supported language for event data."
        )
        return "Unknown Event"

    async def _async_update_data(self) -> list[Any]:
        """Fetch and parse the latest data directly from the URL. Fails if fetch is unsuccessful."""
        _LOGGER.debug("Coordinator updating data from %s", self.event_url)

        session = async_get_clientsession(self.hass)
        raw_events = None

        # --- Attempt: Fetch from URL ---
        try:
            async with session.get(
                self.event_url, timeout=20, allow_redirects=True
            ) as response:
                if response.status == 200:
                    raw_events = await response.json()
                    _LOGGER.debug("Successfully fetched events from URL.")
                else:
                    # Fail on non-200 status
                    _LOGGER.error(
                        "URL fetch failed (Status: %s). HTTP error encountered.",
                        response.status,
                    )
                    raise UpdateFailed(
                        "URL fetch failed with status: %s", response.status
                    )

        except (OSError, aiohttp.http_exceptions.HttpProcessingError) as err:
            # Fail on network/other error
            _LOGGER.error("Network error fetching data from URL: %s.", err)
            raise UpdateFailed(f"Network error fetching data: {err}")

        if raw_events is None:
            # Defensive check, should be covered by the try/except/status check
            raise UpdateFailed("URL fetch returned no data unexpectedly.")

        return raw_events  # Return the raw list for the entity to parse
