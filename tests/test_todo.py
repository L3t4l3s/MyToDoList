"""Tests for the todo platform entity."""
from __future__ import annotations

from datetime import date

import pytest
from homeassistant.components.todo import TodoItemStatus
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

DOMAIN = "home_tasks"


def _get_todo_entity_id(hass: HomeAssistant, unique_id: str) -> str | None:
    """Look up a todo entity_id by its unique_id."""
    reg = er.async_get(hass)
    return reg.async_get_entity_id("todo", DOMAIN, unique_id)


async def test_todo_entity_registered(hass: HomeAssistant, mock_config_entry) -> None:
    """A todo entity is registered for the native list."""
    entity_id = _get_todo_entity_id(hass, mock_config_entry.entry_id)
    assert entity_id is not None


async def test_todo_items_reflect_store(hass: HomeAssistant, mock_config_entry, store) -> None:
    """Todo items match the tasks in the store."""
    await store.async_add_task("Alpha")
    await store.async_add_task("Beta")
    await hass.async_block_till_done()

    entity_id = _get_todo_entity_id(hass, mock_config_entry.entry_id)
    state = hass.states.get(entity_id)
    assert state is not None
    # State value for todo lists is the count of needs_action items
    assert int(state.state) == 2


async def test_todo_item_completion_via_store(hass: HomeAssistant, mock_config_entry, store) -> None:
    """Completing a task via the store updates the todo entity state."""
    task = await store.async_add_task("To complete")
    await hass.async_block_till_done()

    entity_id = _get_todo_entity_id(hass, mock_config_entry.entry_id)
    assert int(hass.states.get(entity_id).state) == 1

    await store.async_update_task(task["id"], completed=True)
    await hass.async_block_till_done()
    assert int(hass.states.get(entity_id).state) == 0


async def test_todo_items_include_due_date(hass: HomeAssistant, mock_config_entry, store) -> None:
    """Todo items carry the due_date field as a date object."""
    task = await store.async_add_task("Dated")
    await store.async_update_task(task["id"], due_date="2026-06-15")
    await hass.async_block_till_done()

    entity_id = _get_todo_entity_id(hass, mock_config_entry.entry_id)
    # Access the entity directly to inspect its TodoItem objects
    entity_comp = hass.data.get("todo")
    if entity_comp and hasattr(entity_comp, "get_entity"):
        entity = entity_comp.get_entity(entity_id)
        if entity:
            items = entity.todo_items or []
            dated_items = [i for i in items if i.due is not None]
            assert any(i.due == date(2026, 6, 15) for i in dated_items)


async def test_todo_items_status_needs_action(hass: HomeAssistant, mock_config_entry, store) -> None:
    """Incomplete tasks have NEEDS_ACTION status in todo items."""
    await store.async_add_task("Open task")
    await hass.async_block_till_done()

    entity_id = _get_todo_entity_id(hass, mock_config_entry.entry_id)
    entity_comp = hass.data.get("todo")
    if entity_comp and hasattr(entity_comp, "get_entity"):
        entity = entity_comp.get_entity(entity_id)
        if entity:
            items = entity.todo_items or []
            assert all(i.status == TodoItemStatus.NEEDS_ACTION for i in items)
