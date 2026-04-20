"""Lightweight async Todoist REST API client.

Replaces ``todoist-api-python`` with a thin ``aiohttp``-based wrapper that
talks directly to the Todoist REST API v1.  This avoids version-specific
quirks in the library (renamed methods, missing parameters, async
generator vs. coroutine differences) and gives us full control over
every field the API supports.

Only the endpoints Home Tasks actually uses are implemented.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

_BASE_URL = "https://api.todoist.com/api/v1"
_TIMEOUT = aiohttp.ClientTimeout(total=30)


class TodoistAPIError(Exception):
    """Raised when the Todoist API returns an error response.

    Carries the API's error_code (e.g. 32 = PREMIUM_ONLY) so callers can
    distinguish recoverable limitations from real failures.
    """

    def __init__(self, status: int, error_code: int | None, message: str) -> None:
        super().__init__(f"Todoist API {status}: {message}")
        self.status = status
        self.error_code = error_code
        self.message = message

    @property
    def is_premium_only(self) -> bool:
        return self.error_code == 32 or self.status == 403


# ---------------------------------------------------------------------------
#  Lightweight data classes (only the fields we read)
# ---------------------------------------------------------------------------

@dataclass
class TodoistDue:
    """Parsed due-date information."""
    date: str | None = None           # "2026-04-10" or "2026-04-10T14:30:00Z"
    string: str | None = None         # "every monday at 9am"
    is_recurring: bool = False
    timezone: str | None = None

    @classmethod
    def from_dict(cls, data: dict | None) -> TodoistDue | None:
        if not data:
            return None
        return cls(
            date=data.get("date"),
            string=data.get("string"),
            is_recurring=data.get("is_recurring", False),
            timezone=data.get("timezone"),
        )


@dataclass
class TodoistTask:
    """Task returned by the Todoist API."""
    id: str = ""
    content: str = ""
    description: str = ""
    project_id: str = ""
    section_id: str | None = None
    parent_id: str | None = None
    order: int = 0
    priority: int = 1
    labels: list[str] = field(default_factory=list)
    due: TodoistDue | None = None
    assignee_id: str | None = None
    is_completed: bool = False
    # Todoist's unified API (api/v1) returns soft-deleted tasks through
    # GET /tasks/{id} with is_deleted=True (the list endpoint filters them).
    # We keep this so callers can reason about "really gone" vs. "still in
    # the API but marked deleted".
    is_deleted: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> TodoistTask:
        # Todoist's unified API (api/v1) reports completion via "checked"
        # (True/False); the older REST v2 used "is_completed".  Read both
        # so this works with whichever shape the server currently returns.
        completed = data.get("checked")
        if completed is None:
            completed = data.get("is_completed", False)
        return cls(
            id=str(data.get("id", "")),
            content=data.get("content", ""),
            description=data.get("description", ""),
            project_id=str(data.get("project_id", "")),
            section_id=str(data["section_id"]) if data.get("section_id") else None,
            parent_id=str(data["parent_id"]) if data.get("parent_id") else None,
            order=data.get("order") or data.get("child_order") or 0,
            priority=data.get("priority", 1),
            labels=data.get("labels") or [],
            due=TodoistDue.from_dict(data.get("due")),
            assignee_id=str(data["assignee_id"]) if data.get("assignee_id") else None,
            is_completed=bool(completed),
            is_deleted=bool(data.get("is_deleted", False)),
        )


@dataclass
class TodoistProject:
    """Project returned by the Todoist API."""
    id: str = ""
    name: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> TodoistProject:
        return cls(id=str(data.get("id", "")), name=data.get("name", ""))


@dataclass
class TodoistCollaborator:
    """Collaborator in a shared project."""
    id: str = ""
    name: str = ""
    email: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> TodoistCollaborator:
        return cls(
            id=str(data.get("id", "")),
            name=data.get("name", ""),
            email=data.get("email", ""),
        )


# ---------------------------------------------------------------------------
#  API Client
# ---------------------------------------------------------------------------

class TodoistAPIClient:
    """Async Todoist REST API client using ``aiohttp``.

    Uses the same Bearer-token authentication as the official library.
    Only implements the endpoints Home Tasks needs.
    """

    def __init__(self, token: str) -> None:
        self._token = token
        self._session: aiohttp.ClientSession | None = None

    # -- session management -------------------------------------------------

    def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=_TIMEOUT,
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "Content-Type": "application/json; charset=utf-8",
                },
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    # -- low-level helpers --------------------------------------------------

    async def _raise_for_status(self, resp: aiohttp.ClientResponse) -> None:
        """Convert HTTP errors into TodoistAPIError carrying the API's error_code."""
        if resp.status < 400:
            return
        body = await resp.text()
        error_code: int | None = None
        message = body
        try:
            payload = json.loads(body) if body else {}
            error_code = payload.get("error_code")
            message = payload.get("error") or payload.get("error_tag") or body
        except (ValueError, TypeError):
            pass
        raise TodoistAPIError(resp.status, error_code, message)

    async def _get(self, path: str, params: dict | None = None) -> Any:
        session = self._get_session()
        async with session.get(f"{_BASE_URL}/{path}", params=params) as resp:
            await self._raise_for_status(resp)
            return await resp.json()

    async def _post(self, path: str, data: dict | None = None) -> Any:
        session = self._get_session()
        payload = json.dumps(data) if data else None
        async with session.post(f"{_BASE_URL}/{path}", data=payload) as resp:
            await self._raise_for_status(resp)
            body = await resp.read()
            if body:
                return json.loads(body)
            return None

    async def _delete(self, path: str) -> None:
        session = self._get_session()
        async with session.delete(f"{_BASE_URL}/{path}") as resp:
            await self._raise_for_status(resp)

    # -- paginated GET (API returns cursor-based pagination) ----------------

    async def _get_all(self, path: str, params: dict | None = None) -> list[dict]:
        """Fetch all pages from a paginated endpoint."""
        results: list[dict] = []
        cursor: str | None = None
        while True:
            p = dict(params or {})
            if cursor:
                p["cursor"] = cursor
            data = await self._get(path, params=p)
            # API may return a list directly or a paginated response
            if isinstance(data, list):
                results.extend(data)
                break
            if isinstance(data, dict):
                items = data.get("results") or data.get("items") or []
                results.extend(items)
                cursor = data.get("next_cursor")
                if not cursor:
                    break
            else:
                break
        return results

    # -- Projects -----------------------------------------------------------

    async def get_projects(self) -> list[TodoistProject]:
        items = await self._get_all("projects")
        return [TodoistProject.from_dict(p) for p in items]

    # -- Collaborators ------------------------------------------------------

    async def get_collaborators(self, project_id: str) -> list[TodoistCollaborator]:
        items = await self._get_all(f"projects/{project_id}/collaborators")
        return [TodoistCollaborator.from_dict(c) for c in items]

    # -- Tasks --------------------------------------------------------------

    async def get_tasks(self, project_id: str | None = None) -> list[TodoistTask]:
        params: dict[str, str] = {}
        if project_id:
            params["project_id"] = project_id
        items = await self._get_all("tasks", params=params)
        return [TodoistTask.from_dict(t) for t in items]

    async def get_task(self, task_id: str) -> TodoistTask:
        data = await self._get(f"tasks/{task_id}")
        return TodoistTask.from_dict(data)

    async def add_task(self, **kwargs: Any) -> TodoistTask:
        """Create a task.  Accepts: content, description, project_id, priority,
        labels, due_string, due_date, due_datetime, assignee_id, parent_id, order."""
        data = _build_payload(kwargs)
        result = await self._post("tasks", data)
        return TodoistTask.from_dict(result)

    async def update_task(self, task_id: str, **kwargs: Any) -> TodoistTask | None:
        """Update a task.  Accepts all fields including order, assignee_id=None."""
        data = _build_payload(kwargs)
        if not data:
            return None
        result = await self._post(f"tasks/{task_id}", data)
        return TodoistTask.from_dict(result) if result else None

    async def complete_task(self, task_id: str) -> None:
        await self._post(f"tasks/{task_id}/close")

    async def uncomplete_task(self, task_id: str) -> None:
        await self._post(f"tasks/{task_id}/reopen")

    async def delete_task(self, task_id: str) -> None:
        await self._delete(f"tasks/{task_id}")

    # -- Reminders ----------------------------------------------------------

    async def get_reminders(self, task_id: str) -> list[dict]:
        """Get reminders for a task.  Returns raw dicts.

        Raises TodoistAPIError on real failures so callers can decide
        whether to retry, fall back, or surface the issue.
        """
        items = await self._get_all("reminders", params={"task_id": task_id})
        return items

    async def add_reminder(
        self,
        task_id: str,
        *,
        reminder_type: str = "relative",
        minute_offset: int | None = None,
        due_string: str | None = None,
        service: str = "push",
    ) -> dict | None:
        """Create a reminder.  Returns the created reminder dict.

        Raises TodoistAPIError(error_code=32) when the user's plan does not
        permit explicit reminders (Premium-only feature for non-zero offsets).
        """
        data: dict[str, Any] = {
            "task_id": task_id,
            "type": reminder_type,
            "service": service,
        }
        if minute_offset is not None:
            data["minute_offset"] = minute_offset
        if due_string is not None:
            data["due_string"] = due_string
        return await self._post("reminders", data)

    async def delete_reminder(self, reminder_id: str) -> None:
        """Delete a reminder.  Raises TodoistAPIError on failure."""
        await self._delete(f"reminders/{reminder_id}")


# ---------------------------------------------------------------------------
#  Payload builder
# ---------------------------------------------------------------------------

def _build_payload(kwargs: dict[str, Any]) -> dict[str, Any]:
    """Build a JSON-safe payload dict, converting dates and keeping None values."""
    data: dict[str, Any] = {}
    for key, value in kwargs.items():
        if value is None:
            # Explicitly include None — lets the API clear fields (e.g. assignee_id)
            data[key] = None
        elif isinstance(value, datetime):
            data[key] = value.strftime("%Y-%m-%dT%H:%M:%S")
        elif isinstance(value, date):
            data[key] = value.isoformat()
        else:
            data[key] = value
    return data
