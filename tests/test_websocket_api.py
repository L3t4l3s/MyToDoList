"""Tests for the Home Tasks WebSocket API commands."""
from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

DOMAIN = "home_tasks"


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
    """When provider_owns_order=True, sort_order equals index, not overlay value."""
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
