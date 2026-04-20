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


async def test_reorder_external_tasks_generic_adapter_move_flow(
    hass: HomeAssistant,
    hass_ws_client,
    external_entry: MockConfigEntry,
) -> None:
    """GenericAdapter.async_reorder_tasks calls todo.move_item and get returns new order.

    This tests the MOVE_TODO_ITEM path (e.g. Google Tasks):
    1. GenericAdapter sees supported_features & 8 → calls todo.move_item per task
    2. The mock simulates HA updating entity.todo_items after each move
    3. get_external_tasks must reflect the new provider order

    Previously broken because:
    - Service name was "item/move" (not "move_item") → ServiceNotFound raised
    - Fallback wrote to overlay, but provider_owns_order=True ignored overlay
    """
    from custom_components.home_tasks.provider_adapters import GenericAdapter

    entity_id = "todo.e2e_external"
    items = [
        MagicMock(uid="t1", summary="Alpha",
                  status=MagicMock(value="needs_action"), due=None, description=None),
        MagicMock(uid="t2", summary="Beta",
                  status=MagicMock(value="needs_action"), due=None, description=None),
        MagicMock(uid="t3", summary="Gamma",
                  status=MagicMock(value="needs_action"), due=None, description=None),
    ]
    mock_entity = MagicMock()
    mock_entity.todo_items = list(items)

    mock_comp = MagicMock()
    mock_comp.get_entity.return_value = mock_entity
    mock_comp.async_unload_entry = AsyncMock(return_value=True)
    mock_comp.async_setup_entry = AsyncMock(return_value=True)
    hass.data["todo"] = mock_comp
    # supported_features=8 → MOVE_TODO_ITEM → GenericAdapter will call todo.move_item
    hass.states.async_set(entity_id, "0", {"supported_features": 8})

    uid_to_item = {m.uid: m for m in items}

    # Register a real todo.move_item service handler that simulates what HA's
    # Google Tasks integration does: reorder entity.todo_items after each move.
    # (hass.services.async_call is read-only and cannot be patched directly.)
    from homeassistant.core import ServiceCall

    async def handle_move_item(call: ServiceCall) -> None:
        uid = call.data["uid"]
        prev_uid = call.data.get("previous_uid")
        current = list(mock_entity.todo_items)
        moved = uid_to_item[uid]
        current = [t for t in current if t.uid != uid]
        if prev_uid is None:
            current.insert(0, moved)
        else:
            idx = next(i for i, t in enumerate(current) if t.uid == prev_uid)
            current.insert(idx + 1, moved)
        mock_entity.todo_items = current

    hass.services.async_register("todo", "move_item", handle_move_item)

    ws = await _ws(hass, hass_ws_client)

    result = await _cmd(ws, 1, "home_tasks/reorder_external_tasks",
                        entity_id=entity_id, task_uids=["t3", "t1", "t2"])
    assert result.get("provider_handled") is True

    # get_external_tasks must reflect the new order from entity.todo_items
    ws2 = await _ws(hass, hass_ws_client)
    result = await _cmd(ws2, 2, "home_tasks/get_external_tasks", entity_id=entity_id)
    titles = [t["title"] for t in sorted(result["tasks"], key=lambda t: t["sort_order"])]
    assert titles == ["Gamma", "Alpha", "Beta"]


async def test_reorder_external_tasks_move_fails_overlay_wins_flow(
    hass: HomeAssistant,
    hass_ws_client,
    external_entry: MockConfigEntry,
) -> None:
    """MOVE_TODO_ITEM supported but todo.move_item fails → overlay order persists on get.

    This is the direct E2E regression test for the original Google Tasks bug:
      1. supported_features=8  (MOVE_TODO_ITEM set)  → provider_owns_order=True
      2. todo.move_item service not available → GenericAdapter returns False
      3. ws_reorder_external_tasks writes sort_order to overlay (fallback)
      4. ws_get_external_tasks with features & 8 = True must STILL use overlay

    With the old broken code (provider_owns_order=True always used idx) this
    test would FAIL — the returned order would be the original provider order.

    Note: the existing overlay_fallback and adapter_declines tests both use
    supported_features=0, so provider_owns_order=False — they would have passed
    even with the old broken code and don't catch this specific regression.
    """
    from custom_components.home_tasks.provider_adapters import GenericAdapter

    entity_id = "todo.e2e_external"

    mock_entity = MagicMock()
    mock_entity.todo_items = [
        MagicMock(uid="t1", summary="Alpha",
                  status=MagicMock(value="needs_action"), due=None, description=None),
        MagicMock(uid="t2", summary="Beta",
                  status=MagicMock(value="needs_action"), due=None, description=None),
        MagicMock(uid="t3", summary="Gamma",
                  status=MagicMock(value="needs_action"), due=None, description=None),
    ]
    mock_comp = MagicMock()
    mock_comp.get_entity.return_value = mock_entity
    mock_comp.async_unload_entry = AsyncMock(return_value=True)
    mock_comp.async_setup_entry = AsyncMock(return_value=True)
    hass.data["todo"] = mock_comp
    # supported_features=8: GenericAdapter tries todo.move_item, but no handler
    # is registered → ServiceNotFound → returns False → overlay fallback
    hass.states.async_set(entity_id, "0", {"supported_features": 8})

    ws = await _ws(hass, hass_ws_client)

    result = await _cmd(ws, 1, "home_tasks/reorder_external_tasks",
                        entity_id=entity_id, task_uids=["t3", "t1", "t2"])
    assert result.get("provider_handled") is False  # move failed → overlay used

    # Despite features & 8 = True (provider_owns_order), overlay must win
    ws2 = await _ws(hass, hass_ws_client)
    result = await _cmd(ws2, 2, "home_tasks/get_external_tasks", entity_id=entity_id)
    titles = [t["title"] for t in sorted(result["tasks"], key=lambda t: t["sort_order"])]
    assert titles == ["Gamma", "Alpha", "Beta"]


async def test_reorder_external_tasks_adapter_declines_falls_back_to_overlay(
    hass: HomeAssistant,
    hass_ws_client,
    external_entry: MockConfigEntry,
) -> None:
    """When a registered adapter explicitly returns False, overlay keeps the order.

    Complementary to test_reorder_external_tasks_move_fails_overlay_wins_flow:
    here the adapter is a GenericAdapter subclass that declines rather than a
    missing service.  supported_features=0 so this doesn't exercise the
    provider_owns_order=True path — that's covered by the _move_fails_ test above.
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
# Rich adapter (Todoist-style) reorder flow
# ---------------------------------------------------------------------------


async def test_reorder_external_tasks_rich_adapter_flow(
    hass: HomeAssistant,
    hass_ws_client,
    external_entry: MockConfigEntry,
) -> None:
    """Reorder via a rich adapter (can_sync_order=True) persists through get.

    Rich adapters (e.g. Todoist) go through a completely different code path
    than GenericAdapter:
      - get_external_tasks calls adapter.async_read_tasks() and passes the
        result to _merge_tasks_with_adapter_data(can_sync_order=True)
      - sort_order comes from item["order"], not from overlay sort_order

    This tests that after reorder_external_tasks the adapter's updated order
    is reflected by get_external_tasks — catching any bug in the rich-adapter
    merge path independent of the GenericAdapter/overlay path.
    """
    from custom_components.home_tasks.provider_adapters import ProviderAdapter

    entity_id = "todo.e2e_external"

    # A rich adapter that owns its task list and updates it on reorder.
    # Subclasses ProviderAdapter (not GenericAdapter) so ws_get_external_tasks
    # takes the rich-adapter branch.
    class _RichAdapter(ProviderAdapter):
        provider_type = "rich_mock"

        def __init__(self):
            # Skip ProviderAdapter.__init__ (needs hass / entity_id / config)
            self._tasks = [
                {"uid": "t1", "summary": "Alpha", "order": 0,
                 "status": "needs_action", "due": None, "due_time": None,
                 "description": None, "priority": None, "labels": [],
                 "sub_items": [], "reminders": []},
                {"uid": "t2", "summary": "Beta",  "order": 1,
                 "status": "needs_action", "due": None, "due_time": None,
                 "description": None, "priority": None, "labels": [],
                 "sub_items": [], "reminders": []},
                {"uid": "t3", "summary": "Gamma", "order": 2,
                 "status": "needs_action", "due": None, "due_time": None,
                 "description": None, "priority": None, "labels": [],
                 "sub_items": [], "reminders": []},
            ]

        class capabilities:
            can_sync_order = True

        async def async_read_tasks(self):
            return list(self._tasks)

        async def async_create_task(self, title, fields=None):
            return None

        async def async_update_task(self, task_uid, fields):
            return {}

        async def async_delete_task(self, task_uid):
            pass

        async def async_reorder_tasks(self, task_uids):
            # Simulate provider updating its order (like Todoist sets child_order)
            uid_to_task = {t["uid"]: t for t in self._tasks}
            for new_order, uid in enumerate(task_uids):
                if uid in uid_to_task:
                    uid_to_task[uid]["order"] = new_order
            self._tasks = [uid_to_task[uid] for uid in task_uids if uid in uid_to_task]
            return True

    adapter = _RichAdapter()
    hass.data.setdefault(f"{DOMAIN}_adapters", {})[entity_id] = adapter
    hass.states.async_set(entity_id, "0", {"supported_features": 0})

    ws = await _ws(hass, hass_ws_client)

    # Initial order: Alpha(0), Beta(1), Gamma(2)
    result = await _cmd(ws, 1, "home_tasks/get_external_tasks", entity_id=entity_id)
    titles_before = [t["title"] for t in sorted(result["tasks"], key=lambda t: t["sort_order"])]
    assert titles_before == ["Alpha", "Beta", "Gamma"]

    # Reorder: Gamma, Alpha, Beta — rich adapter accepts and updates its state
    result = await _cmd(ws, 2, "home_tasks/reorder_external_tasks",
                        entity_id=entity_id, task_uids=["t3", "t1", "t2"])
    assert result.get("provider_handled") is True

    # get_external_tasks must reflect the new order from adapter.async_read_tasks()
    result = await _cmd(ws, 3, "home_tasks/get_external_tasks", entity_id=entity_id)
    titles_after = [t["title"] for t in sorted(result["tasks"], key=lambda t: t["sort_order"])]
    assert titles_after == ["Gamma", "Alpha", "Beta"]

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


# ---------------------------------------------------------------------------
# External task CRUD + overlay field flows
# ---------------------------------------------------------------------------


def _setup_mock_external_entity(hass, entity_id: str, supported_features: int = 0):
    """Register a writable mock todo entity for external task tests.

    Returns (mock_entity, uid_store) where uid_store is a list that
    capture_create_uid() appends to when create_external_task is called.
    """
    mock_entity = MagicMock()
    mock_entity.todo_items = []

    mock_comp = MagicMock()
    mock_comp.get_entity.return_value = mock_entity
    mock_comp.async_unload_entry = AsyncMock(return_value=True)
    mock_comp.async_setup_entry = AsyncMock(return_value=True)
    hass.data["todo"] = mock_comp
    hass.states.async_set(entity_id, "0", {"supported_features": supported_features})
    return mock_entity


async def test_create_external_task_appears_in_get_flow(
    hass: HomeAssistant,
    hass_ws_client,
    external_entry: MockConfigEntry,
) -> None:
    """create_external_task → get_external_tasks returns the new task.

    Catches bugs in the create→get round-trip: wrong field mapping, missing
    UID propagation, or _merge_tasks_with_overlays discarding new tasks.
    """
    entity_id = "todo.e2e_external"
    mock_entity = _setup_mock_external_entity(hass, entity_id)

    # Simulate HA adding the item to the entity when todo.add_item is called
    from homeassistant.core import ServiceCall

    async def handle_add_item(call: ServiceCall) -> None:
        mock_entity.todo_items = [
            MagicMock(uid="new-uid-1", summary=call.data["item"],
                      status=MagicMock(value="needs_action"), due=None, description=None),
        ]

    hass.services.async_register("todo", "add_item", handle_add_item)

    ws = await _ws(hass, hass_ws_client)
    result = await _cmd(ws, 1, "home_tasks/create_external_task",
                        entity_id=entity_id, title="External smoke")
    # create_external_task returns {"uid": ...} or {}; UID may be None for generic
    # The important thing is it doesn't error

    # After create, entity has the new item — get must return it
    result = await _cmd(ws, 2, "home_tasks/get_external_tasks", entity_id=entity_id)
    assert any(t["title"] == "External smoke" for t in result["tasks"])


async def test_external_overlay_fields_persist_through_get_flow(
    hass: HomeAssistant,
    hass_ws_client,
    external_entry: MockConfigEntry,
) -> None:
    """update_external_task with overlay fields → get_external_tasks returns them.

    Overlay fields (priority, tags, due_time) are not synced to the provider —
    they live only in the overlay store.  This test verifies that
    _merge_tasks_with_overlays correctly injects them into the get response.

    Catches bugs where the overlay merge silently drops fields, or where
    a code change to _merge_tasks_with_overlays breaks field propagation
    while all reorder tests remain green (since they don't check these fields).
    """
    entity_id = "todo.e2e_external"
    mock_entity = _setup_mock_external_entity(hass, entity_id)
    mock_entity.todo_items = [
        MagicMock(uid="overlay-task", summary="Overlay Test",
                  status=MagicMock(value="needs_action"), due=None, description=None),
    ]

    ws = await _ws(hass, hass_ws_client)

    # Verify task is present before overlay
    result = await _cmd(ws, 1, "home_tasks/get_external_tasks", entity_id=entity_id)
    task = next(t for t in result["tasks"] if t["id"] == "overlay-task")
    assert task["priority"] is None
    assert task["tags"] == []

    # Set overlay fields via update_external_task
    await _cmd(ws, 2, "home_tasks/update_external_task",
               entity_id=entity_id, task_uid="overlay-task",
               priority=1, tags=["urgent", "e2e"])

    # get must return the overlay fields merged into the task
    result = await _cmd(ws, 3, "home_tasks/get_external_tasks", entity_id=entity_id)
    task = next(t for t in result["tasks"] if t["id"] == "overlay-task")
    assert task["priority"] == 1
    assert sorted(task["tags"]) == ["e2e", "urgent"]

    # Update again: change priority, add a tag → previous values replaced
    await _cmd(ws, 4, "home_tasks/update_external_task",
               entity_id=entity_id, task_uid="overlay-task",
               priority=3, tags=["urgent", "e2e", "new-tag"])

    result = await _cmd(ws, 5, "home_tasks/get_external_tasks", entity_id=entity_id)
    task = next(t for t in result["tasks"] if t["id"] == "overlay-task")
    assert task["priority"] == 3
    assert sorted(task["tags"]) == ["e2e", "new-tag", "urgent"]
