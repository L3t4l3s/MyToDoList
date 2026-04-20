"""Live tests for the Local Todo provider via the GenericAdapter path.

The Local Todo entity is talked to through HA's standard `todo.*` services.
These tests exercise the GenericAdapter against the real entity, verifying
that create / read / update / delete round-trip correctly.

Set up:  HT_LOCAL_TODO_TEST_ENTITY=todo.<your_test_list>
"""
from __future__ import annotations

import asyncio

import pytest

from .config import CONFIG
from .ws_client import HAWebSocketClient

pytestmark = [pytest.mark.live, pytest.mark.live_local_todo]


async def _list_items(ws: HAWebSocketClient, entity_id: str) -> list[dict]:
    """Read all todo items via HA's todo.get_items service."""
    result = await ws.call_service(
        "todo", "get_items",
        {"entity_id": entity_id},
        return_response=True,
    )
    response = (result or {}).get("response", {}).get(entity_id, {})
    return response.get("items", [])


async def _wipe(ws: HAWebSocketClient, entity_id: str) -> None:
    items = await _list_items(ws, entity_id)
    if len(items) > CONFIG.max_existing_items:
        raise RuntimeError(
            f"Refusing to wipe {entity_id}: {len(items)} items > "
            f"max_existing_items={CONFIG.max_existing_items}"
        )
    for it in items:
        await ws.call_service(
            "todo", "remove_item",
            {"entity_id": entity_id, "item": it["uid"]},
        )


@pytest.fixture
async def local_todo_entity(ws_client: HAWebSocketClient) -> str:
    entity_id = CONFIG.local_todo_entity
    assert entity_id, "HT_LOCAL_TODO_TEST_ENTITY must be set"
    await _wipe(ws_client, entity_id)
    return entity_id


# ---------------------------------------------------------------------------
# Direct todo.* service round-trips (these test the contract the
# GenericAdapter relies on — if these fail, the adapter is broken too).
# ---------------------------------------------------------------------------


async def test_add_and_list_item(
    ws_client: HAWebSocketClient, local_todo_entity: str
) -> None:
    """add_item creates an item that appears in get_items."""
    await ws_client.call_service(
        "todo", "add_item",
        {"entity_id": local_todo_entity, "item": "Local round-trip 1"},
    )
    items = await _list_items(ws_client, local_todo_entity)
    assert any(i["summary"] == "Local round-trip 1" for i in items)


async def test_update_item_title(
    ws_client: HAWebSocketClient, local_todo_entity: str
) -> None:
    """update_item with rename changes the summary."""
    await ws_client.call_service(
        "todo", "add_item",
        {"entity_id": local_todo_entity, "item": "Original title"},
    )
    items = await _list_items(ws_client, local_todo_entity)
    item = next(i for i in items if i["summary"] == "Original title")

    await ws_client.call_service(
        "todo", "update_item",
        {"entity_id": local_todo_entity, "item": item["uid"], "rename": "Renamed"},
    )
    items = await _list_items(ws_client, local_todo_entity)
    assert any(i["summary"] == "Renamed" for i in items)
    assert not any(i["summary"] == "Original title" for i in items)


async def test_complete_item(
    ws_client: HAWebSocketClient, local_todo_entity: str
) -> None:
    """update_item with status=completed marks the item done."""
    await ws_client.call_service(
        "todo", "add_item",
        {"entity_id": local_todo_entity, "item": "To complete"},
    )
    items = await _list_items(ws_client, local_todo_entity)
    item = next(i for i in items if i["summary"] == "To complete")

    await ws_client.call_service(
        "todo", "update_item",
        {"entity_id": local_todo_entity, "item": item["uid"], "status": "completed"},
    )
    items = await _list_items(ws_client, local_todo_entity)
    item = next(i for i in items if i["summary"] == "To complete")
    assert item["status"] == "completed"


async def test_remove_item(
    ws_client: HAWebSocketClient, local_todo_entity: str
) -> None:
    """remove_item deletes the item."""
    await ws_client.call_service(
        "todo", "add_item",
        {"entity_id": local_todo_entity, "item": "To remove"},
    )
    items = await _list_items(ws_client, local_todo_entity)
    item = next(i for i in items if i["summary"] == "To remove")

    await ws_client.call_service(
        "todo", "remove_item",
        {"entity_id": local_todo_entity, "item": item["uid"]},
    )
    items = await _list_items(ws_client, local_todo_entity)
    assert not any(i["uid"] == item["uid"] for i in items)


async def test_due_date_round_trip(
    ws_client: HAWebSocketClient, local_todo_entity: str
) -> None:
    """add_item with due_date is stored and returned."""
    await ws_client.call_service(
        "todo", "add_item",
        {
            "entity_id": local_todo_entity,
            "item": "With due date",
            "due_date": "2027-05-15",
        },
    )
    items = await _list_items(ws_client, local_todo_entity)
    item = next(i for i in items if i["summary"] == "With due date")
    assert item.get("due") == "2027-05-15"


async def test_description_round_trip(
    ws_client: HAWebSocketClient, local_todo_entity: str
) -> None:
    """add_item with description (notes) is stored and returned."""
    await ws_client.call_service(
        "todo", "add_item",
        {
            "entity_id": local_todo_entity,
            "item": "With notes",
            "description": "These are some notes",
        },
    )
    items = await _list_items(ws_client, local_todo_entity)
    item = next(i for i in items if i["summary"] == "With notes")
    assert item.get("description") == "These are some notes"


async def test_clear_due_date(
    ws_client: HAWebSocketClient, local_todo_entity: str
) -> None:
    """update_item can clear the due_date by setting it to None."""
    await ws_client.call_service(
        "todo", "add_item",
        {
            "entity_id": local_todo_entity,
            "item": "Clearable due",
            "due_date": "2027-06-01",
        },
    )
    items = await _list_items(ws_client, local_todo_entity)
    item = next(i for i in items if i["summary"] == "Clearable due")
    assert item.get("due") == "2027-06-01"

    await ws_client.call_service(
        "todo", "update_item",
        {
            "entity_id": local_todo_entity,
            "item": item["uid"],
            "due_date": None,
        },
    )
    items = await _list_items(ws_client, local_todo_entity)
    item = next(i for i in items if i["summary"] == "Clearable due")
    assert item.get("due") is None


# NOTE: no reorder-via-home_tasks test here.  In the live test setup
# `todo.ht_test_local` is configured as a NATIVE home_tasks list (it
# exposes sensor.*, binary_sensor.* and calendar.* siblings created by
# home_tasks itself), not as an externally linked list.  Reordering
# through the home_tasks/reorder_external_tasks path therefore errors
# with "No overlay store found".
#
# The GenericAdapter + MOVE_TODO_ITEM code path it would exercise is
# already covered by the Google Tasks reorder test.  If we ever want
# a second confirmation of that path we'd need a dedicated Local-Todo
# entity linked as an external list in home_tasks.
