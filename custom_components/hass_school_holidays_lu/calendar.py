"""School holidays in Luxembourg custom Home Assistant calendar Integration."""

from datetime import date, datetime
import hashlib
import logging

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity

from . import const
from .coordinator import HolidaysDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
):
    """Set up the calendar platform from a config entry."""
    event_url = config_entry.data.get(CONF_URL, const.DEFAULT_URL)
    preferred_lang = config_entry.data.get(const.CONF_LANGUAGE, "EN").lower()

    coordinator = HolidaysDataUpdateCoordinator(hass, event_url)
    await coordinator.async_config_entry_first_refresh()

    entity_name = config_entry.title or f"School Holidays LU ({preferred_lang})"

    async_add_entities(
        [
            HolidaysCalendarEntity(
                coordinator, entity_name, preferred_lang, config_entry.entry_id
            )
        ]
    )

    _LOGGER.info(
        "%s successfully set up with DataUpdateCoordinator (Interval: %s).",
        const.DOMAIN,
        coordinator.update_method,
    )
    return True


class HolidaysCalendarEntity(CalendarEntity, Entity):
    """A calendar entity that fetches events from a URL via a coordinator."""

    def __init__(
        self,
        coordinator: HolidaysDataUpdateCoordinator,
        name: str,
        preferred_lang: str,
        entry_id: str,
    ):
        """Initialize the custom calendar."""
        super().__init__()

        # Store the coordinator and add the entity as a listener for updates
        self.coordinator = coordinator
        self._attr_name = name
        self._preferred_lang = preferred_lang
        self._attr_unique_id = f"{entry_id}_{preferred_lang}"

        self._unsub_update = None
        self._events_cache: list[
            CalendarEvent
        ] = []  # Cache for parsed HA CalendarEvent objects
        self._update_events_cache()  # Initial parsing

        _LOGGER.debug(
            "Initialized HolidaysCalendarEntity for URL: %s (Lang: %s)",
            self.coordinator.event_url,
            self._preferred_lang,
        )

    @property
    def event(self):
        """Return the next calendar event."""
        return None

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return 0

    @property
    def should_poll(self) -> bool:
        """Return false because the coordinator handles the update cycle."""
        return False

    @property
    def available(self) -> bool:
        """Return True if coordinator is connected and has data."""
        return self.coordinator.last_update_success

    # Implement the coordinator update listener logic
    async def async_added_to_hass(self) -> None:
        """When entity is added to hass, register the update callback."""
        # Use coordinator's update signal to trigger entity update
        self._unsub_update = self.coordinator.async_add_listener(
            self._handle_coordinator_update
        )

    async def async_will_remove_from_hass(self) -> None:
        """When entity is removed from hass, remove the update callback."""
        if self._unsub_update:
            self._unsub_update()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # When coordinator data changes, re-parse events and mark entity dirty
        self._update_events_cache()
        self.async_write_ha_state()

    def _update_events_cache(self) -> None:
        """Parse raw data from coordinator into CalendarEvent objects."""
        raw_events = self.coordinator.data
        if not raw_events:
            self._events_cache = []
            return

        events = []
        for raw_event in raw_events:
            try:
                # --- Event Parsing and Validation ---
                start_dt_str = raw_event.get("start_date")
                end_dt_str = raw_event.get("end_date")
                uid = raw_event.get("uid")

                # Retrieve the localized summary using the coordinator's helper
                summary = self.coordinator.get_localized_summary(
                    raw_event, self._preferred_lang
                )

                if not all([summary, start_dt_str, end_dt_str]):
                    _LOGGER.warning(
                        "Skipping malformed event (missing summary, start, or end): %s",
                        raw_event,
                    )
                    continue

                # Parse dates. Assuming ISO 8601 format
                try:
                    start_dt = date.fromisoformat(start_dt_str)
                    end_dt = date.fromisoformat(end_dt_str)
                except ValueError as ve:
                    _LOGGER.error("Date parsing failed for event %s: %s", summary, ve)
                    continue

                # --- Generate deterministic UID if missing ---
                if not uid:
                    unique_string = f"{summary}{start_dt_str}{end_dt_str}"
                    uid = hashlib.sha256(unique_string.encode("utf-8")).hexdigest()

                # Create the CalendarEvent object
                event = CalendarEvent(
                    summary=summary,
                    start=start_dt,
                    end=end_dt,
                    description=raw_event.get("description"),
                    location=raw_event.get("location"),
                    uid=uid,
                )
                events.append(event)
            except (TypeError, AttributeError) as e:
                _LOGGER.error("Error processing individual event %s: %s", raw_event, e)
                continue

        self._events_cache = events
        _LOGGER.debug("Entity cache updated with %s events.", len(events))

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Return cached events between start_date and end_date."""

        # This method now only filters the events from the shared, cached data
        filtered_events = [
            event
            for event in self._events_cache
            # Check if the event overlaps with the requested period
            if event.end >= start_date.date() and event.start <= end_date.date()
        ]

        _LOGGER.debug("Returning %s events from cache for range.", len(filtered_events))
        return filtered_events
