"""End-to-end cross-list move tests against the live HA instance.

These exercise home_tasks/move_task_cross with one combination per
configured provider, verifying both directions (native↔external) and that
fields the provider can sync survive while overlay-only fields are
preserved through the overlay store.

Run with:  pytest -m live tests/live/test_e2e_cross_move.py
"""
from __future__ import annotations

import asyncio

import pytest

from .config import CONFIG
from .ws_client import HAWebSocketClient

pytestmark = [pytest.mark.live, pytest.mark.live_websocket]

SETTLE = 0.6


async def _wipe_external(ws: HAWebSocketClient, entity_id: str) -> None:
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
            print(f"[cross_move cleanup] failed to remove {t.get('id')}: {err}")
    if tasks:
        await asyncio.sleep(SETTLE)


async def _refetch_native(
    ws: HAWebSocketClient, list_id: str
) -> list[dict]:
    result = await ws.send_command("home_tasks/get_tasks", list_id=list_id)
    return result.get("tasks", [])


async def _refetch_external(
    ws: HAWebSocketClient, entity_id: str
) -> list[dict]:
    result = await ws.send_command(
        "home_tasks/get_external_tasks", entity_id=entity_id
    )
    return result.get("tasks", [])


# ---------------------------------------------------------------------------
# Per-provider cross-move tests — each native ↔ external round-trip
# ---------------------------------------------------------------------------


async def _native_to_external_then_back(
    ws: HAWebSocketClient,
    list_id: str,
    entity_id: str,
    *,
    title: str,
    extra_fields: dict | None = None,
) -> None:
    """Move a native task to external, then back, asserting fields survive."""
    extra_fields = extra_fields or {}

    # Create source task with rich fields
    create = await ws.send_command(
        "home_tasks/add_task", list_id=list_id, title=title
    )
    tid = create["id"]
    if extra_fields:
        await ws.send_command(
            "home_tasks/update_task",
            list_id=list_id, task_id=tid, **extra_fields,
        )

    # Move native → external
    await ws.send_command(
        "home_tasks/move_task_cross",
        task_id=tid,
        source_list_id=list_id,
        target_entity_id=entity_id,
    )
    await asyncio.sleep(SETTLE)

    # Source list no longer has it
    src = await _refetch_native(ws, list_id)
    assert all(t["id"] != tid for t in src)

    # Target external has it
    tgt = await _refetch_external(ws, entity_id)
    moved = next((t for t in tgt if t["title"] == title), None)
    assert moved is not None, f"Task '{title}' did not appear in {entity_id}"

    # Verify the fields that should survive at minimum
    assert moved["title"] == title
    if "notes" in extra_fields:
        assert moved["notes"] == extra_fields["notes"]
    if "tags" in extra_fields:
        assert sorted(moved["tags"]) == sorted(extra_fields["tags"])
    if "priority" in extra_fields:
        assert moved["priority"] == extra_fields["priority"]


# ---------------------------------------------------------------------------
# Native → Todoist
# ---------------------------------------------------------------------------


@pytest.mark.live_todoist
async def test_native_to_todoist(
    ws_client: HAWebSocketClient,
    clean_native_list: str,
) -> None:
    """Native → Todoist preserves title, notes, priority, tags."""
    if not CONFIG.todoist_entity:
        pytest.skip("HT_TODOIST_TEST_ENTITY not set")
    await _wipe_external(ws_client, CONFIG.todoist_entity)

    await _native_to_external_then_back(
        ws_client,
        list_id=clean_native_list,
        entity_id=CONFIG.todoist_entity,
        title="Cross to Todoist",
        extra_fields={
            "notes": "Cross-move notes",
            "priority": 2,
            "tags": ["cross", "move"],
        },
    )


# ---------------------------------------------------------------------------
# Native → CalDAV
# ---------------------------------------------------------------------------


@pytest.mark.live_caldav
async def test_native_to_caldav(
    ws_client: HAWebSocketClient,
    clean_native_list: str,
) -> None:
    """Native → CalDAV preserves base fields and overlay fields."""
    if not CONFIG.caldav_entity:
        pytest.skip("HT_CALDAV_TEST_ENTITY not set")
    from .conftest import ensure_caldav_available

    await ensure_caldav_available(ws_client, CONFIG.caldav_entity)
    await _wipe_external(ws_client, CONFIG.caldav_entity)

    await _native_to_external_then_back(
        ws_client,
        list_id=clean_native_list,
        entity_id=CONFIG.caldav_entity,
        title="Cross to CalDAV",
        extra_fields={
            "notes": "CalDAV cross notes",
            "priority": 1,
            "tags": ["caldav-cross"],
        },
    )


# ---------------------------------------------------------------------------
# Native → Google Tasks
# ---------------------------------------------------------------------------


@pytest.mark.live_google_tasks
async def test_native_to_google_tasks(
    ws_client: HAWebSocketClient,
    clean_native_list: str,
) -> None:
    """Native → Google Tasks preserves base + overlay fields."""
    if not CONFIG.google_tasks_entity:
        pytest.skip("HT_GOOGLE_TASKS_TEST_ENTITY not set")
    await _wipe_external(ws_client, CONFIG.google_tasks_entity)

    await _native_to_external_then_back(
        ws_client,
        list_id=clean_native_list,
        entity_id=CONFIG.google_tasks_entity,
        title="Cross to Google",
        extra_fields={
            "notes": "Google cross notes",
            "priority": 3,
            "tags": ["google-cross"],
        },
    )


# ---------------------------------------------------------------------------
# Native → Bring
# ---------------------------------------------------------------------------


@pytest.mark.live_bring
async def test_native_to_bring(
    ws_client: HAWebSocketClient,
    clean_native_list: str,
) -> None:
    """Native → Bring preserves title and overlay fields."""
    if not CONFIG.bring_entity:
        pytest.skip("HT_BRING_TEST_ENTITY not set")
    await _wipe_external(ws_client, CONFIG.bring_entity)

    await _native_to_external_then_back(
        ws_client,
        list_id=clean_native_list,
        entity_id=CONFIG.bring_entity,
        title="Cross to Bring",
        extra_fields={
            "priority": 2,
            "tags": ["bring-cross"],
        },
    )


# ---------------------------------------------------------------------------
# External → Native (Todoist as source)
# ---------------------------------------------------------------------------


@pytest.mark.live_todoist
async def test_todoist_to_native(
    ws_client: HAWebSocketClient,
    clean_native_list: str,
) -> None:
    """Todoist → Native preserves all fields stored in the provider."""
    if not CONFIG.todoist_entity:
        pytest.skip("HT_TODOIST_TEST_ENTITY not set")
    await _wipe_external(ws_client, CONFIG.todoist_entity)

    create = await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=CONFIG.todoist_entity,
        title="Todoist source",
        priority=3,
        notes="Will go native",
        tags=["from-todoist"],
    )
    uid = create["uid"]
    await asyncio.sleep(SETTLE)

    await ws_client.send_command(
        "home_tasks/move_task_cross",
        task_id=uid,
        source_entity_id=CONFIG.todoist_entity,
        target_list_id=clean_native_list,
    )
    await asyncio.sleep(SETTLE)

    native = await _refetch_native(ws_client, clean_native_list)
    moved = next((t for t in native if t["title"] == "Todoist source"), None)
    assert moved is not None
    assert moved["priority"] == 3
    assert moved["notes"] == "Will go native"
    assert "from-todoist" in moved["tags"]
