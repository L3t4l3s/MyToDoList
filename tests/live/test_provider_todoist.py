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
    ws_client: HAWebSocketClient,
    todoist_entity: str,
    todoist_verifier,
) -> None:
    """create_external_task must actually reach Todoist.

    Dual-view assertion:
      - our merged view returns the new task with the uid/title we set
      - Todoist's REST API, queried by task uid, confirms the same
    """
    result = await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=todoist_entity,
        title="Live Todoist task",
    )
    new_uid = result["uid"]
    assert new_uid

    await asyncio.sleep(TODOIST_SETTLE)

    # our view
    tasks = await _refetch(ws_client, todoist_entity)
    task = next((t for t in tasks if t["id"] == new_uid), None)
    assert task is not None, "task not in home_tasks/get_external_tasks response"
    assert task["title"] == "Live Todoist task"

    # provider-side truth
    remote = await todoist_verifier.get_task(new_uid)
    assert remote.content == "Live Todoist task", (
        f"Todoist itself does not have this task.  Remote state: {remote!r}"
    )


async def test_create_with_priority_and_notes(
    ws_client: HAWebSocketClient,
    todoist_entity: str,
    todoist_verifier,
) -> None:
    """priority + notes must be set on Todoist, not only in our view.

    home_tasks priority N maps to Todoist priority N+1 (1=normal … 4=urgent).
    """
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

    remote = await todoist_verifier.get_task(uid)
    assert remote.content == "Priority test"
    assert remote.priority == 4, (
        f"Todoist priority is {remote.priority}, expected 4 "
        "(home_tasks priority 3 → Todoist priority 4)"
    )
    assert remote.description == "Some Todoist notes"


async def test_create_with_tags(
    ws_client: HAWebSocketClient,
    todoist_entity: str,
    todoist_verifier,
) -> None:
    """home_tasks tags must end up as Todoist labels."""
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

    remote = await todoist_verifier.get_task(uid)
    assert "live-test" in remote.labels
    assert "automation" in remote.labels


async def test_create_with_due_date(
    ws_client: HAWebSocketClient,
    todoist_entity: str,
    todoist_verifier,
) -> None:
    """due_date must be stored on Todoist's side, not only in the overlay."""
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

    remote = await todoist_verifier.get_task(uid)
    assert remote.due is not None, "Todoist stored no due date"
    # Todoist returns date as "YYYY-MM-DD" for date-only tasks.
    assert remote.due.date == "2027-08-15", (
        f"Todoist due.date={remote.due.date!r}, expected '2027-08-15'"
    )


async def test_create_with_due_date_and_time(
    ws_client: HAWebSocketClient,
    todoist_entity: str,
    todoist_verifier,
) -> None:
    """due_date + due_time must reach Todoist as a datetime, not just a date."""
    result = await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=todoist_entity,
        title="Due with time",
        due_date="2027-08-15",
        due_time="14:30",
    )
    uid = result["uid"]
    await asyncio.sleep(TODOIST_SETTLE)

    tasks = await _refetch(ws_client, todoist_entity)
    task = next(t for t in tasks if t["id"] == uid)
    assert task["due_date"] == "2027-08-15"
    assert task["due_time"] == "14:30"

    remote = await todoist_verifier.get_task(uid)
    assert remote.due is not None, "Todoist stored no due info"
    # Todoist represents "date+time" in the `date` field as an ISO-8601
    # datetime string (e.g. 2027-08-15T14:30:00).  The date-only form is
    # just "YYYY-MM-DD" without the T.
    assert "T" in (remote.due.date or ""), (
        f"Todoist due.date={remote.due.date!r} looks like a date-only value; "
        "the time component didn't reach Todoist"
    )
    assert remote.due.date.startswith("2027-08-15T14:30"), (
        f"Todoist due.date={remote.due.date!r}, expected to start with "
        "'2027-08-15T14:30' (day + time we sent)"
    )


async def test_update_title_priority_notes(
    ws_client: HAWebSocketClient,
    todoist_entity: str,
    todoist_verifier,
) -> None:
    """update_external_task must push title/priority/notes to Todoist."""
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

    remote = await todoist_verifier.get_task(uid)
    assert remote.content == "Updated"
    assert remote.priority == 3  # home_tasks 2 → Todoist 3
    assert remote.description == "New notes"


async def test_complete_via_update(
    ws_client: HAWebSocketClient,
    todoist_entity: str,
    todoist_verifier,
) -> None:
    """update_external_task with completed=True must close the task at Todoist."""
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

    # At Todoist, the task is either is_completed=True (if still reachable)
    # or 410/404 (if Todoist removes closed tasks from the active endpoint).
    remote = await todoist_verifier.try_get_task(uid)
    if remote is not None:
        assert remote.is_completed is True, (
            f"Todoist still reports task as open: is_completed={remote.is_completed}"
        )
    # (else the task simply isn't in the open-tasks endpoint any more,
    # which also confirms it was closed.)


async def test_delete_removes_task_from_todoist(
    ws_client: HAWebSocketClient,
    todoist_entity: str,
    todoist_verifier,
) -> None:
    """Deleting a task must remove it at Todoist, not just from our overlay.

    The card calls todo.remove_item (HA service) followed by
    home_tasks/delete_external_overlay (overlay cleanup).  This test
    mirrors that sequence and asserts the task is gone from Todoist
    itself via the REST API — catches any silent drop-off where the
    overlay is cleaned up but the upstream task survives.
    """
    create = await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=todoist_entity,
        title="Delete me",
    )
    uid = create["uid"]
    assert uid
    await asyncio.sleep(TODOIST_SETTLE)

    # Provider-side sanity: task really exists before we delete
    pre = await todoist_verifier.get_task(uid)
    assert pre.content == "Delete me"

    # HA's Todoist integration polls asynchronously, so a task created
    # via our adapter (direct REST) may not yet be in HA's local cache
    # when the card calls todo.remove_item — force a refresh first,
    # just like the card's delete flow does implicitly via the entity
    # update on user interaction.
    await ws_client.refresh_entity(todoist_entity)
    await asyncio.sleep(TODOIST_SETTLE)

    # Card's delete path: todo.remove_item + overlay cleanup
    await ws_client.call_service(
        "todo", "remove_item",
        {"item": uid},
        target={"entity_id": todoist_entity},
    )
    await ws_client.send_command(
        "home_tasks/delete_external_overlay",
        entity_id=todoist_entity, task_uid=uid,
    )
    await asyncio.sleep(TODOIST_SETTLE)

    # Our merged view: gone
    tasks = await _refetch(ws_client, todoist_entity)
    assert not any(t["id"] == uid for t in tasks), (
        "Deleted task still appears in home_tasks/get_external_tasks"
    )

    # Provider-side: really gone
    remote = await todoist_verifier.try_get_task(uid)
    assert remote is None, (
        f"Todoist still holds the task after delete: {remote!r}"
    )


async def test_complete_on_recurring_advances_instead_of_closing(
    ws_client: HAWebSocketClient,
    todoist_entity: str,
    todoist_verifier,
) -> None:
    """Checking off a recurring task follows Todoist's semantics (Option A).

    For recurring tasks, ``POST /tasks/{id}/close`` in Todoist does NOT close
    the task — it advances the due date to the next occurrence and leaves
    ``checked=False``.  This is the behaviour the user wants Home Tasks to
    mirror: ticking today's instance off means "done for today", not "stop
    recurring entirely".

    What the test nails down:
      - is_recurring stays True
      - due.date moves forward by exactly one day (daily recurrence)
      - is_completed stays False — the task is still open, just shifted
      - our merged view still returns the task with its new due_date

    If anyone changes the adapter to stop-recurring-on-complete, this test
    breaks — by design.  A different semantic would need a different test.
    """
    from datetime import date, timedelta

    create = await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=todoist_entity,
        title="Daily recurring for complete test",
        due_date=date.today().isoformat(),
        recurrence_enabled=True,
        recurrence_type="interval",
        recurrence_unit="days",
        recurrence_value=1,
    )
    uid = create["uid"]
    await asyncio.sleep(TODOIST_SETTLE)

    before = await todoist_verifier.get_task(uid)
    assert before.due is not None and before.due.is_recurring is True, (
        "Task did not come back as recurring — adapter mapping broken"
    )
    initial_due = before.due.date
    assert initial_due is not None
    initial_dt = date.fromisoformat(initial_due)

    # "Check off" via our card-facing WS command
    await ws_client.send_command(
        "home_tasks/update_external_task",
        entity_id=todoist_entity, task_uid=uid,
        completed=True,
    )
    await asyncio.sleep(TODOIST_SETTLE)

    after = await todoist_verifier.get_task(uid)
    # Option A: recurring close = advance, not end
    assert after.is_completed is False, (
        "Recurring task was fully closed instead of advanced — that's not "
        "Option A (Todoist semantics).  If you intended to change the behaviour, "
        "update this test with the new expectation."
    )
    assert after.due is not None and after.due.is_recurring is True, (
        "Recurrence was lost after completing a recurring task"
    )
    assert after.due.date is not None
    after_dt = date.fromisoformat(after.due.date)
    advance = (after_dt - initial_dt).days
    assert advance == 1, (
        f"Todoist advanced due.date by {advance} day(s) "
        f"({initial_due} → {after.due.date}), expected +1 day"
    )

    # Our merged view must still list the task (with the new due_date), not
    # hide it — otherwise the UI loses recurring tasks right after a check.
    tasks = await _refetch(ws_client, todoist_entity)
    merged = next((t for t in tasks if t["id"] == uid), None)
    assert merged is not None, (
        "After checking off a recurring task, home_tasks/get_external_tasks "
        "no longer returns it.  The task should remain visible with its new "
        "due date (next occurrence)."
    )
    assert merged["completed"] is False, (
        f"Merged view shows completed={merged['completed']}, expected False — "
        "the recurring task is still open (just shifted to next occurrence)."
    )
    assert merged["due_date"] == after.due.date


# ---------------------------------------------------------------------------
# Sub-tasks
# ---------------------------------------------------------------------------


async def test_sub_task_lifecycle(
    ws_client: HAWebSocketClient,
    todoist_entity: str,
    todoist_verifier,
) -> None:
    """Sub-tasks must live at Todoist with parent_id wiring, not in overlay."""
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

    # our view
    tasks = await _refetch(ws_client, todoist_entity)
    parent_task = next(t for t in tasks if t["id"] == pid)
    assert any(s["id"] == sub_id for s in parent_task["sub_items"])

    # provider view: sub-task exists AND its parent_id matches at Todoist
    remote_sub = await todoist_verifier.get_task(sub_id)
    assert remote_sub.content == "First sub"
    assert remote_sub.parent_id == pid, (
        f"Todoist parent_id={remote_sub.parent_id}, expected {pid}.  "
        "The sub-task was created but is not wired to its parent."
    )

    # Rename
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
    sub_local = next(s for s in parent_task["sub_items"] if s["id"] == sub_id)
    assert sub_local["title"] == "Renamed sub"

    remote_sub = await todoist_verifier.get_task(sub_id)
    assert remote_sub.content == "Renamed sub"

    # Delete
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

    assert await todoist_verifier.try_get_task(sub_id) is None, (
        "Sub-task was removed from our view but still exists at Todoist."
    )


# ---------------------------------------------------------------------------
# Recurrence
# ---------------------------------------------------------------------------


async def test_recurrence_round_trip(
    ws_client: HAWebSocketClient,
    todoist_entity: str,
    todoist_verifier,
) -> None:
    """Recurrence lives at Todoist — is_recurring=True and due.string set."""
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
    assert task["recurrence_unit"] == "days"

    remote = await todoist_verifier.get_task(uid)
    assert remote.due is not None, "Todoist task has no due info"
    assert remote.due.is_recurring is True, (
        f"Todoist task isn't recurring: is_recurring={remote.due.is_recurring}, "
        f"due.string={remote.due.string!r}"
    )
    # "every day" is Todoist's canonical shape for daily recurrence
    assert "day" in (remote.due.string or "").lower()


async def test_recurrence_weekdays(
    ws_client: HAWebSocketClient,
    todoist_entity: str,
    todoist_verifier,
) -> None:
    """Weekday recurrence lives at Todoist as a recurring natural-language due."""
    create = await ws_client.send_command(
        "home_tasks/create_external_task",
        entity_id=todoist_entity,
        title="Weekday recurring",
        due_date="2027-09-01",
        recurrence_enabled=True,
        recurrence_type="weekdays",
        recurrence_weekdays=[0, 2, 4],  # Mon, Wed, Fri
    )
    uid = create["uid"]
    await asyncio.sleep(TODOIST_SETTLE)

    tasks = await _refetch(ws_client, todoist_entity)
    task = next(t for t in tasks if t["id"] == uid)
    assert task["recurrence_enabled"] is True

    remote = await todoist_verifier.get_task(uid)
    assert remote.due is not None
    assert remote.due.is_recurring is True
    due_str = (remote.due.string or "").lower()
    # Todoist accepts natural-language like "every mon, wed, fri"
    assert "mon" in due_str or "every" in due_str, (
        f"Todoist due.string={remote.due.string!r} doesn't look like a weekday recurrence"
    )


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
    ws_client: HAWebSocketClient,
    todoist_entity: str,
    todoist_verifier,
) -> None:
    """recurrence_end_type + recurrence_max_count live ONLY in our overlay.

    Todoist doesn't model "recur N times" so these must never leak onto
    the Todoist task — polluting Todoist state would corrupt user data.
    """
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

    # our merged view: overlay fields visible
    tasks = await _refetch(ws_client, todoist_entity)
    task = next(t for t in tasks if t["id"] == uid)
    assert task["recurrence_end_type"] == "count"
    assert task["recurrence_max_count"] == 5

    # Todoist side: the task must still exist unchanged — no weird
    # extra labels like "count=5" or description pollution.
    remote = await todoist_verifier.get_task(uid)
    assert remote.content == "Has end type"
    # description must stay empty (we didn't set notes)
    assert remote.description == "", (
        f"Overlay metadata leaked into Todoist description: {remote.description!r}"
    )
    # no labels smuggled in
    assert remote.labels == [], (
        f"Overlay metadata leaked into Todoist labels: {remote.labels!r}"
    )


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
