"""Calendar platform for the School Holidays LU integration."""

import datetime

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import HolidaysConfigEntry, HolidaysDataUpdateCoordinator

# The coordinator handles all updates.
PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HolidaysConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the calendar platform from a config entry."""
    async_add_entities([HolidaysCalendarEntity(entry.runtime_data, entry)])


class HolidaysCalendarEntity(
    CoordinatorEntity[HolidaysDataUpdateCoordinator], CalendarEntity
):
    """Calendar entity with the school holidays in Luxembourg."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self, coordinator: HolidaysDataUpdateCoordinator, entry: HolidaysConfigEntry
    ) -> None:
        """Initialize the calendar entity."""
        super().__init__(coordinator)
        # Kept identical to earlier versions so the existing entity is reused.
        self._attr_unique_id = f"{entry.entry_id}_{coordinator.language}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            entry_type=DeviceEntryType.SERVICE,
            name=entry.title,
        )

    @property
    def event(self) -> CalendarEvent | None:
        """Return the current or next upcoming event."""
        now = dt_util.now()
        return next(
            (
                event
                for event in self.coordinator.data
                if event.end_datetime_local > now
            ),
            None,
        )

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
    ) -> list[CalendarEvent]:
        """Return events overlapping the requested period."""
        return [
            event
            for event in self.coordinator.data
            if event.start_datetime_local < end_date
            and event.end_datetime_local > start_date
        ]
