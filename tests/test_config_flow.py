"""Tests for the Home Tasks config flow."""
from __future__ import annotations

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

DOMAIN = "home_tasks"


async def test_user_step_shows_menu(hass: HomeAssistant) -> None:
    """Initial user step shows the native/external menu."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.MENU
    assert "native" in result["menu_options"]
    assert "external" in result["menu_options"]


async def test_native_list_creation_success(hass: HomeAssistant) -> None:
    """Creating a native list produces a CREATE_ENTRY result."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "native"}
    )
    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "native"

    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"], {"name": "My Tasks"}
    )
    await hass.async_block_till_done()
    assert result3["type"] == FlowResultType.CREATE_ENTRY
    assert result3["title"] == "My Tasks"
    assert result3["data"]["name"] == "My Tasks"


async def test_native_duplicate_name_rejected(hass: HomeAssistant) -> None:
    """A second list with the same name is rejected with duplicate_name error."""
    entry = MockConfigEntry(domain=DOMAIN, data={"name": "My Tasks"}, title="My Tasks")
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "native"}
    )
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"], {"name": "My Tasks"}
    )
    assert result3["type"] == FlowResultType.FORM
    assert result3["errors"].get("name") == "duplicate_name"


async def test_native_duplicate_name_case_insensitive(hass: HomeAssistant) -> None:
    """Duplicate name check is case-insensitive."""
    entry = MockConfigEntry(domain=DOMAIN, data={"name": "My Tasks"}, title="My Tasks")
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "native"}
    )
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"], {"name": "MY TASKS"}
    )
    assert result3["type"] == FlowResultType.FORM
    assert result3["errors"].get("name") == "duplicate_name"


async def test_native_empty_name_rejected(hass: HomeAssistant) -> None:
    """Empty list name is rejected with empty_name error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "native"}
    )
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"], {"name": "   "}
    )
    assert result3["type"] == FlowResultType.FORM
    assert result3["errors"].get("name") == "empty_name"


async def test_external_aborts_when_no_todo_entities(hass: HomeAssistant) -> None:
    """External flow aborts immediately when no external todo entities exist."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "external"}
    )
    assert result2["type"] == FlowResultType.ABORT
    assert result2["reason"] == "no_external_entities"
