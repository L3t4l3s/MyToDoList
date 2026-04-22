"""Live tests for the Bring (shopping list) provider via the GenericAdapter.

Bring is a shopping-list app with a much smaller field surface than other
providers — basically just title (item name).  Everything else goes through
our overlay, and those overlay fields must NEVER leak into Bring's state
(e.g. someone shoving "priority=3" into the item description would corrupt
the user's shopping list in the Bring app).

Setup:  HT_BRING_TEST_ENTITY=todo.<your_test_list>
"""
from __future__ import annotations

import asyncio

import pytest

from .config import CONFIG
from .ws_client import HAWebSocketClient

pytestmark = [pytest.mark.live, pytest.mark.live_bring]

SETTLE = 0.8  # Bring is slow to sync


async def _wipe(ws: HAWebSocketClient, entity_id: str) -> None:
    result = await ws.send_command(
        "home_tasks/get_external_tasks", entity_id=entity_id
    )
    tasks = result.get("tasks", [])
    if len(tasks) > CONFIG.max_existing_items:
        raise RuntimeError(f"Refusing to wipe {entity_id}: {len(tasks)} > max")
    for t in tasks:
        try:
            await ws.call_service(
                "todo", "remove_item",
                {"entity_id": entity_id, "item": t["id"]},
            )
        except Exception as err:  # noqa: BLE001
            print(f"[bring cleanup] failed to remove {t.get('id')}: {err}")
    if tasks:
        await asyncio.sleep(SETTLE)


async def _refetch(ws: HAWebSocketClient, entity_id: str) -> list[dict]:
    result = await ws.send_command(
        "home_tasks/get_external_tasks", entity_id=entity_id
    )
    return result.get("tasks", [])


def _find_provider_item(items: list[dict], uid: str) -> dict | None:
    return next((i for i in items if i.get("uid") == uid), None)


@pytest.fixture
async def bring_entity(ws_client: HAWebSocketClient) -> str:
    entity_id = CONFIG.bring_entity
    assert entity_id
    await _wipe(ws_client, entity_id)
    return entity_id


# ---------------------------------------------------------------------------
# Basic CRUD — dual-view against todo.get_items
# ---------------------------------------------------------------------------


async def test_create_basic_item(
    ws_client: HAWebSocketClient, bring_entity: str
) -> None:
    """Item created through home_tasks must actually appear in Bring."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=bring_entity,
        title="Bananen",
    )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, bring_entity)
    task = next((t for t in tasks if t["title"] == "Bananen"), None)
    assert task is not None

    items = await ws_client.get_provider_items(bring_entity)
    pi = _find_provider_item(items, task["id"])
    assert pi is not None, "Item not present in Bring itself"
    assert pi["summary"] == "Bananen"


async def test_complete_via_update(
    ws_client: HAWebSocketClient, bring_entity: str
) -> None:
    """Marking a Bring item completed must reach Bring's own list."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=bring_entity,
        title="Milch",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, bring_entity)
    task = next(t for t in tasks if t["title"] == "Milch")
    uid = task["id"]

    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=bring_entity, task_uid=uid,
        completed=True,
    )
    await asyncio.sleep(SETTLE)

    # Provider-side: item must NOT be in the open list anymore.  Whether
    # Bring keeps it in a "completed" bucket or just removes it depends on
    # the HA integration — both outcomes are fine as long as it's gone
    # from needs_action.
    open_items = await ws_client.get_provider_items(
        bring_entity, status="needs_action",
    )
    assert _find_provider_item(open_items, uid) is None, (
        "Completed Bring item is still in the open list — "
        "the check-off never reached Bring."
    )


# ---------------------------------------------------------------------------
# Overlay routing — these fields are ours only, must NOT leak into Bring
# ---------------------------------------------------------------------------


async def test_reopen_from_completed_restores_on_bring(
    ws_client: HAWebSocketClient, bring_entity: str
) -> None:
    """Uncompleting a "bought" Bring item must restore it on the shopping list."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=bring_entity,
        title="Salat",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, bring_entity)
    task = next(t for t in tasks if t["title"] == "Salat")
    uid = task["id"]

    # Complete (mark as bought)
    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=bring_entity, task_uid=uid, completed=True,
    )
    await asyncio.sleep(SETTLE)

    open_items = await ws_client.get_provider_items(
        bring_entity, status="needs_action",
    )
    assert _find_provider_item(open_items, uid) is None, (
        "Item still in Bring's open list after being marked completed"
    )

    # Reopen (put back on the shopping list)
    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=bring_entity, task_uid=uid, completed=False,
    )
    await asyncio.sleep(SETTLE)

    tasks_after = await _refetch(ws_client, bring_entity)
    task_after = next((t for t in tasks_after if t["id"] == uid), None)
    assert task_after is not None and task_after["completed"] is False

    open_after = await ws_client.get_provider_items(
        bring_entity, status="needs_action",
    )
    assert _find_provider_item(open_after, uid) is not None, (
        "Bring did not put the item back on the shopping list after reopen"
    )


async def test_delete_removes_item_from_bring(
    ws_client: HAWebSocketClient, bring_entity: str
) -> None:
    """Deleting a shopping item must remove it at Bring itself."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=bring_entity,
        title="Joghurt",
    )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, bring_entity)
    task = next(t for t in tasks if t["title"] == "Joghurt")
    uid = task["id"]

    items = await ws_client.get_provider_items(bring_entity)
    assert _find_provider_item(items, uid) is not None

    # Card's delete path
    await ws_client.call_service(
        "todo", "remove_item",
        {"item": uid},
        target={"entity_id": bring_entity},
    )
    await ws_client.send_command(
        "home_tasks/delete_external_overlay",
        entity_id=bring_entity, task_uid=uid,
    )
    await asyncio.sleep(SETTLE)

    tasks_after = await _refetch(ws_client, bring_entity)
    assert not any(t["id"] == uid for t in tasks_after)

    # Provider-side: gone from both open and completed
    open_items = await ws_client.get_provider_items(
        bring_entity, status="needs_action",
    )
    completed_items = await ws_client.get_provider_items(
        bring_entity, status="completed",
    )
    assert _find_provider_item(open_items, uid) is None
    assert _find_provider_item(completed_items, uid) is None, (
        "Bring still holds the item after deletion"
    )


async def test_priority_persists_via_overlay_and_not_on_provider(
    ws_client: HAWebSocketClient, bring_entity: str
) -> None:
    """priority is overlay-only; Bring's item data must stay clean."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=bring_entity,
        title="Eier",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, bring_entity)
    task = next(t for t in tasks if t["title"] == "Eier")
    uid = task["id"]

    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=bring_entity, task_uid=uid,
        priority=3,
    )
    await asyncio.sleep(SETTLE)

    # Overlay keeps it
    tasks = await _refetch(ws_client, bring_entity)
    task = next(t for t in tasks if t["title"] == "Eier")
    assert task["priority"] == 3

    # Bring side: summary unchanged, no priority value in the description
    items = await ws_client.get_provider_items(bring_entity)
    pi = _find_provider_item(items, uid)
    assert pi is not None
    assert pi["summary"] == "Eier"
    desc = pi.get("description") or ""
    assert "3" not in desc and "priority" not in desc.lower(), (
        f"Description now contains {desc!r} — priority leaked into Bring"
    )


async def test_tags_persist_via_overlay_and_not_on_provider(
    ws_client: HAWebSocketClient, bring_entity: str
) -> None:
    """tags are overlay-only; they must not end up in Bring's item data."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=bring_entity,
        title="Brot",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, bring_entity)
    task = next(t for t in tasks if t["title"] == "Brot")
    uid = task["id"]

    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=bring_entity, task_uid=uid,
        tags=["bio", "wochenmarkt"],
    )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, bring_entity)
    task = next(t for t in tasks if t["title"] == "Brot")
    assert sorted(task["tags"]) == ["bio", "wochenmarkt"]

    items = await ws_client.get_provider_items(bring_entity)
    pi = _find_provider_item(items, uid)
    assert pi is not None
    assert pi["summary"] == "Brot"
    desc = (pi.get("description") or "").lower()
    assert "bio" not in desc and "wochenmarkt" not in desc, (
        f"Description now contains {desc!r} — tags leaked into Bring"
    )


async def test_assigned_person_persists_via_overlay_and_not_on_provider(
    ws_client: HAWebSocketClient, bring_entity: str
) -> None:
    """assigned_person is overlay-only; must not show up in Bring's data."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=bring_entity,
        title="Käse",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, bring_entity)
    task = next(t for t in tasks if t["title"] == "Käse")
    uid = task["id"]

    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=bring_entity, task_uid=uid,
        assigned_person="person.kevin",
    )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, bring_entity)
    task = next(t for t in tasks if t["title"] == "Käse")
    assert task["assigned_person"] == "person.kevin"

    items = await ws_client.get_provider_items(bring_entity)
    pi = _find_provider_item(items, uid)
    assert pi is not None
    assert pi["summary"] == "Käse"
    desc = (pi.get("description") or "").lower()
    assert "kevin" not in desc and "person" not in desc, (
        f"Description now contains {desc!r} — assigned_person leaked into Bring"
    )
