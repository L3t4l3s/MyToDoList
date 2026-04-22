"""End-to-end tests against a live HA instance via WebSocket.

These tests connect to a running HA, authenticate with a long-lived access
token, and exercise home_tasks/* WebSocket commands the same way the
Lovelace card does.

Run with:  pytest -m live tests/live/test_e2e_websocket.py
"""
from __future__ import annotations

import pytest

from .ws_client import HAWebSocketClient

pytestmark = [pytest.mark.live, pytest.mark.live_websocket]


# ---------------------------------------------------------------------------
# Smoke / connection tests
# ---------------------------------------------------------------------------


async def test_connect_and_get_lists(ws_client: HAWebSocketClient) -> None:
    """get_lists returns at least one list (the configured native test list)."""
    result = await ws_client.send_command("home_tasks/get_lists")
    assert "lists" in result
    assert isinstance(result["lists"], list)
    assert len(result["lists"]) >= 1


async def test_native_test_list_resolves(
    ws_client: HAWebSocketClient, native_list_id: str
) -> None:
    """The configured HT_NATIVE_LIST_NAME resolves to a valid list_id."""
    assert isinstance(native_list_id, str)
    assert len(native_list_id) > 0


async def test_get_external_lists_includes_linked(
    ws_client: HAWebSocketClient,
) -> None:
    """get_external_lists returns the configured external lists."""
    result = await ws_client.send_command("home_tasks/get_external_lists")
    assert "external_lists" in result
    assert isinstance(result["external_lists"], list)


# ---------------------------------------------------------------------------
# Native CRUD against the test list
# ---------------------------------------------------------------------------


async def test_add_get_delete_task(
    ws_client: HAWebSocketClient, clean_native_list: str
) -> None:
    """Add a task → get_tasks shows it → delete it → get_tasks empty."""
    list_id = clean_native_list

    add = await ws_client.send_command(
        "home_tasks/add_task", list_id=list_id, title="WS smoke task"
    )
    task_id = add["id"]
    assert add["title"] == "WS smoke task"

    fetched = await ws_client.send_command("home_tasks/get_tasks", list_id=list_id)
    assert any(t["id"] == task_id for t in fetched["tasks"])

    await ws_client.send_command(
        "home_tasks/delete_task", list_id=list_id, task_id=task_id
    )

    after = await ws_client.send_command("home_tasks/get_tasks", list_id=list_id)
    assert not any(t["id"] == task_id for t in after["tasks"])


async def test_update_task_all_fields(
    ws_client: HAWebSocketClient, clean_native_list: str
) -> None:
    """Update each high-value field individually and verify it persists."""
    list_id = clean_native_list
    add = await ws_client.send_command(
        "home_tasks/add_task", list_id=list_id, title="Updateable"
    )
    tid = add["id"]

    # Title
    await ws_client.send_command(
        "home_tasks/update_task", list_id=list_id, task_id=tid, title="Renamed"
    )
    # Notes
    await ws_client.send_command(
        "home_tasks/update_task", list_id=list_id, task_id=tid, notes="Some notes"
    )
    # Priority
    await ws_client.send_command(
        "home_tasks/update_task", list_id=list_id, task_id=tid, priority=2
    )
    # Tags
    await ws_client.send_command(
        "home_tasks/update_task", list_id=list_id, task_id=tid, tags=["alpha", "beta"]
    )
    # Due date + time
    await ws_client.send_command(
        "home_tasks/update_task",
        list_id=list_id,
        task_id=tid,
        due_date="2027-01-15",
        due_time="14:30",
    )

    fetched = await ws_client.send_command("home_tasks/get_tasks", list_id=list_id)
    task = next(t for t in fetched["tasks"] if t["id"] == tid)
    assert task["title"] == "Renamed"
    assert task["notes"] == "Some notes"
    assert task["priority"] == 2
    assert sorted(task["tags"]) == ["alpha", "beta"]
    assert task["due_date"] == "2027-01-15"
    assert task["due_time"] == "14:30"


async def test_complete_and_reopen_task(
    ws_client: HAWebSocketClient, clean_native_list: str
) -> None:
    """A task can be completed and reopened via update_task."""
    list_id = clean_native_list
    add = await ws_client.send_command(
        "home_tasks/add_task", list_id=list_id, title="Complete me"
    )
    tid = add["id"]

    await ws_client.send_command(
        "home_tasks/update_task", list_id=list_id, task_id=tid, completed=True
    )
    fetched = await ws_client.send_command("home_tasks/get_tasks", list_id=list_id)
    task = next(t for t in fetched["tasks"] if t["id"] == tid)
    assert task["completed"] is True

    await ws_client.send_command(
        "home_tasks/update_task", list_id=list_id, task_id=tid, completed=False
    )
    fetched = await ws_client.send_command("home_tasks/get_tasks", list_id=list_id)
    task = next(t for t in fetched["tasks"] if t["id"] == tid)
    assert task["completed"] is False


# ---------------------------------------------------------------------------
# Sub-task lifecycle
# ---------------------------------------------------------------------------


async def test_sub_task_lifecycle(
    ws_client: HAWebSocketClient, clean_native_list: str
) -> None:
    """add_sub_task → update_sub_task → delete_sub_task all work."""
    list_id = clean_native_list
    parent = await ws_client.send_command(
        "home_tasks/add_task", list_id=list_id, title="Parent"
    )
    pid = parent["id"]

    sub = await ws_client.send_command(
        "home_tasks/add_sub_task", list_id=list_id, task_id=pid, title="Sub item"
    )
    sub_id = sub["id"]

    fetched = await ws_client.send_command("home_tasks/get_tasks", list_id=list_id)
    parent_task = next(t for t in fetched["tasks"] if t["id"] == pid)
    assert any(s["id"] == sub_id for s in parent_task["sub_items"])

    await ws_client.send_command(
        "home_tasks/update_sub_task",
        list_id=list_id,
        task_id=pid,
        sub_task_id=sub_id,
        title="Renamed sub",
        completed=True,
    )

    fetched = await ws_client.send_command("home_tasks/get_tasks", list_id=list_id)
    parent_task = next(t for t in fetched["tasks"] if t["id"] == pid)
    sub = next(s for s in parent_task["sub_items"] if s["id"] == sub_id)
    assert sub["title"] == "Renamed sub"
    assert sub["completed"] is True

    await ws_client.send_command(
        "home_tasks/delete_sub_task",
        list_id=list_id, task_id=pid, sub_task_id=sub_id,
    )

    fetched = await ws_client.send_command("home_tasks/get_tasks", list_id=list_id)
    parent_task = next(t for t in fetched["tasks"] if t["id"] == pid)
    assert not any(s["id"] == sub_id for s in parent_task["sub_items"])


# ---------------------------------------------------------------------------
# Reorder & move
# ---------------------------------------------------------------------------


async def test_reorder_tasks(
    ws_client: HAWebSocketClient, clean_native_list: str
) -> None:
    """reorder_tasks persists a new task order."""
    list_id = clean_native_list

    titles = ["Alpha", "Beta", "Gamma", "Delta"]
    ids: list[str] = []
    for t in titles:
        r = await ws_client.send_command(
            "home_tasks/add_task", list_id=list_id, title=t
        )
        ids.append(r["id"])

    # Reverse the order
    new_order = list(reversed(ids))
    await ws_client.send_command(
        "home_tasks/reorder_tasks", list_id=list_id, task_ids=new_order
    )

    fetched = await ws_client.send_command("home_tasks/get_tasks", list_id=list_id)
    sorted_tasks = sorted(fetched["tasks"], key=lambda t: t["sort_order"])
    fetched_ids = [t["id"] for t in sorted_tasks]
    assert fetched_ids == new_order


async def test_move_task_between_native_lists(
    ws_client: HAWebSocketClient,
    clean_native_list: str,
    native_list_id_secondary: str,
) -> None:
    """move_task transfers a task between two native lists with all fields."""
    pytest.importorskip("pytest")  # placeholder; marker check below
    src = clean_native_list
    tgt = native_list_id_secondary
    if src == tgt:
        pytest.skip("Source and target list are the same")

    # Wipe target too
    target_tasks = await ws_client.send_command("home_tasks/get_tasks", list_id=tgt)
    for t in target_tasks["tasks"]:
        await ws_client.send_command(
            "home_tasks/delete_task", list_id=tgt, task_id=t["id"]
        )

    add = await ws_client.send_command(
        "home_tasks/add_task", list_id=src, title="Movable"
    )
    tid = add["id"]
    await ws_client.send_command(
        "home_tasks/update_task",
        list_id=src, task_id=tid,
        priority=3, tags=["move"], notes="will travel",
    )

    await ws_client.send_command(
        "home_tasks/move_task",
        source_list_id=src,
        target_list_id=tgt,
        task_id=tid,
    )

    src_tasks = await ws_client.send_command("home_tasks/get_tasks", list_id=src)
    assert all(t["id"] != tid for t in src_tasks["tasks"])

    tgt_tasks = await ws_client.send_command("home_tasks/get_tasks", list_id=tgt)
    moved = next((t for t in tgt_tasks["tasks"] if t["title"] == "Movable"), None)
    assert moved is not None
    assert moved["priority"] == 3
    assert moved["tags"] == ["move"]
    assert moved["notes"] == "will travel"


test_move_task_between_native_lists.pytestmark = [
    pytest.mark.live,
    pytest.mark.live_websocket_two_lists,
]


# ---------------------------------------------------------------------------
# Optimistic update sequence (regression: rapid updates must all persist)
# ---------------------------------------------------------------------------


async def test_rapid_sequential_updates(
    ws_client: HAWebSocketClient, clean_native_list: str
) -> None:
    """10 sequential updates to the same field all land correctly."""
    list_id = clean_native_list
    add = await ws_client.send_command(
        "home_tasks/add_task", list_id=list_id, title="Rapid"
    )
    tid = add["id"]

    for i in range(10):
        await ws_client.send_command(
            "home_tasks/update_task",
            list_id=list_id, task_id=tid,
            notes=f"step-{i}",
        )

    fetched = await ws_client.send_command("home_tasks/get_tasks", list_id=list_id)
    task = next(t for t in fetched["tasks"] if t["id"] == tid)
    assert task["notes"] == "step-9"


# ---------------------------------------------------------------------------
# Reminders & recurrence — schedule-only verification
# ---------------------------------------------------------------------------


async def test_reminder_field_persists(
    ws_client: HAWebSocketClient, clean_native_list: str
) -> None:
    """reminders list survives an update + re-fetch cycle."""
    list_id = clean_native_list
    add = await ws_client.send_command(
        "home_tasks/add_task", list_id=list_id, title="Reminder host"
    )
    tid = add["id"]

    await ws_client.send_command(
        "home_tasks/update_task",
        list_id=list_id, task_id=tid,
        due_date="2027-12-01", due_time="09:00",
        reminders=[15, 60, 1440],
    )

    fetched = await ws_client.send_command("home_tasks/get_tasks", list_id=list_id)
    task = next(t for t in fetched["tasks"] if t["id"] == tid)
    assert sorted(task["reminders"]) == [15, 60, 1440]


async def test_recurrence_settings_persist(
    ws_client: HAWebSocketClient, clean_native_list: str
) -> None:
    """Recurrence config survives an update + re-fetch cycle."""
    list_id = clean_native_list
    add = await ws_client.send_command(
        "home_tasks/add_task", list_id=list_id, title="Recurring"
    )
    tid = add["id"]

    await ws_client.send_command(
        "home_tasks/update_task",
        list_id=list_id, task_id=tid,
        recurrence_enabled=True,
        recurrence_type="interval",
        recurrence_unit="days",
        recurrence_value=3,
    )

    fetched = await ws_client.send_command("home_tasks/get_tasks", list_id=list_id)
    task = next(t for t in fetched["tasks"] if t["id"] == tid)
    assert task["recurrence_enabled"] is True
    assert task["recurrence_unit"] == "days"
    assert task["recurrence_value"] == 3


# ---------------------------------------------------------------------------
# Completion flow for recurring tasks — advances due_date, reschedules
# reminders.  Gap #1 + #2 from the v1.10.1 gap analysis.
# ---------------------------------------------------------------------------


async def test_completing_recurring_native_task_advances_due_date(
    ws_client: HAWebSocketClient, clean_native_list: str
) -> None:
    """Completing a recurring native task must advance its due_date.

    Since v1.10.4 _on_task_completed rewrites due_date/due_time on the
    task dict to the next occurrence at completion time.  This is the
    live counterpart to the in-memory integration test — it verifies
    that the mutation survives a round-trip through storage and the
    WebSocket API, not just the in-process store.
    """
    from datetime import date, timedelta

    list_id = clean_native_list
    today = date.today().isoformat()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    # Create a daily-recurring task with today's due_date
    add = await ws_client.send_command(
        "home_tasks/add_task", list_id=list_id, title="Daily advance test"
    )
    tid = add["id"]
    await ws_client.send_command(
        "home_tasks/update_task",
        list_id=list_id, task_id=tid,
        due_date=today,
        recurrence_enabled=True,
        recurrence_type="interval",
        recurrence_unit="days",
        recurrence_value=1,
    )

    # Complete
    await ws_client.send_command(
        "home_tasks/update_task",
        list_id=list_id, task_id=tid, completed=True,
    )

    # Re-read: due_date must have been advanced to tomorrow, task still completed
    fetched = await ws_client.send_command(
        "home_tasks/get_tasks", list_id=list_id,
    )
    task = next(t for t in fetched["tasks"] if t["id"] == tid)
    assert task["completed"] is True, "Task should remain marked completed"
    assert task["due_date"] == tomorrow, (
        f"due_date expected to advance from {today} to {tomorrow}, "
        f"got {task['due_date']}"
    )

    # History must contain the auto-advance trail (by='recurrence')
    history = task.get("history", [])
    auto_advance = [
        h for h in history
        if h.get("field") == "due_date"
        and h.get("by") == "recurrence"
        and h.get("from") == today
        and h.get("to") == tomorrow
    ]
    assert auto_advance, (
        f"Expected a history entry for automatic due_date advance "
        f"({today} → {tomorrow}, by=recurrence); got {history!r}"
    )


async def test_task_reminder_event_fires_for_native_task(
    ws_client: HAWebSocketClient, clean_native_list: str
) -> None:
    """home_tasks_task_reminder fires for a task with an imminent reminder.

    Subscribes to the event bus via the WebSocket API, creates a task whose
    due moment is 90 seconds out with a 1-minute reminder (target ~= 30 s
    from now), and waits for the event to arrive.  Catches silent drop-offs
    where the reminder scheduler would happily take the request but never
    fire.  Uses offset=1 rather than 0 to avoid floating-point races on the
    "delay <= 0" silent-miss guard.
    """
    import asyncio
    from datetime import datetime, timedelta

    DOMAIN = "home_tasks"
    list_id = clean_native_list

    # Ask HA for its configured timezone so due_time matches what the
    # server uses, regardless of the test host's local zone.
    states = await ws_client.get_states()
    ha_tz_name = next(
        (s["attributes"].get("time_zone") for s in states
         if s.get("entity_id") == "zone.home" and s.get("attributes", {}).get("time_zone")),
        None,
    )
    # Fallback to system local if we couldn't read it from HA
    if ha_tz_name:
        try:
            from zoneinfo import ZoneInfo
            ha_tz = ZoneInfo(ha_tz_name)
        except Exception:
            ha_tz = None
    else:
        ha_tz = None

    now_in_ha = datetime.now(ha_tz) if ha_tz else datetime.now().astimezone()
    # 180 s in the future + 2-min offset → reminder target ~60 s from
    # scheduling.  Generous buffer so the test is robust even when run
    # after a full live-suite has left HA with a busy event bus.
    target = now_in_ha + timedelta(seconds=180)
    due_date = target.date().isoformat()
    due_time = target.strftime("%H:%M")

    # Subscribe to the reminder event *before* triggering scheduling.
    received: list[dict] = []
    sub_id = ws_client._next_id
    ws_client._next_id += 1
    await ws_client._ws.send_json({
        "id": sub_id, "type": "subscribe_events",
        "event_type": f"{DOMAIN}_task_reminder",
    })
    while True:
        msg = await asyncio.wait_for(ws_client._ws.receive_json(), timeout=5)
        if msg.get("id") == sub_id and msg.get("type") == "result":
            assert msg.get("success"), f"subscribe_events failed: {msg}"
            break

    try:
        add = await ws_client.send_command(
            "home_tasks/add_task", list_id=list_id, title="Reminder test",
        )
        tid = add["id"]
        await ws_client.send_command(
            "home_tasks/update_task",
            list_id=list_id, task_id=tid,
            due_date=due_date, due_time=due_time,
            reminders=[2],  # 2 min before due → target ~60 s from now
        )

        # Sanity-check the task persisted correctly before we start waiting
        fetched = await ws_client.send_command(
            "home_tasks/get_tasks", list_id=list_id,
        )
        task = next(t for t in fetched["tasks"] if t["id"] == tid)
        assert task.get("reminders") == [2], (
            f"reminders weren't stored: {task.get('reminders')!r}"
        )
        assert task.get("due_date") == due_date and task.get("due_time") == due_time

        # Wait up to 210 s for the event.  Target is ~60 s from update.
        deadline = asyncio.get_event_loop().time() + 210
        while asyncio.get_event_loop().time() < deadline:
            timeout = max(0.1, deadline - asyncio.get_event_loop().time())
            try:
                msg = await asyncio.wait_for(
                    ws_client._ws.receive_json(), timeout=timeout,
                )
            except asyncio.TimeoutError:
                break
            if msg.get("type") == "event" and msg.get("id") == sub_id:
                ev = msg.get("event", {}).get("data", {})
                if ev.get("task_id") == tid:
                    received.append(ev)
                    break

        assert received, (
            f"home_tasks_task_reminder never fired for task {tid} within "
            f"210 s (HA-side due {due_date} {due_time} in tz {ha_tz_name!r}, "
            f"offset=2 min → target ~60 s from scheduling).  Either the "
            f"scheduler silently dropped it or the event bus didn't reach "
            f"the subscriber."
        )
        assert received[0].get("reminder_offset_minutes") == 2
    finally:
        try:
            await ws_client.send_command(
                "unsubscribe_events", subscription=sub_id,
            )
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------


async def test_get_tasks_invalid_list_id(ws_client: HAWebSocketClient) -> None:
    """Querying a non-existent list returns an error response."""
    from .ws_client import WSError
    with pytest.raises(WSError):
        await ws_client.send_command(
            "home_tasks/get_tasks", list_id="nonexistent-list-id-xxxx"
        )


async def test_update_task_unknown_id(
    ws_client: HAWebSocketClient, clean_native_list: str
) -> None:
    """Updating a non-existent task returns an error."""
    from .ws_client import WSError
    with pytest.raises(WSError):
        await ws_client.send_command(
            "home_tasks/update_task",
            list_id=clean_native_list,
            task_id="ghost-task-id",
            title="ghost",
        )
