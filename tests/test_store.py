"""Unit tests for HomeTasksStore."""
from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant

from custom_components.home_tasks.const import MAX_TASKS_PER_LIST


async def test_add_task_defaults(hass: HomeAssistant, store) -> None:
    """A new task has correct default field values."""
    task = await store.async_add_task("Buy milk")
    assert task["title"] == "Buy milk"
    assert task["completed"] is False
    assert task["id"] is not None
    assert task["sort_order"] == 0
    assert task["sub_items"] == []
    assert task["tags"] == []
    assert task["reminders"] == []
    assert task["priority"] is None
    assert task["due_date"] is None


async def test_add_task_increments_sort_order(hass: HomeAssistant, store) -> None:
    """Each new task gets sort_order one higher than the previous max."""
    t1 = await store.async_add_task("First")
    t2 = await store.async_add_task("Second")
    assert t2["sort_order"] == t1["sort_order"] + 1


async def test_add_task_records_history(hass: HomeAssistant, store) -> None:
    """New tasks have a 'created' entry in history."""
    task = await store.async_add_task("History check")
    assert any(h["action"] == "created" for h in task["history"])


async def test_title_empty_rejected(hass: HomeAssistant, store) -> None:
    """Empty (or whitespace-only) titles raise ValueError."""
    with pytest.raises(ValueError, match="must not be empty"):
        await store.async_add_task("   ")


async def test_title_too_long_rejected(hass: HomeAssistant, store) -> None:
    """Titles exceeding MAX_TITLE_LENGTH raise ValueError."""
    with pytest.raises(ValueError):
        await store.async_add_task("x" * 256)


async def test_max_tasks_limit(hass: HomeAssistant, store) -> None:
    """Store refuses to add tasks beyond MAX_TASKS_PER_LIST."""
    for i in range(MAX_TASKS_PER_LIST):
        store._data["tasks"].append({"id": str(i), "title": f"t{i}", "sort_order": i})
    with pytest.raises(ValueError, match="Maximum number of tasks"):
        await store.async_add_task("One too many")


async def test_complete_task(hass: HomeAssistant, store) -> None:
    """Completing a task sets completed=True and records completed_at."""
    task = await store.async_add_task("Do laundry")
    updated = await store.async_update_task(task["id"], completed=True)
    assert updated["completed"] is True
    assert updated["completed_at"] is not None


async def test_reopen_task(hass: HomeAssistant, store) -> None:
    """Reopening a completed task clears completed and completed_at."""
    task = await store.async_add_task("Reopen me")
    await store.async_update_task(task["id"], completed=True)
    reopened = await store.async_reopen_task(task["id"])
    assert reopened["completed"] is False
    assert reopened["completed_at"] is None


async def test_reopen_resets_subtasks(hass: HomeAssistant, store) -> None:
    """Reopening a task resets all its sub-tasks to incomplete."""
    task = await store.async_add_task("Parent")
    sub = await store.async_add_sub_task(task["id"], "Child")
    await store.async_update_sub_task(task["id"], sub["id"], completed=True)
    await store.async_update_task(task["id"], completed=True)
    await store.async_reopen_task(task["id"])
    t = store.get_task(task["id"])
    assert t["sub_items"][0]["completed"] is False


async def test_delete_task(hass: HomeAssistant, store) -> None:
    """Deleted tasks are no longer returned by store.tasks."""
    task = await store.async_add_task("Temporary")
    await store.async_delete_task(task["id"])
    assert all(t["id"] != task["id"] for t in store.tasks)


async def test_get_task_not_found(hass: HomeAssistant, store) -> None:
    """get_task raises ValueError for unknown IDs."""
    with pytest.raises(ValueError, match="Task not found"):
        store.get_task("nonexistent-id")


async def test_update_invalid_priority(hass: HomeAssistant, store) -> None:
    """Priority values outside 1–3 raise ValueError."""
    task = await store.async_add_task("Important")
    with pytest.raises(ValueError, match="priority"):
        await store.async_update_task(task["id"], priority=5)


async def test_update_invalid_recurrence_unit(hass: HomeAssistant, store) -> None:
    """Invalid recurrence_unit values raise ValueError."""
    task = await store.async_add_task("Recurring")
    with pytest.raises(ValueError, match="recurrence_unit"):
        await store.async_update_task(task["id"], recurrence_unit="fortnightly")


async def test_update_invalid_date_format(hass: HomeAssistant, store) -> None:
    """Malformed due_date raises ValueError."""
    task = await store.async_add_task("Dated task")
    with pytest.raises(ValueError):
        await store.async_update_task(task["id"], due_date="2026/04/01")


async def test_update_invalid_time_format(hass: HomeAssistant, store) -> None:
    """Malformed due_time raises ValueError."""
    task = await store.async_add_task("Timed task")
    with pytest.raises(ValueError):
        await store.async_update_task(task["id"], due_time="9:00")


async def test_tags_deduplication(hass: HomeAssistant, store) -> None:
    """Duplicate tags (including case variants) are de-duplicated."""
    task = await store.async_add_task("Tagged")
    updated = await store.async_update_task(task["id"], tags=["chore", "chore", "CHORE"])
    assert updated["tags"] == ["chore"]


async def test_tags_lowercased(hass: HomeAssistant, store) -> None:
    """Tags are stored in lowercase."""
    task = await store.async_add_task("Tagged")
    updated = await store.async_update_task(task["id"], tags=["Urgent", "KITCHEN"])
    assert "urgent" in updated["tags"]
    assert "kitchen" in updated["tags"]


async def test_history_tracks_field_change(hass: HomeAssistant, store) -> None:
    """Changing a tracked field appends an 'updated' entry to history."""
    task = await store.async_add_task("Title track")
    await store.async_update_task(task["id"], title="Renamed task", actor="user1")
    t = store.get_task(task["id"])
    assert any(h["action"] == "updated" and h.get("field") == "title" for h in t["history"])


async def test_sub_task_crud(hass: HomeAssistant, store) -> None:
    """Sub-tasks can be added, updated, and deleted."""
    task = await store.async_add_task("Parent")
    sub = await store.async_add_sub_task(task["id"], "Child")
    assert sub["title"] == "Child"
    assert sub["completed"] is False

    await store.async_update_sub_task(task["id"], sub["id"], completed=True)
    t = store.get_task(task["id"])
    assert t["sub_items"][0]["completed"] is True

    await store.async_delete_sub_task(task["id"], sub["id"])
    assert store.get_task(task["id"])["sub_items"] == []


async def test_reorder_tasks(hass: HomeAssistant, store) -> None:
    """Reordering tasks updates sort_order values correctly."""
    t1 = await store.async_add_task("First")
    t2 = await store.async_add_task("Second")
    t3 = await store.async_add_task("Third")
    # Put t3 first, t1 second, t2 third
    await store.async_reorder_tasks([t3["id"], t1["id"], t2["id"]])
    task_map = {t["id"]: t for t in store.tasks}
    assert task_map[t3["id"]]["sort_order"] < task_map[t1["id"]]["sort_order"]
    assert task_map[t1["id"]]["sort_order"] < task_map[t2["id"]]["sort_order"]


async def test_recurrence_remaining_count_decrements(hass: HomeAssistant, store) -> None:
    """Completing a count-limited recurring task decrements remaining count."""
    task = await store.async_add_task("Counted")
    await store.async_update_task(
        task["id"],
        recurrence_enabled=True,
        recurrence_unit="days",
        recurrence_value=1,
        recurrence_end_type="count",
        recurrence_max_count=5,
    )
    await store.async_update_task(task["id"], completed=True)
    t = store.get_task(task["id"])
    assert t["recurrence_remaining_count"] == 4


async def test_move_task_between_lists(hass: HomeAssistant, store) -> None:
    """async_export_task removes a task; async_import_task adds it to another store."""
    from custom_components.home_tasks.store import HomeTasksStore
    # Create a second independent store
    store2 = HomeTasksStore(hass, "fake-entry-id-2")
    await store2.async_load()

    task = await store.async_add_task("Move me")
    task_id = task["id"]
    exported = await store.async_export_task(task_id)
    assert all(t["id"] != task_id for t in store.tasks)

    imported = await store2.async_import_task(exported)
    assert any(t["id"] == task_id for t in store2.tasks)
    assert imported["title"] == "Move me"


# ---------------------------------------------------------------------------
# Standalone validation helpers
# ---------------------------------------------------------------------------

def test_validate_text_not_string() -> None:
    from custom_components.home_tasks.store import validate_text
    with pytest.raises(ValueError, match="must be a string"):
        validate_text(123, 255, "field")


def test_validate_text_too_long() -> None:
    from custom_components.home_tasks.store import validate_text
    with pytest.raises(ValueError, match="exceeds maximum length"):
        validate_text("x" * 300, 255, "field")


def test_validate_date_not_string() -> None:
    from custom_components.home_tasks.store import validate_date
    with pytest.raises(ValueError, match="must be a string"):
        validate_date(20260401)  # type: ignore[arg-type]


def test_validate_date_wrong_format() -> None:
    from custom_components.home_tasks.store import validate_date
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        validate_date("01/04/2026")


def test_validate_date_empty_string_returns_none() -> None:
    from custom_components.home_tasks.store import validate_date
    assert validate_date("  ") is None


def test_validate_time_not_string() -> None:
    from custom_components.home_tasks.store import validate_time
    with pytest.raises(ValueError, match="must be a string"):
        validate_time(1200)  # type: ignore[arg-type]


def test_validate_time_wrong_format() -> None:
    from custom_components.home_tasks.store import validate_time
    with pytest.raises(ValueError, match="HH:MM"):
        validate_time("9:00")


def test_validate_time_invalid_components() -> None:
    from custom_components.home_tasks.store import validate_time
    with pytest.raises(ValueError, match="invalid time"):
        validate_time("25:00")


def test_validate_time_empty_returns_none() -> None:
    from custom_components.home_tasks.store import validate_time
    assert validate_time("  ") is None


# ---------------------------------------------------------------------------
# Migration helpers
# ---------------------------------------------------------------------------

async def test_backfill_migrates_old_recurrence_interval(hass: HomeAssistant, store) -> None:
    """Old recurrence_interval string is migrated to value + unit."""
    store._data["tasks"].append({
        "id": "old-task", "title": "Old", "completed": False, "sort_order": 99,
        "recurrence_interval": "weekly",
    })
    store._backfill_recurrence_fields()
    t = store.get_task("old-task")
    assert t["recurrence_value"] == 1
    assert t["recurrence_unit"] == "weeks"
    assert "recurrence_interval" not in t


async def test_backfill_migrates_daily_interval(hass: HomeAssistant, store) -> None:
    store._data["tasks"].append({
        "id": "old-daily", "title": "Daily", "completed": False, "sort_order": 100,
        "recurrence_interval": "daily",
    })
    store._backfill_recurrence_fields()
    t = store.get_task("old-daily")
    assert t["recurrence_value"] == 1
    assert t["recurrence_unit"] == "days"


async def test_migrate_v1_to_v2_adds_external_fields(hass: HomeAssistant, store) -> None:
    """Migration adds external_id and sync_source to tasks that lack them."""
    store._data["tasks"].append({
        "id": "v1-task", "title": "V1", "completed": False, "sort_order": 98,
    })
    store._migrate_v1_to_v2()
    t = store.get_task("v1-task")
    assert t["external_id"] is None
    assert t["sync_source"] is None


# ---------------------------------------------------------------------------
# Callback hooks
# ---------------------------------------------------------------------------

async def test_on_task_created_callback(hass: HomeAssistant) -> None:
    """on_task_created fires when a task is added (standalone store)."""
    from custom_components.home_tasks.store import HomeTasksStore
    s = HomeTasksStore(hass, "cb-entry-1")
    await s.async_load()
    created = []
    s.on_task_created = lambda task: created.append(task["id"])
    task = await s.async_add_task("CB task")
    assert task["id"] in created


async def test_on_reminders_changed_callback(hass: HomeAssistant) -> None:
    """on_reminders_changed fires when due_date changes."""
    from custom_components.home_tasks.store import HomeTasksStore
    s = HomeTasksStore(hass, "cb-entry-2")
    await s.async_load()
    changed = []
    s.on_reminders_changed = lambda task: changed.append(task["id"])
    task = await s.async_add_task("Reminder task")
    await s.async_update_task(task["id"], due_date="2026-06-01", reminders=[30])
    assert len(changed) >= 1


async def test_on_task_assigned_callback(hass: HomeAssistant) -> None:
    """on_task_assigned fires when assigned_person changes."""
    from custom_components.home_tasks.store import HomeTasksStore
    s = HomeTasksStore(hass, "cb-entry-3")
    await s.async_load()
    assigned = []
    s.on_task_assigned = lambda task, prev: assigned.append((task["id"], prev))
    task = await s.async_add_task("Assign task")
    await s.async_update_task(task["id"], assigned_person="person.alice")
    assert len(assigned) == 1
    assert assigned[0][1] is None  # previous was None


async def test_listener_add_and_remove(hass: HomeAssistant) -> None:
    """Listener is called on changes; removal stops future calls."""
    from custom_components.home_tasks.store import HomeTasksStore
    s = HomeTasksStore(hass, "listener-entry")
    await s.async_load()
    called = []
    remove = s.async_add_listener(lambda: called.append(1))
    await s.async_add_task("Trigger")
    assert len(called) == 1
    remove()
    await s.async_add_task("No trigger")
    assert len(called) == 1  # removed — not called again


# ---------------------------------------------------------------------------
# Additional async_update_task validation
# ---------------------------------------------------------------------------

async def test_update_notes_too_long(hass: HomeAssistant, store) -> None:
    task = await store.async_add_task("Noted")
    with pytest.raises(ValueError, match="Notes"):
        await store.async_update_task(task["id"], notes="x" * 10001)


async def test_update_notes_not_string(hass: HomeAssistant, store) -> None:
    task = await store.async_add_task("Noted")
    with pytest.raises(ValueError, match="string"):
        await store.async_update_task(task["id"], notes=123)  # type: ignore[arg-type]


async def test_update_completed_not_bool(hass: HomeAssistant, store) -> None:
    task = await store.async_add_task("Bool task")
    with pytest.raises(ValueError, match="boolean"):
        await store.async_update_task(task["id"], completed="yes")  # type: ignore[arg-type]


async def test_update_recurrence_value_zero(hass: HomeAssistant, store) -> None:
    task = await store.async_add_task("Recurrence")
    with pytest.raises(ValueError, match="recurrence_value"):
        await store.async_update_task(task["id"], recurrence_value=0)


async def test_update_recurrence_enabled_not_bool(hass: HomeAssistant, store) -> None:
    task = await store.async_add_task("Recurrence")
    with pytest.raises(ValueError, match="recurrence_enabled"):
        await store.async_update_task(task["id"], recurrence_enabled="yes")  # type: ignore[arg-type]


async def test_update_recurrence_type_invalid(hass: HomeAssistant, store) -> None:
    task = await store.async_add_task("Recurrence")
    with pytest.raises(ValueError, match="recurrence_type"):
        await store.async_update_task(task["id"], recurrence_type="monthly")


async def test_update_recurrence_weekdays_invalid_value(hass: HomeAssistant, store) -> None:
    task = await store.async_add_task("Recurrence")
    with pytest.raises(ValueError, match="recurrence_weekdays"):
        await store.async_update_task(task["id"], recurrence_weekdays=[7])


async def test_update_recurrence_weekdays_not_list(hass: HomeAssistant, store) -> None:
    task = await store.async_add_task("Recurrence")
    with pytest.raises(ValueError, match="recurrence_weekdays"):
        await store.async_update_task(task["id"], recurrence_weekdays="mon")  # type: ignore[arg-type]


async def test_update_recurrence_end_type_invalid(hass: HomeAssistant, store) -> None:
    task = await store.async_add_task("Recurrence")
    with pytest.raises(ValueError, match="recurrence_end_type"):
        await store.async_update_task(task["id"], recurrence_end_type="year")


async def test_update_recurrence_max_count_zero(hass: HomeAssistant, store) -> None:
    task = await store.async_add_task("Recurrence")
    with pytest.raises(ValueError, match="recurrence_max_count"):
        await store.async_update_task(task["id"], recurrence_max_count=0)


async def test_update_recurrence_remaining_count_negative(hass: HomeAssistant, store) -> None:
    task = await store.async_add_task("Recurrence")
    with pytest.raises(ValueError, match="recurrence_remaining_count"):
        await store.async_update_task(task["id"], recurrence_remaining_count=-1)


async def test_update_assigned_person_too_long(hass: HomeAssistant, store) -> None:
    task = await store.async_add_task("Assigned")
    with pytest.raises(ValueError, match="assigned_person"):
        await store.async_update_task(task["id"], assigned_person="x" * 300)


async def test_update_tags_not_list(hass: HomeAssistant, store) -> None:
    task = await store.async_add_task("Tagged")
    with pytest.raises(ValueError, match="tags"):
        await store.async_update_task(task["id"], tags="urgent")  # type: ignore[arg-type]


async def test_update_reminders_not_list(hass: HomeAssistant, store) -> None:
    task = await store.async_add_task("Reminder")
    with pytest.raises(ValueError, match="reminders"):
        await store.async_update_task(task["id"], reminders=30)  # type: ignore[arg-type]


async def test_update_reminders_invalid_value(hass: HomeAssistant, store) -> None:
    task = await store.async_add_task("Reminder")
    with pytest.raises(ValueError, match="reminder"):
        await store.async_update_task(task["id"], reminders=[-1])


# ---------------------------------------------------------------------------
# History tracking for individual fields
# ---------------------------------------------------------------------------

async def test_history_tracks_due_date_change(hass: HomeAssistant, store) -> None:
    task = await store.async_add_task("Dated")
    await store.async_update_task(task["id"], due_date="2026-06-01")
    t = store.get_task(task["id"])
    assert any(h.get("field") == "due_date" for h in t["history"])


async def test_history_tracks_priority_change(hass: HomeAssistant, store) -> None:
    task = await store.async_add_task("Priority")
    await store.async_update_task(task["id"], priority=3)
    t = store.get_task(task["id"])
    assert any(h.get("field") == "priority" for h in t["history"])


async def test_history_tracks_tags_change(hass: HomeAssistant, store) -> None:
    task = await store.async_add_task("Tags")
    await store.async_update_task(task["id"], tags=["work"])
    t = store.get_task(task["id"])
    assert any(h.get("field") == "tags" for h in t["history"])


async def test_history_tracks_notes_change(hass: HomeAssistant, store) -> None:
    task = await store.async_add_task("Notes")
    await store.async_update_task(task["id"], notes="some notes")
    t = store.get_task(task["id"])
    assert any(h.get("field") == "notes" for h in t["history"])


async def test_history_tracks_recurrence_enabled_change(hass: HomeAssistant, store) -> None:
    task = await store.async_add_task("Recurrence hist")
    await store.async_update_task(task["id"], recurrence_enabled=True)
    t = store.get_task(task["id"])
    assert any(h.get("field") == "recurrence_enabled" for h in t["history"])


async def test_history_tracks_reopened_via_update(hass: HomeAssistant, store) -> None:
    task = await store.async_add_task("Reopen track")
    await store.async_update_task(task["id"], completed=True)
    await store.async_update_task(task["id"], completed=False)
    t = store.get_task(task["id"])
    assert any(h["action"] == "reopened" for h in t["history"])


async def test_trim_history_limits_to_max(hass: HomeAssistant, store) -> None:
    """History is trimmed to _MAX_HISTORY entries in-place."""
    from custom_components.home_tasks.store import _MAX_HISTORY, _trim_history
    task = await store.async_add_task("History trim")
    t = store.get_task(task["id"])
    for i in range(_MAX_HISTORY + 10):
        t["history"].append({"ts": "2026-01-01", "action": "updated", "field": "title",
                              "from": str(i), "to": str(i + 1)})
    _trim_history(t["history"])
    assert len(t["history"]) == _MAX_HISTORY


# ---------------------------------------------------------------------------
# Sub-task reorder
# ---------------------------------------------------------------------------

async def test_reorder_sub_tasks(hass: HomeAssistant, store) -> None:
    task = await store.async_add_task("Parent")
    s1 = await store.async_add_sub_task(task["id"], "First")
    s2 = await store.async_add_sub_task(task["id"], "Second")
    s3 = await store.async_add_sub_task(task["id"], "Third")
    await store.async_reorder_sub_tasks(task["id"], [s3["id"], s1["id"], s2["id"]])
    t = store.get_task(task["id"])
    assert t["sub_items"][0]["id"] == s3["id"]
    assert t["sub_items"][2]["id"] == s2["id"]


# ---------------------------------------------------------------------------
# Recurrence max_count behaviour
# ---------------------------------------------------------------------------

async def test_recurrence_max_count_sets_remaining(hass: HomeAssistant, store) -> None:
    """Setting recurrence_max_count also resets remaining_count."""
    task = await store.async_add_task("Counted")
    updated = await store.async_update_task(
        task["id"],
        recurrence_enabled=True,
        recurrence_unit="days",
        recurrence_value=1,
        recurrence_end_type="count",
        recurrence_max_count=3,
    )
    assert updated["recurrence_remaining_count"] == 3


async def test_recurrence_remaining_zero_disables_recurrence(hass: HomeAssistant, store) -> None:
    """When remaining_count reaches 0, recurrence_enabled is set to False."""
    task = await store.async_add_task("One-shot")
    await store.async_update_task(
        task["id"],
        recurrence_enabled=True,
        recurrence_unit="days",
        recurrence_value=1,
        recurrence_end_type="count",
        recurrence_max_count=1,
    )
    await store.async_update_task(task["id"], completed=True)
    t = store.get_task(task["id"])
    assert t["recurrence_remaining_count"] == 0
    assert t["recurrence_enabled"] is False


async def test_store_loads_from_existing_data(hass: HomeAssistant) -> None:
    """HomeTasksStore loads from disk on second instantiation."""
    from custom_components.home_tasks.store import HomeTasksStore
    s1 = HomeTasksStore(hass, "persist-entry")
    await s1.async_load()
    task = await s1.async_add_task("Persisted task")

    # Second instance reads from the same storage key
    s2 = HomeTasksStore(hass, "persist-entry")
    await s2.async_load()
    assert any(t["id"] == task["id"] for t in s2.tasks)


async def test_history_tracks_due_time_change(hass: HomeAssistant, store) -> None:
    task = await store.async_add_task("Timed")
    await store.async_update_task(task["id"], due_date="2026-06-01", due_time="09:00")
    t = store.get_task(task["id"])
    assert any(h.get("field") == "due_time" for h in t["history"])


async def test_history_tracks_assigned_person_change(hass: HomeAssistant, store) -> None:
    task = await store.async_add_task("Assigned")
    await store.async_update_task(task["id"], assigned_person="person.bob")
    t = store.get_task(task["id"])
    assert any(h.get("field") == "assigned_person" for h in t["history"])


async def test_reopen_already_open_is_noop(hass: HomeAssistant, store) -> None:
    """Reopening a task that's already open returns it unchanged."""
    task = await store.async_add_task("Already open")
    result = await store.async_reopen_task(task["id"])
    assert result["completed"] is False  # unchanged, no error


async def test_on_task_reopened_callback(hass: HomeAssistant) -> None:
    """on_task_reopened fires when a completed task is explicitly reopened."""
    from custom_components.home_tasks.store import HomeTasksStore
    s = HomeTasksStore(hass, "cb-reopen")
    await s.async_load()
    reopened = []
    s.on_task_reopened = lambda task: reopened.append(task["id"])
    task = await s.async_add_task("Reopen CB")
    await s.async_update_task(task["id"], completed=True)
    await s.async_reopen_task(task["id"])
    assert task["id"] in reopened


async def test_on_task_deleted_callback(hass: HomeAssistant) -> None:
    """on_task_deleted fires when a task is deleted."""
    from custom_components.home_tasks.store import HomeTasksStore
    s = HomeTasksStore(hass, "cb-delete")
    await s.async_load()
    deleted = []
    s.on_task_deleted = lambda task_id: deleted.append(task_id)
    task = await s.async_add_task("Delete CB")
    await s.async_delete_task(task["id"])
    assert task["id"] in deleted


async def test_recurrence_start_date_valid(hass: HomeAssistant, store) -> None:
    """recurrence_start_date accepts a valid date string."""
    task = await store.async_add_task("Start date")
    updated = await store.async_update_task(
        task["id"], recurrence_start_date="2026-01-01"
    )
    assert updated["recurrence_start_date"] == "2026-01-01"


async def test_recurrence_end_date_valid(hass: HomeAssistant, store) -> None:
    """recurrence_end_date accepts a valid date string."""
    task = await store.async_add_task("End date")
    updated = await store.async_update_task(
        task["id"], recurrence_end_date="2027-12-31"
    )
    assert updated["recurrence_end_date"] == "2027-12-31"


async def test_recurrence_weekdays_deduplicated(hass: HomeAssistant, store) -> None:
    """Duplicate weekday values are de-duplicated and sorted."""
    task = await store.async_add_task("Weekdays")
    updated = await store.async_update_task(
        task["id"], recurrence_weekdays=[4, 1, 4, 1, 0]
    )
    assert updated["recurrence_weekdays"] == [0, 1, 4]
