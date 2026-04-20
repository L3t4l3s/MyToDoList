"""Unit tests for the lightweight Todoist REST API client.

Mocks aiohttp.ClientSession so the tests don't hit the real Todoist API
(those round-trips are covered by tests/live/test_provider_todoist.py).
"""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.home_tasks.todoist_api import (
    TodoistAPIClient,
    TodoistAPIError,
    TodoistCollaborator,
    TodoistDue,
    TodoistProject,
    TodoistTask,
    _build_payload,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# _build_payload helper
# ---------------------------------------------------------------------------


class TestBuildPayload:
    """_build_payload converts dates/datetimes and preserves Nones."""

    def test_empty(self):
        assert _build_payload({}) == {}

    def test_passes_strings_through(self):
        assert _build_payload({"content": "Buy milk"}) == {"content": "Buy milk"}

    def test_keeps_none_values(self):
        # None must be kept so the API can clear fields like assignee_id
        assert _build_payload({"assignee_id": None}) == {"assignee_id": None}

    def test_converts_date(self):
        from datetime import date
        result = _build_payload({"due_date": date(2027, 5, 15)})
        assert result["due_date"] == "2027-05-15"

    def test_converts_datetime(self):
        from datetime import datetime
        result = _build_payload({"due_datetime": datetime(2027, 5, 15, 9, 30)})
        assert result["due_datetime"] == "2027-05-15T09:30:00"


# ---------------------------------------------------------------------------
# Dataclass from_dict converters
# ---------------------------------------------------------------------------


class TestTodoistDueFromDict:
    def test_none_returns_none(self):
        assert TodoistDue.from_dict(None) is None

    def test_empty_returns_none(self):
        assert TodoistDue.from_dict({}) is None

    def test_full_data(self):
        d = TodoistDue.from_dict({
            "date": "2027-05-15T09:30:00",
            "string": "every day at 9am",
            "is_recurring": True,
            "timezone": "Europe/Berlin",
        })
        assert d.date == "2027-05-15T09:30:00"
        assert d.string == "every day at 9am"
        assert d.is_recurring is True
        assert d.timezone == "Europe/Berlin"

    def test_partial_data(self):
        d = TodoistDue.from_dict({"date": "2027-05-15"})
        assert d.date == "2027-05-15"
        assert d.string is None
        assert d.is_recurring is False


class TestTodoistTaskFromDict:
    def test_minimal(self):
        t = TodoistTask.from_dict({"id": 12345, "content": "Buy milk"})
        assert t.id == "12345"  # always cast to str
        assert t.content == "Buy milk"
        assert t.priority == 1
        assert t.labels == []
        assert t.due is None
        assert t.is_completed is False

    def test_full_with_due(self):
        t = TodoistTask.from_dict({
            "id": "abc",
            "content": "Test",
            "description": "Desc",
            "project_id": 999,
            "section_id": 111,
            "parent_id": 222,
            "order": 5,
            "priority": 4,
            "labels": ["urgent", "work"],
            "due": {"date": "2027-05-15", "is_recurring": False},
            "assignee_id": 7,
            "is_completed": True,
        })
        assert t.id == "abc"
        assert t.project_id == "999"
        assert t.section_id == "111"
        assert t.parent_id == "222"
        assert t.order == 5
        assert t.priority == 4
        assert t.labels == ["urgent", "work"]
        assert t.due is not None
        assert t.due.date == "2027-05-15"
        assert t.assignee_id == "7"
        assert t.is_completed is True

    def test_child_order_fallback(self):
        t = TodoistTask.from_dict({"id": "1", "content": "x", "child_order": 3})
        assert t.order == 3

    def test_no_section_or_parent_keeps_none(self):
        t = TodoistTask.from_dict({"id": "1", "content": "x"})
        assert t.section_id is None
        assert t.parent_id is None
        assert t.assignee_id is None


class TestTodoistProjectFromDict:
    def test_basic(self):
        p = TodoistProject.from_dict({"id": 42, "name": "Inbox"})
        assert p.id == "42"
        assert p.name == "Inbox"


class TestTodoistCollaboratorFromDict:
    def test_basic(self):
        c = TodoistCollaborator.from_dict({
            "id": 1, "name": "Alice", "email": "alice@example.com"
        })
        assert c.id == "1"
        assert c.name == "Alice"
        assert c.email == "alice@example.com"


# ---------------------------------------------------------------------------
# TodoistAPIError
# ---------------------------------------------------------------------------


class TestTodoistAPIError:
    def test_premium_only_by_error_code(self):
        err = TodoistAPIError(403, 32, "Premium only feature")
        assert err.is_premium_only is True

    def test_premium_only_by_status(self):
        err = TodoistAPIError(403, None, "Forbidden")
        assert err.is_premium_only is True

    def test_other_error_not_premium(self):
        err = TodoistAPIError(404, 19, "Not found")
        assert err.is_premium_only is False

    def test_message_in_str(self):
        err = TodoistAPIError(400, 19, "Required argument is missing")
        assert "Required argument is missing" in str(err)
        assert "400" in str(err)


# ---------------------------------------------------------------------------
# TodoistAPIClient — using a fully mocked aiohttp.ClientSession
# ---------------------------------------------------------------------------


class _MockResponse:
    """Minimal async-context-manager mock for aiohttp responses."""

    def __init__(self, status: int = 200, body: str = "", json_data=None):
        self.status = status
        self._body = body
        self._json = json_data

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def text(self):
        return self._body

    async def read(self):
        return self._body.encode() if isinstance(self._body, str) else self._body

    async def json(self):
        return self._json


class _MockSession:
    """Records get/post/delete calls and returns canned responses."""

    def __init__(self):
        self.closed = False
        self.calls: list[tuple[str, str, dict | None, str | None]] = []
        self._next: dict[str, _MockResponse] = {}

    def queue(self, method: str, response: _MockResponse) -> None:
        self._next[method.upper()] = response

    def get(self, url, params=None):
        self.calls.append(("GET", url, params, None))
        return self._next.get("GET", _MockResponse(200, "[]", []))

    def post(self, url, data=None):
        self.calls.append(("POST", url, None, data))
        return self._next.get("POST", _MockResponse(200, "{}", {}))

    def delete(self, url):
        self.calls.append(("DELETE", url, None, None))
        return self._next.get("DELETE", _MockResponse(204, "", None))

    async def close(self):
        self.closed = True


@pytest.fixture
def client_with_session():
    """Yields (TodoistAPIClient, _MockSession) — session is pre-installed."""
    session = _MockSession()
    client = TodoistAPIClient("fake-token")
    client._session = session  # type: ignore[assignment]
    return client, session


# ---------------------------------------------------------------------------
# Low-level _raise_for_status / _post / _get / _delete
# ---------------------------------------------------------------------------


class TestRaiseForStatus:
    """_raise_for_status converts HTTP errors to TodoistAPIError."""

    async def test_2xx_does_not_raise(self):
        client = TodoistAPIClient("tok")
        await client._raise_for_status(_MockResponse(200, ""))
        await client._raise_for_status(_MockResponse(201, ""))

    async def test_premium_only_400_extracts_error_code(self):
        client = TodoistAPIClient("tok")
        body = json.dumps({
            "error": "Premium only feature",
            "error_code": 32,
            "error_tag": "PREMIUM_ONLY",
        })
        with pytest.raises(TodoistAPIError) as exc_info:
            await client._raise_for_status(_MockResponse(403, body))
        assert exc_info.value.error_code == 32
        assert exc_info.value.is_premium_only is True
        assert "Premium only feature" in exc_info.value.message

    async def test_unparseable_body_uses_raw_text(self):
        client = TodoistAPIClient("tok")
        with pytest.raises(TodoistAPIError) as exc_info:
            await client._raise_for_status(_MockResponse(500, "Internal server error"))
        assert exc_info.value.message == "Internal server error"
        assert exc_info.value.error_code is None


class TestSession:
    """Session is created lazily and reused; close cleans up."""

    async def test_get_session_creates_once(self):
        client = TodoistAPIClient("tok")
        with patch("custom_components.home_tasks.todoist_api.aiohttp.ClientSession") as mock_session_cls:
            instance = MagicMock()
            instance.closed = False
            mock_session_cls.return_value = instance
            s1 = client._get_session()
            s2 = client._get_session()
            assert s1 is s2
            assert mock_session_cls.call_count == 1

    async def test_close_closes_session(self):
        client = TodoistAPIClient("tok")
        session = MagicMock()
        session.closed = False
        session.close = AsyncMock()
        client._session = session
        await client.close()
        session.close.assert_awaited_once()

    async def test_close_skips_if_no_session(self):
        client = TodoistAPIClient("tok")
        # Should not raise
        await client.close()


# ---------------------------------------------------------------------------
# High-level API methods
# ---------------------------------------------------------------------------


class TestProjectsCollaborators:
    """get_projects and get_collaborators."""

    async def test_get_projects_paginated_list(self, client_with_session):
        client, session = client_with_session
        session.queue("GET", _MockResponse(200, json_data=[
            {"id": 1, "name": "Inbox"},
            {"id": 2, "name": "Work"},
        ]))
        projects = await client.get_projects()
        assert len(projects) == 2
        assert projects[0].name == "Inbox"

    async def test_get_projects_paginated_dict(self, client_with_session):
        client, session = client_with_session
        session.queue("GET", _MockResponse(200, json_data={
            "results": [{"id": 1, "name": "P1"}],
            "next_cursor": None,
        }))
        projects = await client.get_projects()
        assert len(projects) == 1

    async def test_get_collaborators(self, client_with_session):
        client, session = client_with_session
        session.queue("GET", _MockResponse(200, json_data=[
            {"id": 1, "name": "Alice", "email": "a@x"},
        ]))
        collabs = await client.get_collaborators("proj-1")
        assert collabs[0].name == "Alice"
        # Confirm URL contains the project id
        assert "projects/proj-1/collaborators" in session.calls[0][1]


class TestTasks:
    """get_tasks / get_task / add_task / update_task / complete / uncomplete / delete."""

    async def test_get_tasks_with_project_filter(self, client_with_session):
        client, session = client_with_session
        session.queue("GET", _MockResponse(200, json_data=[
            {"id": "t1", "content": "First"},
        ]))
        tasks = await client.get_tasks(project_id="proj-1")
        assert tasks[0].id == "t1"
        # The project_id was passed as a query param
        assert session.calls[0][2] == {"project_id": "proj-1"}

    async def test_get_task_by_id(self, client_with_session):
        client, session = client_with_session
        session.queue("GET", _MockResponse(200, json_data={"id": "abc", "content": "X"}))
        task = await client.get_task("abc")
        assert task.id == "abc"
        assert "tasks/abc" in session.calls[0][1]

    async def test_add_task_returns_dataclass(self, client_with_session):
        client, session = client_with_session
        session.queue("POST", _MockResponse(200, "{}", json_data=None))
        # Override read() to return JSON bytes for the task
        resp = _MockResponse(200, json.dumps({"id": "new-1", "content": "Hi"}))
        session.queue("POST", resp)
        task = await client.add_task(content="Hi", project_id="p1")
        assert task.id == "new-1"
        assert task.content == "Hi"

    async def test_update_task_no_data_returns_none(self, client_with_session):
        client, session = client_with_session
        result = await client.update_task("t1")  # no fields
        assert result is None

    async def test_update_task_with_fields(self, client_with_session):
        client, session = client_with_session
        session.queue("POST", _MockResponse(
            200, json.dumps({"id": "t1", "content": "Updated"})
        ))
        task = await client.update_task("t1", content="Updated")
        assert task.content == "Updated"

    async def test_complete_task(self, client_with_session):
        client, session = client_with_session
        session.queue("POST", _MockResponse(204, ""))
        await client.complete_task("t1")
        assert session.calls[0] == ("POST", "https://api.todoist.com/api/v1/tasks/t1/close", None, None)

    async def test_uncomplete_task(self, client_with_session):
        client, session = client_with_session
        session.queue("POST", _MockResponse(204, ""))
        await client.uncomplete_task("t1")
        assert "tasks/t1/reopen" in session.calls[0][1]

    async def test_delete_task(self, client_with_session):
        client, session = client_with_session
        session.queue("DELETE", _MockResponse(204, ""))
        await client.delete_task("t1")
        assert session.calls[0][0] == "DELETE"
        assert "tasks/t1" in session.calls[0][1]


class TestReminders:
    """get_reminders / add_reminder / delete_reminder."""

    async def test_get_reminders_returns_list(self, client_with_session):
        client, session = client_with_session
        session.queue("GET", _MockResponse(200, json_data=[
            {"id": "r1", "minute_offset": 30},
        ]))
        result = await client.get_reminders("t1")
        assert len(result) == 1
        assert result[0]["minute_offset"] == 30

    async def test_get_reminders_passes_task_id_param(self, client_with_session):
        client, session = client_with_session
        session.queue("GET", _MockResponse(200, json_data=[]))
        await client.get_reminders("task-xyz")
        assert session.calls[0][2] == {"task_id": "task-xyz"}

    async def test_add_reminder_relative(self, client_with_session):
        client, session = client_with_session
        session.queue("POST", _MockResponse(200, json.dumps({"id": "r-new"})))
        result = await client.add_reminder("t1", minute_offset=60)
        assert result == {"id": "r-new"}

    async def test_add_reminder_premium_only_raises(self, client_with_session):
        client, session = client_with_session
        body = json.dumps({"error": "Premium only feature", "error_code": 32})
        session.queue("POST", _MockResponse(403, body))
        with pytest.raises(TodoistAPIError) as exc_info:
            await client.add_reminder("t1", minute_offset=60)
        assert exc_info.value.is_premium_only is True

    async def test_delete_reminder(self, client_with_session):
        client, session = client_with_session
        session.queue("DELETE", _MockResponse(204, ""))
        await client.delete_reminder("r1")
        assert "reminders/r1" in session.calls[0][1]


class TestPagination:
    """_get_all walks cursor-based responses until next_cursor is null."""

    async def test_single_page_dict_no_cursor(self, client_with_session):
        client, session = client_with_session
        session.queue("GET", _MockResponse(200, json_data={
            "results": [{"id": 1}, {"id": 2}],
            "next_cursor": None,
        }))
        items = await client._get_all("projects")
        assert len(items) == 2

    async def test_unexpected_response_breaks(self, client_with_session):
        client, session = client_with_session
        session.queue("GET", _MockResponse(200, json_data="unexpected string"))
        items = await client._get_all("projects")
        assert items == []
