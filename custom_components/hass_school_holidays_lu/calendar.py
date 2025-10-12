"""
Home Assistant Custom Calendar Integration (Example)

This module implements a custom calendar entity that fetches events
from a specified external URL containing a JSON list of events, 
with a local file fallback if the URL fetch fails.
"""
import asyncio
from datetime import datetime, timedelta, date
import json
import logging
import hashlib 
import os # NEW: Required for file path manipulation

# Standard HA library imports (mocked/aliased for this runnable example structure)
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.core import HomeAssistant, Config, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL


_LOGGER = logging.getLogger(__name__)

# Replace this with your actual external event URL
DEFAULT_URL = "https://example.com/events.json" 
# Updated DOMAIN to match your new integration name
DOMAIN = "hass_school_holidays_lu" 

# Define the supported languages for lookup
SUPPORTED_LANGUAGES = ["en", "fr", "de", "lb"]

CONF_LANGUAGE = "language"

# NEW: Filename for the local data fallback
FALLBACK_FILENAME = "events_fallback.json"


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    """Set up the calendar platform from a config entry."""
    # Retrieve the URL from the configuration entry data
    event_url = config_entry.data.get(CONF_URL, DEFAULT_URL)

    preferred_lang = config_entry.data.get(CONF_LANGUAGE, "EN").lower()

    # Use the title from the config entry, or default name
    entity_name = config_entry.title or "School Holidays LU"

    async_add_entities([CustomCalendarEntity(hass, event_url, entity_name, preferred_lang)])
    _LOGGER.info(f"CustomUrlCalendar successfully set up from config entry for URL: {event_url}")
    return True


class CustomCalendarEntity(CalendarEntity):
    """A calendar entity that fetches events from a URL."""

    def __init__(self, hass: HomeAssistant, event_url: str, name: str, preferred_lang: str):
        """Initialize the custom calendar."""
        # Call the mocked or actual CalendarEntity init
        super().__init__() 
        self.hass = hass
        self._event_url = event_url
        self._preferred_lang = preferred_lang
        self._attr_name = name
        self._attr_unique_id = f"{DOMAIN}_{hash(event_url)}"
        
        _LOGGER.debug(f"Initialized CustomCalendarEntity for URL: {self._event_url}")


    @property
    def event(self):
        """Return the next calendar event."""
        return None

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return 0
        
    async def _async_load_events_from_file(self, filename: str):
        """Load event data from a local JSON file in the component directory."""
        
        hass = self.hass 
        
        # Construct the path: <HA_CONFIG_DIR>/custom_components/hass_school_holidays_lu/events_fallback.json
        component_dir = os.path.join(hass.config.config_dir, "custom_components", DOMAIN)
        filepath = os.path.join(component_dir, filename)

        if not os.path.exists(filepath):
            _LOGGER.warning(f"Fallback file not found at: {filepath}")
            return None

        try:
            # File reading is a blocking IO operation, must use async_add_executor_job
            def load_json():
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)

            raw_events = await hass.async_add_executor_job(load_json)
            _LOGGER.info(f"Successfully loaded events from fallback file: {filepath}")
            return raw_events
            
        except json.JSONDecodeError:
            _LOGGER.error(f"Failed to decode JSON from fallback file: {filepath}")
            return None
        except Exception as e:
            _LOGGER.error(f"Error reading fallback file {filepath}: {e}")
            return None


    async def async_get_events(self, hass: HomeAssistant, start_date: datetime, end_date: datetime):
        """Return events between start_date and end_date, with URL fetch and file fallback.

        The events are fetched from the external JSON URL, with localized titles.
        """
        _LOGGER.debug(f"Fetching events from {self._event_url} between {start_date} and {end_date}")
        
        session = async_get_clientsession(hass)
        raw_events = None

        # --- 1. Primary Attempt: Fetch from URL ---
        try:
            async with session.get(self._event_url, timeout=10) as response:
                if response.status == 200:
                    raw_events = await response.json()
                    _LOGGER.debug("Successfully fetched events from URL.")
                else:
                    _LOGGER.warning(f"URL fetch failed (Status: {response.status}). HTTP error encountered.")
        
        except Exception as err:
            _LOGGER.error(f"Network error fetching data from URL: {err}. Proceeding to fallback.")
            
        # --- 2. Secondary Attempt: Fallback to local file if raw_events is None or HTTP failed ---
        if raw_events is None:
            raw_events = await self._async_load_events_from_file(FALLBACK_FILENAME)

        if raw_events is None:
             _LOGGER.error("Failed to retrieve events from both URL and fallback file. Returning empty list.")
             return []

        # Determine the preferred language code (e.g., 'FR')
        preferred_lang = self._preferred_lang
        _LOGGER.debug(f"Using configured language: {preferred_lang}")
            
        def _get_localized_summary(localized_summary_data, preferred_lang, fallback_lang="en"):
            """Picks the best summary string based on preferred language and fallback."""
            
            # 1. Try the preferred language (e.g., 'FR')
            if preferred_lang in localized_summary_data:
                return localized_summary_data[preferred_lang]

            # 2. Try the primary fallback (English 'EN')
            if fallback_lang in localized_summary_data:
                _LOGGER.debug(f"Title missing for {preferred_lang}, falling back to {fallback_lang}.")
                return localized_summary_data[fallback_lang]
                
            # 3. Try any available supported language as a last resort
            for lang in SUPPORTED_LANGUAGES:
                 if lang in localized_summary_data:
                    _LOGGER.warning(f"Title missing for {preferred_lang} and EN, using available language {lang}.")
                    return localized_summary_data[lang]
                    
            # 4. Final fallback
            _LOGGER.error(f"No valid summary found in any supported language for event data.")
            return "Unknown Event"


        events = []
        for raw_event in raw_events:
            try:
                # --- Event Parsing and Validation ---
                start_dt_str = raw_event.get("start_date")
                end_dt_str = raw_event.get("end_date")
                uid = raw_event.get("uid")
                
                # Retrieve the localized summary
                summary = _get_localized_summary(raw_event, preferred_lang)

                if not all([summary, start_dt_str, end_dt_str]):
                    _LOGGER.warning(f"Skipping malformed event (missing summary, start, or end): {raw_event}")
                    continue

                # Parse dates. HA requires aware datetime objects.
                # Assuming the external JSON uses ISO 8601 format (e.g., "2025-10-15T10:00:00+02:00")
                try:
                    start_dt = date.fromisoformat(start_dt_str)
                    end_dt = date.fromisoformat(end_dt_str)
                except ValueError as ve:
                    _LOGGER.error(f"Date parsing failed for event {summary}: {ve}")
                    continue

                # Skip events that are outside the requested range
                if end_dt <= start_date.date() or start_dt >= end_date.date():
                    continue
                
                # --- Generate deterministic UID if missing ---
                if not uid:
                    # Concatenate the critical, unchanging event details
                    unique_string = f"{summary}{start_dt_str}{end_dt_str}"
                    # Use SHA256 to create a deterministic hash as the UID
                    uid = hashlib.sha256(unique_string.encode('utf-8')).hexdigest()
                    _LOGGER.debug(f"Generated UID for event '{summary}': {uid[:8]}...")


                # Create the CalendarEvent object
                event = CalendarEvent(
                    summary=summary,
                    start=start_dt,
                    end=end_dt,
                    description=raw_event.get("description"),
                    location=raw_event.get("location"),
                    uid=uid, # Use the retrieved or generated UID
                )
                events.append(event)

            except Exception as e:
                _LOGGER.error(f"Error processing individual event {raw_event}: {e}")
                continue

        _LOGGER.debug(f"Successfully processed {len(events)} events.")
        return events
