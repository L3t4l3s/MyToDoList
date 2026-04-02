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
