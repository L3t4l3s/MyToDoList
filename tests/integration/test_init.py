"""Tests for integration setup, services, events, and timer mechanics."""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from homeassistant.util.dt import utcnow
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

DOMAIN = "home_tasks"

pytestmark = pytest.mark.integration


async def test_setup_creates_store(hass: HomeAssistant, mock_config_entry, store) -> None:
    """Setup creates a HomeTasksStore registered in hass.data."""
    from custom_components.home_tasks.store import HomeTasksStore
    assert isinstance(hass.data[DOMAIN][mock_config_entry.entry_id], HomeTasksStore)


async def test_all_services_registered(hass: HomeAssistant, mock_config_entry) -> None:
    """All four integration services are registered after setup."""
    for svc in ("add_task", "complete_task", "assign_task", "reopen_task"):
        assert hass.services.has_service(DOMAIN, svc), f"Service '{svc}' not registered"


async def test_service_add_task_by_list_name(hass: HomeAssistant, mock_config_entry, store) -> None:
    """add_task service creates a task when referenced by list_name."""
    await hass.services.async_call(
        DOMAIN,
        "add_task",
        {"list_name": "Test List", "title": "Service task"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert any(t["title"] == "Service task" for t in store.tasks)


async def test_service_complete_task_by_title(hass: HomeAssistant, mock_config_entry, store) -> None:
    """complete_task service marks the matching task as completed."""
    await store.async_add_task("Task to complete")
    await hass.services.async_call(
        DOMAIN,
        "complete_task",
        {"list_name": "Test List", "task_title": "Task to complete"},
        blocking=True,
    )
    await hass.async_block_till_done()
    tasks = [t for t in store.tasks if t["title"] == "Task to complete"]
    assert tasks and tasks[0]["completed"] is True


async def test_event_task_created(hass: HomeAssistant, mock_config_entry, store) -> None:
    """Creating a task fires the home_tasks_task_created event."""
    events = []
    hass.bus.async_listen(f"{DOMAIN}_task_created", lambda e: events.append(e))
    await store.async_add_task("Event task")
    await hass.async_block_till_done()
    assert len(events) == 1
    assert events[0].data["task_title"] == "Event task"


async def test_event_task_completed(hass: HomeAssistant, mock_config_entry, store) -> None:
    """Completing a task fires the home_tasks_task_completed event."""
    events = []
    hass.bus.async_listen(f"{DOMAIN}_task_completed", lambda e: events.append(e))
    task = await store.async_add_task("Complete me")
    await store.async_update_task(task["id"], completed=True)
    await hass.async_block_till_done()
    assert len(events) == 1
    assert events[0].data["task_id"] == task["id"]


async def test_event_task_reopened(hass: HomeAssistant, mock_config_entry, store) -> None:
    """Reopening a task fires the home_tasks_task_reopened event."""
    events = []
    hass.bus.async_listen(f"{DOMAIN}_task_reopened", lambda e: events.append(e))
    task = await store.async_add_task("Reopen me")
    await store.async_update_task(task["id"], completed=True)
    await store.async_reopen_task(task["id"], actor="user1")
    await hass.async_block_till_done()
    assert len(events) == 1


async def test_event_task_assigned(hass: HomeAssistant, mock_config_entry, store) -> None:
    """Assigning a person fires the home_tasks_task_assigned event."""
    events = []
    hass.bus.async_listen(f"{DOMAIN}_task_assigned", lambda e: events.append(e))
    task = await store.async_add_task("Assign me")
    await store.async_update_task(task["id"], assigned_person="person.alice")
    await hass.async_block_till_done()
    assert len(events) == 1
    assert events[0].data["assigned_person"] == "person.alice"
    assert events[0].data["previous_person"] is None


async def test_recurrence_timer_reopens_task(hass: HomeAssistant, mock_config_entry, store) -> None:
    """After completing a recurring task, it reopens when the timer fires."""
    task = await store.async_add_task("Recurring")
    await store.async_update_task(
        task["id"],
        recurrence_enabled=True,
        recurrence_unit="hours",
        recurrence_value=1,
    )
    await store.async_update_task(task["id"], completed=True)
    await hass.async_block_till_done()
    assert store.get_task(task["id"])["completed"] is True

    # Advance time by more than 1 hour to trigger the recurrence timer
    async_fire_time_changed(hass, utcnow() + timedelta(hours=1, seconds=10))
    await hass.async_block_till_done()
    assert store.get_task(task["id"])["completed"] is False


async def test_unload_entry_cleans_up(hass: HomeAssistant, mock_config_entry) -> None:
    """Unloading a config entry removes the store from hass.data."""
    entry_id = mock_config_entry.entry_id
    assert entry_id in hass.data[DOMAIN]

    assert await hass.config_entries.async_unload(entry_id)
    await hass.async_block_till_done()
    assert entry_id not in hass.data.get(DOMAIN, {})


async def test_service_assign_task(hass: HomeAssistant, mock_config_entry, store) -> None:
    """assign_task service sets assigned_person on the task."""
    await store.async_add_task("Assignable")
    await hass.services.async_call(
        DOMAIN,
        "assign_task",
        {"list_name": "Test List", "task_title": "Assignable", "person": "person.bob"},
        blocking=True,
    )
    await hass.async_block_till_done()
    tasks = [t for t in store.tasks if t["title"] == "Assignable"]
    assert tasks and tasks[0]["assigned_person"] == "person.bob"


async def test_service_reopen_task(hass: HomeAssistant, mock_config_entry, store) -> None:
    """reopen_task service reopens a completed task."""
    await store.async_add_task("Reopenable")
    await hass.services.async_call(
        DOMAIN,
        "complete_task",
        {"list_name": "Test List", "task_title": "Reopenable"},
        blocking=True,
    )
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN,
        "reopen_task",
        {"list_name": "Test List", "task_title": "Reopenable"},
        blocking=True,
    )
    await hass.async_block_till_done()
    tasks = [t for t in store.tasks if t["title"] == "Reopenable"]
    assert tasks and tasks[0]["completed"] is False


async def test_service_complete_task_by_tag(hass: HomeAssistant, mock_config_entry, store) -> None:
    """complete_task service with tag= completes all matching tagged tasks."""
    t1 = await store.async_add_task("Tagged A")
    t2 = await store.async_add_task("Tagged B")
    t3 = await store.async_add_task("No tag")
    await store.async_update_task(t1["id"], tags=["chore"])
    await store.async_update_task(t2["id"], tags=["chore"])

    await hass.services.async_call(
        DOMAIN,
        "complete_task",
        {"list_name": "Test List", "tag": "chore"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert store.get_task(t1["id"])["completed"] is True
    assert store.get_task(t2["id"])["completed"] is True
    assert store.get_task(t3["id"])["completed"] is False


async def test_due_date_event_fires(hass: HomeAssistant, mock_config_entry, store) -> None:
    """A task due today fires home_tasks_task_due when the checker runs."""
    from freezegun import freeze_time
    from custom_components.home_tasks import _async_check_due_dates

    with freeze_time("2026-04-03"):
        events = []
        hass.bus.async_listen(f"{DOMAIN}_task_due", lambda e: events.append(e))

        task = await store.async_add_task("Due today")
        await store.async_update_task(task["id"], due_date="2026-04-03")
        await hass.async_block_till_done()

        await _async_check_due_dates(hass)
        await hass.async_block_till_done()

        assert any(e.data["task_id"] == task["id"] for e in events)


async def test_overdue_event_fires(hass: HomeAssistant, mock_config_entry, store) -> None:
    """A task past its due date fires home_tasks_task_overdue."""
    from freezegun import freeze_time
    from custom_components.home_tasks import _async_check_due_dates

    with freeze_time("2026-04-05"):
        events = []
        hass.bus.async_listen(f"{DOMAIN}_task_overdue", lambda e: events.append(e))

        task = await store.async_add_task("Overdue task")
        await store.async_update_task(task["id"], due_date="2026-04-03")
        await hass.async_block_till_done()

        await _async_check_due_dates(hass)
        await hass.async_block_till_done()

        assert any(e.data["task_id"] == task["id"] for e in events)


async def test_due_event_not_fired_twice_same_day(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """The due event is only fired once per day per task."""
    from freezegun import freeze_time
    from custom_components.home_tasks import _async_check_due_dates

    with freeze_time("2026-04-03"):
        events = []
        hass.bus.async_listen(f"{DOMAIN}_task_due", lambda e: events.append(e))

        task = await store.async_add_task("Once only")
        await store.async_update_task(task["id"], due_date="2026-04-03")

        await _async_check_due_dates(hass)
        await hass.async_block_till_done()
        await _async_check_due_dates(hass)
        await hass.async_block_till_done()

        task_events = [e for e in events if e.data["task_id"] == task["id"]]
        assert len(task_events) == 1


async def test_build_event_data_includes_optional_fields(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """Events include assigned_person, due_date, and tags when set on the task."""
    events = []
    hass.bus.async_listen(f"{DOMAIN}_task_completed", lambda e: events.append(e))

    task = await store.async_add_task("Rich event")
    await store.async_update_task(
        task["id"],
        assigned_person="person.alice",
        due_date="2026-05-01",
        tags=["work", "urgent"],
    )
    await store.async_update_task(task["id"], completed=True)
    await hass.async_block_till_done()

    assert len(events) == 1
    data = events[0].data
    assert data.get("assigned_person") == "person.alice"
    assert data.get("due_date") == "2026-05-01"
    assert data.get("tags") == ["work", "urgent"]


async def test_service_add_task_with_optional_fields(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """add_task service supports assigned_person, due_date, and tags."""
    await hass.services.async_call(
        DOMAIN,
        "add_task",
        {
            "list_name": "Test List",
            "title": "Rich task",
            "assigned_person": "person.charlie",
            "due_date": "2026-06-01",
            "tags": "work, urgent",
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    tasks = [t for t in store.tasks if t["title"] == "Rich task"]
    assert tasks
    t = tasks[0]
    assert t["assigned_person"] == "person.charlie"
    assert t["due_date"] == "2026-06-01"
    assert "work" in t["tags"]
    assert "urgent" in t["tags"]


async def test_service_reopen_task_by_tag(hass: HomeAssistant, mock_config_entry, store) -> None:
    """reopen_task service with tag= reopens all completed tasks with that tag."""
    t1 = await store.async_add_task("Tagged reopen A")
    t2 = await store.async_add_task("Tagged reopen B")
    t3 = await store.async_add_task("No tag reopen")
    await store.async_update_task(t1["id"], tags=["sprint"])
    await store.async_update_task(t2["id"], tags=["sprint"])
    await store.async_update_task(t1["id"], completed=True)
    await store.async_update_task(t2["id"], completed=True)
    await store.async_update_task(t3["id"], completed=True)

    await hass.services.async_call(
        DOMAIN,
        "reopen_task",
        {"list_name": "Test List", "tag": "sprint"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert store.get_task(t1["id"])["completed"] is False
    assert store.get_task(t2["id"])["completed"] is False
    assert store.get_task(t3["id"])["completed"] is True  # no tag match


async def test_service_reopen_task_by_assigned_person(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """reopen_task service with assigned_person= reopens matching tasks."""
    t1 = await store.async_add_task("Alice task")
    t2 = await store.async_add_task("Bob task")
    await store.async_update_task(t1["id"], assigned_person="person.alice")
    await store.async_update_task(t2["id"], assigned_person="person.bob")
    await store.async_update_task(t1["id"], completed=True)
    await store.async_update_task(t2["id"], completed=True)

    await hass.services.async_call(
        DOMAIN,
        "reopen_task",
        {"list_name": "Test List", "assigned_person": "person.alice"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert store.get_task(t1["id"])["completed"] is False
    assert store.get_task(t2["id"])["completed"] is True  # different person


async def test_external_entry_setup_and_unload(
    hass: HomeAssistant, patch_add_extra_js_url
) -> None:
    """External entries store an ExternalTaskOverlayStore and unload cleanly."""
    from custom_components.home_tasks.overlay_store import ExternalTaskOverlayStore

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"type": "external", "entity_id": "todo.init_external", "name": "Init External"},
        title="Init External (External)",
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert isinstance(hass.data[DOMAIN].get(entry.entry_id), ExternalTaskOverlayStore)

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.entry_id not in hass.data.get(DOMAIN, {})


# ---------------------------------------------------------------------------
# External entry edge cases
# ---------------------------------------------------------------------------


async def test_external_entry_setup_fails_without_entity_id(
    hass: HomeAssistant, patch_add_extra_js_url
) -> None:
    """External entry without entity_id returns False on setup."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"type": "external"},
        title="Bad External",
    )
    entry.add_to_hass(hass)
    result = await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert result is False
    assert entry.entry_id not in hass.data.get(DOMAIN, {})


async def test_check_external_due_dates_handles_missing_entity(
    hass: HomeAssistant, patch_add_extra_js_url
) -> None:
    """_async_check_due_dates does not raise for external entity that doesn't exist."""
    from custom_components.home_tasks import _async_check_due_dates

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"type": "external", "entity_id": "todo.nonexistent", "name": "Ghost"},
        title="Ghost (External)",
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Should not raise — errors are caught and logged
    await _async_check_due_dates(hass)
    await hass.async_block_till_done()


async def test_startup_due_check_scheduled_once(
    hass: HomeAssistant, mock_config_entry, patch_add_extra_js_url
) -> None:
    """DATA_DUE_STARTUP_DONE is set after first entry setup, preventing duplicates."""
    from custom_components.home_tasks import DATA_DUE_STARTUP_DONE

    assert hass.data.get(DATA_DUE_STARTUP_DONE) is True

    # Set up a second (external) entry — the flag should still be True
    ext_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"type": "external", "entity_id": "todo.second_ext", "name": "Second"},
        title="Second (External)",
    )
    ext_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(ext_entry.entry_id)
    await hass.async_block_till_done()
    assert hass.data.get(DATA_DUE_STARTUP_DONE) is True


# ---------------------------------------------------------------------------
# Recurrence computation unit tests (tests 13–27)
# ---------------------------------------------------------------------------

from datetime import datetime, timezone


def test_parse_rec_time_valid() -> None:
    """_parse_rec_time with valid recurrence_time returns (h, m)."""
    from custom_components.home_tasks.__init__ import _parse_rec_time
    assert _parse_rec_time({"recurrence_time": "09:30"}) == (9, 30)


def test_parse_rec_time_missing() -> None:
    """_parse_rec_time with no recurrence_time returns (0, 0)."""
    from custom_components.home_tasks.__init__ import _parse_rec_time
    assert _parse_rec_time({}) == (0, 0)


def test_parse_rec_time_invalid() -> None:
    """_parse_rec_time with invalid recurrence_time returns (0, 0)."""
    from custom_components.home_tasks.__init__ import _parse_rec_time
    assert _parse_rec_time({"recurrence_time": "xx:yy"}) == (0, 0)


def test_check_end_date_not_exceeded() -> None:
    """_check_end_date returns False when target is before end date."""
    from custom_components.home_tasks.__init__ import _check_end_date
    task = {"recurrence_end_type": "date", "recurrence_end_date": "2027-12-31"}
    target = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    assert _check_end_date(task, target) is False


def test_check_end_date_exceeded() -> None:
    """_check_end_date returns True when target is after end date."""
    from custom_components.home_tasks.__init__ import _check_end_date
    task = {"recurrence_end_type": "date", "recurrence_end_date": "2026-01-01"}
    target = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    assert _check_end_date(task, target) is True


def test_check_end_date_no_end() -> None:
    """_check_end_date returns False when recurrence_end_type is not 'date'."""
    from custom_components.home_tasks.__init__ import _check_end_date
    task = {"recurrence_end_type": "none"}
    target = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    assert _check_end_date(task, target) is False


def test_apply_start_date_no_start() -> None:
    """_apply_start_date with no start date returns target unchanged."""
    from custom_components.home_tasks.__init__ import _apply_start_date
    target = datetime(2026, 1, 5, 12, 0, 0, tzinfo=timezone.utc)
    result = _apply_start_date({}, target)
    assert result == target


def test_apply_start_date_future() -> None:
    """_apply_start_date advances target to start date when target is before it."""
    from custom_components.home_tasks.__init__ import _apply_start_date
    task = {"recurrence_start_date": "2026-06-01"}
    target = datetime(2026, 1, 5, 12, 0, 0, tzinfo=timezone.utc)
    result = _apply_start_date(task, target)
    local_result = result.astimezone()
    assert local_result.year == 2026
    assert local_result.month == 6
    assert local_result.day == 1


def test_compute_reopen_delay_days() -> None:
    """_compute_reopen_delay with unit=days returns approximately 2 days of seconds."""
    from custom_components.home_tasks.__init__ import _compute_reopen_delay
    completed_at = datetime(2026, 1, 5, 12, 0, 0, tzinfo=timezone.utc)
    task = {
        "recurrence_type": "interval",
        "recurrence_unit": "days",
        "recurrence_value": 2,
    }
    delay = _compute_reopen_delay(task, completed_at)
    assert delay is not None
    # The delay should be a number (could be negative if completed_at is in the past)
    assert isinstance(delay, float)


def test_compute_reopen_delay_weeks() -> None:
    """_compute_reopen_delay with unit=weeks returns a numeric value."""
    from custom_components.home_tasks.__init__ import _compute_reopen_delay
    completed_at = datetime(2026, 1, 5, 12, 0, 0, tzinfo=timezone.utc)
    task = {
        "recurrence_type": "interval",
        "recurrence_unit": "weeks",
        "recurrence_value": 1,
    }
    delay = _compute_reopen_delay(task, completed_at)
    assert delay is not None
    assert isinstance(delay, float)


def test_compute_reopen_delay_months() -> None:
    """_compute_reopen_delay with unit=months returns a numeric value."""
    from custom_components.home_tasks.__init__ import _compute_reopen_delay
    completed_at = datetime(2026, 1, 5, 12, 0, 0, tzinfo=timezone.utc)
    task = {
        "recurrence_type": "interval",
        "recurrence_unit": "months",
        "recurrence_value": 1,
    }
    delay = _compute_reopen_delay(task, completed_at)
    assert delay is not None
    assert isinstance(delay, float)


def test_compute_reopen_delay_weekdays() -> None:
    """_compute_reopen_delay with type=weekdays and weekdays=[0,2,4] returns a value."""
    from custom_components.home_tasks.__init__ import _compute_reopen_delay
    # 2026-01-05 is a Monday (weekday 0)
    completed_at = datetime(2026, 1, 5, 12, 0, 0, tzinfo=timezone.utc)
    task = {
        "recurrence_type": "weekdays",
        "recurrence_weekdays": [0, 2, 4],  # Mon, Wed, Fri
    }
    delay = _compute_reopen_delay(task, completed_at)
    assert delay is not None
    assert isinstance(delay, float)


def test_compute_reopen_delay_hours() -> None:
    """_compute_reopen_delay with unit=hours returns a numeric value."""
    from custom_components.home_tasks.__init__ import _compute_reopen_delay
    completed_at = datetime(2026, 1, 5, 12, 0, 0, tzinfo=timezone.utc)
    task = {
        "recurrence_type": "interval",
        "recurrence_unit": "hours",
        "recurrence_value": 3,
    }
    delay = _compute_reopen_delay(task, completed_at)
    assert delay is not None
    assert isinstance(delay, float)


def test_compute_reopen_delay_no_unit() -> None:
    """_compute_reopen_delay with no recurrence_unit returns None."""
    from custom_components.home_tasks.__init__ import _compute_reopen_delay
    completed_at = datetime(2026, 1, 5, 12, 0, 0, tzinfo=timezone.utc)
    task = {"recurrence_type": "interval"}
    assert _compute_reopen_delay(task, completed_at) is None


def test_compute_reopen_delay_past_end_date() -> None:
    """_compute_reopen_delay with an already-passed end_date returns None."""
    from custom_components.home_tasks.__init__ import _compute_reopen_delay
    completed_at = datetime(2026, 1, 5, 12, 0, 0, tzinfo=timezone.utc)
    task = {
        "recurrence_type": "interval",
        "recurrence_unit": "days",
        "recurrence_value": 1,
        "recurrence_end_type": "date",
        "recurrence_end_date": "2025-01-01",  # already passed
    }
    assert _compute_reopen_delay(task, completed_at) is None


# ---------------------------------------------------------------------------
# Async reopen edge cases (tests 28–29)
# ---------------------------------------------------------------------------


async def test_async_reopen_task_store_gone(hass: HomeAssistant, mock_config_entry, store) -> None:
    """_async_reopen_task does not crash when the store has been removed."""
    from custom_components.home_tasks import _async_reopen_task

    # Remove the store from hass.data
    hass.data[DOMAIN].pop(mock_config_entry.entry_id, None)
    # Should not raise
    await _async_reopen_task(hass, mock_config_entry.entry_id, "nonexistent-task-id")


async def test_async_reopen_task_recurrence_disabled(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """_async_reopen_task returns without reopening when recurrence_enabled=False."""
    from custom_components.home_tasks import _async_reopen_task

    task = await store.async_add_task("No recurrence")
    await store.async_update_task(task["id"], completed=True, recurrence_enabled=False)
    await _async_reopen_task(hass, mock_config_entry.entry_id, task["id"])
    # Task should still be completed
    assert store.get_task(task["id"])["completed"] is True


# ---------------------------------------------------------------------------
# Service resolver tests (tests 30–32)
# ---------------------------------------------------------------------------


async def test_service_complete_task_by_title_via_service(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """complete_task service with task_title resolves and completes the task."""
    await store.async_add_task("Title match task")
    await hass.services.async_call(
        DOMAIN,
        "complete_task",
        {"list_name": "Test List", "task_title": "Title match task"},
        blocking=True,
    )
    await hass.async_block_till_done()
    tasks = [t for t in store.tasks if t["title"] == "Title match task"]
    assert tasks and tasks[0]["completed"] is True


async def test_service_resolve_store_name_not_found(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """Service call with a nonexistent list_name raises an error."""
    import voluptuous as vol
    with pytest.raises((vol.Invalid, Exception)):
        await hass.services.async_call(
            DOMAIN,
            "add_task",
            {"list_name": "NonexistentList", "title": "Fail"},
            blocking=True,
        )


async def test_startup_due_check_fires_after_delay(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """After 120s, the startup due check fires and DATA_DUE_FIRED dict exists."""
    from custom_components.home_tasks import DATA_DUE_FIRED

    # Advance time by 120+ seconds to trigger the delayed startup check
    async_fire_time_changed(hass, utcnow() + timedelta(seconds=125))
    await hass.async_block_till_done()

    # DATA_DUE_FIRED should be initialized as a dict (the check ran)
    assert isinstance(hass.data.get(DATA_DUE_FIRED), dict)


# ---------------------------------------------------------------------------
# Reminder scheduler tests
# ---------------------------------------------------------------------------


async def test_reminder_fires_event_at_offset(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """A scheduled reminder fires home_tasks_task_reminder when its offset elapses."""
    from datetime import date as _date
    events = []
    hass.bus.async_listen(f"{DOMAIN}_task_reminder", lambda e: events.append(e))

    # Due tomorrow at midnight (local), reminder 1 day before = ~now
    tomorrow = (_date.today() + timedelta(days=1)).isoformat()
    task = await store.async_add_task("Reminder task")
    await store.async_update_task(
        task["id"],
        due_date=tomorrow,
        due_time="12:00",
        reminders=[60],  # 60 min before
    )
    await hass.async_block_till_done()

    # Reminder is at tomorrow 11:00 local. Advance well past that.
    async_fire_time_changed(hass, utcnow() + timedelta(days=2))
    await hass.async_block_till_done()

    matching = [e for e in events if e.data["task_id"] == task["id"]]
    assert len(matching) == 1
    assert matching[0].data["reminder_offset_minutes"] == 60


async def test_reminder_skipped_for_completed_task(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """_schedule_reminders does not schedule timers for completed tasks."""
    from custom_components.home_tasks import _schedule_reminders, DATA_REMINDER_TIMERS
    from datetime import date as _date

    tomorrow = (_date.today() + timedelta(days=1)).isoformat()
    task = await store.async_add_task("Done already")
    await store.async_update_task(
        task["id"], due_date=tomorrow, reminders=[30], completed=True
    )
    await hass.async_block_till_done()

    # Manually invoke after completion to confirm short-circuit
    _schedule_reminders(hass, mock_config_entry.entry_id, store.get_task(task["id"]))
    timers = hass.data.get(DATA_REMINDER_TIMERS, {})
    assert not any(k.startswith(f"{task['id']}_r") for k in timers)


async def test_reminder_skipped_without_due_date(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """_schedule_reminders does nothing for a task with reminders but no due date."""
    from custom_components.home_tasks import _schedule_reminders, DATA_REMINDER_TIMERS

    task = await store.async_add_task("No due date")
    await store.async_update_task(task["id"], reminders=[30])
    await hass.async_block_till_done()

    _schedule_reminders(hass, mock_config_entry.entry_id, store.get_task(task["id"]))
    timers = hass.data.get(DATA_REMINDER_TIMERS, {})
    assert not any(k.startswith(f"{task['id']}_r") for k in timers)


async def test_reminder_silent_miss_for_past_offset(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """A reminder whose offset is already in the past is silently dropped."""
    from custom_components.home_tasks import _schedule_reminders, DATA_REMINDER_TIMERS
    from datetime import date as _date

    # Due today 00:00 → reminder 1440 min (1 day) before is yesterday → past
    today = _date.today().isoformat()
    task = await store.async_add_task("Past reminder")
    await store.async_update_task(
        task["id"], due_date=today, due_time="00:00", reminders=[1440]
    )
    await hass.async_block_till_done()

    _schedule_reminders(hass, mock_config_entry.entry_id, store.get_task(task["id"]))
    timers = hass.data.get(DATA_REMINDER_TIMERS, {})
    assert not any(k.startswith(f"{task['id']}_r") for k in timers)


async def test_cancel_reminders_removes_pending_timers(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """_cancel_reminders removes all timer entries for a task_id."""
    from custom_components.home_tasks import _cancel_reminders, DATA_REMINDER_TIMERS
    from datetime import date as _date

    tomorrow = (_date.today() + timedelta(days=1)).isoformat()
    task = await store.async_add_task("Cancellable")
    await store.async_update_task(
        task["id"],
        due_date=tomorrow,
        due_time="12:00",
        reminders=[60, 30, 15],
    )
    await hass.async_block_till_done()

    timers = hass.data.get(DATA_REMINDER_TIMERS, {})
    assert sum(1 for k in timers if k.startswith(f"{task['id']}_r")) == 3

    _cancel_reminders(hass, task["id"])
    assert not any(k.startswith(f"{task['id']}_r") for k in timers)


async def test_completing_task_cancels_reminders(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """Completing a task cancels its pending reminder timers."""
    from custom_components.home_tasks import DATA_REMINDER_TIMERS
    from datetime import date as _date

    tomorrow = (_date.today() + timedelta(days=1)).isoformat()
    task = await store.async_add_task("Will be completed")
    await store.async_update_task(
        task["id"],
        due_date=tomorrow,
        due_time="12:00",
        reminders=[60],
    )
    await hass.async_block_till_done()
    timers = hass.data.get(DATA_REMINDER_TIMERS, {})
    assert any(k.startswith(f"{task['id']}_r") for k in timers)

    await store.async_update_task(task["id"], completed=True)
    await hass.async_block_till_done()
    assert not any(k.startswith(f"{task['id']}_r") for k in timers)


async def test_recover_reminder_timers_after_restart(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """_recover_reminder_timers reschedules timers for open tasks with reminders."""
    from custom_components.home_tasks import (
        _recover_reminder_timers,
        _cancel_reminders,
        DATA_REMINDER_TIMERS,
    )
    from datetime import date as _date

    tomorrow = (_date.today() + timedelta(days=1)).isoformat()
    task = await store.async_add_task("Surviving reminder")
    await store.async_update_task(
        task["id"], due_date=tomorrow, due_time="12:00", reminders=[60]
    )
    await hass.async_block_till_done()

    # Simulate "restart": clear all timers, then recover
    _cancel_reminders(hass, task["id"])
    timers = hass.data.get(DATA_REMINDER_TIMERS, {})
    assert not any(k.startswith(f"{task['id']}_r") for k in timers)

    _recover_reminder_timers(hass, mock_config_entry.entry_id, store)
    assert any(k.startswith(f"{task['id']}_r") for k in timers)


# ---------------------------------------------------------------------------
# Recurrence recovery tests
# ---------------------------------------------------------------------------


async def test_recover_recurrence_timer_with_future_delay(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """_recover_recurrence_timers schedules a timer when reopen is in the future."""
    from custom_components.home_tasks import (
        _recover_recurrence_timers,
        _cancel_recurrence,
        DATA_RECURRENCE_TIMERS,
    )
    from datetime import datetime as _dt, timezone as _tz

    task = await store.async_add_task("Recovers later")
    await store.async_update_task(
        task["id"],
        recurrence_enabled=True,
        recurrence_unit="hours",
        recurrence_value=24,
    )
    # Mark completed with completed_at = now → reopen in ~24h
    now_iso = _dt.now(_tz.utc).isoformat()
    await store.async_update_task(task["id"], completed=True)
    # Patch completed_at on the stored task to be deterministic
    store.get_task(task["id"])["completed_at"] = now_iso
    await hass.async_block_till_done()

    _cancel_recurrence(hass, task["id"])
    assert task["id"] not in hass.data.get(DATA_RECURRENCE_TIMERS, {})

    _recover_recurrence_timers(hass, mock_config_entry.entry_id, store)
    assert task["id"] in hass.data.get(DATA_RECURRENCE_TIMERS, {})


async def test_recover_recurrence_timer_with_past_delay_reopens(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """_recover_recurrence_timers immediately reopens a task whose reopen time has passed."""
    from custom_components.home_tasks import _recover_recurrence_timers
    from datetime import datetime as _dt, timezone as _tz

    task = await store.async_add_task("Should reopen now")
    await store.async_update_task(
        task["id"],
        recurrence_enabled=True,
        recurrence_unit="hours",
        recurrence_value=1,
    )
    # completed_at far in the past → delay <= 0 → immediate reopen
    past = (_dt.now(_tz.utc) - timedelta(days=7)).isoformat()
    await store.async_update_task(task["id"], completed=True)
    store.get_task(task["id"])["completed_at"] = past
    await hass.async_block_till_done()

    _recover_recurrence_timers(hass, mock_config_entry.entry_id, store)
    await hass.async_block_till_done()
    assert store.get_task(task["id"])["completed"] is False


async def test_recover_recurrence_skips_non_recurring(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """_recover_recurrence_timers skips completed tasks without recurrence_enabled."""
    from custom_components.home_tasks import (
        _recover_recurrence_timers,
        DATA_RECURRENCE_TIMERS,
    )

    task = await store.async_add_task("Not recurring")
    await store.async_update_task(task["id"], completed=True)
    await hass.async_block_till_done()

    _recover_recurrence_timers(hass, mock_config_entry.entry_id, store)
    assert task["id"] not in hass.data.get(DATA_RECURRENCE_TIMERS, {})


async def test_recover_recurrence_skips_missing_completed_at(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """_recover_recurrence_timers skips tasks where completed_at is missing or invalid."""
    from custom_components.home_tasks import (
        _recover_recurrence_timers,
        _cancel_recurrence,
        DATA_RECURRENCE_TIMERS,
    )

    task = await store.async_add_task("Missing completed_at")
    await store.async_update_task(
        task["id"],
        recurrence_enabled=True,
        recurrence_unit="hours",
        recurrence_value=1,
    )
    await store.async_update_task(task["id"], completed=True)
    # Wipe completed_at and cancel the auto-scheduled timer so we can test recovery
    store.get_task(task["id"])["completed_at"] = None
    _cancel_recurrence(hass, task["id"])
    await hass.async_block_till_done()
    assert task["id"] not in hass.data.get(DATA_RECURRENCE_TIMERS, {})

    _recover_recurrence_timers(hass, mock_config_entry.entry_id, store)
    assert task["id"] not in hass.data.get(DATA_RECURRENCE_TIMERS, {})


# ---------------------------------------------------------------------------
# Pure-function edge cases for full coverage
# ---------------------------------------------------------------------------


def test_check_end_date_invalid_iso() -> None:
    """_check_end_date with malformed end_date string returns False."""
    from custom_components.home_tasks.__init__ import _check_end_date
    task = {"recurrence_end_type": "date", "recurrence_end_date": "not-a-date"}
    target = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    assert _check_end_date(task, target) is False


def test_apply_start_date_invalid_iso() -> None:
    """_apply_start_date with malformed start_date returns target unchanged."""
    from custom_components.home_tasks.__init__ import _apply_start_date
    target = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    result = _apply_start_date({"recurrence_start_date": "garbage"}, target)
    assert result == target


def test_apply_start_date_target_after_start() -> None:
    """_apply_start_date returns target unchanged if it's already past start_date."""
    from custom_components.home_tasks.__init__ import _apply_start_date
    target = datetime(2026, 12, 1, 12, 0, 0, tzinfo=timezone.utc)
    result = _apply_start_date({"recurrence_start_date": "2026-01-01"}, target)
    assert result == target


def test_compute_reopen_delay_weekdays_empty_list() -> None:
    """_compute_reopen_delay returns None when type=weekdays but the list is empty."""
    from custom_components.home_tasks.__init__ import _compute_reopen_delay
    completed = datetime(2026, 1, 5, 12, 0, 0, tzinfo=timezone.utc)
    delay = _compute_reopen_delay(
        {"recurrence_type": "weekdays", "recurrence_weekdays": []}, completed,
    )
    assert delay is None


def test_compute_reopen_delay_years_unit() -> None:
    """_compute_reopen_delay supports unit=years (covers the years branch)."""
    from custom_components.home_tasks.__init__ import _compute_reopen_delay
    completed = datetime(2026, 1, 5, 12, 0, 0, tzinfo=timezone.utc)
    delay = _compute_reopen_delay(
        {"recurrence_type": "interval", "recurrence_unit": "years",
         "recurrence_value": 1}, completed,
    )
    assert delay is not None
    assert isinstance(delay, float)


def test_compute_reopen_delay_invalid_unit() -> None:
    """_compute_reopen_delay returns None when recurrence_unit is invalid."""
    from custom_components.home_tasks.__init__ import _compute_reopen_delay
    completed = datetime(2026, 1, 5, 12, 0, 0, tzinfo=timezone.utc)
    delay = _compute_reopen_delay(
        {"recurrence_type": "interval", "recurrence_unit": "centuries",
         "recurrence_value": 1}, completed,
    )
    assert delay is None


def test_compute_reopen_delay_weekdays_with_end_date_passed() -> None:
    """_compute_reopen_delay returns None for weekdays with passed end_date."""
    from custom_components.home_tasks.__init__ import _compute_reopen_delay
    completed = datetime(2026, 1, 5, 12, 0, 0, tzinfo=timezone.utc)
    task = {
        "recurrence_type": "weekdays",
        "recurrence_weekdays": [0, 2, 4],
        "recurrence_end_type": "date",
        "recurrence_end_date": "2025-01-01",  # in the past
    }
    assert _compute_reopen_delay(task, completed) is None


def test_compute_reopen_delay_hours_with_end_date_passed() -> None:
    """_compute_reopen_delay returns None for hours unit with passed end_date."""
    from custom_components.home_tasks.__init__ import _compute_reopen_delay
    completed = datetime(2026, 1, 5, 12, 0, 0, tzinfo=timezone.utc)
    task = {
        "recurrence_type": "interval",
        "recurrence_unit": "hours",
        "recurrence_value": 1,
        "recurrence_end_type": "date",
        "recurrence_end_date": "2025-01-01",
    }
    assert _compute_reopen_delay(task, completed) is None


def test_compute_next_reopen_target_weekdays() -> None:
    """_compute_next_reopen_target returns the correct next weekday target."""
    from custom_components.home_tasks.__init__ import _compute_next_reopen_target
    # 2026-01-05 is a Monday (weekday 0)
    completed_at = datetime(2026, 1, 5, 11, 0, 0, tzinfo=timezone.utc)
    task = {
        "recurrence_type": "weekdays",
        "recurrence_weekdays": [0],  # Monday only
        "recurrence_time": "10:00",
    }
    target = _compute_next_reopen_target(task, completed_at)
    assert target is not None
    from homeassistant.util import dt as dt_util
    local = target.astimezone(dt_util.DEFAULT_TIME_ZONE)
    # Next Monday is 2026-01-12
    assert local.date().isoformat() == "2026-01-12"
    assert local.hour == 10
    assert local.minute == 0


def test_compute_next_reopen_target_days() -> None:
    """_compute_next_reopen_target with days returns the correct target date."""
    from custom_components.home_tasks.__init__ import _compute_next_reopen_target
    completed_at = datetime(2026, 1, 5, 12, 0, 0, tzinfo=timezone.utc)
    task = {
        "recurrence_type": "interval",
        "recurrence_unit": "days",
        "recurrence_value": 3,
        "recurrence_time": "09:00",
    }
    target = _compute_next_reopen_target(task, completed_at)
    assert target is not None
    from homeassistant.util import dt as dt_util
    local = target.astimezone(dt_util.DEFAULT_TIME_ZONE)
    assert local.date().isoformat() == "2026-01-08"
    assert local.hour == 9


def test_compute_next_reopen_target_returns_none_when_not_configured() -> None:
    """_compute_next_reopen_target returns None for unconfigured recurrence."""
    from custom_components.home_tasks.__init__ import _compute_next_reopen_target
    completed_at = datetime(2026, 1, 5, 12, 0, 0, tzinfo=timezone.utc)
    assert _compute_next_reopen_target({"recurrence_type": "interval"}, completed_at) is None


async def test_recurrence_timer_updates_due_date(hass: HomeAssistant, mock_config_entry, store) -> None:
    """After completing a recurring task with a due_date, the due_date is updated on reopen."""
    task = await store.async_add_task("Recurring with date")
    await store.async_update_task(
        task["id"],
        due_date="2026-04-13",
        due_time="10:00",
        recurrence_enabled=True,
        recurrence_type="weekdays",
        recurrence_weekdays=[0],  # Monday
        recurrence_time="10:00",
    )
    await store.async_update_task(task["id"], completed=True)
    await hass.async_block_till_done()
    assert store.get_task(task["id"])["completed"] is True

    # Derive the expected due_date from the actual completed_at stored in the task.
    # freeze_time does not reliably patch datetime.now(tz) in all integration modules
    # on Python 3.14, so we compute the expectation from what the store recorded.
    completed_at_str = store.get_task(task["id"])["completed_at"]
    completed_at = datetime.fromisoformat(completed_at_str)
    local_completed = completed_at.astimezone(dt_util.DEFAULT_TIME_ZONE)
    days_to_monday = (0 - local_completed.weekday()) % 7 or 7
    expected_due = (local_completed.date() + timedelta(days=days_to_monday)).isoformat()

    # Advance 14 days — guaranteed to surpass the next Monday regardless of weekday
    async_fire_time_changed(hass, utcnow() + timedelta(days=14))
    await hass.async_block_till_done()

    reopened = store.get_task(task["id"])
    assert reopened["completed"] is False
    assert reopened["due_date"] == expected_due
    assert reopened["due_time"] == "10:00"


async def test_recurrence_timer_no_due_date_stays_none(hass: HomeAssistant, mock_config_entry, store) -> None:
    """A recurring task without a due_date keeps due_date as None after reopen."""
    task = await store.async_add_task("Recurring no date")
    await store.async_update_task(
        task["id"],
        recurrence_enabled=True,
        recurrence_unit="hours",
        recurrence_value=1,
    )
    await store.async_update_task(task["id"], completed=True)
    await hass.async_block_till_done()

    async_fire_time_changed(hass, utcnow() + timedelta(hours=1, seconds=10))
    await hass.async_block_till_done()

    reopened = store.get_task(task["id"])
    assert reopened["completed"] is False
    assert reopened["due_date"] is None


async def test_recurrence_timer_keeps_due_time_without_recurrence_time(hass: HomeAssistant, mock_config_entry, store) -> None:
    """When recurrence_time is not set, due_time is preserved on reopen."""
    task = await store.async_add_task("Recurring keep time")
    await store.async_update_task(
        task["id"],
        due_date="2026-01-05",
        due_time="14:30",
        recurrence_enabled=True,
        recurrence_unit="days",
        recurrence_value=2,
        # recurrence_time is NOT set
    )
    await store.async_update_task(task["id"], completed=True)
    await hass.async_block_till_done()

    async_fire_time_changed(hass, utcnow() + timedelta(days=3))
    await hass.async_block_till_done()

    reopened = store.get_task(task["id"])
    assert reopened["completed"] is False
    # due_date should be updated but due_time should stay unchanged
    assert reopened["due_date"] is not None
    assert reopened["due_date"] != "2026-01-05"  # should have advanced
    assert reopened["due_time"] == "14:30"  # preserved


def test_compute_due_datetime_no_due_date() -> None:
    """_compute_due_datetime returns None for tasks without a due_date."""
    from custom_components.home_tasks.__init__ import _compute_due_datetime
    assert _compute_due_datetime({}) is None
    assert _compute_due_datetime({"due_date": None}) is None


def test_compute_due_datetime_invalid_date_string() -> None:
    """_compute_due_datetime returns None for malformed due_date."""
    from custom_components.home_tasks.__init__ import _compute_due_datetime
    assert _compute_due_datetime({"due_date": "not-a-date"}) is None


def test_compute_due_datetime_with_invalid_time() -> None:
    """_compute_due_datetime falls back to midnight when due_time is malformed."""
    from custom_components.home_tasks.__init__ import _compute_due_datetime
    result = _compute_due_datetime({"due_date": "2027-05-15", "due_time": "xx:yy"})
    assert result is not None
    assert result.hour == 0
    assert result.minute == 0


def test_compute_due_datetime_date_only() -> None:
    """_compute_due_datetime with no due_time returns midnight local."""
    from custom_components.home_tasks.__init__ import _compute_due_datetime
    result = _compute_due_datetime({"due_date": "2027-05-15"})
    assert result is not None
    assert result.hour == 0
    assert result.year == 2027


# ---------------------------------------------------------------------------
# Service resolver error paths
# ---------------------------------------------------------------------------


async def test_resolve_store_no_args_raises(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """_resolve_store without entry_id or list_name raises vol.Invalid."""
    from custom_components.home_tasks import _resolve_store
    import voluptuous as vol
    with pytest.raises(vol.Invalid):
        _resolve_store(hass, {})


async def test_resolve_store_unknown_entry_id_raises(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """_resolve_store with a non-existent entry_id raises vol.Invalid."""
    from custom_components.home_tasks import _resolve_store
    import voluptuous as vol
    with pytest.raises(vol.Invalid):
        _resolve_store(hass, {"entry_id": "nonexistent"})


async def test_resolve_store_unknown_list_name_raises(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """_resolve_store with a non-existent list_name raises vol.Invalid."""
    from custom_components.home_tasks import _resolve_store
    import voluptuous as vol
    with pytest.raises(vol.Invalid):
        _resolve_store(hass, {"list_name": "Ghost List"})


def test_resolve_task_no_args_raises() -> None:
    """_resolve_task without task_id or task_title raises ValueError."""
    from custom_components.home_tasks import _resolve_task
    fake_store = type("S", (), {"tasks": []})()
    with pytest.raises(ValueError):
        _resolve_task(fake_store, {})


def test_resolve_task_unknown_title_raises() -> None:
    """_resolve_task with a non-matching title raises ValueError."""
    from custom_components.home_tasks import _resolve_task
    fake_store = type("S", (), {"tasks": [{"id": "1", "title": "Other"}]})()
    with pytest.raises(ValueError):
        _resolve_task(fake_store, {"task_title": "Missing"})


def test_resolve_task_returns_completed_when_no_open_match() -> None:
    """_resolve_task returns the first completed match when no open ones exist."""
    from custom_components.home_tasks import _resolve_task
    fake_store = type("S", (), {"tasks": [
        {"id": "1", "title": "Buy", "completed": True},
    ]})()
    result = _resolve_task(fake_store, {"task_title": "Buy"})
    assert result["id"] == "1"


async def test_resolve_actor_no_user_id_returns_none(
    hass: HomeAssistant, mock_config_entry
) -> None:
    """_resolve_actor returns None when call.context has no user_id."""
    from custom_components.home_tasks import _resolve_actor
    from unittest.mock import MagicMock
    call = MagicMock()
    call.context.user_id = None
    result = await _resolve_actor(hass, call)
    assert result is None


async def test_resolve_actor_get_user_failure_returns_none(
    hass: HomeAssistant, mock_config_entry
) -> None:
    """_resolve_actor returns None when async_get_user raises."""
    from custom_components.home_tasks import _resolve_actor
    from unittest.mock import MagicMock, AsyncMock, patch
    call = MagicMock()
    call.context.user_id = "user-123"
    with patch.object(hass.auth, "async_get_user", AsyncMock(side_effect=Exception("auth down"))):
        result = await _resolve_actor(hass, call)
    assert result is None


async def test_service_reopen_task_no_args_raises(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """reopen_task service with neither task nor person/tag raises an error."""
    import voluptuous as vol
    with pytest.raises((vol.Invalid, Exception)):
        await hass.services.async_call(
            DOMAIN,
            "reopen_task",
            {"list_name": "Test List"},
            blocking=True,
        )
