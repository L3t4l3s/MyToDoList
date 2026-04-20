"""Tests for the calendar platform entity."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

DOMAIN = "home_tasks"

pytestmark = pytest.mark.integration


def _get_calendar_entity_id(hass: HomeAssistant, entry_id: str) -> str | None:
    """Look up a calendar entity_id by config entry."""
    reg = er.async_get(hass)
    return reg.async_get_entity_id("calendar", DOMAIN, f"{entry_id}_calendar")


async def test_calendar_entity_registered(
    hass: HomeAssistant, mock_config_entry
) -> None:
    """A calendar entity is registered for native lists."""
    entity_id = _get_calendar_entity_id(hass, mock_config_entry.entry_id)
    assert entity_id is not None


async def test_calendar_not_created_for_external_entry(
    hass: HomeAssistant, patch_add_extra_js_url
) -> None:
    """External entries do not get a calendar entity."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    ext_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"type": "external", "entity_id": "todo.ext_cal", "name": "Ext"},
        title="Ext (External)",
    )
    ext_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(ext_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = _get_calendar_entity_id(hass, ext_entry.entry_id)
    assert entity_id is None


async def test_calendar_state_off_when_no_current_event(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """Calendar state is 'off' when no task has a due date near now."""
    await store.async_add_task("No due date")
    await hass.async_block_till_done()

    entity_id = _get_calendar_entity_id(hass, mock_config_entry.entry_id)
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "off"


async def test_calendar_event_property_returns_nearest(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """The event property returns the nearest upcoming task."""
    t_far = await store.async_add_task("Far away")
    await store.async_update_task(t_far["id"], due_date="2099-01-01")
    t_near = await store.async_add_task("Soon")
    await store.async_update_task(t_near["id"], due_date="2027-01-01")
    await hass.async_block_till_done()

    entity_id = _get_calendar_entity_id(hass, mock_config_entry.entry_id)
    entity_comp = hass.data.get("calendar")
    if entity_comp and hasattr(entity_comp, "get_entity"):
        entity = entity_comp.get_entity(entity_id)
        if entity:
            evt = entity.event
            assert evt is not None
            assert evt.summary == "Soon"


async def test_calendar_excludes_completed_tasks(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """Completed tasks do not appear as calendar events."""
    task = await store.async_add_task("Done task")
    await store.async_update_task(task["id"], due_date="2027-06-15", completed=True)
    await hass.async_block_till_done()

    entity_id = _get_calendar_entity_id(hass, mock_config_entry.entry_id)
    entity_comp = hass.data.get("calendar")
    if entity_comp and hasattr(entity_comp, "get_entity"):
        entity = entity_comp.get_entity(entity_id)
        if entity:
            assert entity.event is None


async def test_calendar_excludes_tasks_without_due(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """Tasks without due_date do not appear in the calendar."""
    await store.async_add_task("No due")
    await hass.async_block_till_done()

    entity_id = _get_calendar_entity_id(hass, mock_config_entry.entry_id)
    entity_comp = hass.data.get("calendar")
    if entity_comp and hasattr(entity_comp, "get_entity"):
        entity = entity_comp.get_entity(entity_id)
        if entity:
            assert entity.event is None


async def test_calendar_get_events_returns_tasks_in_range(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """async_get_events returns only tasks whose due date falls in range."""
    t_in = await store.async_add_task("In range")
    await store.async_update_task(t_in["id"], due_date="2027-06-15")
    t_out = await store.async_add_task("Out of range")
    await store.async_update_task(t_out["id"], due_date="2028-01-01")
    await hass.async_block_till_done()

    entity_id = _get_calendar_entity_id(hass, mock_config_entry.entry_id)
    entity_comp = hass.data.get("calendar")
    if entity_comp and hasattr(entity_comp, "get_entity"):
        entity = entity_comp.get_entity(entity_id)
        if entity:
            start = datetime(2027, 6, 1, tzinfo=timezone.utc)
            end = datetime(2027, 7, 1, tzinfo=timezone.utc)
            events = await entity.async_get_events(hass, start, end)
            summaries = [e.summary for e in events]
            assert "In range" in summaries
            assert "Out of range" not in summaries


async def test_calendar_timed_event_has_datetime_start(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """A task with due_time produces a timed CalendarEvent."""
    task = await store.async_add_task("Timed task")
    await store.async_update_task(task["id"], due_date="2027-06-15", due_time="14:30")
    await hass.async_block_till_done()

    entity_id = _get_calendar_entity_id(hass, mock_config_entry.entry_id)
    entity_comp = hass.data.get("calendar")
    if entity_comp and hasattr(entity_comp, "get_entity"):
        entity = entity_comp.get_entity(entity_id)
        if entity:
            start = datetime(2027, 6, 1, tzinfo=timezone.utc)
            end = datetime(2027, 7, 1, tzinfo=timezone.utc)
            events = await entity.async_get_events(hass, start, end)
            assert len(events) == 1
            evt = events[0]
            assert isinstance(evt.start, datetime)
            assert evt.start.hour == 14
            assert evt.start.minute == 30
            # End is 1 hour after start
            assert evt.end - evt.start == timedelta(hours=1)


async def test_calendar_allday_event_has_date_start(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """A task with only due_date produces an all-day CalendarEvent."""
    task = await store.async_add_task("All day")
    await store.async_update_task(task["id"], due_date="2027-06-15")
    await hass.async_block_till_done()

    entity_id = _get_calendar_entity_id(hass, mock_config_entry.entry_id)
    entity_comp = hass.data.get("calendar")
    if entity_comp and hasattr(entity_comp, "get_entity"):
        entity = entity_comp.get_entity(entity_id)
        if entity:
            start = datetime(2027, 6, 1, tzinfo=timezone.utc)
            end = datetime(2027, 7, 1, tzinfo=timezone.utc)
            events = await entity.async_get_events(hass, start, end)
            assert len(events) == 1
            evt = events[0]
            assert isinstance(evt.start, date)
            assert not isinstance(evt.start, datetime)
            assert evt.start == date(2027, 6, 15)
            assert evt.end == date(2027, 6, 16)  # all-day: end = next day


async def test_calendar_description_includes_notes(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """Notes appear in the event description."""
    task = await store.async_add_task("With notes")
    await store.async_update_task(task["id"], due_date="2027-06-15", notes="Remember this")
    await hass.async_block_till_done()

    entity_id = _get_calendar_entity_id(hass, mock_config_entry.entry_id)
    entity_comp = hass.data.get("calendar")
    if entity_comp and hasattr(entity_comp, "get_entity"):
        entity = entity_comp.get_entity(entity_id)
        if entity:
            start = datetime(2027, 6, 1, tzinfo=timezone.utc)
            end = datetime(2027, 7, 1, tzinfo=timezone.utc)
            events = await entity.async_get_events(hass, start, end)
            assert events
            assert "Remember this" in events[0].description


async def test_calendar_description_includes_metadata(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """Priority, tags, and sub-task progress appear in the description."""
    task = await store.async_add_task("Rich task")
    await store.async_update_task(
        task["id"],
        due_date="2027-06-15",
        priority=3,
        tags=["urgent", "work"],
    )
    await store.async_add_sub_task(task["id"], "Sub A")
    await hass.async_block_till_done()

    entity_id = _get_calendar_entity_id(hass, mock_config_entry.entry_id)
    entity_comp = hass.data.get("calendar")
    if entity_comp and hasattr(entity_comp, "get_entity"):
        entity = entity_comp.get_entity(entity_id)
        if entity:
            start = datetime(2027, 6, 1, tzinfo=timezone.utc)
            end = datetime(2027, 7, 1, tzinfo=timezone.utc)
            events = await entity.async_get_events(hass, start, end)
            assert events
            desc = events[0].description
            assert "High" in desc
            assert "#urgent" in desc
            assert "#work" in desc
            assert "Sub-tasks:" in desc


async def test_calendar_description_none_when_no_data(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """Tasks with no notes/metadata have description=None."""
    task = await store.async_add_task("Bare task")
    await store.async_update_task(task["id"], due_date="2027-06-15")
    await hass.async_block_till_done()

    entity_id = _get_calendar_entity_id(hass, mock_config_entry.entry_id)
    entity_comp = hass.data.get("calendar")
    if entity_comp and hasattr(entity_comp, "get_entity"):
        entity = entity_comp.get_entity(entity_id)
        if entity:
            start = datetime(2027, 6, 1, tzinfo=timezone.utc)
            end = datetime(2027, 7, 1, tzinfo=timezone.utc)
            events = await entity.async_get_events(hass, start, end)
            assert events
            assert events[0].description is None


async def test_calendar_updates_on_store_change(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """Calendar reflects store changes immediately via the listener."""
    entity_id = _get_calendar_entity_id(hass, mock_config_entry.entry_id)
    entity_comp = hass.data.get("calendar")
    if entity_comp and hasattr(entity_comp, "get_entity"):
        entity = entity_comp.get_entity(entity_id)
        if entity:
            assert entity.event is None

            task = await store.async_add_task("Appears")
            await store.async_update_task(task["id"], due_date="2099-01-01")
            await hass.async_block_till_done()

            assert entity.event is not None
            assert entity.event.summary == "Appears"
