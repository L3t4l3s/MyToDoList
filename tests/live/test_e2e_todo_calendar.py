"""Live E2E tests for the todo and calendar entities of native lists.

These test what the Companion App / Apple Watch actually sees: HA service
calls (todo.get_items, todo.add_item, calendar.get_events) against the
real running HA instance, not mocked Python objects.

Run with:  pytest -m live tests/live/test_e2e_todo_calendar.py
"""
from __future__ import annotations

import asyncio
from datetime import date, timedelta

import pytest

from .config import CONFIG
from .ws_client import HAWebSocketClient

pytestmark = [pytest.mark.live, pytest.mark.live_websocket]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _todo_get_items(ws: HAWebSocketClient, entity_id: str) -> list[dict]:
    """Read todo items via the standard todo.get_items service."""
    result = await ws.call_service(
        "todo", "get_items",
        {"entity_id": entity_id},
        return_response=True,
    )
    return (result or {}).get("response", {}).get(entity_id, {}).get("items", [])


async def _calendar_get_events(
    ws: HAWebSocketClient, entity_id: str, start: str, end: str
) -> list[dict]:
    """Read calendar events via the calendar.get_events service."""
    result = await ws.call_service(
        "calendar", "get_events",
        {"entity_id": entity_id, "start_date_time": start, "end_date_time": end},
        return_response=True,
    )
    return (result or {}).get("response", {}).get(entity_id, {}).get("events", [])


def _todo_entity_id() -> str:
    """Derive the todo entity_id from the configured native list name."""
    name = (CONFIG.native_list_name or "").lower().replace("-", "_").replace(" ", "_")
    return f"todo.{name}"


def _calendar_entity_id() -> str:
    """Derive the calendar entity_id from the configured native list name."""
    name = (CONFIG.native_list_name or "").lower().replace("-", "_").replace(" ", "_")
    return f"calendar.{name}_calendar"


# ---------------------------------------------------------------------------
# Todo entity — live round-trips
# ---------------------------------------------------------------------------


async def test_todo_add_item_round_trip(
    ws_client: HAWebSocketClient, clean_native_list: str
) -> None:
    """todo.add_item → todo.get_items shows the task."""
    entity_id = _todo_entity_id()
    await ws_client.call_service(
        "todo", "add_item",
        {"entity_id": entity_id, "item": "Live todo test"},
    )
    items = await _todo_get_items(ws_client, entity_id)
    assert any(i["summary"] == "Live todo test" for i in items)


async def test_todo_add_item_with_due_date(
    ws_client: HAWebSocketClient, clean_native_list: str
) -> None:
    """todo.add_item with due_date stores the date."""
    entity_id = _todo_entity_id()
    await ws_client.call_service(
        "todo", "add_item",
        {"entity_id": entity_id, "item": "Due task", "due_date": "2027-09-15"},
    )
    items = await _todo_get_items(ws_client, entity_id)
    item = next(i for i in items if i["summary"] == "Due task")
    assert item["due"] == "2027-09-15"


async def test_todo_add_item_with_due_datetime(
    ws_client: HAWebSocketClient, clean_native_list: str
) -> None:
    """todo.add_item with due_datetime stores both date and time."""
    entity_id = _todo_entity_id()
    await ws_client.call_service(
        "todo", "add_item",
        {"entity_id": entity_id, "item": "Timed task",
         "due_datetime": "2027-09-15 14:30:00"},
    )
    items = await _todo_get_items(ws_client, entity_id)
    item = next(i for i in items if i["summary"] == "Timed task")
    # The due field should contain a datetime string with the time
    assert "14:30" in item["due"]


async def test_todo_complete_sets_completed_timestamp(
    ws_client: HAWebSocketClient, clean_native_list: str
) -> None:
    """Completing a task via todo.update_item results in a completed status."""
    entity_id = _todo_entity_id()
    await ws_client.call_service(
        "todo", "add_item",
        {"entity_id": entity_id, "item": "Complete me live"},
    )
    items = await _todo_get_items(ws_client, entity_id)
    item = next(i for i in items if i["summary"] == "Complete me live")

    await ws_client.call_service(
        "todo", "update_item",
        {"entity_id": entity_id, "item": item["uid"], "status": "completed"},
    )
    items = await _todo_get_items(ws_client, entity_id)
    item = next(i for i in items if i["summary"] == "Complete me live")
    assert item["status"] == "completed"


async def test_todo_ws_then_todo_service_round_trip(
    ws_client: HAWebSocketClient, clean_native_list: str
) -> None:
    """Task created via WS home_tasks/add_task is visible via todo.get_items."""
    list_id = clean_native_list
    entity_id = _todo_entity_id()

    result = await ws_client.send_command(
        "home_tasks/add_task", list_id=list_id, title="WS to todo"
    )
    await ws_client.send_command(
        "home_tasks/update_task",
        list_id=list_id, task_id=result["id"],
        due_date="2027-07-01", due_time="10:00",
        notes="Cross-channel test", priority=2, tags=["live"],
    )

    items = await _todo_get_items(ws_client, entity_id)
    item = next(i for i in items if i["summary"] == "WS to todo")
    assert "10:00" in item["due"]
    assert item.get("description") == "Cross-channel test"


# ---------------------------------------------------------------------------
# Calendar entity — live round-trips
# ---------------------------------------------------------------------------


async def test_calendar_shows_task_with_due_date(
    ws_client: HAWebSocketClient, clean_native_list: str
) -> None:
    """A task with due_date appears in calendar.get_events."""
    list_id = clean_native_list
    cal_id = _calendar_entity_id()

    await ws_client.send_command(
        "home_tasks/add_task", list_id=list_id, title="Cal event"
    )
    tasks = (await ws_client.send_command(
        "home_tasks/get_tasks", list_id=list_id
    ))["tasks"]
    tid = next(t["id"] for t in tasks if t["title"] == "Cal event")
    await ws_client.send_command(
        "home_tasks/update_task",
        list_id=list_id, task_id=tid, due_date="2027-08-15",
    )

    events = await _calendar_get_events(
        ws_client, cal_id, "2027-08-01T00:00:00", "2027-09-01T00:00:00"
    )
    assert any(e["summary"] == "Cal event" for e in events)


async def test_calendar_timed_event(
    ws_client: HAWebSocketClient, clean_native_list: str
) -> None:
    """A task with due_date + due_time produces a timed calendar event."""
    list_id = clean_native_list
    cal_id = _calendar_entity_id()

    await ws_client.send_command(
        "home_tasks/add_task", list_id=list_id, title="Timed cal"
    )
    tasks = (await ws_client.send_command(
        "home_tasks/get_tasks", list_id=list_id
    ))["tasks"]
    tid = next(t["id"] for t in tasks if t["title"] == "Timed cal")
    await ws_client.send_command(
        "home_tasks/update_task",
        list_id=list_id, task_id=tid,
        due_date="2027-08-15", due_time="14:30",
    )

    events = await _calendar_get_events(
        ws_client, cal_id, "2027-08-01T00:00:00", "2027-09-01T00:00:00"
    )
    evt = next(e for e in events if e["summary"] == "Timed cal")
    # Timed events have T in the start string
    assert "T" in evt["start"]
    assert "14:30" in evt["start"]


async def test_calendar_excludes_completed(
    ws_client: HAWebSocketClient, clean_native_list: str
) -> None:
    """Completed tasks do not appear in calendar events."""
    list_id = clean_native_list
    cal_id = _calendar_entity_id()

    await ws_client.send_command(
        "home_tasks/add_task", list_id=list_id, title="Will complete"
    )
    tasks = (await ws_client.send_command(
        "home_tasks/get_tasks", list_id=list_id
    ))["tasks"]
    tid = next(t["id"] for t in tasks if t["title"] == "Will complete")
    await ws_client.send_command(
        "home_tasks/update_task",
        list_id=list_id, task_id=tid,
        due_date="2027-08-15", completed=True,
    )

    events = await _calendar_get_events(
        ws_client, cal_id, "2027-08-01T00:00:00", "2027-09-01T00:00:00"
    )
    assert not any(e["summary"] == "Will complete" for e in events)


async def test_calendar_excludes_no_due(
    ws_client: HAWebSocketClient, clean_native_list: str
) -> None:
    """Tasks without due_date do not appear in calendar events."""
    list_id = clean_native_list
    cal_id = _calendar_entity_id()

    await ws_client.send_command(
        "home_tasks/add_task", list_id=list_id, title="No due"
    )

    events = await _calendar_get_events(
        ws_client, cal_id, "2020-01-01T00:00:00", "2099-12-31T00:00:00"
    )
    assert not any(e["summary"] == "No due" for e in events)


async def test_calendar_rich_description(
    ws_client: HAWebSocketClient, clean_native_list: str
) -> None:
    """Calendar event description includes notes, priority, tags."""
    list_id = clean_native_list
    cal_id = _calendar_entity_id()

    await ws_client.send_command(
        "home_tasks/add_task", list_id=list_id, title="Rich cal"
    )
    tasks = (await ws_client.send_command(
        "home_tasks/get_tasks", list_id=list_id
    ))["tasks"]
    tid = next(t["id"] for t in tasks if t["title"] == "Rich cal")
    await ws_client.send_command(
        "home_tasks/update_task",
        list_id=list_id, task_id=tid,
        due_date="2027-08-15",
        notes="Important meeting",
        priority=3,
        tags=["meeting", "urgent"],
    )

    events = await _calendar_get_events(
        ws_client, cal_id, "2027-08-01T00:00:00", "2027-09-01T00:00:00"
    )
    evt = next(e for e in events if e["summary"] == "Rich cal")
    desc = evt.get("description", "")
    assert "Important meeting" in desc
    assert "High" in desc
    assert "#meeting" in desc
    assert "#urgent" in desc
