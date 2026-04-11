"""Live tests for the Google Tasks provider via the GenericAdapter.

Google Tasks supports a small subset of fields (title, notes, due_date,
completed). Everything else (priority, tags, reminders, sub-tasks beyond
flat list, recurrence) goes through the home_tasks overlay.

Setup:  HT_GOOGLE_TASKS_TEST_ENTITY=todo.<your_test_list>
"""
from __future__ import annotations

import asyncio

import pytest

from .config import CONFIG
from .ws_client import HAWebSocketClient

pytestmark = [pytest.mark.live, pytest.mark.live_google_tasks]

SETTLE = 0.6


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
            print(f"[google_tasks cleanup] failed to remove {t.get('id')}: {err}")
    if tasks:
        await asyncio.sleep(SETTLE)


async def _refetch(ws: HAWebSocketClient, entity_id: str) -> list[dict]:
    result = await ws.send_command(
        "home_tasks/get_external_tasks", entity_id=entity_id
    )
    return result.get("tasks", [])


@pytest.fixture
async def google_entity(ws_client: HAWebSocketClient) -> str:
    entity_id = CONFIG.google_tasks_entity
    assert entity_id
    await _wipe(ws_client, entity_id)
    return entity_id


# ---------------------------------------------------------------------------
# Basic CRUD
# ---------------------------------------------------------------------------


async def test_create_basic_task(
    ws_client: HAWebSocketClient, google_entity: str
) -> None:
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=google_entity,
        title="Google smoke",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, google_entity)
    assert any(t["title"] == "Google smoke" for t in tasks)


async def test_create_with_notes(
    ws_client: HAWebSocketClient, google_entity: str
) -> None:
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=google_entity,
        title="Google notes",
        notes="A Google Tasks description",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, google_entity)
    task = next(t for t in tasks if t["title"] == "Google notes")
    assert task["notes"] == "A Google Tasks description"


async def test_create_with_due_date(
    ws_client: HAWebSocketClient, google_entity: str
) -> None:
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=google_entity,
        title="Due Google",
        due_date="2027-12-10",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, google_entity)
    task = next(t for t in tasks if t["title"] == "Due Google")
    assert task["due_date"] == "2027-12-10"


async def test_update_title(
    ws_client: HAWebSocketClient, google_entity: str
) -> None:
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=google_entity,
        title="Google original",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, google_entity)
    task = next(t for t in tasks if t["title"] == "Google original")

    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=google_entity, task_uid=task["id"],
        title="Google renamed",
    )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, google_entity)
    assert any(t["title"] == "Google renamed" for t in tasks)


async def test_complete_via_update(
    ws_client: HAWebSocketClient, google_entity: str
) -> None:
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=google_entity,
        title="Google to complete",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, google_entity)
    task = next(t for t in tasks if t["title"] == "Google to complete")

    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=google_entity, task_uid=task["id"],
        completed=True,
    )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, google_entity)
    task = next((t for t in tasks if t["id"] == task["id"]), None)
    if task is not None:
        assert task["completed"] is True


# ---------------------------------------------------------------------------
# Overlay routing
# ---------------------------------------------------------------------------


async def test_priority_persists_via_overlay(
    ws_client: HAWebSocketClient, google_entity: str
) -> None:
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=google_entity,
        title="Google priority",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, google_entity)
    task = next(t for t in tasks if t["title"] == "Google priority")

    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=google_entity, task_uid=task["id"],
        priority=2,
    )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, google_entity)
    task = next(t for t in tasks if t["title"] == "Google priority")
    assert task["priority"] == 2


async def test_tags_persist_via_overlay(
    ws_client: HAWebSocketClient, google_entity: str
) -> None:
    await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=google_entity,
        title="Google tags",
    )
    await asyncio.sleep(SETTLE)
    tasks = await _refetch(ws_client, google_entity)
    task = next(t for t in tasks if t["title"] == "Google tags")

    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=google_entity, task_uid=task["id"],
        tags=["google", "live"],
    )
    await asyncio.sleep(SETTLE)

    tasks = await _refetch(ws_client, google_entity)
    task = next(t for t in tasks if t["title"] == "Google tags")
    assert sorted(task["tags"]) == ["google", "live"]
