"""Tests for the Home Tasks WebSocket API commands."""
from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

DOMAIN = "home_tasks"

pytestmark = pytest.mark.integration


async def test_ws_get_lists(hass: HomeAssistant, hass_ws_client, mock_config_entry) -> None:
    """get_lists returns the configured native list."""
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "home_tasks/get_lists"})
    msg = await client.receive_json()
    assert msg["success"] is True
    names = [lst["name"] for lst in msg["result"]["lists"]]
    assert "Test List" in names


async def test_ws_get_lists_excludes_external(
    hass: HomeAssistant, hass_ws_client, mock_config_entry, patch_add_extra_js_url
) -> None:
    """get_lists does not include external-type entries."""
    ext_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"type": "external", "entity_id": "todo.external", "name": "External"},
        title="External (External)",
    )
    ext_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(ext_entry.entry_id)
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": "home_tasks/get_lists"})
    msg = await client.receive_json()
    assert msg["success"] is True
    names = [lst["name"] for lst in msg["result"]["lists"]]
    assert "External" not in names
    assert "Test List" in names


async def test_ws_add_task(hass: HomeAssistant, hass_ws_client, mock_config_entry) -> None:
    """add_task creates a task and returns it."""
    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 2,
        "type": "home_tasks/add_task",
        "list_id": mock_config_entry.entry_id,
        "title": "WebSocket task",
    })
    msg = await client.receive_json()
    assert msg["success"] is True
    assert msg["result"]["title"] == "WebSocket task"
    assert msg["result"]["id"] is not None


async def test_ws_get_tasks(hass: HomeAssistant, hass_ws_client, mock_config_entry, store) -> None:
    """get_tasks returns all tasks for the list."""
    await store.async_add_task("Alpha")
    await store.async_add_task("Beta")

    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 3,
        "type": "home_tasks/get_tasks",
        "list_id": mock_config_entry.entry_id,
    })
    msg = await client.receive_json()
    assert msg["success"] is True
    titles = [t["title"] for t in msg["result"]["tasks"]]
    assert "Alpha" in titles
    assert "Beta" in titles


async def test_ws_update_task(hass: HomeAssistant, hass_ws_client, mock_config_entry, store) -> None:
    """update_task modifies the task and returns the updated version."""
    task = await store.async_add_task("Original title")

    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 4,
        "type": "home_tasks/update_task",
        "list_id": mock_config_entry.entry_id,
        "task_id": task["id"],
        "title": "Updated title",
        "priority": 2,
    })
    msg = await client.receive_json()
    assert msg["success"] is True
    assert msg["result"]["title"] == "Updated title"
    assert msg["result"]["priority"] == 2


async def test_ws_delete_task(hass: HomeAssistant, hass_ws_client, mock_config_entry, store) -> None:
    """delete_task removes the task from the store."""
    task = await store.async_add_task("To delete")

    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 5,
        "type": "home_tasks/delete_task",
        "list_id": mock_config_entry.entry_id,
        "task_id": task["id"],
    })
    msg = await client.receive_json()
    assert msg["success"] is True
    assert all(t["id"] != task["id"] for t in store.tasks)


async def test_ws_add_and_delete_sub_task(
    hass: HomeAssistant, hass_ws_client, mock_config_entry, store
) -> None:
    """add_sub_task creates a sub-task; delete_sub_task removes it."""
    task = await store.async_add_task("Parent")
    client = await hass_ws_client(hass)

    # Add sub-task
    await client.send_json({
        "id": 6,
        "type": "home_tasks/add_sub_task",
        "list_id": mock_config_entry.entry_id,
        "task_id": task["id"],
        "title": "Child task",
    })
    msg = await client.receive_json()
    assert msg["success"] is True
    sub_id = msg["result"]["id"]
    assert msg["result"]["title"] == "Child task"

    # Delete sub-task
    await client.send_json({
        "id": 7,
        "type": "home_tasks/delete_sub_task",
        "list_id": mock_config_entry.entry_id,
        "task_id": task["id"],
        "sub_task_id": sub_id,
    })
    msg = await client.receive_json()
    assert msg["success"] is True
    assert store.get_task(task["id"])["sub_items"] == []


async def test_ws_reorder_tasks(hass: HomeAssistant, hass_ws_client, mock_config_entry, store) -> None:
    """reorder_tasks changes sort_order of tasks."""
    t1 = await store.async_add_task("First")
    t2 = await store.async_add_task("Second")

    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 8,
        "type": "home_tasks/reorder_tasks",
        "list_id": mock_config_entry.entry_id,
        "task_ids": [t2["id"], t1["id"]],
    })
    msg = await client.receive_json()
    assert msg["success"] is True
    task_map = {t["id"]: t for t in store.tasks}
    assert task_map[t2["id"]]["sort_order"] < task_map[t1["id"]]["sort_order"]


async def test_ws_invalid_list_id_returns_error(
    hass: HomeAssistant, hass_ws_client, mock_config_entry
) -> None:
    """Commands with an unknown list_id return a failure result."""
    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 9,
        "type": "home_tasks/get_tasks",
        "list_id": "nonexistent-entry-id",
    })
    msg = await client.receive_json()
    assert msg["success"] is False
    assert msg["error"]["code"] == "invalid_request"


async def test_ws_move_task(
    hass: HomeAssistant, hass_ws_client, mock_config_entry, store, patch_add_extra_js_url
) -> None:
    """move_task transfers a task from one list to another."""
    entry2 = MockConfigEntry(
        domain=DOMAIN, data={"name": "Second List"}, title="Second List"
    )
    entry2.add_to_hass(hass)
    await hass.config_entries.async_setup(entry2.entry_id)
    await hass.async_block_till_done()

    task = await store.async_add_task("Move me")
    task_id = task["id"]

    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 10,
        "type": "home_tasks/move_task",
        "source_list_id": mock_config_entry.entry_id,
        "target_list_id": entry2.entry_id,
        "task_id": task_id,
    })
    msg = await client.receive_json()
    assert msg["success"] is True

    # Task removed from source
    assert all(t["id"] != task_id for t in store.tasks)
    # Task present in target
    store2 = hass.data[DOMAIN][entry2.entry_id]
    assert any(t["id"] == task_id for t in store2.tasks)


async def test_ws_move_task_same_list_error(
    hass: HomeAssistant, hass_ws_client, mock_config_entry, store
) -> None:
    """move_task returns an error when source and target are the same list."""
    task = await store.async_add_task("Same list")
    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 11,
        "type": "home_tasks/move_task",
        "source_list_id": mock_config_entry.entry_id,
        "target_list_id": mock_config_entry.entry_id,
        "task_id": task["id"],
    })
    msg = await client.receive_json()
    assert msg["success"] is False
    assert msg["error"]["code"] == "invalid_request"


async def test_ws_update_sub_task(
    hass: HomeAssistant, hass_ws_client, mock_config_entry, store
) -> None:
    """update_sub_task modifies sub-task title and completed state."""
    task = await store.async_add_task("Parent")
    sub = await store.async_add_sub_task(task["id"], "Original sub")

    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 12,
        "type": "home_tasks/update_sub_task",
        "list_id": mock_config_entry.entry_id,
        "task_id": task["id"],
        "sub_task_id": sub["id"],
        "title": "Updated sub",
        "completed": True,
    })
    msg = await client.receive_json()
    assert msg["success"] is True
    assert msg["result"]["title"] == "Updated sub"
    assert msg["result"]["completed"] is True


async def test_ws_reorder_sub_tasks(
    hass: HomeAssistant, hass_ws_client, mock_config_entry, store
) -> None:
    """reorder_sub_tasks changes the order of sub-tasks."""
    task = await store.async_add_task("Parent")
    s1 = await store.async_add_sub_task(task["id"], "First")
    s2 = await store.async_add_sub_task(task["id"], "Second")

    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 13,
        "type": "home_tasks/reorder_sub_tasks",
        "list_id": mock_config_entry.entry_id,
        "task_id": task["id"],
        "sub_task_ids": [s2["id"], s1["id"]],
    })
    msg = await client.receive_json()
    assert msg["success"] is True
    t = store.get_task(task["id"])
    assert t["sub_items"][0]["id"] == s2["id"]


# ---------------------------------------------------------------------------
# External overlay WebSocket commands
# ---------------------------------------------------------------------------


@pytest.fixture
async def external_config_entry(hass: HomeAssistant, patch_add_extra_js_url) -> MockConfigEntry:
    """Create and load an external Home Tasks config entry (overlay store)."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"type": "external", "entity_id": "todo.ws_external", "name": "WS External"},
        title="WS External (External)",
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_ws_get_external_lists_empty(
    hass: HomeAssistant, hass_ws_client, mock_config_entry
) -> None:
    """get_external_lists returns empty when no external todo entities exist."""
    client = await hass_ws_client(hass)
    await client.send_json({"id": 20, "type": "home_tasks/get_external_lists"})
    msg = await client.receive_json()
    assert msg["success"] is True
    assert isinstance(msg["result"]["external_lists"], list)


async def test_ws_update_external_overlay(
    hass: HomeAssistant, hass_ws_client, external_config_entry
) -> None:
    """update_external_overlay sets priority/tags on the overlay store."""
    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 21,
        "type": "home_tasks/update_external_overlay",
        "entity_id": "todo.ws_external",
        "task_uid": "ext-uid-1",
        "priority": 2,
        "tags": ["work", "urgent"],
    })
    msg = await client.receive_json()
    assert msg["success"] is True
    assert msg["result"]["priority"] == 2
    assert "work" in msg["result"]["tags"]


async def test_ws_add_external_sub_task(
    hass: HomeAssistant, hass_ws_client, external_config_entry
) -> None:
    """add_external_sub_task adds a sub-task to the overlay."""
    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 22,
        "type": "home_tasks/add_external_sub_task",
        "entity_id": "todo.ws_external",
        "task_uid": "ext-uid-2",
        "title": "External sub",
    })
    msg = await client.receive_json()
    assert msg["success"] is True
    assert msg["result"]["title"] == "External sub"
    assert msg["result"]["completed"] is False


async def test_ws_update_external_sub_task(
    hass: HomeAssistant, hass_ws_client, external_config_entry
) -> None:
    """update_external_sub_task modifies a sub-task in the overlay."""
    # First add
    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 23,
        "type": "home_tasks/add_external_sub_task",
        "entity_id": "todo.ws_external",
        "task_uid": "ext-uid-3",
        "title": "Original",
    })
    add_msg = await client.receive_json()
    sub_id = add_msg["result"]["id"]

    # Then update
    await client.send_json({
        "id": 24,
        "type": "home_tasks/update_external_sub_task",
        "entity_id": "todo.ws_external",
        "task_uid": "ext-uid-3",
        "sub_task_id": sub_id,
        "completed": True,
    })
    upd_msg = await client.receive_json()
    assert upd_msg["success"] is True
    assert upd_msg["result"]["completed"] is True


async def test_ws_delete_external_sub_task(
    hass: HomeAssistant, hass_ws_client, external_config_entry
) -> None:
    """delete_external_sub_task removes a sub-task from the overlay."""
    client = await hass_ws_client(hass)
    # Add
    await client.send_json({
        "id": 25,
        "type": "home_tasks/add_external_sub_task",
        "entity_id": "todo.ws_external",
        "task_uid": "ext-uid-4",
        "title": "To delete",
    })
    add_msg = await client.receive_json()
    sub_id = add_msg["result"]["id"]

    # Delete
    await client.send_json({
        "id": 26,
        "type": "home_tasks/delete_external_sub_task",
        "entity_id": "todo.ws_external",
        "task_uid": "ext-uid-4",
        "sub_task_id": sub_id,
    })
    del_msg = await client.receive_json()
    assert del_msg["success"] is True


async def test_ws_reorder_external_sub_tasks(
    hass: HomeAssistant, hass_ws_client, external_config_entry
) -> None:
    """reorder_external_sub_tasks reorders sub-tasks in the overlay."""
    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 27,
        "type": "home_tasks/add_external_sub_task",
        "entity_id": "todo.ws_external",
        "task_uid": "ext-uid-5",
        "title": "First",
    })
    s1 = await client.receive_json()
    await client.send_json({
        "id": 28,
        "type": "home_tasks/add_external_sub_task",
        "entity_id": "todo.ws_external",
        "task_uid": "ext-uid-5",
        "title": "Second",
    })
    s2 = await client.receive_json()

    await client.send_json({
        "id": 29,
        "type": "home_tasks/reorder_external_sub_tasks",
        "entity_id": "todo.ws_external",
        "task_uid": "ext-uid-5",
        "sub_task_ids": [s2["result"]["id"], s1["result"]["id"]],
    })
    msg = await client.receive_json()
    assert msg["success"] is True


async def test_ws_delete_external_overlay(
    hass: HomeAssistant, hass_ws_client, external_config_entry
) -> None:
    """delete_external_overlay removes overlay data for a task uid."""
    # Set an overlay first
    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 30,
        "type": "home_tasks/update_external_overlay",
        "entity_id": "todo.ws_external",
        "task_uid": "ext-uid-del",
        "priority": 1,
    })
    await client.receive_json()

    # Delete it
    await client.send_json({
        "id": 31,
        "type": "home_tasks/delete_external_overlay",
        "entity_id": "todo.ws_external",
        "task_uid": "ext-uid-del",
    })
    del_msg = await client.receive_json()
    assert del_msg["success"] is True


async def test_ws_native_command_on_external_entry_error(
    hass: HomeAssistant, hass_ws_client, external_config_entry
) -> None:
    """Native commands (get_tasks) return an error when used with an external entry_id."""
    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 33,
        "type": "home_tasks/get_tasks",
        "list_id": external_config_entry.entry_id,
    })
    msg = await client.receive_json()
    assert msg["success"] is False
    assert msg["error"]["code"] == "invalid_request"


async def test_ws_external_command_unknown_entity_error(
    hass: HomeAssistant, hass_ws_client, mock_config_entry
) -> None:
    """External commands return an error when the entity_id has no overlay store."""
    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 32,
        "type": "home_tasks/update_external_overlay",
        "entity_id": "todo.does_not_exist",
        "task_uid": "uid-1",
        "priority": 1,
    })
    msg = await client.receive_json()
    assert msg["success"] is False
    assert msg["error"]["code"] == "invalid_request"


# ---------------------------------------------------------------------------
# External task merge / get_external_tasks tests
# ---------------------------------------------------------------------------


async def test_ws_get_external_tasks_merges_overlay(
    hass: HomeAssistant, hass_ws_client, external_config_entry
) -> None:
    """get_external_tasks returns external items merged with overlay data."""
    from unittest.mock import MagicMock
    from datetime import date
    from homeassistant.components.todo import TodoItem, TodoItemStatus

    # Register a mock todo entity so _get_external_todo_items can read it
    mock_entity = MagicMock()
    mock_entity.todo_items = [
        TodoItem(uid="ext-1", summary="Task A", status=TodoItemStatus.NEEDS_ACTION, due=date(2026, 6, 15)),
        TodoItem(uid="ext-2", summary="Task B", status=TodoItemStatus.COMPLETED, due=None),
    ]
    mock_comp = MagicMock()
    mock_comp.get_entity.return_value = mock_entity
    hass.data["todo"] = mock_comp
    hass.states.async_set("todo.ws_external", "1")

    # Set overlay for ext-1
    from custom_components.home_tasks.overlay_store import ExternalTaskOverlayStore
    overlay_store = hass.data[DOMAIN][external_config_entry.entry_id]
    assert isinstance(overlay_store, ExternalTaskOverlayStore)
    await overlay_store.async_set_overlay("ext-1", priority=3, tags=["urgent"])

    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 40,
        "type": "home_tasks/get_external_tasks",
        "entity_id": "todo.ws_external",
    })
    msg = await client.receive_json()
    assert msg["success"] is True
    tasks = msg["result"]["tasks"]
    assert len(tasks) == 2

    task_a = next(t for t in tasks if t["id"] == "ext-1")
    assert task_a["title"] == "Task A"
    assert task_a["priority"] == 3
    assert task_a["tags"] == ["urgent"]
    assert task_a["due_date"] == "2026-06-15"
    assert task_a["_external"] is True

    task_b = next(t for t in tasks if t["id"] == "ext-2")
    assert task_b["completed"] is True


async def test_merge_tasks_provider_owns_order_true_ignores_overlay(
    hass: HomeAssistant,
) -> None:
    """When provider_owns_order=True, overlay sort_order is ignored.

    This is the correct behaviour when the provider's MOVE_TODO_ITEM is
    working: the provider's index is the source of truth so reorders made
    externally (e.g. in the Google Tasks app) aren't shadowed by a stale
    overlay sort_order from a previous in-card reorder.
    """
    from custom_components.home_tasks.overlay_store import ExternalTaskOverlayStore
    from custom_components.home_tasks.websocket_api import _merge_tasks_with_overlays

    overlay_store = ExternalTaskOverlayStore(hass, "todo.order_test")
    await overlay_store.async_load()
    await overlay_store.async_set_overlay("uid-1", sort_order=99)

    external_items = [
        {"uid": "uid-1", "summary": "First", "status": "needs_action", "due": None, "due_time": None, "description": None},
        {"uid": "uid-2", "summary": "Second", "status": "needs_action", "due": None, "due_time": None, "description": None},
    ]
    tasks = _merge_tasks_with_overlays(external_items, overlay_store, provider_owns_order=True)
    # Overlay is suppressed — provider index wins
    assert tasks[0]["sort_order"] == 0
    assert tasks[1]["sort_order"] == 1


async def test_merge_tasks_provider_owns_order_false_uses_overlay_sort(
    hass: HomeAssistant,
) -> None:
    """When provider_owns_order=False, overlay sort_order is used if set."""
    from custom_components.home_tasks.overlay_store import ExternalTaskOverlayStore
    from custom_components.home_tasks.websocket_api import _merge_tasks_with_overlays

    overlay_store = ExternalTaskOverlayStore(hass, "todo.order_test2")
    await overlay_store.async_load()
    await overlay_store.async_set_overlay("uid-1", sort_order=99)

    external_items = [
        {"uid": "uid-1", "summary": "First", "status": "needs_action", "due": None, "due_time": None, "description": None},
        {"uid": "uid-2", "summary": "Second", "status": "needs_action", "due": None, "due_time": None, "description": None},
    ]
    tasks = _merge_tasks_with_overlays(external_items, overlay_store, provider_owns_order=False)
    assert tasks[0]["sort_order"] == 99  # overlay value
    assert tasks[1]["sort_order"] == 1   # fallback to index


async def test_get_external_todo_items_skips_no_uid(
    hass: HomeAssistant,
) -> None:
    """_get_external_todo_items skips items with uid=None."""
    from unittest.mock import MagicMock
    from homeassistant.components.todo import TodoItem, TodoItemStatus
    from custom_components.home_tasks.websocket_api import _get_external_todo_items

    mock_entity = MagicMock()
    mock_entity.todo_items = [
        TodoItem(uid="abc", summary="Has UID", status=TodoItemStatus.NEEDS_ACTION),
        TodoItem(uid=None, summary="No UID", status=TodoItemStatus.NEEDS_ACTION),
    ]
    mock_comp = MagicMock()
    mock_comp.get_entity.return_value = mock_entity
    hass.data["todo"] = mock_comp
    hass.states.async_set("todo.uid_test", "2")

    items = _get_external_todo_items(hass, "todo.uid_test")
    assert len(items) == 1
    assert items[0]["uid"] == "abc"


async def test_get_external_todo_items_splits_datetime_due(
    hass: HomeAssistant,
) -> None:
    """_get_external_todo_items splits a datetime due into date and time parts."""
    from unittest.mock import MagicMock
    from datetime import datetime, timezone
    from homeassistant.components.todo import TodoItem, TodoItemStatus
    from custom_components.home_tasks.websocket_api import _get_external_todo_items

    mock_entity = MagicMock()
    mock_entity.todo_items = [
        TodoItem(
            uid="dt-1",
            summary="Datetime due",
            status=TodoItemStatus.NEEDS_ACTION,
            due=datetime(2026, 6, 15, 14, 30, tzinfo=timezone.utc),
        ),
    ]
    mock_comp = MagicMock()
    mock_comp.get_entity.return_value = mock_entity
    hass.data["todo"] = mock_comp
    hass.states.async_set("todo.dt_test", "1")

    items = _get_external_todo_items(hass, "todo.dt_test")
    assert len(items) == 1
    # The due is converted to local time; verify it has date and time parts
    assert items[0]["due"] is not None
    assert items[0]["due_time"] is not None
    # Verify date format YYYY-MM-DD
    import re
    assert re.match(r"^\d{4}-\d{2}-\d{2}$", items[0]["due"])
    # Verify time format HH:MM
    assert re.match(r"^\d{2}:\d{2}$", items[0]["due_time"])


async def test_get_external_todo_items_entity_not_found(
    hass: HomeAssistant,
) -> None:
    """_get_external_todo_items raises ValueError for nonexistent entity."""
    from custom_components.home_tasks.websocket_api import _get_external_todo_items

    with pytest.raises(ValueError, match="Entity not found"):
        _get_external_todo_items(hass, "todo.nonexistent_entity")


# ---------------------------------------------------------------------------
# WS error branches: invalid / nonexistent list_id (tests 1–10)
# ---------------------------------------------------------------------------

BAD_LIST_ID = "nonexistent-list-id-xyz"


async def test_ws_get_tasks_invalid_list(
    hass: HomeAssistant, hass_ws_client, mock_config_entry
) -> None:
    """get_tasks with a nonexistent list_id returns invalid_request."""
    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 50, "type": "home_tasks/get_tasks", "list_id": BAD_LIST_ID,
    })
    msg = await client.receive_json()
    assert msg["success"] is False
    assert msg["error"]["code"] == "invalid_request"


async def test_ws_add_task_invalid_list(
    hass: HomeAssistant, hass_ws_client, mock_config_entry
) -> None:
    """add_task with a nonexistent list_id returns invalid_request."""
    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 51, "type": "home_tasks/add_task",
        "list_id": BAD_LIST_ID, "title": "Fail",
    })
    msg = await client.receive_json()
    assert msg["success"] is False
    assert msg["error"]["code"] == "invalid_request"


async def test_ws_update_task_invalid_list(
    hass: HomeAssistant, hass_ws_client, mock_config_entry
) -> None:
    """update_task with a nonexistent list_id returns invalid_request."""
    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 52, "type": "home_tasks/update_task",
        "list_id": BAD_LIST_ID, "task_id": "fake-task-id",
    })
    msg = await client.receive_json()
    assert msg["success"] is False
    assert msg["error"]["code"] == "invalid_request"


async def test_ws_delete_task_invalid_list(
    hass: HomeAssistant, hass_ws_client, mock_config_entry
) -> None:
    """delete_task with a nonexistent list_id returns invalid_request."""
    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 53, "type": "home_tasks/delete_task",
        "list_id": BAD_LIST_ID, "task_id": "fake-task-id",
    })
    msg = await client.receive_json()
    assert msg["success"] is False
    assert msg["error"]["code"] == "invalid_request"


async def test_ws_reorder_tasks_invalid_list(
    hass: HomeAssistant, hass_ws_client, mock_config_entry
) -> None:
    """reorder_tasks with a nonexistent list_id returns invalid_request."""
    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 54, "type": "home_tasks/reorder_tasks",
        "list_id": BAD_LIST_ID, "task_ids": [],
    })
    msg = await client.receive_json()
    assert msg["success"] is False
    assert msg["error"]["code"] == "invalid_request"


async def test_ws_add_sub_task_invalid_list(
    hass: HomeAssistant, hass_ws_client, mock_config_entry
) -> None:
    """add_sub_task with a nonexistent list_id returns invalid_request."""
    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 55, "type": "home_tasks/add_sub_task",
        "list_id": BAD_LIST_ID, "task_id": "fake-task-id", "title": "Sub",
    })
    msg = await client.receive_json()
    assert msg["success"] is False
    assert msg["error"]["code"] == "invalid_request"


async def test_ws_update_sub_task_invalid_list(
    hass: HomeAssistant, hass_ws_client, mock_config_entry
) -> None:
    """update_sub_task with a nonexistent list_id returns invalid_request."""
    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 56, "type": "home_tasks/update_sub_task",
        "list_id": BAD_LIST_ID, "task_id": "fake-task-id",
        "sub_task_id": "fake-sub-id",
    })
    msg = await client.receive_json()
    assert msg["success"] is False
    assert msg["error"]["code"] == "invalid_request"


async def test_ws_delete_sub_task_invalid_list(
    hass: HomeAssistant, hass_ws_client, mock_config_entry
) -> None:
    """delete_sub_task with a nonexistent list_id returns invalid_request."""
    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 57, "type": "home_tasks/delete_sub_task",
        "list_id": BAD_LIST_ID, "task_id": "fake-task-id",
        "sub_task_id": "fake-sub-id",
    })
    msg = await client.receive_json()
    assert msg["success"] is False
    assert msg["error"]["code"] == "invalid_request"


async def test_ws_reorder_sub_tasks_invalid_list(
    hass: HomeAssistant, hass_ws_client, mock_config_entry
) -> None:
    """reorder_sub_tasks with a nonexistent list_id returns invalid_request."""
    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 58, "type": "home_tasks/reorder_sub_tasks",
        "list_id": BAD_LIST_ID, "task_id": "fake-task-id",
        "sub_task_ids": [],
    })
    msg = await client.receive_json()
    assert msg["success"] is False
    assert msg["error"]["code"] == "invalid_request"


async def test_ws_move_task_invalid_source(
    hass: HomeAssistant, hass_ws_client, mock_config_entry
) -> None:
    """move_task with a nonexistent source_list_id returns invalid_request."""
    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 59, "type": "home_tasks/move_task",
        "source_list_id": BAD_LIST_ID,
        "target_list_id": mock_config_entry.entry_id,
        "task_id": "fake-task-id",
    })
    msg = await client.receive_json()
    assert msg["success"] is False
    assert msg["error"]["code"] == "invalid_request"


async def test_ws_get_external_tasks_no_overlay_store(
    hass: HomeAssistant, hass_ws_client, mock_config_entry
) -> None:
    """get_external_tasks for an entity with no overlay store returns error."""
    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 60, "type": "home_tasks/get_external_tasks",
        "entity_id": "todo.no_overlay_entity",
    })
    msg = await client.receive_json()
    assert msg["success"] is False
    assert msg["error"]["code"] == "invalid_request"


async def test_ws_get_external_lists_with_linked(
    hass: HomeAssistant, hass_ws_client, mock_config_entry, patch_add_extra_js_url
) -> None:
    """get_external_lists shows linked=True and supported_features for linked entities."""
    from homeassistant.helpers import entity_registry as er

    # Register a fake todo entity from another integration
    reg = er.async_get(hass)
    reg.async_get_or_create(
        "todo", "caldav", "fake-caldav-uid", suggested_object_id="ws_external"
    )
    # Set state with supported_features
    hass.states.async_set("todo.ws_external", "0", {"supported_features": 119})

    # Create an external config entry linking to this entity
    ext_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"type": "external", "entity_id": "todo.ws_external", "name": "WS External"},
        title="WS External (External)",
    )
    ext_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(ext_entry.entry_id)
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)
    await client.send_json({"id": 61, "type": "home_tasks/get_external_lists"})
    msg = await client.receive_json()
    assert msg["success"] is True
    lists = msg["result"]["external_lists"]
    matched = [el for el in lists if el["entity_id"] == "todo.ws_external"]
    assert len(matched) == 1
    assert matched[0]["linked"] is True
    assert matched[0]["supported_features"] == 119


# ---------------------------------------------------------------------------
# move_task_cross — universal cross-list move (native ↔ external)
# ---------------------------------------------------------------------------


class _MockAdapter:
    """In-memory adapter that records create/delete calls and stores tasks."""

    def __init__(self, provider_type="generic"):
        from custom_components.home_tasks.provider_adapters import ProviderCapabilities
        self.provider_type = provider_type
        self.capabilities = ProviderCapabilities(
            can_sync_priority=True,
            can_sync_labels=True,
            can_sync_order=True,
            can_sync_due_time=True,
            can_sync_description=True,
            can_sync_assignee=True,
            can_sync_sub_items=True,
            can_sync_recurrence=True,
            can_sync_reminders=True,
        )
        self.created: list[dict] = []
        self.deleted: list[str] = []
        self._tasks: list[dict] = []
        self._next_id = 1

    async def async_create_task(self, fields):
        uid = f"mock-uid-{self._next_id}"
        self._next_id += 1
        item = {"uid": uid, "summary": fields.get("title", ""), "status": "needs_action"}
        item.update({k: v for k, v in fields.items() if k != "title"})
        self._tasks.append(item)
        self.created.append({"uid": uid, **fields})
        return uid, {}

    async def async_delete_task(self, task_uid):
        self.deleted.append(task_uid)
        self._tasks = [t for t in self._tasks if t["uid"] != task_uid]

    async def async_read_tasks(self):
        return list(self._tasks)

    async def async_add_sub_task(self, parent_uid, title):
        return None

    async def _sync_reminders(self, uid, reminders):
        pass


async def test_ws_move_task_cross_native_to_native(
    hass: HomeAssistant, hass_ws_client, mock_config_entry, store, patch_add_extra_js_url
) -> None:
    """move_task_cross delegates native→native to async_export/import_task."""
    entry2 = MockConfigEntry(domain=DOMAIN, data={"name": "Target List"}, title="Target List")
    entry2.add_to_hass(hass)
    await hass.config_entries.async_setup(entry2.entry_id)
    await hass.async_block_till_done()

    task = await store.async_add_task("Cross move me")
    await store.async_update_task(task["id"], priority=2, tags=["work"])

    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 100,
        "type": "home_tasks/move_task_cross",
        "task_id": task["id"],
        "source_list_id": mock_config_entry.entry_id,
        "target_list_id": entry2.entry_id,
    })
    msg = await client.receive_json()
    assert msg["success"] is True
    assert all(t["id"] != task["id"] for t in store.tasks)
    target_store = hass.data[DOMAIN][entry2.entry_id]
    moved = next(t for t in target_store.tasks if t["title"] == "Cross move me")
    assert moved["priority"] == 2
    assert moved["tags"] == ["work"]


async def test_ws_move_task_cross_missing_source(
    hass: HomeAssistant, hass_ws_client, mock_config_entry
) -> None:
    """move_task_cross without any source returns invalid_request."""
    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 101,
        "type": "home_tasks/move_task_cross",
        "task_id": "fake",
        "target_list_id": mock_config_entry.entry_id,
    })
    msg = await client.receive_json()
    assert msg["success"] is False


async def test_ws_move_task_cross_missing_target(
    hass: HomeAssistant, hass_ws_client, mock_config_entry
) -> None:
    """move_task_cross without any target returns invalid_request."""
    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 102,
        "type": "home_tasks/move_task_cross",
        "task_id": "fake",
        "source_list_id": mock_config_entry.entry_id,
    })
    msg = await client.receive_json()
    assert msg["success"] is False


async def test_ws_move_task_cross_native_to_native_same_error(
    hass: HomeAssistant, hass_ws_client, mock_config_entry, store
) -> None:
    """move_task_cross with identical native source/target returns error."""
    task = await store.async_add_task("Same list")
    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 103,
        "type": "home_tasks/move_task_cross",
        "task_id": task["id"],
        "source_list_id": mock_config_entry.entry_id,
        "target_list_id": mock_config_entry.entry_id,
    })
    msg = await client.receive_json()
    assert msg["success"] is False


async def test_ws_move_task_cross_native_to_external(
    hass: HomeAssistant, hass_ws_client, mock_config_entry, store,
    external_config_entry,
) -> None:
    """move_task_cross sends task to external adapter and removes it from source."""
    # Replace the auto-registered adapter with our mock
    mock_adapter = _MockAdapter("generic")
    hass.data.setdefault(f"{DOMAIN}_adapters", {})["todo.ws_external"] = mock_adapter

    task = await store.async_add_task("Going external")
    await store.async_update_task(
        task["id"], notes="some notes", priority=3, tags=["urgent"], reminders=[60]
    )

    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 104,
        "type": "home_tasks/move_task_cross",
        "task_id": task["id"],
        "source_list_id": mock_config_entry.entry_id,
        "target_entity_id": "todo.ws_external",
    })
    msg = await client.receive_json()
    assert msg["success"] is True

    # Source: removed
    assert all(t["id"] != task["id"] for t in store.tasks)
    # Target: created via adapter
    assert len(mock_adapter.created) == 1
    assert mock_adapter.created[0]["title"] == "Going external"
    assert mock_adapter.created[0]["priority"] == 3

    # Overlay should hold all overlay-eligible fields (priority, tags, reminders, etc.)
    from custom_components.home_tasks.overlay_store import ExternalTaskOverlayStore
    overlay = hass.data[DOMAIN][external_config_entry.entry_id]
    assert isinstance(overlay, ExternalTaskOverlayStore)
    new_uid = mock_adapter.created[0]["uid"]
    saved = overlay.get_overlay(new_uid)
    assert saved.get("tags") == ["urgent"]
    assert saved.get("reminders") == [60]


async def test_ws_move_task_cross_external_to_native(
    hass: HomeAssistant, hass_ws_client, mock_config_entry, store,
    external_config_entry,
) -> None:
    """move_task_cross reads source from external adapter (rich path) and creates a native task."""
    mock_adapter = _MockAdapter("generic")
    # Pre-populate adapter — return values match the adapter contract (ISO strings)
    mock_adapter._tasks.append({
        "uid": "ext-uid-99",
        "summary": "External original",
        "status": "needs_action",
        "due": "2026-07-01",
        "priority": 2,
        "labels": ["from_provider"],
        "sub_items": [],
    })
    hass.data.setdefault(f"{DOMAIN}_adapters", {})["todo.ws_external"] = mock_adapter

    # Set an overlay field so we can verify it's read during the merge
    overlay = hass.data[DOMAIN][external_config_entry.entry_id]
    await overlay.async_set_overlay("ext-uid-99", reminders=[15])

    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 105,
        "type": "home_tasks/move_task_cross",
        "task_id": "ext-uid-99",
        "source_entity_id": "todo.ws_external",
        "target_list_id": mock_config_entry.entry_id,
    })
    msg = await client.receive_json()
    assert msg["success"] is True

    # Native target should now have the task
    moved = next((t for t in store.tasks if t["title"] == "External original"), None)
    assert moved is not None
    assert moved["due_date"] == "2026-07-01"
    assert moved["priority"] == 2
    assert moved["tags"] == ["from_provider"]
    assert moved["reminders"] == [15]

    # Source provider was deleted from
    assert "ext-uid-99" in mock_adapter.deleted


async def test_ws_move_task_cross_external_to_external(
    hass: HomeAssistant, hass_ws_client, mock_config_entry, patch_add_extra_js_url
) -> None:
    """move_task_cross transfers between two external entities via adapters (rich path)."""
    # Two external entries
    src_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"type": "external", "entity_id": "todo.src_ext", "name": "Source Ext"},
        title="Source Ext (External)",
    )
    src_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(src_entry.entry_id)
    tgt_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"type": "external", "entity_id": "todo.tgt_ext", "name": "Target Ext"},
        title="Target Ext (External)",
    )
    tgt_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(tgt_entry.entry_id)
    await hass.async_block_till_done()

    src_adapter = _MockAdapter("generic")
    tgt_adapter = _MockAdapter("generic")
    src_adapter._tasks.append({
        "uid": "src-uid-1",
        "summary": "Cross-ext task",
        "status": "needs_action",
        "labels": [],
        "sub_items": [],
    })
    hass.data.setdefault(f"{DOMAIN}_adapters", {})["todo.src_ext"] = src_adapter
    hass.data[f"{DOMAIN}_adapters"]["todo.tgt_ext"] = tgt_adapter

    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 106,
        "type": "home_tasks/move_task_cross",
        "task_id": "src-uid-1",
        "source_entity_id": "todo.src_ext",
        "target_entity_id": "todo.tgt_ext",
    })
    msg = await client.receive_json()
    assert msg["success"] is True

    # Created on target adapter, deleted from source
    assert len(tgt_adapter.created) == 1
    assert tgt_adapter.created[0]["title"] == "Cross-ext task"
    assert "src-uid-1" in src_adapter.deleted


# ---------------------------------------------------------------------------
# create / update / reorder external tasks (adapter-routed)
# ---------------------------------------------------------------------------


async def test_ws_create_external_task_via_adapter(
    hass: HomeAssistant, hass_ws_client, external_config_entry
) -> None:
    """create_external_task forwards to adapter and returns the new uid."""
    mock_adapter = _MockAdapter("generic")
    hass.data.setdefault(f"{DOMAIN}_adapters", {})["todo.ws_external"] = mock_adapter

    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 200,
        "type": "home_tasks/create_external_task",
        "entity_id": "todo.ws_external",
        "title": "New external task",
        "priority": 2,
    })
    msg = await client.receive_json()
    assert msg["success"] is True
    assert msg["result"]["uid"].startswith("mock-uid-")
    assert mock_adapter.created[0]["title"] == "New external task"
    assert mock_adapter.created[0]["priority"] == 2


async def test_ws_create_external_task_overlay_for_unsynced_reminders(
    hass: HomeAssistant, hass_ws_client, external_config_entry
) -> None:
    """create_external_task stores reminders in overlay when adapter cannot sync them."""
    from custom_components.home_tasks.provider_adapters import ProviderCapabilities

    mock_adapter = _MockAdapter("generic")
    # Override capabilities to NOT sync reminders
    mock_adapter.capabilities = ProviderCapabilities(
        can_sync_priority=True,
        can_sync_labels=True,
        can_sync_order=True,
        can_sync_due_time=True,
        can_sync_description=True,
        can_sync_assignee=True,
        can_sync_sub_items=True,
        can_sync_recurrence=True,
        can_sync_reminders=False,
    )
    hass.data.setdefault(f"{DOMAIN}_adapters", {})["todo.ws_external"] = mock_adapter

    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 201,
        "type": "home_tasks/create_external_task",
        "entity_id": "todo.ws_external",
        "title": "Reminder task",
        "reminders": [30, 60],
    })
    msg = await client.receive_json()
    assert msg["success"] is True
    new_uid = msg["result"]["uid"]

    overlay = hass.data[DOMAIN][external_config_entry.entry_id]
    saved = overlay.get_overlay(new_uid)
    assert saved.get("reminders") == [30, 60]


async def test_ws_update_external_task_routes_unsynced_to_overlay(
    hass: HomeAssistant, hass_ws_client, external_config_entry
) -> None:
    """update_external_task stores unsynced fields in the overlay."""
    class _UnsyncedAdapter(_MockAdapter):
        async def async_update_task(self, task_uid, fields):
            # Pretend nothing is synced; everything is unsynced
            return dict(fields)

    adapter = _UnsyncedAdapter("generic")
    hass.data.setdefault(f"{DOMAIN}_adapters", {})["todo.ws_external"] = adapter

    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 202,
        "type": "home_tasks/update_external_task",
        "entity_id": "todo.ws_external",
        "task_uid": "uid-x",
        "priority": 3,
        "tags": ["a", "b"],
    })
    msg = await client.receive_json()
    assert msg["success"] is True
    assert "priority" in msg["result"]["unsynced"]
    assert "tags" in msg["result"]["unsynced"]

    overlay = hass.data[DOMAIN][external_config_entry.entry_id]
    saved = overlay.get_overlay("uid-x")
    assert saved.get("priority") == 3
    assert saved.get("tags") == ["a", "b"]


async def test_ws_reorder_external_tasks_provider_handled(
    hass: HomeAssistant, hass_ws_client, external_config_entry
) -> None:
    """reorder_external_tasks reports provider_handled=True when adapter accepts it."""
    class _ReorderAdapter(_MockAdapter):
        async def async_reorder_tasks(self, task_uids):
            self.last_reorder = task_uids
            return True

    adapter = _ReorderAdapter("generic")
    hass.data.setdefault(f"{DOMAIN}_adapters", {})["todo.ws_external"] = adapter

    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 203,
        "type": "home_tasks/reorder_external_tasks",
        "entity_id": "todo.ws_external",
        "task_uids": ["a", "b", "c"],
    })
    msg = await client.receive_json()
    assert msg["success"] is True
    assert msg["result"]["provider_handled"] is True
    assert adapter.last_reorder == ["a", "b", "c"]


async def test_ws_reorder_external_tasks_falls_back_to_overlay(
    hass: HomeAssistant, hass_ws_client, external_config_entry
) -> None:
    """reorder_external_tasks falls back to overlay sort_order when adapter declines."""
    class _NoReorderAdapter(_MockAdapter):
        async def async_reorder_tasks(self, task_uids):
            return False  # provider does not handle order

    adapter = _NoReorderAdapter("generic")
    hass.data.setdefault(f"{DOMAIN}_adapters", {})["todo.ws_external"] = adapter

    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 204,
        "type": "home_tasks/reorder_external_tasks",
        "entity_id": "todo.ws_external",
        "task_uids": ["x", "y", "z"],
    })
    msg = await client.receive_json()
    assert msg["success"] is True
    assert msg["result"]["provider_handled"] is False

    overlay = hass.data[DOMAIN][external_config_entry.entry_id]
    assert overlay.get_overlay("x").get("sort_order") == 0
    assert overlay.get_overlay("y").get("sort_order") == 1
    assert overlay.get_overlay("z").get("sort_order") == 2


# ---------------------------------------------------------------------------
# Adapter sub-task commands when capabilities.can_sync_sub_items=True
# ---------------------------------------------------------------------------


class _SubTaskAdapter(_MockAdapter):
    """Mock adapter with sub-task tracking for the four sub-task commands."""

    def __init__(self, provider_type="generic"):
        super().__init__(provider_type)
        self._sub_calls: dict[str, list] = {
            "add": [], "update": [], "delete": [], "reorder": [],
        }

    async def async_add_sub_task(self, parent_uid, title):
        self._sub_calls["add"].append((parent_uid, title))
        return f"sub-{len(self._sub_calls['add'])}"

    async def async_update_sub_task(self, sub_task_uid, **fields):
        self._sub_calls["update"].append((sub_task_uid, fields))
        return True

    async def async_delete_sub_task(self, sub_task_uid):
        self._sub_calls["delete"].append(sub_task_uid)
        return True

    async def async_reorder_sub_tasks(self, parent_uid, sub_task_uids):
        self._sub_calls["reorder"].append((parent_uid, list(sub_task_uids)))
        return True


async def test_ws_add_external_sub_task_via_adapter(
    hass: HomeAssistant, hass_ws_client, external_config_entry
) -> None:
    """add_external_sub_task delegates to adapter when can_sync_sub_items=True."""
    adapter = _SubTaskAdapter()
    hass.data.setdefault(f"{DOMAIN}_adapters", {})["todo.ws_external"] = adapter

    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 300,
        "type": "home_tasks/add_external_sub_task",
        "entity_id": "todo.ws_external",
        "task_uid": "parent-1",
        "title": "Sub via adapter",
    })
    msg = await client.receive_json()
    assert msg["success"] is True
    assert msg["result"]["title"] == "Sub via adapter"
    assert msg["result"]["completed"] is False
    assert ("parent-1", "Sub via adapter") in adapter._sub_calls["add"]


async def test_ws_update_external_sub_task_via_adapter(
    hass: HomeAssistant, hass_ws_client, external_config_entry
) -> None:
    """update_external_sub_task delegates to adapter when supported."""
    adapter = _SubTaskAdapter()
    hass.data.setdefault(f"{DOMAIN}_adapters", {})["todo.ws_external"] = adapter

    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 301,
        "type": "home_tasks/update_external_sub_task",
        "entity_id": "todo.ws_external",
        "task_uid": "parent-1",
        "sub_task_id": "sub-99",
        "title": "Renamed sub",
        "completed": True,
    })
    msg = await client.receive_json()
    assert msg["success"] is True
    assert adapter._sub_calls["update"][0][0] == "sub-99"
    assert adapter._sub_calls["update"][0][1]["title"] == "Renamed sub"
    assert adapter._sub_calls["update"][0][1]["completed"] is True


async def test_ws_delete_external_sub_task_via_adapter(
    hass: HomeAssistant, hass_ws_client, external_config_entry
) -> None:
    """delete_external_sub_task delegates to adapter when supported."""
    adapter = _SubTaskAdapter()
    hass.data.setdefault(f"{DOMAIN}_adapters", {})["todo.ws_external"] = adapter

    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 302,
        "type": "home_tasks/delete_external_sub_task",
        "entity_id": "todo.ws_external",
        "task_uid": "parent-1",
        "sub_task_id": "sub-42",
    })
    msg = await client.receive_json()
    assert msg["success"] is True
    assert "sub-42" in adapter._sub_calls["delete"]


async def test_ws_reorder_external_sub_tasks_via_adapter(
    hass: HomeAssistant, hass_ws_client, external_config_entry
) -> None:
    """reorder_external_sub_tasks delegates to adapter when supported."""
    adapter = _SubTaskAdapter()
    hass.data.setdefault(f"{DOMAIN}_adapters", {})["todo.ws_external"] = adapter

    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 303,
        "type": "home_tasks/reorder_external_sub_tasks",
        "entity_id": "todo.ws_external",
        "task_uid": "parent-1",
        "sub_task_ids": ["a", "b", "c"],
    })
    msg = await client.receive_json()
    assert msg["success"] is True
    assert adapter._sub_calls["reorder"][0] == ("parent-1", ["a", "b", "c"])


# ---------------------------------------------------------------------------
# get_external_tasks rich adapter path (vs. generic path already covered)
# ---------------------------------------------------------------------------


async def test_ws_get_external_tasks_via_rich_adapter(
    hass: HomeAssistant, hass_ws_client, external_config_entry
) -> None:
    """get_external_tasks reads from adapter.async_read_tasks when adapter is rich."""
    adapter = _MockAdapter("generic")
    adapter._tasks.append({
        "uid": "rich-1",
        "summary": "Rich adapter task",
        "status": "needs_action",
        "labels": ["alpha"],
        "sub_items": [],
        "priority": 2,
    })
    hass.data.setdefault(f"{DOMAIN}_adapters", {})["todo.ws_external"] = adapter

    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 304,
        "type": "home_tasks/get_external_tasks",
        "entity_id": "todo.ws_external",
    })
    msg = await client.receive_json()
    assert msg["success"] is True
    tasks = msg["result"]["tasks"]
    assert any(t["id"] == "rich-1" for t in tasks)
    rich = next(t for t in tasks if t["id"] == "rich-1")
    assert rich["title"] == "Rich adapter task"
    assert rich["tags"] == ["alpha"]
    assert rich["priority"] == 2


# ---------------------------------------------------------------------------
# create_external_task / update_external_task fallback paths (no adapter)
# ---------------------------------------------------------------------------


async def test_ws_create_external_task_without_adapter_uses_generic(
    hass: HomeAssistant, hass_ws_client, external_config_entry
) -> None:
    """When no adapter is registered, create_external_task falls back to GenericAdapter."""
    # Remove any pre-registered adapter
    hass.data.get(f"{DOMAIN}_adapters", {}).pop("todo.ws_external", None)

    # Mock the generic adapter's async_create_task by patching at the module level
    from unittest.mock import AsyncMock, patch
    with patch(
        "custom_components.home_tasks.websocket_api.GenericAdapter"
    ) as mock_generic:
        instance = mock_generic.return_value
        instance.async_create_task = AsyncMock(return_value=(None, {}))

        client = await hass_ws_client(hass)
        await client.send_json({
            "id": 305,
            "type": "home_tasks/create_external_task",
            "entity_id": "todo.ws_external",
            "title": "Generic create",
        })
        msg = await client.receive_json()
        assert msg["success"] is True
        assert msg["result"]["uid"] is None
        instance.async_create_task.assert_awaited_once()


async def test_ws_update_external_task_without_adapter_uses_generic(
    hass: HomeAssistant, hass_ws_client, external_config_entry
) -> None:
    """When no adapter is registered, update_external_task falls back to GenericAdapter."""
    hass.data.get(f"{DOMAIN}_adapters", {}).pop("todo.ws_external", None)

    from unittest.mock import AsyncMock, patch
    with patch(
        "custom_components.home_tasks.websocket_api.GenericAdapter"
    ) as mock_generic:
        instance = mock_generic.return_value
        instance.async_update_task = AsyncMock(return_value={"priority": 3})

        client = await hass_ws_client(hass)
        await client.send_json({
            "id": 306,
            "type": "home_tasks/update_external_task",
            "entity_id": "todo.ws_external",
            "task_uid": "uid-1",
            "title": "x",
        })
        msg = await client.receive_json()
        assert msg["success"] is True
        instance.async_update_task.assert_awaited_once()


# ---------------------------------------------------------------------------
# Cross-move generic-target fallback path (no adapter on target)
# ---------------------------------------------------------------------------


async def test_ws_move_task_cross_native_to_generic_target(
    hass: HomeAssistant, hass_ws_client, mock_config_entry, store, patch_add_extra_js_url,
) -> None:
    """move_task_cross to an external entity without an adapter uses GenericAdapter
    and discovers the new uid via re-fetch."""
    # Set up an external entry but DON'T register an adapter for it
    ext_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"type": "external", "entity_id": "todo.cross_generic", "name": "CrossGen"},
        title="CrossGen (External)",
    )
    ext_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(ext_entry.entry_id)
    await hass.async_block_till_done()

    # Remove the auto-registered adapter so the generic fallback runs
    hass.data.get(f"{DOMAIN}_adapters", {}).pop("todo.cross_generic", None)

    task = await store.async_add_task("Move via generic")
    await store.async_update_task(task["id"], priority=2, tags=["g1"])

    # Patch GenericAdapter so its async_create_task and _get_external_todo_items work
    from unittest.mock import AsyncMock, patch
    with patch(
        "custom_components.home_tasks.websocket_api.GenericAdapter"
    ) as mock_generic, patch(
        "custom_components.home_tasks.websocket_api._get_external_todo_items",
        return_value=[{"uid": "new-uid-99", "summary": "Move via generic"}],
    ):
        instance = mock_generic.return_value
        instance.async_create_task = AsyncMock(return_value=(None, {}))
        instance.async_delete_task = AsyncMock()

        client = await hass_ws_client(hass)
        await client.send_json({
            "id": 307,
            "type": "home_tasks/move_task_cross",
            "task_id": task["id"],
            "source_list_id": mock_config_entry.entry_id,
            "target_entity_id": "todo.cross_generic",
        })
        msg = await client.receive_json()
        assert msg["success"] is True
        assert all(t["id"] != task["id"] for t in store.tasks)
        instance.async_create_task.assert_awaited_once()

    # Overlay should have the moved fields under the discovered uid
    overlay = hass.data[DOMAIN][ext_entry.entry_id]
    saved = overlay.get_overlay("new-uid-99")
    assert saved.get("priority") == 2
    assert saved.get("tags") == ["g1"]


async def test_ws_move_task_cross_generic_source_with_adapter(
    hass: HomeAssistant, hass_ws_client, mock_config_entry, store, external_config_entry,
) -> None:
    """move_task_cross from a generic external source (no adapter) to native list."""
    # Remove any adapter so the generic _get_external_todo_items path runs for source
    hass.data.get(f"{DOMAIN}_adapters", {}).pop("todo.ws_external", None)

    from unittest.mock import patch, AsyncMock

    with patch(
        "custom_components.home_tasks.websocket_api._get_external_todo_items",
        return_value=[{
            "uid": "src-only-99",
            "summary": "Generic source",
            "status": "needs_action",
            "due": "2027-04-15",
        }],
    ), patch(
        "custom_components.home_tasks.websocket_api.GenericAdapter"
    ) as mock_generic:
        instance = mock_generic.return_value
        instance.async_delete_task = AsyncMock()

        client = await hass_ws_client(hass)
        await client.send_json({
            "id": 308,
            "type": "home_tasks/move_task_cross",
            "task_id": "src-only-99",
            "source_entity_id": "todo.ws_external",
            "target_list_id": mock_config_entry.entry_id,
        })
        msg = await client.receive_json()
        assert msg["success"] is True
        moved = next((t for t in store.tasks if t["title"] == "Generic source"), None)
        assert moved is not None
        assert moved["due_date"] == "2027-04-15"
        instance.async_delete_task.assert_awaited_once_with("src-only-99")


# ---------------------------------------------------------------------------
# Cross-move native → external with recurrence + sub-items (covers more branches)
# ---------------------------------------------------------------------------


async def test_ws_move_task_cross_with_recurrence_and_subitems(
    hass: HomeAssistant, hass_ws_client, mock_config_entry, store, external_config_entry,
) -> None:
    """Native task with recurrence config + sub-items moved to a rich adapter."""
    adapter = _SubTaskAdapter("generic")
    hass.data.setdefault(f"{DOMAIN}_adapters", {})["todo.ws_external"] = adapter

    task = await store.async_add_task("Recurring with subs")
    tid = task["id"]
    await store.async_update_task(
        tid,
        recurrence_enabled=True,
        recurrence_unit="days",
        recurrence_value=1,
        recurrence_type="interval",
    )
    await store.async_add_sub_task(tid, "first sub")
    await store.async_add_sub_task(tid, "second sub")

    client = await hass_ws_client(hass)
    await client.send_json({
        "id": 309,
        "type": "home_tasks/move_task_cross",
        "task_id": tid,
        "source_list_id": mock_config_entry.entry_id,
        "target_entity_id": "todo.ws_external",
    })
    msg = await client.receive_json()
    assert msg["success"] is True
    # Adapter received recurrence + the two sub-tasks
    assert adapter.created[0]["recurrence_enabled"] is True
    assert len(adapter._sub_calls["add"]) == 2
    sub_titles = [c[1] for c in adapter._sub_calls["add"]]
    assert "first sub" in sub_titles
    assert "second sub" in sub_titles
