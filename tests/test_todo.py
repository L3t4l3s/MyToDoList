"""Tests for the todo platform entity."""
from __future__ import annotations

from datetime import date

import pytest
from homeassistant.components.todo import TodoItem, TodoItemStatus
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


async def test_todo_create_via_service(hass: HomeAssistant, mock_config_entry, store) -> None:
    """todo.add_item service calls async_create_todo_item and adds task to store."""
    entity_id = _get_todo_entity_id(hass, mock_config_entry.entry_id)
    await hass.services.async_call(
        "todo", "add_item",
        {"entity_id": entity_id, "item": "Via service"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert any(t["title"] == "Via service" for t in store.tasks)


async def test_todo_create_with_due_date(hass: HomeAssistant, mock_config_entry, store) -> None:
    """todo.add_item with due_date stores the date on the task."""
    entity_id = _get_todo_entity_id(hass, mock_config_entry.entry_id)
    await hass.services.async_call(
        "todo", "add_item",
        {"entity_id": entity_id, "item": "With due", "due_date": date(2026, 6, 15)},
        blocking=True,
    )
    await hass.async_block_till_done()
    tasks = [t for t in store.tasks if t["title"] == "With due"]
    assert tasks and tasks[0]["due_date"] == "2026-06-15"


async def test_todo_update_via_service(hass: HomeAssistant, mock_config_entry, store) -> None:
    """todo.update_item service calls async_update_todo_item and updates task."""
    task = await store.async_add_task("To rename")
    await hass.async_block_till_done()

    entity_id = _get_todo_entity_id(hass, mock_config_entry.entry_id)
    await hass.services.async_call(
        "todo", "update_item",
        {"entity_id": entity_id, "item": task["id"], "rename": "Renamed"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert store.get_task(task["id"])["title"] == "Renamed"


async def test_todo_update_status_completed(hass: HomeAssistant, mock_config_entry, store) -> None:
    """Updating a todo item status to completed marks it done."""
    task = await store.async_add_task("Mark complete")
    await hass.async_block_till_done()

    entity_id = _get_todo_entity_id(hass, mock_config_entry.entry_id)
    await hass.services.async_call(
        "todo", "update_item",
        {"entity_id": entity_id, "item": task["id"], "status": "completed"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert store.get_task(task["id"])["completed"] is True


async def test_todo_delete_via_service(hass: HomeAssistant, mock_config_entry, store) -> None:
    """todo.remove_item service calls async_delete_todo_items and removes task."""
    task = await store.async_add_task("To delete")
    await hass.async_block_till_done()

    entity_id = _get_todo_entity_id(hass, mock_config_entry.entry_id)
    await hass.services.async_call(
        "todo", "remove_item",
        {"entity_id": entity_id, "item": [task["id"]]},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert all(t["id"] != task["id"] for t in store.tasks)


async def test_todo_create_with_description(hass: HomeAssistant, mock_config_entry, store) -> None:
    """todo.add_item with description stores it as notes on the task."""
    entity_id = _get_todo_entity_id(hass, mock_config_entry.entry_id)
    await hass.services.async_call(
        "todo", "add_item",
        {"entity_id": entity_id, "item": "With notes", "description": "My note"},
        blocking=True,
    )
    await hass.async_block_till_done()
    tasks = [t for t in store.tasks if t["title"] == "With notes"]
    assert tasks and tasks[0]["notes"] == "My note"


async def test_todo_create_as_completed(hass: HomeAssistant, mock_config_entry, store) -> None:
    """async_create_todo_item with COMPLETED status creates the task as completed."""
    entity_id = _get_todo_entity_id(hass, mock_config_entry.entry_id)
    entity_comp = hass.data.get("todo")
    if entity_comp and hasattr(entity_comp, "get_entity"):
        entity = entity_comp.get_entity(entity_id)
        if entity:
            item = TodoItem(summary="Already done", status=TodoItemStatus.COMPLETED)
            await entity.async_create_todo_item(item)
            await hass.async_block_till_done()
            tasks = [t for t in store.tasks if t["title"] == "Already done"]
            assert tasks and tasks[0]["completed"] is True


async def test_todo_update_with_due_date(hass: HomeAssistant, mock_config_entry, store) -> None:
    """todo.update_item with due_date stores the date on the task."""
    task = await store.async_add_task("Set due")
    await hass.async_block_till_done()

    entity_id = _get_todo_entity_id(hass, mock_config_entry.entry_id)
    await hass.services.async_call(
        "todo", "update_item",
        {"entity_id": entity_id, "item": task["id"], "due_date": date(2026, 9, 1)},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert store.get_task(task["id"])["due_date"] == "2026-09-01"


async def test_todo_external_entry_skipped(hass: HomeAssistant, patch_add_extra_js_url) -> None:
    """External entries do not create a todo entity."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from homeassistant.helpers import entity_registry as er

    ext_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"type": "external", "entity_id": "todo.external_test", "name": "External"},
        title="External (External)",
    )
    ext_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(ext_entry.entry_id)
    await hass.async_block_till_done()

    # No todo entity should be registered for the external entry
    reg = er.async_get(hass)
    entity_id = reg.async_get_entity_id("todo", DOMAIN, ext_entry.entry_id)
    assert entity_id is None
