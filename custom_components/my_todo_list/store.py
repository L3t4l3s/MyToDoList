"""Data store for My ToDo List - per-entry storage."""

from __future__ import annotations

import logging
import re
import uuid
from collections.abc import Callable
from datetime import datetime, timezone

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import (
    MAX_NOTES_LENGTH,
    MAX_RECURRENCE_VALUE,
    MAX_SUB_ITEMS_PER_TASK,
    MAX_TASKS_PER_LIST,
    MAX_TITLE_LENGTH,
    STORAGE_VERSION,
    VALID_RECURRENCE_UNITS,
)

_LOGGER = logging.getLogger(__name__)

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_text(value: str, max_length: int, field_name: str) -> str:
    """Validate and return a trimmed text field."""
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    value = value.strip()
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if len(value) > max_length:
        raise ValueError(f"{field_name} exceeds maximum length of {max_length}")
    return value


def validate_date(value: str | None) -> str | None:
    """Validate a date string (YYYY-MM-DD) or None."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("due_date must be a string or null")
    value = value.strip()
    if not value:
        return None
    if not _DATE_PATTERN.match(value):
        raise ValueError("due_date must be in YYYY-MM-DD format")
    try:
        year, month, day = int(value[:4]), int(value[5:7]), int(value[8:10])
        if not (1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31):
            raise ValueError("due_date contains invalid date components")
    except (IndexError, TypeError) as err:
        raise ValueError("due_date must be in YYYY-MM-DD format") from err
    return value


class MyToDoListStore:
    """Manage todo list data for a single list (one per config entry)."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        """Initialize the store."""
        self._store = Store(hass, STORAGE_VERSION, f"my_todo_list_{entry_id}")
        self._data: dict | None = None
        self.on_task_completed: Callable[[dict], None] | None = None
        self.on_task_deleted: Callable[[str], None] | None = None

    async def async_load(self) -> None:
        """Load data from disk."""
        data = await self._store.async_load()
        if data is None:
            self._data = {"tasks": []}
            await self._async_save()
        else:
            self._data = data
            self._backfill_recurrence_fields()

    def _backfill_recurrence_fields(self) -> None:
        """Add missing recurrence fields and migrate old format."""
        _MIGRATE = {
            "daily": (1, "days"),
            "weekly": (1, "weeks"),
            "biweekly": (2, "weeks"),
            "monthly": (1, "months"),
        }
        for task in self._data.get("tasks", []):
            # Migrate old recurrence_interval string to value + unit
            old = task.pop("recurrence_interval", None)
            if old and old in _MIGRATE and "recurrence_value" not in task:
                val, unit = _MIGRATE[old]
                task["recurrence_value"] = val
                task["recurrence_unit"] = unit
            task.setdefault("recurrence_value", 1)
            task.setdefault("recurrence_unit", None)
            task.setdefault("recurrence_enabled", False)
            task.setdefault("completed_at", None)

    async def _async_save(self) -> None:
        """Save data to disk."""
        await self._store.async_save(self._data)

    @property
    def tasks(self) -> list[dict]:
        """Return all tasks sorted by order."""
        return sorted(self._data["tasks"], key=lambda t: t["sort_order"])

    async def async_add_task(self, title: str) -> dict:
        """Add a task."""
        title = validate_text(title, MAX_TITLE_LENGTH, "Task title")
        if len(self._data["tasks"]) >= MAX_TASKS_PER_LIST:
            raise ValueError(f"Maximum number of tasks ({MAX_TASKS_PER_LIST}) reached")
        max_order = max((t["sort_order"] for t in self._data["tasks"]), default=-1)
        task = {
            "id": str(uuid.uuid4()),
            "title": title,
            "completed": False,
            "notes": "",
            "due_date": None,
            "sort_order": max_order + 1,
            "sub_items": [],
            "recurrence_value": 1,
            "recurrence_unit": None,
            "recurrence_enabled": False,
            "completed_at": None,
        }
        self._data["tasks"].append(task)
        await self._async_save()
        return task

    def get_task(self, task_id: str) -> dict:
        """Get a task by ID."""
        for task in self._data["tasks"]:
            if task["id"] == task_id:
                return task
        raise ValueError("Task not found")

    async def async_update_task(self, task_id: str, **kwargs) -> dict:
        """Update a task's fields."""
        task = self.get_task(task_id)
        if "title" in kwargs:
            kwargs["title"] = validate_text(kwargs["title"], MAX_TITLE_LENGTH, "Task title")
        if "notes" in kwargs:
            notes = kwargs["notes"]
            if not isinstance(notes, str):
                raise ValueError("Notes must be a string")
            if len(notes) > MAX_NOTES_LENGTH:
                raise ValueError(f"Notes exceed maximum length of {MAX_NOTES_LENGTH}")
        if "due_date" in kwargs:
            kwargs["due_date"] = validate_date(kwargs["due_date"])
        if "completed" in kwargs and not isinstance(kwargs["completed"], bool):
            raise ValueError("completed must be a boolean")
        if "recurrence_unit" in kwargs:
            val = kwargs["recurrence_unit"]
            if val is not None and val not in VALID_RECURRENCE_UNITS:
                raise ValueError(f"recurrence_unit must be one of {VALID_RECURRENCE_UNITS} or null")
        if "recurrence_value" in kwargs:
            val = kwargs["recurrence_value"]
            if not isinstance(val, int) or val < 1 or val > MAX_RECURRENCE_VALUE:
                raise ValueError(f"recurrence_value must be an integer between 1 and {MAX_RECURRENCE_VALUE}")
        if "recurrence_enabled" in kwargs and not isinstance(kwargs["recurrence_enabled"], bool):
            raise ValueError("recurrence_enabled must be a boolean")

        was_completed = task.get("completed", False)
        allowed = ("title", "completed", "notes", "due_date", "recurrence_value", "recurrence_unit", "recurrence_enabled")
        for key, value in kwargs.items():
            if key in allowed:
                task[key] = value

        # Track completed_at timestamp
        is_completed = task.get("completed", False)
        if is_completed and not was_completed:
            task["completed_at"] = datetime.now(timezone.utc).isoformat()
            # Notify recurrence scheduler
            if self.on_task_completed and task.get("recurrence_enabled") and task.get("recurrence_unit"):
                self.on_task_completed(task)
        elif not is_completed and was_completed:
            task["completed_at"] = None

        await self._async_save()
        return task

    async def async_delete_task(self, task_id: str) -> None:
        """Delete a task."""
        self.get_task(task_id)  # validate existence
        self._data["tasks"] = [t for t in self._data["tasks"] if t["id"] != task_id]
        if self.on_task_deleted:
            self.on_task_deleted(task_id)
        await self._async_save()

    async def async_reorder_tasks(self, task_ids: list[str]) -> None:
        """Reorder tasks."""
        if len(task_ids) > len(self._data["tasks"]):
            raise ValueError("Too many task IDs provided")
        task_map = {t["id"]: t for t in self._data["tasks"]}
        for index, tid in enumerate(task_ids):
            if tid in task_map:
                task_map[tid]["sort_order"] = index
        await self._async_save()

    # --- Sub-item methods ---

    async def async_add_sub_item(self, task_id: str, title: str) -> dict:
        """Add a sub-item to a task."""
        title = validate_text(title, MAX_TITLE_LENGTH, "Sub-item title")
        task = self.get_task(task_id)
        if len(task["sub_items"]) >= MAX_SUB_ITEMS_PER_TASK:
            raise ValueError(f"Maximum number of sub-items ({MAX_SUB_ITEMS_PER_TASK}) reached")
        sub_item = {"id": str(uuid.uuid4()), "title": title, "completed": False}
        task["sub_items"].append(sub_item)
        await self._async_save()
        return sub_item

    async def async_update_sub_item(self, task_id: str, sub_item_id: str, **kwargs) -> dict:
        """Update a sub-item."""
        task = self.get_task(task_id)
        for sub in task["sub_items"]:
            if sub["id"] == sub_item_id:
                if "title" in kwargs:
                    kwargs["title"] = validate_text(kwargs["title"], MAX_TITLE_LENGTH, "Sub-item title")
                if "completed" in kwargs and not isinstance(kwargs["completed"], bool):
                    raise ValueError("completed must be a boolean")
                for key, value in kwargs.items():
                    if key in ("title", "completed"):
                        sub[key] = value
                await self._async_save()
                return sub
        raise ValueError("Sub-item not found")

    async def async_delete_sub_item(self, task_id: str, sub_item_id: str) -> None:
        """Delete a sub-item."""
        task = self.get_task(task_id)
        original_len = len(task["sub_items"])
        task["sub_items"] = [s for s in task["sub_items"] if s["id"] != sub_item_id]
        if len(task["sub_items"]) == original_len:
            raise ValueError("Sub-item not found")
        await self._async_save()
