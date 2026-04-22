"""Live tests for HA's built-in Shopping List provider via the GenericAdapter.

Shopping List (domain: ``shopping_list``) is the most minimal todo provider
HA ships with — strictly *title + status*, no description, no due date,
no subtasks.  That minimalism is exactly what makes it worth testing: any
unsupported field that our GenericAdapter accidentally sends to the provider
will either crash the service call or leak data into a place the user can
see it in HA's own Shopping List UI.

This file mirrors the Bring live-test structure (`test_provider_bring.py`).
Bring is the closest comparison — another minimal shopping-list-shaped
provider — but Bring does support item descriptions, whereas Shopping List
does not.  So this file is stricter than Bring's about overlay-only fields.

Setup:  HT_SHOPPING_LIST_TEST_ENTITY=todo.<shopping_list_entity>
        (HA creates ``todo.shopping_list`` by default when you enable the
        "Shopping List" integration in Settings → Integrations.)
"""
from __future__ import annotations

import asyncio

import pytest

from .config import CONFIG
from .ws_client import HAWebSocketClient

pytestmark = [pytest.mark.live, pytest.mark.live_shopping_list]

SETTLE = 0.4


def _find_provider_item(items: list[dict], uid: str) -> dict | None:
    return next((i for i in items if i.get("uid") == uid), None)


async def _wipe(ws: HAWebSocketClient, entity_id: str) -> None:
    result = await ws.send_command(
        "home_tasks/get_external_tasks", entity_id=entity_id
    )
    tasks = result.get("tasks", [])
    if len(tasks) > CONFIG.max_existing_items:
        raise RuntimeError(
            f"Refusing to wipe {entity_id}: {len(tasks)} > max"
        )
    for t in tasks:
        try:
            await ws.call_service(
                "todo", "remove_item",
                {"item": t["id"]},
                target={"entity_id": entity_id},
            )
        except Exception as err:  # noqa: BLE001
            print(f"[shopping_list cleanup] {err}")
    if tasks:
        await asyncio.sleep(SETTLE)


async def _refetch(ws: HAWebSocketClient, entity_id: str) -> list[dict]:
    result = await ws.send_command(
        "home_tasks/get_external_tasks", entity_id=entity_id
    )
    return result.get("tasks", [])


@pytest.fixture
async def shopping_list(ws_client: HAWebSocketClient):
    entity_id = CONFIG.shopping_list_entity
    assert entity_id, "HT_SHOPPING_LIST_TEST_ENTITY must be set"
    await _wipe(ws_client, entity_id)
    yield entity_id
    try:
        await _wipe(ws_client, entity_id)
    except Exception as err:  # noqa: BLE001
        print(f"[shopping_list teardown] {err}")


# ---------------------------------------------------------------------------
# Basic CRUD — dual-view against todo.get_items
# ---------------------------------------------------------------------------


async def test_create_basic_item(
    ws_client: HAWebSocketClient, shopping_list: str
) -> None:
    """Item created through home_tasks must actually appear in Shopping List."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=shopping_list,
        title="Milk",
    )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, shopping_list)
    task = next((t for t in tasks if t["title"] == "Milk"), None)
    assert task is not None

    items = await ws_client.get_provider_items(shopping_list)
    pi = _find_provider_item(items, task["id"])
    assert pi is not None, "Item not present in Shopping List itself"
    assert pi["summary"] == "Milk"


async def test_complete_via_update(
    ws_client: HAWebSocketClient, shopping_list: str
) -> None:
    """Check-off must reach HA's Shopping List state."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=shopping_list,
        title="Bread",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, shopping_list)
    task = next(t for t in tasks if t["title"] == "Bread")
    uid = task["id"]

    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=shopping_list, task_uid=uid,
        completed=True,
    )
    await asyncio.sleep(SETTLE)

    # Provider-side: item must NOT be in the open list anymore.  Whether
    # HA keeps a completed bucket or just removes it on check-off depends
    # on the integration — both outcomes are fine as long as it's gone
    # from needs_action.
    open_items = await ws_client.get_provider_items(
        shopping_list, status="needs_action",
    )
    assert _find_provider_item(open_items, uid) is None, (
        "Completed Shopping List item is still in the open list — "
        "the check-off never reached the provider."
    )


async def test_delete_removes_item_from_shopping_list(
    ws_client: HAWebSocketClient, shopping_list: str
) -> None:
    """Deleting via the card's path must wipe the item from Shopping List."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=shopping_list,
        title="Eggs",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, shopping_list)
    task = next(t for t in tasks if t["title"] == "Eggs")
    uid = task["id"]

    items = await ws_client.get_provider_items(shopping_list)
    assert _find_provider_item(items, uid) is not None

    # Card's delete path
    await ws_client.call_service(
        "todo", "remove_item",
        {"item": uid},
        target={"entity_id": shopping_list},
    )
    await ws_client.send_command(
        "home_tasks/delete_external_overlay",
        entity_id=shopping_list, task_uid=uid,
    )
    await asyncio.sleep(SETTLE)

    tasks_after = await _refetch(ws_client, shopping_list)
    assert not any(t["id"] == uid for t in tasks_after)

    open_items = await ws_client.get_provider_items(
        shopping_list, status="needs_action",
    )
    completed_items = await ws_client.get_provider_items(
        shopping_list, status="completed",
    )
    assert _find_provider_item(open_items, uid) is None
    assert _find_provider_item(completed_items, uid) is None, (
        "Shopping List still holds the item after deletion"
    )


# ---------------------------------------------------------------------------
# Overlay routing — Shopping List has NO description and NO due_date.
# These fields must stay local and never reach the provider's state.
# ---------------------------------------------------------------------------


async def test_notes_are_overlay_only_and_dont_leak(
    ws_client: HAWebSocketClient, shopping_list: str
) -> None:
    """notes → overlay only.  Shopping List has no description field.

    If our adapter blindly ships `description` to `todo.add_item`, HA's
    service layer rejects it (Shopping List lacks SET_DESCRIPTION_ON_ITEM).
    That would surface here as a failed create.  If the adapter silently
    strips description, the notes must still live in our overlay.
    """
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=shopping_list,
        title="Cheese",
        notes="aged cheddar",
    )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, shopping_list)
    task = next(t for t in tasks if t["title"] == "Cheese")
    assert task["notes"] == "aged cheddar", (
        "notes lost between create and fetch — overlay didn't persist it"
    )

    items = await ws_client.get_provider_items(shopping_list)
    pi = _find_provider_item(items, task["id"])
    assert pi is not None
    assert pi["summary"] == "Cheese"
    desc = pi.get("description") or ""
    assert "cheddar" not in desc and "aged" not in desc, (
        f"Shopping List item description is {desc!r} — notes leaked "
        f"into the provider's state."
    )


async def test_due_date_is_overlay_only_and_dont_leak(
    ws_client: HAWebSocketClient, shopping_list: str
) -> None:
    """due_date → overlay only.  Shopping List has no due_date field."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=shopping_list,
        title="Yogurt",
        due_date="2027-09-15",
    )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, shopping_list)
    task = next(t for t in tasks if t["title"] == "Yogurt")
    assert task["due_date"] == "2027-09-15", (
        "due_date lost between create and fetch — overlay didn't persist it"
    )

    items = await ws_client.get_provider_items(shopping_list)
    pi = _find_provider_item(items, task["id"])
    assert pi is not None
    assert pi["summary"] == "Yogurt"
    assert not pi.get("due"), (
        f"Shopping List item has due={pi.get('due')!r} — due_date leaked "
        f"into the provider's state."
    )
