"""Live tests for the Local Todo provider via the home_tasks external-list path.

The sibling file test_provider_local_todo.py drives HA's todo.* services
directly — useful as a contract test of HA itself, but it doesn't
exercise our home_tasks/* adapter path.

This file does: a Local Todo entity that's been linked as an *external*
list inside home_tasks is the target, and every test talks to it via
home_tasks/create_external_task + friends, then dual-view verifies via
todo.get_items.  That's the same surface the card uses.

Setup:  HT_LOCAL_TODO_EXTERNAL_TEST_ENTITY=todo.<your_local_todo_entity>
        AND the entity must be registered as an external list in
        home_tasks (Settings → Integrations → Home Tasks → Add list →
        External).
"""
from __future__ import annotations

import asyncio

import pytest

from .config import CONFIG
from .ws_client import HAWebSocketClient

pytestmark = [pytest.mark.live, pytest.mark.live_local_todo_external]

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
            print(f"[local_todo_external cleanup] {err}")
    if tasks:
        await asyncio.sleep(SETTLE)


async def _refetch(ws: HAWebSocketClient, entity_id: str) -> list[dict]:
    result = await ws.send_command(
        "home_tasks/get_external_tasks", entity_id=entity_id
    )
    return result.get("tasks", [])


@pytest.fixture
async def local_todo_external(ws_client: HAWebSocketClient):
    entity_id = CONFIG.local_todo_external_entity
    assert entity_id, "HT_LOCAL_TODO_EXTERNAL_TEST_ENTITY must be set"
    await _wipe(ws_client, entity_id)
    yield entity_id
    try:
        await _wipe(ws_client, entity_id)
    except Exception as err:  # noqa: BLE001
        print(f"[local_todo_external teardown] {err}")


# ---------------------------------------------------------------------------
# CRUD — dual-view against todo.get_items on the HA Local Todo entity
# ---------------------------------------------------------------------------


async def test_create_basic_task(
    ws_client: HAWebSocketClient, local_todo_external: str
) -> None:
    """create_external_task must reach the Local Todo entity itself."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=local_todo_external,
        title="LT smoke",
    )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, local_todo_external)
    task = next((t for t in tasks if t["title"] == "LT smoke"), None)
    assert task is not None

    items = await ws_client.get_provider_items(local_todo_external)
    pi = _find_provider_item(items, task["id"])
    assert pi is not None
    assert pi["summary"] == "LT smoke"


async def test_create_with_notes(
    ws_client: HAWebSocketClient, local_todo_external: str
) -> None:
    """Notes round-trip through the Local Todo VTODO description."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=local_todo_external,
        title="LT with notes",
        notes="A note from home_tasks",
    )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, local_todo_external)
    task = next(t for t in tasks if t["title"] == "LT with notes")
    assert task["notes"] == "A note from home_tasks"

    items = await ws_client.get_provider_items(local_todo_external)
    pi = _find_provider_item(items, task["id"])
    assert pi is not None
    assert pi.get("description") == "A note from home_tasks"


async def test_create_with_due_date(
    ws_client: HAWebSocketClient, local_todo_external: str
) -> None:
    """due_date is stored on the Local Todo entity."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=local_todo_external,
        title="LT due date",
        due_date="2027-09-15",
    )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, local_todo_external)
    task = next(t for t in tasks if t["title"] == "LT due date")
    assert task["due_date"] == "2027-09-15"

    items = await ws_client.get_provider_items(local_todo_external)
    pi = _find_provider_item(items, task["id"])
    assert pi is not None
    assert pi.get("due") == "2027-09-15"


async def test_update_title(
    ws_client: HAWebSocketClient, local_todo_external: str
) -> None:
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=local_todo_external,
        title="LT original",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, local_todo_external)
    task = next(t for t in tasks if t["title"] == "LT original")
    uid = task["id"]

    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=local_todo_external, task_uid=uid,
        title="LT renamed",
    )
    await asyncio.sleep(SETTLE)

    items = await ws_client.get_provider_items(local_todo_external)
    pi = _find_provider_item(items, uid)
    assert pi is not None
    assert pi["summary"] == "LT renamed"


async def test_complete_via_update(
    ws_client: HAWebSocketClient, local_todo_external: str
) -> None:
    """Check-off flips the VTODO status at Local Todo."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=local_todo_external,
        title="LT to complete",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, local_todo_external)
    task = next(t for t in tasks if t["title"] == "LT to complete")
    uid = task["id"]

    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=local_todo_external, task_uid=uid,
        completed=True,
    )
    await asyncio.sleep(SETTLE)

    open_items = await ws_client.get_provider_items(
        local_todo_external, status="needs_action",
    )
    assert _find_provider_item(open_items, uid) is None


# ---------------------------------------------------------------------------
# Reorder — Local Todo has MOVE_TODO_ITEM support (features=127)
# ---------------------------------------------------------------------------


async def test_reorder_pushes_to_local_todo(
    ws_client: HAWebSocketClient, local_todo_external: str
) -> None:
    """Local Todo supports MOVE_TODO_ITEM natively — reorder must reach it.

    Same code path as the Google Tasks reorder test (GenericAdapter +
    TodoListEntity.async_move_todo_item), run against a second provider
    so a regression in either integration surfaces directly.
    """
    titles = ["LTA", "LTB", "LTC"]
    for t in titles:
        await ws_client.send_command(
            "home_tasks/create_external_task",
            entity_id=local_todo_external, title=t,
        )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, local_todo_external)
    uid_by_title = {t["title"]: t["id"] for t in tasks if t["title"] in titles}
    assert len(uid_by_title) == 3
    uids = [uid_by_title[t] for t in titles]

    new_order = [uids[2], uids[0], uids[1]]
    expected = ["LTC", "LTA", "LTB"]

    result = await ws_client.send_command(
        "home_tasks/reorder_external_tasks",
        entity_id=local_todo_external,
        task_uids=new_order,
    )
    assert result["provider_handled"] is True, (
        "Local Todo has MOVE_TODO_ITEM in supported_features; the reorder "
        "must go through entity.async_move_todo_item, not fall back to "
        "the overlay."
    )
    await asyncio.sleep(SETTLE)

    items = await ws_client.get_provider_items(local_todo_external)
    provider_titles = [
        i["summary"] for i in items if i["uid"] in uids
    ]
    assert provider_titles == expected, (
        f"Local Todo provider still reports {provider_titles}, expected "
        f"{expected}.  The reorder landed in overlay but didn't reach "
        f"the Local Todo entity."
    )


# ---------------------------------------------------------------------------
# Delete + reopen via the home_tasks adapter path
# ---------------------------------------------------------------------------


async def test_delete_removes_task_from_local_todo(
    ws_client: HAWebSocketClient, local_todo_external: str
) -> None:
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=local_todo_external,
        title="LT delete me",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, local_todo_external)
    task = next(t for t in tasks if t["title"] == "LT delete me")
    uid = task["id"]

    await ws_client.call_service(
        "todo", "remove_item",
        {"item": uid},
        target={"entity_id": local_todo_external},
    )
    await ws_client.send_command(
        "home_tasks/delete_external_overlay",
        entity_id=local_todo_external, task_uid=uid,
    )
    await asyncio.sleep(SETTLE)

    items = await ws_client.get_provider_items(local_todo_external)
    assert _find_provider_item(items, uid) is None


async def test_reopen_from_completed(
    ws_client: HAWebSocketClient, local_todo_external: str
) -> None:
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=local_todo_external,
        title="LT reopen",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, local_todo_external)
    task = next(t for t in tasks if t["title"] == "LT reopen")
    uid = task["id"]

    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=local_todo_external, task_uid=uid, completed=True,
    )
    await asyncio.sleep(SETTLE)

    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=local_todo_external, task_uid=uid, completed=False,
    )
    await asyncio.sleep(SETTLE)

    open_items = await ws_client.get_provider_items(
        local_todo_external, status="needs_action",
    )
    pi = _find_provider_item(open_items, uid)
    assert pi is not None, "Task wasn't restored to Local Todo's open list"
