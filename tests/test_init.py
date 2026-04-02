"""Tests for integration setup, services, events, and timer mechanics."""
from __future__ import annotations

from datetime import timedelta

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.util.dt import utcnow
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

DOMAIN = "home_tasks"


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
