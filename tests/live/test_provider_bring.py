"""Live tests for the Bring (shopping list) provider via the GenericAdapter.

Bring is a shopping-list app with a much smaller field surface than other
providers — basically just title (item name) and category. Most home_tasks
fields go through the overlay.

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


@pytest.fixture
async def bring_entity(ws_client: HAWebSocketClient) -> str:
    entity_id = CONFIG.bring_entity
    assert entity_id
    await _wipe(ws_client, entity_id)
    return entity_id


# ---------------------------------------------------------------------------
# Basic CRUD
# ---------------------------------------------------------------------------


async def test_create_basic_item(
    ws_client: HAWebSocketClient, bring_entity: str
) -> None:
    """create_external_task adds a Bring shopping item."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=bring_entity,
        title="Bananen",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, bring_entity)
    assert any(t["title"] == "Bananen" for t in tasks)


async def test_complete_via_update(
    ws_client: HAWebSocketClient, bring_entity: str
) -> None:
    """Marking a Bring item completed removes it from the active list."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=bring_entity,
        title="Milch",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, bring_entity)
    task = next(t for t in tasks if t["title"] == "Milch")

    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=bring_entity, task_uid=task["id"],
        completed=True,
    )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, bring_entity)
    # Bring may either remove completed items or mark them done
    task = next((t for t in tasks if t["id"] == task["id"]), None)
    assert task is None or task["completed"] is True


# ---------------------------------------------------------------------------
# Overlay routing — Bring supports almost no fields, everything goes here
# ---------------------------------------------------------------------------


async def test_priority_persists_via_overlay(
    ws_client: HAWebSocketClient, bring_entity: str
) -> None:
    """priority is overlay-only for Bring."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=bring_entity,
        title="Eier",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, bring_entity)
    task = next(t for t in tasks if t["title"] == "Eier")

    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=bring_entity, task_uid=task["id"],
        priority=3,
    )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, bring_entity)
    task = next(t for t in tasks if t["title"] == "Eier")
    assert task["priority"] == 3


async def test_tags_persist_via_overlay(
    ws_client: HAWebSocketClient, bring_entity: str
) -> None:
    """tags are overlay-only for Bring."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=bring_entity,
        title="Brot",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, bring_entity)
    task = next(t for t in tasks if t["title"] == "Brot")

    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=bring_entity, task_uid=task["id"],
        tags=["bio", "wochenmarkt"],
    )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, bring_entity)
    task = next(t for t in tasks if t["title"] == "Brot")
    assert sorted(task["tags"]) == ["bio", "wochenmarkt"]


async def test_assigned_person_persists_via_overlay(
    ws_client: HAWebSocketClient, bring_entity: str
) -> None:
    """assigned_person is overlay-only for Bring."""
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=bring_entity,
        title="Käse",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, bring_entity)
    task = next(t for t in tasks if t["title"] == "Käse")

    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=bring_entity, task_uid=task["id"],
        assigned_person="person.kevin",
    )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, bring_entity)
    task = next(t for t in tasks if t["title"] == "Käse")
    assert task["assigned_person"] == "person.kevin"
