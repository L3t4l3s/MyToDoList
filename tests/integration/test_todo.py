"""Tests for the todo platform entity."""
from __future__ import annotations

from datetime import date, datetime

import pytest
from homeassistant.components.todo import TodoItem, TodoItemStatus
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

DOMAIN = "home_tasks"

pytestmark = pytest.mark.integration


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


# ---------------------------------------------------------------------------
# Due-date preservation on update
# ---------------------------------------------------------------------------


async def test_todo_update_preserves_due_date_on_title_change(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """Renaming a task via todo.update_item does not clear its due_date."""
    task = await store.async_add_task("Original")
    await store.async_update_task(task["id"], due_date="2026-06-15")
    await hass.async_block_till_done()

    entity_id = _get_todo_entity_id(hass, mock_config_entry.entry_id)
    await hass.services.async_call(
        "todo", "update_item",
        {"entity_id": entity_id, "item": task["id"], "rename": "New name"},
        blocking=True,
    )
    await hass.async_block_till_done()
    updated = store.get_task(task["id"])
    assert updated["title"] == "New name"
    assert updated["due_date"] == "2026-06-15"


async def test_todo_update_clears_due_date(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """Setting due_date to None via todo.update_item clears the date."""
    task = await store.async_add_task("Has date")
    await store.async_update_task(task["id"], due_date="2026-06-15")
    await hass.async_block_till_done()

    entity_id = _get_todo_entity_id(hass, mock_config_entry.entry_id)
    # HA passes a complete TodoItem — with due=None to clear
    entity_comp = hass.data.get("todo")
    if entity_comp and hasattr(entity_comp, "get_entity"):
        entity = entity_comp.get_entity(entity_id)
        if entity:
            item = TodoItem(
                uid=task["id"],
                summary="Has date",
                status=TodoItemStatus.NEEDS_ACTION,
                due=None,
            )
            await entity.async_update_todo_item(item)
            await hass.async_block_till_done()
            assert store.get_task(task["id"])["due_date"] is None


# ---------------------------------------------------------------------------
# Edge cases (tests 47–48)
# ---------------------------------------------------------------------------


async def test_todo_update_item_no_uid_is_noop(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """async_update_todo_item with uid=None is a no-op."""
    task = await store.async_add_task("Pre-existing")
    await hass.async_block_till_done()

    entity_id = _get_todo_entity_id(hass, mock_config_entry.entry_id)
    entity_comp = hass.data.get("todo")
    if entity_comp and hasattr(entity_comp, "get_entity"):
        entity = entity_comp.get_entity(entity_id)
        if entity:
            item = TodoItem(uid=None, summary="Ghost", status=TodoItemStatus.NEEDS_ACTION)
            await entity.async_update_todo_item(item)
            await hass.async_block_till_done()
            # Original task unchanged
            assert store.get_task(task["id"])["title"] == "Pre-existing"
            # No new tasks
            assert len(store.tasks) == 1


async def test_todo_update_item_with_description(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """async_update_todo_item with description sets notes on the task."""
    task = await store.async_add_task("Described task")
    await hass.async_block_till_done()

    entity_id = _get_todo_entity_id(hass, mock_config_entry.entry_id)
    entity_comp = hass.data.get("todo")
    if entity_comp and hasattr(entity_comp, "get_entity"):
        entity = entity_comp.get_entity(entity_id)
        if entity:
            item = TodoItem(
                uid=task["id"],
                summary="Described task",
                status=TodoItemStatus.NEEDS_ACTION,
                description="My notes",
            )
            await entity.async_update_todo_item(item)
            await hass.async_block_till_done()
            assert store.get_task(task["id"])["notes"] == "My notes"


# ---------------------------------------------------------------------------
# New features: due_time as datetime, completed_at, move support
# ---------------------------------------------------------------------------


async def test_todo_items_expose_due_datetime(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """When due_time is set, TodoItem.due is a datetime, not just a date."""
    from datetime import datetime

    task = await store.async_add_task("Timed")
    await store.async_update_task(task["id"], due_date="2027-05-15", due_time="14:30")
    await hass.async_block_till_done()

    entity_id = _get_todo_entity_id(hass, mock_config_entry.entry_id)
    entity_comp = hass.data.get("todo")
    if entity_comp and hasattr(entity_comp, "get_entity"):
        entity = entity_comp.get_entity(entity_id)
        if entity:
            items = entity.todo_items or []
            timed = [i for i in items if i.uid == task["id"]]
            assert timed
            assert isinstance(timed[0].due, datetime)
            assert timed[0].due.hour == 14
            assert timed[0].due.minute == 30


async def test_todo_items_expose_date_only_when_no_time(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """When due_time is not set, TodoItem.due remains a plain date."""
    task = await store.async_add_task("Date only")
    await store.async_update_task(task["id"], due_date="2027-05-15")
    await hass.async_block_till_done()

    entity_id = _get_todo_entity_id(hass, mock_config_entry.entry_id)
    entity_comp = hass.data.get("todo")
    if entity_comp and hasattr(entity_comp, "get_entity"):
        entity = entity_comp.get_entity(entity_id)
        if entity:
            items = entity.todo_items or []
            item = next(i for i in items if i.uid == task["id"])
            assert type(item.due) is date  # plain date, NOT datetime subclass


async def test_todo_items_expose_completed_at(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """Completed tasks expose TodoItem.completed as a datetime."""
    from datetime import datetime as _dt

    task = await store.async_add_task("Will complete")
    await store.async_update_task(task["id"], completed=True)
    await hass.async_block_till_done()

    entity_id = _get_todo_entity_id(hass, mock_config_entry.entry_id)
    entity_comp = hass.data.get("todo")
    if entity_comp and hasattr(entity_comp, "get_entity"):
        entity = entity_comp.get_entity(entity_id)
        if entity:
            items = entity.todo_items or []
            item = next(i for i in items if i.uid == task["id"])
            assert item.completed is not None
            assert isinstance(item.completed, _dt)


async def test_todo_items_no_completed_at_when_open(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """Open tasks have TodoItem.completed = None."""
    task = await store.async_add_task("Still open")
    await hass.async_block_till_done()

    entity_id = _get_todo_entity_id(hass, mock_config_entry.entry_id)
    entity_comp = hass.data.get("todo")
    if entity_comp and hasattr(entity_comp, "get_entity"):
        entity = entity_comp.get_entity(entity_id)
        if entity:
            items = entity.todo_items or []
            item = next(i for i in items if i.uid == task["id"])
            assert item.completed is None


async def test_todo_create_with_due_datetime(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """Creating a todo item with a datetime due stores both date and time."""
    from datetime import datetime

    entity_id = _get_todo_entity_id(hass, mock_config_entry.entry_id)
    entity_comp = hass.data.get("todo")
    if entity_comp and hasattr(entity_comp, "get_entity"):
        entity = entity_comp.get_entity(entity_id)
        if entity:
            local_tz = datetime.now().astimezone().tzinfo
            due_dt = datetime(2027, 8, 20, 9, 30, tzinfo=local_tz)
            item = TodoItem(summary="Datetime create", due=due_dt)
            await entity.async_create_todo_item(item)
            await hass.async_block_till_done()
            tasks = [t for t in store.tasks if t["title"] == "Datetime create"]
            assert tasks
            assert tasks[0]["due_date"] == "2027-08-20"
            assert tasks[0]["due_time"] == "09:30"


async def test_todo_update_with_due_datetime(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """Updating with a datetime due stores both date and time."""
    from datetime import datetime

    task = await store.async_add_task("Set datetime")
    await hass.async_block_till_done()

    entity_id = _get_todo_entity_id(hass, mock_config_entry.entry_id)
    entity_comp = hass.data.get("todo")
    if entity_comp and hasattr(entity_comp, "get_entity"):
        entity = entity_comp.get_entity(entity_id)
        if entity:
            local_tz = datetime.now().astimezone().tzinfo
            item = TodoItem(
                uid=task["id"],
                summary="Set datetime",
                status=TodoItemStatus.NEEDS_ACTION,
                due=datetime(2027, 8, 20, 14, 0, tzinfo=local_tz),
            )
            await entity.async_update_todo_item(item)
            await hass.async_block_till_done()
            updated = store.get_task(task["id"])
            assert updated["due_date"] == "2027-08-20"
            assert updated["due_time"] == "14:00"


async def test_todo_update_date_only_clears_time(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """Updating with a date (not datetime) clears due_time."""
    task = await store.async_add_task("Had time")
    await store.async_update_task(task["id"], due_date="2027-05-15", due_time="10:00")
    await hass.async_block_till_done()

    entity_id = _get_todo_entity_id(hass, mock_config_entry.entry_id)
    entity_comp = hass.data.get("todo")
    if entity_comp and hasattr(entity_comp, "get_entity"):
        entity = entity_comp.get_entity(entity_id)
        if entity:
            item = TodoItem(
                uid=task["id"],
                summary="Had time",
                status=TodoItemStatus.NEEDS_ACTION,
                due=date(2027, 5, 15),  # date only → clears time
            )
            await entity.async_update_todo_item(item)
            await hass.async_block_till_done()
            updated = store.get_task(task["id"])
            assert updated["due_date"] == "2027-05-15"
            assert updated["due_time"] is None


async def test_todo_move_item(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """async_move_todo_item reorders tasks correctly."""
    t1 = await store.async_add_task("First")
    t2 = await store.async_add_task("Second")
    t3 = await store.async_add_task("Third")
    await hass.async_block_till_done()

    entity_id = _get_todo_entity_id(hass, mock_config_entry.entry_id)
    entity_comp = hass.data.get("todo")
    if entity_comp and hasattr(entity_comp, "get_entity"):
        entity = entity_comp.get_entity(entity_id)
        if entity:
            # Move "Third" to first position (previous_uid=None)
            await entity.async_move_todo_item(t3["id"], previous_uid=None)
            await hass.async_block_till_done()
            ordered = sorted(store.tasks, key=lambda t: t["sort_order"])
            assert [t["id"] for t in ordered] == [t3["id"], t1["id"], t2["id"]]

            # Move "First" after "Third"
            await entity.async_move_todo_item(t1["id"], previous_uid=t3["id"])
            await hass.async_block_till_done()
            ordered = sorted(store.tasks, key=lambda t: t["sort_order"])
            assert [t["id"] for t in ordered] == [t3["id"], t1["id"], t2["id"]]
