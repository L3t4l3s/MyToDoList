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
