"""Unit tests for ExternalTaskOverlayStore."""
from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant


@pytest.fixture
async def overlay_store(hass: HomeAssistant):
    """Create a standalone ExternalTaskOverlayStore for testing."""
    from custom_components.home_tasks.overlay_store import ExternalTaskOverlayStore
    store = ExternalTaskOverlayStore(hass, "todo.test_external")
    await store.async_load()
    return store


async def test_empty_overlay_returned_for_unknown_uid(hass: HomeAssistant, overlay_store) -> None:
    """get_overlay returns defaults for a UID that hasn't been set."""
    overlay = overlay_store.get_overlay("unknown-uid")
    assert overlay["priority"] is None
    assert overlay["tags"] == []
    assert overlay["sub_items"] == []
    assert overlay["recurrence_enabled"] is False


async def test_set_and_get_overlay(hass: HomeAssistant, overlay_store) -> None:
    """Setting an overlay field persists it."""
    await overlay_store.async_set_overlay("uid-1", priority=2, tags=["urgent"])
    overlay = overlay_store.get_overlay("uid-1")
    assert overlay["priority"] == 2
    assert overlay["tags"] == ["urgent"]


async def test_overlay_tags_deduplicated(hass: HomeAssistant, overlay_store) -> None:
    """Duplicate tags in overlay are de-duplicated and lowercased."""
    await overlay_store.async_set_overlay("uid-2", tags=["A", "a", "B"])
    overlay = overlay_store.get_overlay("uid-2")
    assert overlay["tags"] == ["a", "b"]


async def test_delete_overlay(hass: HomeAssistant, overlay_store) -> None:
    """Deleted overlays revert to defaults."""
    await overlay_store.async_set_overlay("uid-3", priority=3)
    await overlay_store.async_delete_overlay("uid-3")
    overlay = overlay_store.get_overlay("uid-3")
    assert overlay["priority"] is None


async def test_sub_task_add_update_delete(hass: HomeAssistant, overlay_store) -> None:
    """Sub-tasks can be added, updated, and deleted in the overlay."""
    sub = await overlay_store.async_add_sub_task("uid-4", "Sub-task title")
    assert sub["title"] == "Sub-task title"
    assert sub["completed"] is False

    updated = await overlay_store.async_update_sub_task("uid-4", sub["id"], completed=True)
    assert updated["completed"] is True

    await overlay_store.async_delete_sub_task("uid-4", sub["id"])
    overlay = overlay_store.get_overlay("uid-4")
    assert overlay["sub_items"] == []


async def test_sub_task_update_nonexistent_overlay_raises(hass: HomeAssistant, overlay_store) -> None:
    """Updating a sub-task on a UID with no overlay raises ValueError."""
    with pytest.raises(ValueError, match="Overlay not found"):
        await overlay_store.async_update_sub_task("no-overlay", "sub-id", completed=True)


async def test_sub_task_delete_nonexistent_raises(hass: HomeAssistant, overlay_store) -> None:
    """Deleting a sub-task that doesn't exist raises ValueError."""
    await overlay_store.async_add_sub_task("uid-5", "Exists")
    with pytest.raises(ValueError):
        await overlay_store.async_delete_sub_task("uid-5", "wrong-sub-id")


async def test_invalid_priority_raises(hass: HomeAssistant, overlay_store) -> None:
    """Setting an invalid priority raises ValueError."""
    with pytest.raises(ValueError, match="priority"):
        await overlay_store.async_set_overlay("uid-6", priority=99)


async def test_invalid_recurrence_unit_raises(hass: HomeAssistant, overlay_store) -> None:
    """Setting an invalid recurrence_unit raises ValueError."""
    with pytest.raises(ValueError, match="recurrence_unit"):
        await overlay_store.async_set_overlay("uid-7", recurrence_unit="fortnightly")


async def test_get_all_overlays(hass: HomeAssistant, overlay_store) -> None:
    """get_all_overlays returns all stored overlays with defaults filled in."""
    await overlay_store.async_set_overlay("uid-a", priority=1)
    await overlay_store.async_set_overlay("uid-b", priority=2)
    overlays = overlay_store.get_all_overlays()
    assert "uid-a" in overlays
    assert "uid-b" in overlays
    assert overlays["uid-a"]["priority"] == 1
    assert overlays["uid-b"]["tags"] == []  # default filled in


async def test_reorder_sub_tasks(hass: HomeAssistant, overlay_store) -> None:
    """Sub-tasks can be reordered within the overlay."""
    s1 = await overlay_store.async_add_sub_task("uid-c", "First")
    s2 = await overlay_store.async_add_sub_task("uid-c", "Second")
    await overlay_store.async_reorder_sub_tasks("uid-c", [s2["id"], s1["id"]])
    overlay = overlay_store.get_overlay("uid-c")
    assert overlay["sub_items"][0]["id"] == s2["id"]
    assert overlay["sub_items"][1]["id"] == s1["id"]


# ---------------------------------------------------------------------------
# Sub-task limits and overlay-not-found errors
# ---------------------------------------------------------------------------

async def test_sub_task_max_limit(hass: HomeAssistant, overlay_store) -> None:
    """Adding sub-tasks beyond the limit raises ValueError."""
    from custom_components.home_tasks.const import MAX_SUB_TASKS_PER_TASK
    for i in range(MAX_SUB_TASKS_PER_TASK):
        await overlay_store.async_add_sub_task("uid-limit", f"Sub {i}")
    with pytest.raises(ValueError, match="Maximum number of sub-tasks"):
        await overlay_store.async_add_sub_task("uid-limit", "One too many")


async def test_delete_sub_task_overlay_not_found(hass: HomeAssistant, overlay_store) -> None:
    """Deleting a sub-task when the overlay doesn't exist raises ValueError."""
    with pytest.raises(ValueError, match="Overlay not found"):
        await overlay_store.async_delete_sub_task("no-overlay-uid", "sub-id")


async def test_reorder_sub_tasks_overlay_not_found(hass: HomeAssistant, overlay_store) -> None:
    """Reordering sub-tasks when the overlay doesn't exist raises ValueError."""
    with pytest.raises(ValueError, match="Overlay not found"):
        await overlay_store.async_reorder_sub_tasks("no-overlay-uid", ["sub-id"])


async def test_update_sub_task_completed_not_bool(hass: HomeAssistant, overlay_store) -> None:
    """update_sub_task raises when completed is not a bool."""
    sub = await overlay_store.async_add_sub_task("uid-bool", "Sub")
    with pytest.raises(ValueError, match="boolean"):
        await overlay_store.async_update_sub_task("uid-bool", sub["id"], completed="yes")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Persistence: load from existing data
# ---------------------------------------------------------------------------

async def test_overlay_persists_across_reload(hass: HomeAssistant) -> None:
    """Overlay data loaded from disk on second instantiation."""
    from custom_components.home_tasks.overlay_store import ExternalTaskOverlayStore
    store1 = ExternalTaskOverlayStore(hass, "todo.persist_test")
    await store1.async_load()
    await store1.async_set_overlay("uid-persist", priority=3, tags=["urgent"])

    # Second instance reads the same storage key
    store2 = ExternalTaskOverlayStore(hass, "todo.persist_test")
    await store2.async_load()
    overlay = store2.get_overlay("uid-persist")
    assert overlay["priority"] == 3
    assert "urgent" in overlay["tags"]


# ---------------------------------------------------------------------------
# Listener support
# ---------------------------------------------------------------------------

async def test_overlay_listener_fires_on_change(hass: HomeAssistant, overlay_store) -> None:
    """Listeners are notified when overlay data is saved."""
    called = []
    remove = overlay_store.async_add_listener(lambda: called.append(1))
    await overlay_store.async_set_overlay("uid-listener", priority=1)
    assert len(called) == 1
    remove()
    await overlay_store.async_set_overlay("uid-listener", priority=2)
    assert len(called) == 1  # removed — not called again


# ---------------------------------------------------------------------------
# _validate_overlay_fields: all remaining branches
# ---------------------------------------------------------------------------

async def test_invalid_due_time(hass: HomeAssistant, overlay_store) -> None:
    with pytest.raises(ValueError, match="HH:MM"):
        await overlay_store.async_set_overlay("uid-t", due_time="9:00")


async def test_invalid_assigned_person(hass: HomeAssistant, overlay_store) -> None:
    with pytest.raises(ValueError, match="assigned_person"):
        await overlay_store.async_set_overlay("uid-t", assigned_person="x" * 300)


async def test_tags_not_list(hass: HomeAssistant, overlay_store) -> None:
    with pytest.raises(ValueError, match="tags"):
        await overlay_store.async_set_overlay("uid-t", tags="urgent")  # type: ignore[arg-type]


async def test_tags_non_string_element(hass: HomeAssistant, overlay_store) -> None:
    with pytest.raises(ValueError, match="string"):
        await overlay_store.async_set_overlay("uid-t", tags=[123])  # type: ignore[arg-type]


async def test_tags_element_too_long(hass: HomeAssistant, overlay_store) -> None:
    from custom_components.home_tasks.const import MAX_TAG_LENGTH
    with pytest.raises(ValueError, match="Tag exceeds"):
        await overlay_store.async_set_overlay("uid-t", tags=["x" * (MAX_TAG_LENGTH + 1)])


async def test_reminders_not_list(hass: HomeAssistant, overlay_store) -> None:
    with pytest.raises(ValueError, match="reminders"):
        await overlay_store.async_set_overlay("uid-t", reminders=30)  # type: ignore[arg-type]


async def test_reminders_invalid_value(hass: HomeAssistant, overlay_store) -> None:
    with pytest.raises(ValueError, match="reminder"):
        await overlay_store.async_set_overlay("uid-t", reminders=[-1])


async def test_recurrence_value_zero(hass: HomeAssistant, overlay_store) -> None:
    with pytest.raises(ValueError, match="recurrence_value"):
        await overlay_store.async_set_overlay("uid-t", recurrence_value=0)


async def test_recurrence_enabled_not_bool(hass: HomeAssistant, overlay_store) -> None:
    with pytest.raises(ValueError, match="recurrence_enabled"):
        await overlay_store.async_set_overlay("uid-t", recurrence_enabled="yes")  # type: ignore[arg-type]


async def test_recurrence_type_invalid(hass: HomeAssistant, overlay_store) -> None:
    with pytest.raises(ValueError, match="recurrence_type"):
        await overlay_store.async_set_overlay("uid-t", recurrence_type="monthly")


async def test_recurrence_weekdays_invalid(hass: HomeAssistant, overlay_store) -> None:
    with pytest.raises(ValueError, match="recurrence_weekdays"):
        await overlay_store.async_set_overlay("uid-t", recurrence_weekdays=[7])


async def test_recurrence_end_type_invalid(hass: HomeAssistant, overlay_store) -> None:
    with pytest.raises(ValueError, match="recurrence_end_type"):
        await overlay_store.async_set_overlay("uid-t", recurrence_end_type="year")


async def test_recurrence_max_count_zero(hass: HomeAssistant, overlay_store) -> None:
    with pytest.raises(ValueError, match="recurrence_max_count"):
        await overlay_store.async_set_overlay("uid-t", recurrence_max_count=0)


async def test_recurrence_remaining_count_negative(hass: HomeAssistant, overlay_store) -> None:
    with pytest.raises(ValueError, match="recurrence_remaining_count"):
        await overlay_store.async_set_overlay("uid-t", recurrence_remaining_count=-1)


async def test_recurrence_start_date_invalid(hass: HomeAssistant, overlay_store) -> None:
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        await overlay_store.async_set_overlay("uid-t", recurrence_start_date="01/01/2026")


async def test_recurrence_time_invalid(hass: HomeAssistant, overlay_store) -> None:
    with pytest.raises(ValueError, match="HH:MM"):
        await overlay_store.async_set_overlay("uid-t", recurrence_time="9:30")


async def test_valid_recurrence_overlay(hass: HomeAssistant, overlay_store) -> None:
    """A fully-specified recurrence overlay is accepted."""
    overlay = await overlay_store.async_set_overlay(
        "uid-full",
        recurrence_enabled=True,
        recurrence_type="weekdays",
        recurrence_weekdays=[0, 2, 4],
        recurrence_start_date="2026-01-01",
        recurrence_time="08:00",
        recurrence_end_type="date",
        recurrence_end_date="2026-12-31",
    )
    assert overlay["recurrence_enabled"] is True
    assert overlay["recurrence_weekdays"] == [0, 2, 4]


# ---------------------------------------------------------------------------
# _strip_default_overlays and selective storage
# ---------------------------------------------------------------------------


async def test_strip_default_overlays_removes_defaults(hass: HomeAssistant, overlay_store) -> None:
    """_strip_default_overlays removes an overlay that is entirely defaults."""
    overlay_store._data = {"overlays": {"uid-1": {
        "priority": None,
        "tags": [],
        "recurrence_enabled": False,
        "sort_order": 0,
        "due_time": None,
        "assigned_person": None,
        "reminders": [],
        "recurrence_value": 1,
        "recurrence_unit": None,
        "recurrence_type": "interval",
        "recurrence_weekdays": [],
        "recurrence_start_date": None,
        "recurrence_time": None,
        "recurrence_end_type": "none",
        "recurrence_end_date": None,
        "recurrence_max_count": None,
        "recurrence_remaining_count": None,
        "history": [],
        "completed_at": None,
    }}}
    overlay_store._strip_default_overlays()
    # All fields matched defaults (sub_items excluded from strip by design),
    # so the overlay entry should be removed entirely.
    assert overlay_store._data["overlays"] == {}


async def test_strip_default_overlays_keeps_nondefault_fields(hass: HomeAssistant, overlay_store) -> None:
    """_strip_default_overlays keeps non-default values and removes default ones."""
    overlay_store._data = {"overlays": {"uid-2": {
        "priority": 2,
        "tags": [],
    }}}
    overlay_store._strip_default_overlays()
    stored = overlay_store._data["overlays"]["uid-2"]
    assert stored["priority"] == 2
    assert "tags" not in stored


async def test_set_overlay_only_stores_explicit_fields(hass: HomeAssistant, overlay_store) -> None:
    """async_set_overlay stores only the fields that were explicitly passed."""
    await overlay_store.async_set_overlay("uid-explicit", priority=2)
    raw = overlay_store._data["overlays"]["uid-explicit"]
    assert raw["priority"] == 2
    # Should NOT contain all 20 default fields — only the one we set
    assert "tags" not in raw
    assert "recurrence_enabled" not in raw
    assert "sort_order" not in raw


async def test_update_sub_task_wrong_id_raises(hass: HomeAssistant, overlay_store) -> None:
    """Updating a sub-task with the wrong sub_task_id raises ValueError."""
    sub = await overlay_store.async_add_sub_task("uid-sub", "A sub-task")
    with pytest.raises(ValueError, match="Sub-task not found"):
        await overlay_store.async_update_sub_task("uid-sub", "wrong-sub-id", completed=True)


# ---------------------------------------------------------------------------
# Remaining gaps (tests 49–50)
# ---------------------------------------------------------------------------


async def test_overlay_reminders_dedup_sort(hass: HomeAssistant, overlay_store) -> None:
    """Duplicate reminders in overlay are de-duplicated and sorted."""
    await overlay_store.async_set_overlay("uid-rem", reminders=[60, 30, 60])
    overlay = overlay_store.get_overlay("uid-rem")
    assert overlay["reminders"] == [30, 60]


async def test_overlay_tags_empty_after_strip_skipped(hass: HomeAssistant, overlay_store) -> None:
    """Whitespace-only tags are stripped, only valid tags stored in overlay."""
    await overlay_store.async_set_overlay("uid-strip", tags=["valid", "  "])
    overlay = overlay_store.get_overlay("uid-strip")
    assert overlay["tags"] == ["valid"]
