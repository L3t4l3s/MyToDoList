"""Live tests for the Todoist provider via home_tasks/external_* commands.

These hit the real Todoist API.  Requires a dedicated test project linked
through home_tasks (HT_TODOIST_TEST_ENTITY).  The TodoistAdapter is the
only "rich" adapter and exercises the most code paths in provider_adapters.py.

Run with:  pytest -m live tests/live/test_provider_todoist.py
"""
from __future__ import annotations

import asyncio

import pytest

from .config import CONFIG
from .ws_client import HAWebSocketClient

pytestmark = [pytest.mark.live, pytest.mark.live_todoist]


# Todoist's internal sync is asynchronous; give it a moment after writes.
TODOIST_SETTLE = 0.4


async def _wipe_todoist(ws: HAWebSocketClient, entity_id: str) -> None:
    """Delete all tasks in the test project via the external API."""
    result = await ws.send_command(
        "home_tasks/get_external_tasks", entity_id=entity_id
    )
    tasks = result.get("tasks", [])
    if len(tasks) > CONFIG.max_existing_items:
        raise RuntimeError(
            f"Refusing to wipe {entity_id}: {len(tasks)} tasks > "
            f"max_existing_items={CONFIG.max_existing_items}"
        )
    for t in tasks:
        try:
            await ws.call_service(
                "todo", "remove_item",
                {"entity_id": entity_id, "item": t["id"]},
            )
        except Exception as err:  # noqa: BLE001
            print(f"[todoist cleanup] failed to remove {t.get('id')}: {err}")
    if tasks:
        await asyncio.sleep(TODOIST_SETTLE)


@pytest.fixture
async def todoist_entity(ws_client: HAWebSocketClient) -> str:
    entity_id = CONFIG.todoist_entity
    assert entity_id, "HT_TODOIST_TEST_ENTITY must be set"
    await _wipe_todoist(ws_client, entity_id)
    return entity_id


async def _refetch(
    ws: HAWebSocketClient, entity_id: str, *, retries: int = 3
) -> list[dict]:
    """Re-read tasks from the provider, retrying briefly to allow sync."""
    for attempt in range(retries):
        result = await ws.send_command(
            "home_tasks/get_external_tasks", entity_id=entity_id
        )
        tasks = result.get("tasks", [])
        if tasks:
            return tasks
        await asyncio.sleep(TODOIST_SETTLE)
    return tasks


# ---------------------------------------------------------------------------
# Basic CRUD
# ---------------------------------------------------------------------------


async def test_create_basic_task(
    ws_client: HAWebSocketClient, todoist_entity: str
) -> None:
    """create_external_task returns a uid that's then visible in get_external_tasks."""
    result = await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=todoist_entity,
        title="Live Todoist task",
    )
    new_uid = result["uid"]
    assert new_uid

    await asyncio.sleep(TODOIST_SETTLE)
    tasks = await _refetch(ws_client, todoist_entity)
    assert any(t["id"] == new_uid for t in tasks)
    task = next(t for t in tasks if t["id"] == new_uid)
    assert task["title"] == "Live Todoist task"


async def test_create_with_priority_and_notes(
    ws_client: HAWebSocketClient, todoist_entity: str
) -> None:
    """Create with priority + notes; both fields survive a re-fetch."""
    result = await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=todoist_entity,
        title="Priority test",
        priority=3,
        notes="Some Todoist notes",
    )
    uid = result["uid"]
    await asyncio.sleep(TODOIST_SETTLE)

    tasks = await _refetch(ws_client, todoist_entity)
    task = next(t for t in tasks if t["id"] == uid)
    assert task["priority"] == 3
    assert task["notes"] == "Some Todoist notes"


async def test_create_with_tags(
    ws_client: HAWebSocketClient, todoist_entity: str
) -> None:
    """Tags become Todoist labels and round-trip back."""
    result = await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=todoist_entity,
        title="Labeled task",
        tags=["live-test", "automation"],
    )
    uid = result["uid"]
    await asyncio.sleep(TODOIST_SETTLE)

    tasks = await _refetch(ws_client, todoist_entity)
    task = next(t for t in tasks if t["id"] == uid)
    assert "live-test" in task["tags"]
    assert "automation" in task["tags"]


async def test_create_with_due_date(
    ws_client: HAWebSocketClient, todoist_entity: str
) -> None:
    """A future due_date round-trips correctly."""
    result = await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=todoist_entity,
        title="Due someday",
        due_date="2027-08-15",
    )
    uid = result["uid"]
    await asyncio.sleep(TODOIST_SETTLE)

    tasks = await _refetch(ws_client, todoist_entity)
    task = next(t for t in tasks if t["id"] == uid)
    assert task["due_date"] == "2027-08-15"


async def test_update_title_priority_notes(
    ws_client: HAWebSocketClient, todoist_entity: str
) -> None:
    """update_external_task changes title, priority, notes individually."""
    create = await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=todoist_entity,
        title="Original",
    )
    uid = create["uid"]

    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=todoist_entity, task_uid=uid,
        title="Updated", priority=2, notes="New notes",
    )
    await asyncio.sleep(TODOIST_SETTLE)

    tasks = await _refetch(ws_client, todoist_entity)
    task = next(t for t in tasks if t["id"] == uid)
    assert task["title"] == "Updated"
    assert task["priority"] == 2
    assert task["notes"] == "New notes"


async def test_complete_via_update(
    ws_client: HAWebSocketClient, todoist_entity: str
) -> None:
    """update_external_task with completed=True marks the task done."""
    create = await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=todoist_entity,
        title="Will be completed",
    )
    uid = create["uid"]

    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=todoist_entity, task_uid=uid,
        completed=True,
    )
    await asyncio.sleep(TODOIST_SETTLE)

    tasks = await _refetch(ws_client, todoist_entity)
    task = next((t for t in tasks if t["id"] == uid), None)
    # Completed Todoist tasks may or may not be returned by the API depending
    # on filter; either they're absent or marked completed.
    if task is not None:
        assert task["completed"] is True


# ---------------------------------------------------------------------------
# Sub-tasks
# ---------------------------------------------------------------------------


async def test_sub_task_lifecycle(
    ws_client: HAWebSocketClient, todoist_entity: str
) -> None:
    """add_sub_task → update → delete via the external API."""
    parent = await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=todoist_entity,
        title="Sub-task parent",
    )
    pid = parent["uid"]

    sub = await ws_client.send_command(
        "home_tasks/add_external_sub_task",
        entity_id=todoist_entity,
        task_uid=pid,
        title="First sub",
    )
    sub_id = sub["id"]
    await asyncio.sleep(TODOIST_SETTLE)

    tasks = await _refetch(ws_client, todoist_entity)
    parent_task = next(t for t in tasks if t["id"] == pid)
    assert any(s["id"] == sub_id for s in parent_task["sub_items"])

    await ws_client.send_command(
        "home_tasks/update_external_sub_task",
        entity_id=todoist_entity,
        task_uid=pid,
        sub_task_id=sub_id,
        title="Renamed sub",
    )
    await asyncio.sleep(TODOIST_SETTLE)

    tasks = await _refetch(ws_client, todoist_entity)
    parent_task = next(t for t in tasks if t["id"] == pid)
    sub = next(s for s in parent_task["sub_items"] if s["id"] == sub_id)
    assert sub["title"] == "Renamed sub"

    await ws_client.send_command(
        "home_tasks/delete_external_sub_task",
        entity_id=todoist_entity,
        task_uid=pid,
        sub_task_id=sub_id,
    )
    await asyncio.sleep(TODOIST_SETTLE)

    tasks = await _refetch(ws_client, todoist_entity)
    parent_task = next(t for t in tasks if t["id"] == pid)
    assert not any(s["id"] == sub_id for s in parent_task["sub_items"])


# ---------------------------------------------------------------------------
# Recurrence
# ---------------------------------------------------------------------------


async def test_recurrence_round_trip(
    ws_client: HAWebSocketClient, todoist_entity: str
) -> None:
    """Setting recurrence on creation produces a recurring task in Todoist."""
    create = await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=todoist_entity,
        title="Daily recurring",
        due_date="2027-09-01",
        recurrence_enabled=True,
        recurrence_type="interval",
        recurrence_unit="days",
        recurrence_value=1,
    )
    uid = create["uid"]
    await asyncio.sleep(TODOIST_SETTLE)

    tasks = await _refetch(ws_client, todoist_entity)
    task = next(t for t in tasks if t["id"] == uid)
    assert task["recurrence_enabled"] is True
    # Provider may parse "every day" → recurrence_unit=days, value=1
    assert task["recurrence_unit"] == "days"


async def test_recurrence_weekdays(
    ws_client: HAWebSocketClient, todoist_entity: str
) -> None:
    """Weekday-based recurrence becomes 'every Mon, Wed, Fri' in Todoist."""
    create = await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=todoist_entity,
        title="Weekday recurring",
        due_date="2027-09-01",
        recurrence_enabled=True,
        recurrence_type="weekdays",
        recurrence_weekdays=[0, 2, 4],
    )
    uid = create["uid"]
    await asyncio.sleep(TODOIST_SETTLE)

    tasks = await _refetch(ws_client, todoist_entity)
    task = next(t for t in tasks if t["id"] == uid)
    assert task["recurrence_enabled"] is True


# ---------------------------------------------------------------------------
# Reminders
# ---------------------------------------------------------------------------


async def test_reminders_premium_only_does_not_destroy_existing(
    ws_client: HAWebSocketClient, todoist_entity: str
) -> None:
    """Setting Premium-only reminders on a Free account must NOT delete the
    implicit reminder Todoist created for tasks with due_datetime.

    REGRESSION TEST for the bug found via the live tests:
      - Todoist Free accounts cannot create reminders with non-zero
        minute_offset (returns 403 PREMIUM_ONLY).
      - Old _sync_reminders deleted existing reminders BEFORE attempting
        to add new ones, then the adds failed silently → task ended up
        with no reminders at all (data loss).
      - New _sync_reminders attempts adds first, aborts on PREMIUM_ONLY,
        and leaves the existing reminders intact.

    This test verifies the new behavior: even when we ask for offsets the
    free tier can't honor, the implicit at-due-time reminder survives.
    """
    create = await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=todoist_entity,
        title="Reminder preservation",
        due_date="2027-10-01",
        due_time="09:00",
    )
    uid = create["uid"]
    await asyncio.sleep(TODOIST_SETTLE)

    # Snapshot reminders BEFORE the update — Todoist auto-creates one
    # for any task with due_datetime.
    before = await _refetch(ws_client, todoist_entity)
    task_before = next(t for t in before if t["id"] == uid)
    reminders_before = sorted(task_before.get("reminders", []))

    # Try to set Premium-only reminders.  This will fail at the API level
    # but must NOT delete the existing implicit reminder.
    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=todoist_entity, task_uid=uid,
        reminders=[60, 1440],
    )
    await asyncio.sleep(TODOIST_SETTLE * 2)

    after = await _refetch(ws_client, todoist_entity)
    task_after = next(t for t in after if t["id"] == uid)
    reminders_after = sorted(task_after.get("reminders", []))

    # The implicit reminder must still be present (no data loss)
    assert reminders_after == reminders_before, (
        f"Reminders changed unexpectedly: before={reminders_before} "
        f"after={reminders_after}.  This means _sync_reminders deleted "
        f"the implicit reminder and failed to replace it."
    )


# ---------------------------------------------------------------------------
# Overlay routing — fields the provider can't sync go to overlay
# ---------------------------------------------------------------------------


async def test_recurrence_end_type_persists_via_overlay(
    ws_client: HAWebSocketClient, todoist_entity: str
) -> None:
    """recurrence_end_type lives in overlay (Todoist can't store it)."""
    create = await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=todoist_entity,
        title="Has end type",
    )
    uid = create["uid"]

    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=todoist_entity, task_uid=uid,
        recurrence_end_type="count",
        recurrence_max_count=5,
    )
    await asyncio.sleep(TODOIST_SETTLE)

    tasks = await _refetch(ws_client, todoist_entity)
    task = next(t for t in tasks if t["id"] == uid)
    assert task["recurrence_end_type"] == "count"
    assert task["recurrence_max_count"] == 5


# ---------------------------------------------------------------------------
# Reorder
# ---------------------------------------------------------------------------


async def test_reorder_external_tasks(
    ws_client: HAWebSocketClient, todoist_entity: str
) -> None:
    """reorder_external_tasks must push the new order to Todoist itself.

    Dual-view test: we verify BOTH our merged get_external_tasks view AND
    the provider-native todo.get_items view.  If Todoist never received
    the reorder, todo.get_items (which re-fetches from Todoist) still
    returns the old order — both views agreeing is evidence the change
    reached Todoist.

    Todoist uses the rich-adapter path: TodoistAdapter.async_reorder_tasks
    sets child_order via the REST API directly.
    """
    titles_in_order = ["Order 1", "Order 2", "Order 3"]
    uids = []
    for title in titles_in_order:
        r = await ws_client.send_command(
            "home_tasks/create_external_task",
            entity_id=todoist_entity, title=title,
        )
        uids.append(r["uid"])
    await asyncio.sleep(TODOIST_SETTLE)

    new_order = list(reversed(uids))
    expected_titles = list(reversed(titles_in_order))

    result = await ws_client.send_command(
        "home_tasks/reorder_external_tasks",
        entity_id=todoist_entity,
        task_uids=new_order,
    )
    assert result["provider_handled"] is True, (
        "Todoist reorder was NOT handled by the provider adapter — "
        "the card's overlay fallback took over.  Todoist itself still "
        "has the old order.  Check TodoistAdapter.async_reorder_tasks."
    )
    # Todoist sync is asynchronous — allow a beat for child_order to propagate.
    await asyncio.sleep(TODOIST_SETTLE * 2)

    # --- View 1: our merged view ---
    result = await ws_client.send_command(
        "home_tasks/get_external_tasks", entity_id=todoist_entity,
    )
    our_tasks = [t for t in result["tasks"] if t["id"] in uids]
    ordered = sorted(our_tasks, key=lambda t: t["sort_order"])
    assert [t["id"] for t in ordered] == new_order

    # --- View 2: provider's own view via todo.get_items ---
    # TodoistAdapter writes directly to Todoist's REST API, so HA's
    # Todoist integration entity lags until its next poll.  Force-refresh
    # before reading so the get_items call reflects what Todoist currently
    # holds rather than HA's cached snapshot.
    provider_items = await ws_client.get_provider_items(
        todoist_entity, refresh_first=True,
    )
    provider_titles = [
        i["summary"] for i in provider_items if i["uid"] in uids
    ]
    assert provider_titles == expected_titles, (
        f"Todoist provider still reports order {provider_titles}, expected "
        f"{expected_titles}.  The reorder did NOT reach Todoist."
    )
