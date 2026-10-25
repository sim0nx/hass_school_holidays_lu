"""Fixtures for the School Holidays LU tests."""

from collections.abc import Generator
import json
from pathlib import Path
from typing import Any

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.hass_school_holidays_lu.const import (
    CONF_LANGUAGE,
    DATA_URL,
    DOMAIN,
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable custom integrations in all tests."""


@pytest.fixture
def holidays_data() -> list[Any]:
    """Return the sample dataset."""
    fixture = Path(__file__).parent / "fixtures" / "school_holidays.json"
    return json.loads(fixture.read_text(encoding="utf-8"))


@pytest.fixture
def mock_api(
    aioclient_mock: AiohttpClientMocker, holidays_data: list[Any]
) -> Generator[AiohttpClientMocker]:
    """Mock the data.public.lu download."""
    aioclient_mock.get(DATA_URL, json=holidays_data)
    yield aioclient_mock


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a config entry as created by the current config flow."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="School Holidays LU (EN)",
        data={CONF_LANGUAGE: "en"},
        entry_id="01TESTENTRY",
    )
