"""Tests for the config flow."""

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.hass_school_holidays_lu.const import CONF_LANGUAGE, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType


@pytest.mark.parametrize(
    ("hass_language", "expected_default"),
    [
        ("en", "en"),
        ("de", "de"),
        ("fr", "fr"),
        ("lb", "lb"),
        ("pt-BR", "en"),
        ("de-CH", "de"),
    ],
)
async def test_default_language(
    hass: HomeAssistant, hass_language: str, expected_default: str
) -> None:
    """The form defaults to the HA language, or English when unsupported."""
    hass.config.language = hass_language
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    schema = result["data_schema"].schema
    key = next(k for k in schema if k == CONF_LANGUAGE)
    assert key.default() == expected_default


async def test_create_entry(hass: HomeAssistant, mock_api) -> None:
    """Test creating an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_LANGUAGE: "lb"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "School Holidays LU (LB)"
    assert result["data"] == {CONF_LANGUAGE: "lb"}


async def test_single_instance(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Only one entry is allowed."""
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"
