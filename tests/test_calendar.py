"""Tests for the calendar platform."""

from datetime import timedelta

from freezegun.api import FrozenDateTimeFactory
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.hass_school_holidays_lu.const import (
    CONF_LANGUAGE,
    DATA_URL,
    DOMAIN,
)
from homeassistant.components.calendar import DOMAIN as CALENDAR_DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

ENTITY_ID = "calendar.school_holidays_lu_en"


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


@pytest.fixture(autouse=True)
async def set_tz(hass: HomeAssistant) -> None:
    """Use the Luxembourg time zone."""
    await hass.config.async_set_time_zone("Europe/Luxembourg")


async def test_state_during_holiday(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_api: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """The calendar is on during a holiday and exposes it."""
    freezer.move_to("2026-02-15 12:00:00+01:00")
    await _setup(hass, mock_config_entry)

    state = hass.states.get(ENTITY_ID)
    assert state.state == STATE_ON
    assert state.attributes["message"] == "Carnival holidays"
    assert state.attributes["all_day"] is True
    assert state.attributes["start_time"] == "2026-02-14 00:00:00"
    # The dataset end date (22nd) is inclusive.
    assert state.attributes["end_time"] == "2026-02-23 00:00:00"
    assert state.attributes["friendly_name"] == "School Holidays LU (EN)"

    entity = entity_registry.async_get(ENTITY_ID)
    assert entity.unique_id == "01TESTENTRY_en"
    device = device_registry.async_get(entity.device_id)
    assert device.entry_type is dr.DeviceEntryType.SERVICE


async def test_state_transitions(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_api: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
) -> None:
    """The calendar switches off after the last day and shows the next event."""
    freezer.move_to("2026-02-22 23:59:00+01:00")
    await _setup(hass, mock_config_entry)
    assert hass.states.get(ENTITY_ID).state == STATE_ON

    freezer.tick(timedelta(minutes=2))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    state = hass.states.get(ENTITY_ID)
    assert state.state == STATE_OFF
    assert state.attributes["message"] == "Easter holidays"


async def test_out_of_order_data(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_api: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Events are sorted, so the earliest upcoming one is shown."""
    freezer.move_to("2026-04-20 12:00:00+02:00")
    await _setup(hass, mock_config_entry)
    state = hass.states.get(ENTITY_ID)
    assert state.state == STATE_OFF
    assert state.attributes["message"] == "Public holiday on Ascension Day"


async def test_get_events(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_api: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
) -> None:
    """calendar.get_events returns overlapping events only."""
    freezer.move_to("2026-02-15 12:00:00+01:00")
    await _setup(hass, mock_config_entry)

    async def _events(start: str, end: str) -> list[str]:
        result = await hass.services.async_call(
            CALENDAR_DOMAIN,
            "get_events",
            {"start_date_time": start, "end_date_time": end},
            target={"entity_id": ENTITY_ID},
            blocking=True,
            return_response=True,
        )
        return [e["summary"] for e in result[ENTITY_ID]["events"]]

    # The day after Carnival ends: not included (end is exclusive).
    assert await _events("2026-02-23T00:00:00+01:00", "2026-02-24T00:00:00+01:00") == []
    # The last day of Carnival: included.
    assert await _events("2026-02-22T10:00:00+01:00", "2026-02-22T11:00:00+01:00") == [
        "Carnival holidays"
    ]
    assert await _events("2026-01-01T00:00:00+01:00", "2026-04-01T00:00:00+02:00") == [
        "Christmas holidays",
        "Carnival holidays",
        "Easter holidays",
    ]


async def test_legacy_entry(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_api: AiohttpClientMocker,
    entity_registry: er.EntityRegistry,
) -> None:
    """Entries created by 0.1.0 (uppercase language + stored URL) keep working."""
    freezer.move_to("2026-02-15 12:00:00+01:00")
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="School Holidays LU (DE)",
        data={"url": "https://example.invalid/old", CONF_LANGUAGE: "DE"},
        entry_id="01LEGACY",
    )
    entry.add_to_hass(hass)
    # Entity as registered by 0.1.0.
    entity_registry.async_get_or_create(
        CALENDAR_DOMAIN,
        DOMAIN,
        "01LEGACY_de",
        suggested_object_id="school_holidays_lu_de",
        config_entry=entry,
    )
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    # The stored URL is ignored, the constant is used.
    assert mock_api.mock_calls[0][1].human_repr() == DATA_URL
    state = hass.states.get("calendar.school_holidays_lu_de")
    assert state.state == STATE_ON
    assert state.attributes["message"] == "Karnevalsferien"
    assert len(er.async_entries_for_config_entry(entity_registry, entry.entry_id)) == 1


async def test_language_fallback(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Missing translations fall back to English, then any language."""
    freezer.move_to("2026-02-15 12:00:00+01:00")
    aioclient_mock.get(
        DATA_URL,
        json=[
            {"en": "Holiday A", "start_date": "2026-02-14", "end_date": "2026-02-16"},
            {"de": "Ferien B", "start_date": "2026-03-01", "end_date": "2026-03-02"},
            {"start_date": "2026-04-01", "end_date": "2026-04-02"},
            {"en": "Broken", "start_date": "not-a-date", "end_date": "2026-04-02"},
            {"en": "No end", "start_date": "2026-05-01"},
            "garbage",
        ],
    )
    entry = MockConfigEntry(domain=DOMAIN, title="LB", data={CONF_LANGUAGE: "lb"})
    await _setup(hass, entry)
    coordinator = entry.runtime_data
    assert [e.summary for e in coordinator.data] == [
        "Holiday A",
        "Ferien B",
        "Unknown Event",
    ]


@pytest.mark.parametrize(
    "mock_kwargs",
    [
        {"status": 500},
        {"exc": TimeoutError()},
        {"text": "not json"},
        {"json": {"a": 1}},
    ],
)
async def test_setup_retry(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
    mock_kwargs: dict,
) -> None:
    """A failed first fetch puts the entry into retry instead of failing."""
    aioclient_mock.get(DATA_URL, **mock_kwargs)
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_update_failure_and_recovery(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    aioclient_mock: AiohttpClientMocker,
    holidays_data: list,
    mock_config_entry: MockConfigEntry,
) -> None:
    """The entity becomes unavailable on failure and recovers afterwards."""
    freezer.move_to("2026-02-15 12:00:00+01:00")
    aioclient_mock.get(DATA_URL, json=holidays_data)
    await _setup(hass, mock_config_entry)
    assert hass.states.get(ENTITY_ID).state == STATE_ON

    aioclient_mock.clear_requests()
    aioclient_mock.get(DATA_URL, status=503)
    freezer.tick(timedelta(days=1, seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == STATE_UNAVAILABLE

    aioclient_mock.clear_requests()
    aioclient_mock.get(DATA_URL, json=holidays_data)
    freezer.tick(timedelta(days=1, seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == STATE_ON  # Feb 17: still Carnival


async def test_unload(
    hass: HomeAssistant,
    mock_api: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test unloading the entry."""
    await _setup(hass, mock_config_entry)
    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED
