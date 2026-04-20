"""End-to-end flow tests for the Home Tasks WebSocket API.

Scope: native home_tasks lists only.  Every command sequence here exercises
the real store + websocket_api code against pytest-hacc's in-memory HA,
using only fixtures and mocks provided by HA's own test infrastructure
(``hass``, ``hass_ws_client``, ``MockConfigEntry``).  No hand-crafted
mocks of ``hass.data["todo"]`` or self-registered fake services.

External-list (provider) flows were previously tested in this file via
hand-built MagicMock entities and self-registered "todo.move_item"-style
services.  Those tests proved tautological — they asserted that our code
called the names our code used, without ever verifying HA itself offered
those names.  Exactly the pattern that let the Google Tasks reorder bug
ship silently.  External-list verification now lives in ``tests/live/``,
where reorder/create/update is exercised against real providers (Google
Tasks, Todoist, ...) with a dual-view assertion that queries
``todo.get_items`` directly to confirm the provider actually received
the change.

Run:  pytest tests/e2e/ -v
"""
from __future__ import annotations

import pytest
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

    result = await _cmd(ws, 1, "home_tasks/get_lists")
    list_id = result["lists"][0]["id"]

    task = await _cmd(ws, 2, "home_tasks/add_task", list_id=list_id, title="Flow task")
    task_id = task["id"]
    assert task["title"] == "Flow task"

    updated_task = await _cmd(ws, 3, "home_tasks/update_task",
                              list_id=list_id, task_id=task_id, priority=2)
    assert updated_task["priority"] == 2

    result = await _cmd(ws, 4, "home_tasks/get_tasks", list_id=list_id)
    assert any(t["id"] == task_id for t in result["tasks"])

    await _cmd(ws, 5, "home_tasks/update_task",
               list_id=list_id, task_id=task_id,
               title="Renamed", notes="some note")

    result = await _cmd(ws, 6, "home_tasks/get_tasks", list_id=list_id)
    found = next(t for t in result["tasks"] if t["id"] == task_id)
    assert found["title"] == "Renamed"
    assert found["notes"] == "some note"

    await _cmd(ws, 7, "home_tasks/delete_task", list_id=list_id, task_id=task_id)

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

    t1 = await _cmd(ws, 2, "home_tasks/add_task", list_id=list_id, title="Alpha")
    t2 = await _cmd(ws, 3, "home_tasks/add_task", list_id=list_id, title="Beta")
    t3 = await _cmd(ws, 4, "home_tasks/add_task", list_id=list_id, title="Gamma")
    id1, id2, id3 = t1["id"], t2["id"], t3["id"]

    await _cmd(ws, 5, "home_tasks/reorder_tasks",
               list_id=list_id, task_ids=[id3, id2, id1])

    result = await _cmd(ws, 6, "home_tasks/get_tasks", list_id=list_id)
    ordered = sorted(result["tasks"], key=lambda t: t["sort_order"])
    titles = [t["title"] for t in ordered]
    assert titles == ["Gamma", "Beta", "Alpha"]


async def test_sub_task_crud_flow(
    hass: HomeAssistant,
    hass_ws_client,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Full sub-task create → reorder → delete cycle."""
    ws = await _ws(hass, hass_ws_client)
    result = await _cmd(ws, 1, "home_tasks/get_lists")
    list_id = result["lists"][0]["id"]

    task = await _cmd(ws, 2, "home_tasks/add_task", list_id=list_id, title="Parent")
    task_id = task["id"]

    s1 = await _cmd(ws, 3, "home_tasks/add_sub_task",
                    list_id=list_id, task_id=task_id, title="Sub A")
    s2 = await _cmd(ws, 4, "home_tasks/add_sub_task",
                    list_id=list_id, task_id=task_id, title="Sub B")

    result = await _cmd(ws, 5, "home_tasks/get_tasks", list_id=list_id)
    parent = next(t for t in result["tasks"] if t["id"] == task_id)
    assert len(parent["sub_items"]) == 2

    await _cmd(ws, 6, "home_tasks/reorder_sub_tasks",
               list_id=list_id, task_id=task_id, sub_task_ids=[s2["id"], s1["id"]])

    result = await _cmd(ws, 7, "home_tasks/get_tasks", list_id=list_id)
    parent = next(t for t in result["tasks"] if t["id"] == task_id)
    assert parent["sub_items"][0]["title"] == "Sub B"
    assert parent["sub_items"][1]["title"] == "Sub A"

    await _cmd(ws, 8, "home_tasks/delete_sub_task",
               list_id=list_id, task_id=task_id, sub_task_id=s2["id"])

    result = await _cmd(ws, 9, "home_tasks/get_tasks", list_id=list_id)
    parent = next(t for t in result["tasks"] if t["id"] == task_id)
    assert len(parent["sub_items"]) == 1
    assert parent["sub_items"][0]["title"] == "Sub A"
