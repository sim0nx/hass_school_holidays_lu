"""Data update coordinator for the School Holidays LU Calendar integration."""

import datetime
import hashlib
import logging
from typing import Any

import aiohttp

from homeassistant.components.calendar import CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_LANGUAGE,
    DATA_URL,
    DEFAULT_LANGUAGE,
    DOMAIN,
    FALLBACK_SUMMARY,
    REQUEST_TIMEOUT,
    SUPPORTED_LANGUAGES,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

type HolidaysConfigEntry = ConfigEntry[HolidaysDataUpdateCoordinator]


def normalize_language(language: str | None) -> str:
    """Map a language code (e.g. "EN", "de-CH") to a supported dataset language."""
    if language:
        code = language.lower().split("-")[0].split("_")[0]
        if code in SUPPORTED_LANGUAGES:
            return code
    return DEFAULT_LANGUAGE


def get_localized_summary(raw_event: dict[str, Any], language: str) -> str:
    """Pick the summary in the preferred language, falling back to English, then any."""
    for lang in (language, DEFAULT_LANGUAGE, *SUPPORTED_LANGUAGES):
        if summary := raw_event.get(lang):
            if lang != language:
                _LOGGER.debug("Summary missing for %s, using %s", language, lang)
            return summary
    _LOGGER.warning("No summary found in any supported language for %s", raw_event)
    return FALLBACK_SUMMARY


def parse_events(raw_events: list[Any], language: str) -> list[CalendarEvent]:
    """Parse the raw dataset into all-day calendar events, sorted by start."""
    events: list[CalendarEvent] = []
    for raw_event in raw_events:
        if not isinstance(raw_event, dict):
            _LOGGER.warning("Skipping malformed event: %s", raw_event)
            continue

        start_str = raw_event.get("start_date")
        end_str = raw_event.get("end_date")
        if not isinstance(start_str, str) or not isinstance(end_str, str):
            _LOGGER.warning("Skipping event without start or end date: %s", raw_event)
            continue

        try:
            start = datetime.date.fromisoformat(start_str)
            # The dataset end date is inclusive, the calendar end date is exclusive.
            end = datetime.date.fromisoformat(end_str) + datetime.timedelta(days=1)
        except ValueError as err:
            _LOGGER.warning("Skipping event with invalid date %s: %s", raw_event, err)
            continue

        summary = get_localized_summary(raw_event, language)

        if not (uid := raw_event.get("uid")):
            uid = hashlib.sha256(f"{summary}{start_str}{end_str}".encode()).hexdigest()

        events.append(CalendarEvent(summary=summary, start=start, end=end, uid=uid))

    events.sort(key=lambda event: (event.start, event.end))
    return events


class HolidaysDataUpdateCoordinator(DataUpdateCoordinator[list[CalendarEvent]]):
    """Coordinator to fetch and parse the school holidays data."""

    config_entry: HolidaysConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: HolidaysConfigEntry) -> None:
        """Initialize the data update coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.language = normalize_language(config_entry.data.get(CONF_LANGUAGE))

    async def _async_update_data(self) -> list[CalendarEvent]:
        """Fetch the dataset and parse it into calendar events."""
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(
                DATA_URL, timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
            ) as response:
                response.raise_for_status()
                raw_events = await response.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Error fetching school holidays: {err}") from err
        except ValueError as err:
            raise UpdateFailed(f"Invalid JSON in school holidays data: {err}") from err

        if not isinstance(raw_events, list):
            raise UpdateFailed("Unexpected school holidays data format")

        return parse_events(raw_events, self.language)
