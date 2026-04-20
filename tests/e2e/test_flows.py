"""End-to-end flow tests for the Home Tasks WebSocket API.

These tests drive the full WebSocket command chains against an in-memory HA
instance — the same code path a real browser card uses.  They complement the
unit tests (which test individual functions in isolation) by catching bugs
where multiple commands interact incorrectly, like the reorder→get sort_order
regression where wrong service names + flawed merge logic caused tasks to snap
back to their original order.

Run:  pytest tests/e2e/ -v
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

pytestmark = pytest.mark.e2e

DOMAIN = "home_tasks"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _ws(hass, hass_ws_client):
    """Open a WebSocket client connected to hass."""
    return await hass_ws_client(hass)


async def _cmd(ws, msg_id: int, type_: str, **kwargs) -> dict:
    """Send a WS command and return the result dict."""
    await ws.send_json({"id": msg_id, "type": type_, **kwargs})
    resp = await ws.receive_json()
    assert resp.get("success"), f"WS command failed: {resp}"
    return resp.get("result", {})


async def _cmd_fail(ws, msg_id: int, type_: str, **kwargs) -> dict:
    """Send a WS command that is expected to fail, return the error dict."""
    await ws.send_json({"id": msg_id, "type": type_, **kwargs})
    resp = await ws.receive_json()
    assert not resp.get("success"), f"Expected failure but got success: {resp}"
    return resp.get("error", {})


def _populate_todo_entity(hass: HomeAssistant, entity_id: str, items: list) -> None:
    """Populate an HA todo entity's todo_items on the entity component mock.

    This only works when hass.data["todo"] already has a get_entity mock that
    returns a mock entity.  We set todo_items on it directly.
    """
    entity_comp = hass.data.get("todo")
    if entity_comp and hasattr(entity_comp, "get_entity"):
        entity = entity_comp.get_entity(entity_id)
        if entity is not None:
            entity.todo_items = items


@pytest.fixture
async def external_entry(hass: HomeAssistant, mock_config_entry, patch_add_extra_js_url):
    """Create an external config entry with overlay store for 'todo.e2e_external'."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"type": "external", "entity_id": "todo.e2e_external", "name": "E2E External"},
        title="E2E External (External)",
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


# ---------------------------------------------------------------------------
# Native list CRUD flows
# ---------------------------------------------------------------------------


async def test_create_update_delete_task_flow(
    hass: HomeAssistant,
    hass_ws_client,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Full create → get → update → get → delete → get cycle on a native list."""
    ws = await _ws(hass, hass_ws_client)

    # Get the list id
    result = await _cmd(ws, 1, "home_tasks/get_lists")
    list_id = result["lists"][0]["id"]

    # Create — add_task returns the task dict directly
    task = await _cmd(ws, 2, "home_tasks/add_task", list_id=list_id, title="Flow task")
    task_id = task["id"]
    assert task["title"] == "Flow task"

    # Set priority via update_task (priority is not in add_task schema)
    updated_task = await _cmd(ws, 3, "home_tasks/update_task",
                              list_id=list_id, task_id=task_id, priority=2)
    assert updated_task["priority"] == 2

    # Get — task present
    result = await _cmd(ws, 4, "home_tasks/get_tasks", list_id=list_id)
    assert any(t["id"] == task_id for t in result["tasks"])

    # Update title and notes
    await _cmd(ws, 5, "home_tasks/update_task",
               list_id=list_id, task_id=task_id,
               title="Renamed", notes="some note")

    # Get — reflects update
    result = await _cmd(ws, 6, "home_tasks/get_tasks", list_id=list_id)
    found = next(t for t in result["tasks"] if t["id"] == task_id)
    assert found["title"] == "Renamed"
    assert found["notes"] == "some note"

    # Delete
    await _cmd(ws, 7, "home_tasks/delete_task", list_id=list_id, task_id=task_id)

    # Get — task gone
    result = await _cmd(ws, 8, "home_tasks/get_tasks", list_id=list_id)
    assert not any(t["id"] == task_id for t in result["tasks"])


async def test_reorder_tasks_flow(
    hass: HomeAssistant,
    hass_ws_client,
    mock_config_entry: MockConfigEntry,
) -> None:
    """reorder_tasks → get_tasks returns tasks in the new order."""
    ws = await _ws(hass, hass_ws_client)
    result = await _cmd(ws, 1, "home_tasks/get_lists")
    list_id = result["lists"][0]["id"]

    # add_task returns the task dict directly (not {"task": ...})
    t1 = await _cmd(ws, 2, "home_tasks/add_task", list_id=list_id, title="Alpha")
    t2 = await _cmd(ws, 3, "home_tasks/add_task", list_id=list_id, title="Beta")
    t3 = await _cmd(ws, 4, "home_tasks/add_task", list_id=list_id, title="Gamma")
    id1, id2, id3 = t1["id"], t2["id"], t3["id"]

    # Reverse order
    await _cmd(ws, 5, "home_tasks/reorder_tasks",
               list_id=list_id, task_ids=[id3, id2, id1])

    result = await _cmd(ws, 6, "home_tasks/get_tasks", list_id=list_id)
    ordered = sorted(result["tasks"], key=lambda t: t["sort_order"])
    titles = [t["title"] for t in ordered]
    assert titles == ["Gamma", "Beta", "Alpha"]


# ---------------------------------------------------------------------------
# External task reorder flows — the regression that was fixed
# ---------------------------------------------------------------------------


async def test_reorder_external_tasks_overlay_fallback_flow(
    hass: HomeAssistant,
    hass_ws_client,
    external_entry: MockConfigEntry,
) -> None:
    """Reorder via overlay (no adapter) persists through get.

    This is the regression test for the bug where:
    1. No adapter registered for the entity → overlay-only path
    2. reorder_external_tasks writes sort_order to overlay
    3. get_external_tasks must return tasks in the overlaid order
    """
    entity_id = "todo.e2e_external"

    # Set up a mock todo entity — pattern from existing integration tests.
    # Overwriting hass.data["todo"] with a MagicMock is the standard approach
    # used by test_ws_get_external_tasks_merges_overlay in test_websocket_api.py.
    mock_entity = MagicMock()
    mock_entity.todo_items = [
        MagicMock(uid="t1", summary="Alpha",
                  status=MagicMock(value="needs_action"), due=None, description=None),
        MagicMock(uid="t2", summary="Beta",
                  status=MagicMock(value="needs_action"), due=None, description=None),
        MagicMock(uid="t3", summary="Gamma",
                  status=MagicMock(value="needs_action"), due=None, description=None),
    ]
    # Build a hybrid mock: get_entity() is sync (returns mock_entity),
    # async_unload_entry / async_setup_entry are awaitable (for HA teardown).
    mock_comp = MagicMock()
    mock_comp.get_entity.return_value = mock_entity
    mock_comp.async_unload_entry = AsyncMock(return_value=True)
    mock_comp.async_setup_entry = AsyncMock(return_value=True)
    hass.data["todo"] = mock_comp
    hass.states.async_set(entity_id, "0", {"supported_features": 0})

    ws = await _ws(hass, hass_ws_client)

    # Initial order: Alpha(0), Beta(1), Gamma(2)
    result = await _cmd(ws, 1, "home_tasks/get_external_tasks", entity_id=entity_id)
    titles_before = [t["title"] for t in sorted(result["tasks"], key=lambda t: t["sort_order"])]
    assert titles_before == ["Alpha", "Beta", "Gamma"]

    # Reorder: Gamma, Alpha, Beta — no adapter → overlay fallback
    result = await _cmd(ws, 2, "home_tasks/reorder_external_tasks",
                        entity_id=entity_id, task_uids=["t3", "t1", "t2"])
    assert result.get("provider_handled") is False

    # Get again — must reflect new order
    result = await _cmd(ws, 3, "home_tasks/get_external_tasks", entity_id=entity_id)
    titles_after = [t["title"] for t in sorted(result["tasks"], key=lambda t: t["sort_order"])]
    assert titles_after == ["Gamma", "Alpha", "Beta"]


async def test_reorder_external_tasks_adapter_accepts_flow(
    hass: HomeAssistant,
    hass_ws_client,
    external_entry: MockConfigEntry,
) -> None:
    """Reorder via adapter that returns True (provider_handled=True)."""
    entity_id = "todo.e2e_external"

    # Register a mock adapter that accepts reorder
    reordered_uids = []

    class _AcceptAdapter:
        async def async_reorder_tasks(self, task_uids):
            reordered_uids.extend(task_uids)
            return True

    hass.data.setdefault(f"{DOMAIN}_adapters", {})[entity_id] = _AcceptAdapter()

    ws = await _ws(hass, hass_ws_client)
    result = await _cmd(ws, 1, "home_tasks/reorder_external_tasks",
                        entity_id=entity_id, task_uids=["t3", "t1", "t2"])
    assert result.get("provider_handled") is True
    assert reordered_uids == ["t3", "t1", "t2"]

    # Clean up
    del hass.data[f"{DOMAIN}_adapters"][entity_id]


async def test_reorder_external_tasks_adapter_declines_falls_back_to_overlay(
    hass: HomeAssistant,
    hass_ws_client,
    external_entry: MockConfigEntry,
) -> None:
    """When adapter returns False, overlay fallback keeps the correct order on get.

    This tests the defensive path: even when the adapter declines to reorder,
    the overlay stores the user's intended order, and get_external_tasks
    returns it correctly.
    """
    from custom_components.home_tasks.provider_adapters import GenericAdapter

    entity_id = "todo.e2e_external"

    # Set up a mock todo entity with 3 tasks BEFORE registering the adapter,
    # since get_external_tasks uses the generic path (reads from hass.data["todo"]).
    mock_entity = MagicMock()
    mock_entity.todo_items = [
        MagicMock(uid="t1", summary="Alpha",
                  status=MagicMock(value="needs_action"), due=None, description=None),
        MagicMock(uid="t2", summary="Beta",
                  status=MagicMock(value="needs_action"), due=None, description=None),
        MagicMock(uid="t3", summary="Gamma",
                  status=MagicMock(value="needs_action"), due=None, description=None),
    ]
    # Hybrid mock: get_entity() is sync; async_* methods are awaitable for HA teardown
    mock_comp = MagicMock()
    mock_comp.get_entity.return_value = mock_entity
    mock_comp.async_unload_entry = AsyncMock(return_value=True)
    mock_comp.async_setup_entry = AsyncMock(return_value=True)
    hass.data["todo"] = mock_comp
    hass.states.async_set(entity_id, "0", {"supported_features": 0})

    # Use a GenericAdapter subclass that declines reorder — this keeps the
    # generic read path (get_external_tasks uses GenericAdapter → overlay path).
    class _DeclineAdapter(GenericAdapter):
        async def async_reorder_tasks(self, task_uids):
            return False

    hass.data.setdefault(f"{DOMAIN}_adapters", {})[entity_id] = _DeclineAdapter(
        hass, entity_id, {"provider_type": "generic"}
    )

    ws = await _ws(hass, hass_ws_client)
    result = await _cmd(ws, 1, "home_tasks/reorder_external_tasks",
                        entity_id=entity_id, task_uids=["t3", "t1", "t2"])
    assert result.get("provider_handled") is False  # fell back to overlay

    # get_external_tasks must still return the intended order (from overlay)
    ws2 = await _ws(hass, hass_ws_client)
    result = await _cmd(ws2, 2, "home_tasks/get_external_tasks", entity_id=entity_id)
    titles = [t["title"] for t in sorted(result["tasks"], key=lambda t: t["sort_order"])]
    assert titles == ["Gamma", "Alpha", "Beta"]

    # Clean up
    del hass.data[f"{DOMAIN}_adapters"][entity_id]


# ---------------------------------------------------------------------------
# Sub-task flows
# ---------------------------------------------------------------------------


async def test_sub_task_crud_flow(
    hass: HomeAssistant,
    hass_ws_client,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Full sub-task create → reorder → delete cycle."""
    ws = await _ws(hass, hass_ws_client)
    result = await _cmd(ws, 1, "home_tasks/get_lists")
    list_id = result["lists"][0]["id"]

    # add_task returns the task dict directly
    task = await _cmd(ws, 2, "home_tasks/add_task", list_id=list_id, title="Parent")
    task_id = task["id"]

    # add_sub_task returns the sub dict directly
    s1 = await _cmd(ws, 3, "home_tasks/add_sub_task",
                    list_id=list_id, task_id=task_id, title="Sub A")
    s2 = await _cmd(ws, 4, "home_tasks/add_sub_task",
                    list_id=list_id, task_id=task_id, title="Sub B")

    # Verify both sub-tasks present — native tasks use "sub_items" key
    result = await _cmd(ws, 5, "home_tasks/get_tasks", list_id=list_id)
    parent = next(t for t in result["tasks"] if t["id"] == task_id)
    assert len(parent["sub_items"]) == 2

    # Reorder: B before A
    await _cmd(ws, 6, "home_tasks/reorder_sub_tasks",
               list_id=list_id, task_id=task_id, sub_task_ids=[s2["id"], s1["id"]])

    result = await _cmd(ws, 7, "home_tasks/get_tasks", list_id=list_id)
    parent = next(t for t in result["tasks"] if t["id"] == task_id)
    # sub_items are ordered by list position (no sort_order field on sub-tasks)
    assert parent["sub_items"][0]["title"] == "Sub B"
    assert parent["sub_items"][1]["title"] == "Sub A"

    # Delete sub B
    await _cmd(ws, 8, "home_tasks/delete_sub_task",
               list_id=list_id, task_id=task_id, sub_task_id=s2["id"])

    result = await _cmd(ws, 9, "home_tasks/get_tasks", list_id=list_id)
    parent = next(t for t in result["tasks"] if t["id"] == task_id)
    assert len(parent["sub_items"]) == 1
    assert parent["sub_items"][0]["title"] == "Sub A"
