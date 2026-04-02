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


async def test_native_name_too_long_rejected(hass: HomeAssistant) -> None:
    """A name exceeding MAX_LIST_NAME_LENGTH is rejected with name_too_long error."""
    from custom_components.home_tasks.const import MAX_LIST_NAME_LENGTH
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "native"}
    )
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"], {"name": "x" * (MAX_LIST_NAME_LENGTH + 1)}
    )
    assert result3["type"] == FlowResultType.FORM
    assert result3["errors"].get("name") == "name_too_long"


async def test_external_flow_shows_form_when_entities_available(hass: HomeAssistant) -> None:
    """External flow shows a form when there is at least one external todo entity."""
    from homeassistant.helpers import entity_registry as er

    reg = er.async_get(hass)
    # Register a fake todo entity that is NOT owned by home_tasks
    reg.async_get_or_create(
        "todo",
        "google_tasks",
        "test_list_unique_id",
        original_name="Google Tasks",
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "external"}
    )
    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "external"


async def test_external_flow_creates_entry(hass: HomeAssistant) -> None:
    """Submitting the external form creates a config entry."""
    from homeassistant.helpers import entity_registry as er

    reg = er.async_get(hass)
    ext_entry = reg.async_get_or_create(
        "todo",
        "google_tasks",
        "ext_unique_2",
        original_name="My Google List",
    )
    entity_id = ext_entry.entity_id

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "external"}
    )
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"], {"entity_id": entity_id}
    )
    await hass.async_block_till_done()
    assert result3["type"] == FlowResultType.CREATE_ENTRY
    assert result3["data"]["entity_id"] == entity_id
    assert result3["data"]["type"] == "external"
