"""Data store for Home Tasks - per-entry storage."""

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
    MAX_REMINDER_OFFSET_MINUTES,
    MAX_REMINDERS_PER_TASK,
    MAX_SUB_TASKS_PER_TASK,
    MAX_TAG_LENGTH,
    MAX_TAGS_PER_TASK,
    MAX_TASKS_PER_LIST,
    MAX_TITLE_LENGTH,
    STORAGE_VERSION,
    VALID_RECURRENCE_UNITS,
)

_LOGGER = logging.getLogger(__name__)

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIME_PATTERN = re.compile(r"^\d{2}:\d{2}$")


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


def validate_date(value: str | None, field_name: str = "due_date") -> str | None:
    """Validate a date string (YYYY-MM-DD) or None."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string or null")
    value = value.strip()
    if not value:
        return None
    if not _DATE_PATTERN.match(value):
        raise ValueError(f"{field_name} must be in YYYY-MM-DD format")
    try:
        year, month, day = int(value[:4]), int(value[5:7]), int(value[8:10])
        if not (1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31):
            raise ValueError(f"{field_name} contains invalid date components")
    except (IndexError, TypeError) as err:
        raise ValueError(f"{field_name} must be in YYYY-MM-DD format") from err
    return value


def validate_time(value: str | None) -> str | None:
    """Validate a time string (HH:MM) or None."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("due_time must be a string or null")
    value = value.strip()
    if not value:
        return None
    if not _TIME_PATTERN.match(value):
        raise ValueError("due_time must be in HH:MM format")
    h, m = int(value[:2]), int(value[3:5])
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError("due_time contains invalid time components")
    return value


class HomeTasksStore:
    """Manage todo list data for a single list (one per config entry)."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        """Initialize the store."""
        self._store = Store(hass, STORAGE_VERSION, f"home_tasks_{entry_id}")
        self._data: dict | None = None
        self._listeners: list[Callable[[], None]] = []
        self.on_task_completed: Callable[[dict], None] | None = None
        self.on_task_created: Callable[[dict], None] | None = None
        self.on_task_deleted: Callable[[str], None] | None = None
        self.on_task_assigned: Callable[[dict, str | None], None] | None = None
        self.on_task_reopened: Callable[[dict], None] | None = None
        self.on_reminders_changed: Callable[[dict], None] | None = None

    def async_add_listener(self, callback: Callable[[], None]) -> Callable[[], None]:
        """Add a listener for data changes. Returns a removal callable."""
        self._listeners.append(callback)
        return lambda: self._listeners.remove(callback) if callback in self._listeners else None

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
            task.setdefault("priority", None)
            task.setdefault("due_time", None)
            task.setdefault("reminders", [])
            task.setdefault("recurrence_value", 1)
            task.setdefault("recurrence_unit", None)
            task.setdefault("recurrence_enabled", False)
            task.setdefault("recurrence_type", "interval")
            task.setdefault("recurrence_weekdays", [])
            task.setdefault("recurrence_time", None)
            task.setdefault("recurrence_end_type", "none")
            task.setdefault("recurrence_end_date", None)
            task.setdefault("recurrence_max_count", None)
            task.setdefault("recurrence_remaining_count", None)
            task.setdefault("completed_at", None)
            task.setdefault("assigned_person", None)
            task.setdefault("tags", [])

    async def _async_save(self) -> None:
        """Save data to disk."""
        await self._store.async_save(self._data)
        for listener in self._listeners:
            listener()

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
            "priority": None,
            "due_time": None,
            "reminders": [],
            "recurrence_value": 1,
            "recurrence_unit": None,
            "recurrence_enabled": False,
            "recurrence_type": "interval",
            "recurrence_weekdays": [],
            "recurrence_time": None,
            "recurrence_end_type": "none",
            "recurrence_end_date": None,
            "recurrence_max_count": None,
            "recurrence_remaining_count": None,
            "completed_at": None,
            "assigned_person": None,
            "tags": [],
        }
        self._data["tasks"].append(task)
        await self._async_save()
        if self.on_task_created:
            self.on_task_created(task)
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
            if kwargs["due_date"] is None:
                kwargs["due_time"] = None  # clear time when date is cleared
        if "due_time" in kwargs:
            kwargs["due_time"] = validate_time(kwargs["due_time"])
        if "completed" in kwargs and not isinstance(kwargs["completed"], bool):
            raise ValueError("completed must be a boolean")
        if "priority" in kwargs:
            val = kwargs["priority"]
            if val is not None and val not in (1, 2, 3):
                raise ValueError("priority must be 1 (low), 2 (medium), 3 (high), or null")
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
        if "recurrence_type" in kwargs:
            val = kwargs["recurrence_type"]
            if val not in ("interval", "weekdays"):
                raise ValueError("recurrence_type must be 'interval' or 'weekdays'")
        if "recurrence_weekdays" in kwargs:
            val = kwargs["recurrence_weekdays"]
            if not isinstance(val, list):
                raise ValueError("recurrence_weekdays must be a list")
            if not all(isinstance(d, int) and 0 <= d <= 6 for d in val):
                raise ValueError("recurrence_weekdays entries must be integers 0–6")
            kwargs["recurrence_weekdays"] = sorted(set(val))
        if "recurrence_time" in kwargs:
            kwargs["recurrence_time"] = validate_time(kwargs["recurrence_time"])
        if "recurrence_end_type" in kwargs:
            val = kwargs["recurrence_end_type"]
            if val not in ("none", "date", "count"):
                raise ValueError("recurrence_end_type must be 'none', 'date', or 'count'")
        if "recurrence_end_date" in kwargs:
            kwargs["recurrence_end_date"] = validate_date(kwargs["recurrence_end_date"], "recurrence_end_date")
        if "recurrence_max_count" in kwargs:
            val = kwargs["recurrence_max_count"]
            if val is not None and (not isinstance(val, int) or val < 1):
                raise ValueError("recurrence_max_count must be a positive integer or null")
        if "recurrence_remaining_count" in kwargs:
            val = kwargs["recurrence_remaining_count"]
            if val is not None and (not isinstance(val, int) or val < 0):
                raise ValueError("recurrence_remaining_count must be a non-negative integer or null")
        if "assigned_person" in kwargs:
            val = kwargs["assigned_person"]
            if val is not None and (not isinstance(val, str) or len(val) > MAX_TITLE_LENGTH):
                raise ValueError("assigned_person must be a string entity_id or null")
        if "tags" in kwargs:
            tags = kwargs["tags"]
            if not isinstance(tags, list):
                raise ValueError("tags must be a list")
            if len(tags) > MAX_TAGS_PER_TASK:
                raise ValueError(f"Maximum of {MAX_TAGS_PER_TASK} tags allowed")
            cleaned = []
            seen = set()
            for tag in tags:
                if not isinstance(tag, str):
                    raise ValueError("Each tag must be a string")
                tag = tag.strip().lower()
                if not tag:
                    continue
                if len(tag) > MAX_TAG_LENGTH:
                    raise ValueError(f"Tag exceeds maximum length of {MAX_TAG_LENGTH}")
                if tag not in seen:
                    cleaned.append(tag)
                    seen.add(tag)
            kwargs["tags"] = cleaned
        if "reminders" in kwargs:
            val = kwargs["reminders"]
            if not isinstance(val, list):
                raise ValueError("reminders must be a list")
            if len(val) > MAX_REMINDERS_PER_TASK:
                raise ValueError(f"Maximum of {MAX_REMINDERS_PER_TASK} reminders allowed")
            if not all(isinstance(r, int) and 0 <= r <= MAX_REMINDER_OFFSET_MINUTES for r in val):
                raise ValueError(f"Each reminder must be an integer between 0 and {MAX_REMINDER_OFFSET_MINUTES}")
            kwargs["reminders"] = sorted(set(val))

        was_completed = task.get("completed", False)
        previous_person = task.get("assigned_person")
        old_due_date = task.get("due_date")
        old_due_time = task.get("due_time")
        old_reminders = task.get("reminders", [])

        allowed = ("title", "completed", "notes", "due_date", "due_time", "priority", "reminders", "recurrence_value", "recurrence_unit", "recurrence_enabled", "recurrence_type", "recurrence_weekdays", "recurrence_time", "recurrence_end_type", "recurrence_end_date", "recurrence_max_count", "recurrence_remaining_count", "assigned_person", "tags")
        for key, value in kwargs.items():
            if key in allowed:
                task[key] = value

        # When max_count is set without an explicit remaining override, reset remaining to match
        if "recurrence_max_count" in kwargs and "recurrence_remaining_count" not in kwargs:
            task["recurrence_remaining_count"] = task.get("recurrence_max_count")

        # Track completed_at timestamp
        is_completed = task.get("completed", False)
        if is_completed and not was_completed:
            task["completed_at"] = datetime.now(timezone.utc).isoformat()
            # Decrement remaining recurrence count
            if task.get("recurrence_end_type") == "count" and task.get("recurrence_remaining_count") is not None:
                remaining = task["recurrence_remaining_count"] - 1
                task["recurrence_remaining_count"] = max(0, remaining)
                if remaining <= 0:
                    task["recurrence_enabled"] = False
            # Notify recurrence scheduler (only if still enabled after decrement)
            if self.on_task_completed and task.get("recurrence_enabled"):
                rec_type = task.get("recurrence_type", "interval")
                if rec_type == "weekdays" and task.get("recurrence_weekdays"):
                    self.on_task_completed(task)
                elif rec_type == "interval" and task.get("recurrence_unit"):
                    self.on_task_completed(task)
        elif not is_completed and was_completed:
            task["completed_at"] = None

        # Notify reminder scheduler when due date/time or reminders change
        if self.on_reminders_changed and (
            task.get("due_date") != old_due_date
            or task.get("due_time") != old_due_time
            or task.get("reminders", []) != old_reminders
        ):
            self.on_reminders_changed(task)

        # Notify about person assignment changes
        new_person = task.get("assigned_person")
        if new_person != previous_person and self.on_task_assigned:
            self.on_task_assigned(task, previous_person)

        await self._async_save()
        return task

    async def async_reopen_task(self, task_id: str) -> dict:
        """Reopen a completed task and reset its sub-tasks."""
        task = self.get_task(task_id)
        if not task.get("completed"):
            return task  # already open, nothing to do

        task["completed"] = False
        task["completed_at"] = None
        for sub in task.get("sub_items", []):
            sub["completed"] = False
        await self._async_save()

        if self.on_task_reopened:
            self.on_task_reopened(task)
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

    async def async_export_task(self, task_id: str) -> dict:
        """Remove a task from this list and return its data (for cross-list move)."""
        task = self.get_task(task_id)
        self._data["tasks"] = [t for t in self._data["tasks"] if t["id"] != task_id]
        await self._async_save()
        if self.on_task_deleted:
            self.on_task_deleted(task_id)
        return dict(task)

    async def async_import_task(self, task: dict) -> dict:
        """Insert an existing task dict into this list (for cross-list move)."""
        max_order = max((t["sort_order"] for t in self._data["tasks"]), default=-1)
        task = {**task, "sort_order": max_order + 1}
        self._data["tasks"].append(task)
        await self._async_save()
        if self.on_task_created:
            self.on_task_created(task)
        return task

    # --- Sub-task methods ---

    async def async_add_sub_task(self, task_id: str, title: str) -> dict:
        """Add a sub-task to a task."""
        title = validate_text(title, MAX_TITLE_LENGTH, "Sub-task title")
        task = self.get_task(task_id)
        if len(task["sub_items"]) >= MAX_SUB_TASKS_PER_TASK:
            raise ValueError(f"Maximum number of sub-tasks ({MAX_SUB_TASKS_PER_TASK}) reached")
        sub_task = {"id": str(uuid.uuid4()), "title": title, "completed": False}
        task["sub_items"].append(sub_task)
        await self._async_save()
        return sub_task

    async def async_update_sub_task(self, task_id: str, sub_task_id: str, **kwargs) -> dict:
        """Update a sub-task."""
        task = self.get_task(task_id)
        for sub in task["sub_items"]:
            if sub["id"] == sub_task_id:
                if "title" in kwargs:
                    kwargs["title"] = validate_text(kwargs["title"], MAX_TITLE_LENGTH, "Sub-task title")
                if "completed" in kwargs and not isinstance(kwargs["completed"], bool):
                    raise ValueError("completed must be a boolean")
                for key, value in kwargs.items():
                    if key in ("title", "completed"):
                        sub[key] = value
                await self._async_save()
                return sub
        raise ValueError("Sub-task not found")

    async def async_reorder_sub_tasks(self, task_id: str, sub_task_ids: list[str]) -> None:
        """Reorder sub-tasks within a task."""
        task = self.get_task(task_id)
        id_to_sub = {s["id"]: s for s in task["sub_items"]}
        task["sub_items"] = [id_to_sub[sid] for sid in sub_task_ids if sid in id_to_sub]
        await self._async_save()

    async def async_delete_sub_task(self, task_id: str, sub_task_id: str) -> None:
        """Delete a sub-task."""
        task = self.get_task(task_id)
        original_len = len(task["sub_items"])
        task["sub_items"] = [s for s in task["sub_items"] if s["id"] != sub_task_id]
        if len(task["sub_items"]) == original_len:
            raise ValueError("Sub-task not found")
        await self._async_save()
