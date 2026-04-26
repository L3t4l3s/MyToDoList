"""Data store for Home Tasks - per-entry storage."""

from __future__ import annotations

import logging
import re
import uuid
from collections.abc import Callable
from datetime import datetime, timezone

_REOPEN_UNCHANGED = object()  # sentinel for "do not change this field"

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
    VALID_MONTH_PATTERNS,
    VALID_NTH_WEEK,
    VALID_RECURRENCE_UNITS,
)

_LOGGER = logging.getLogger(__name__)

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIME_PATTERN = re.compile(r"^\d{2}:\d{2}$")
_MMDD_PATTERN = re.compile(r"^\d{2}-\d{2}$")

_MAX_HISTORY = 50  # max history entries per task
_HISTORY_FIELDS = ("title", "due_date", "due_time", "priority", "assigned_person", "tags", "notes", "recurrence_enabled")


def _trim_history(hist: list) -> None:
    """Trim history in-place to _MAX_HISTORY entries."""
    if len(hist) > _MAX_HISTORY:
        del hist[:-_MAX_HISTORY]


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


# ---------------------------------------------------------------------------
# Per-field validators — shared between HomeTasksStore.async_update_task and
# ExternalTaskOverlayStore.async_set_overlay so the rules stay in one place.
# ---------------------------------------------------------------------------

def validate_notes(value):
    if not isinstance(value, str):
        raise ValueError("Notes must be a string")
    if len(value) > MAX_NOTES_LENGTH:
        raise ValueError(f"Notes exceed maximum length of {MAX_NOTES_LENGTH}")
    return value


def validate_priority(value):
    if value is not None and value not in (1, 2, 3):
        raise ValueError("priority must be 1 (low), 2 (medium), 3 (high), or null")
    return value


def validate_completed(value):
    if not isinstance(value, bool):
        raise ValueError("completed must be a boolean")
    return value


def validate_recurrence_unit(value):
    if value is not None and value not in VALID_RECURRENCE_UNITS:
        raise ValueError(f"recurrence_unit must be one of {VALID_RECURRENCE_UNITS} or null")
    return value


def validate_recurrence_value(value):
    if not isinstance(value, int) or value < 1 or value > MAX_RECURRENCE_VALUE:
        raise ValueError(f"recurrence_value must be an integer between 1 and {MAX_RECURRENCE_VALUE}")
    return value


def validate_recurrence_enabled(value):
    if not isinstance(value, bool):
        raise ValueError("recurrence_enabled must be a boolean")
    return value


def validate_recurrence_type(value):
    # "weekdays" is accepted for backward compatibility with old stored tasks;
    # new tasks always use "interval" — the legacy mode is normalised on load.
    if value not in ("interval", "weekdays"):
        raise ValueError("recurrence_type must be 'interval' or 'weekdays'")
    return value


def validate_recurrence_month_pattern(value):
    if value is not None and value not in VALID_MONTH_PATTERNS:
        raise ValueError(
            f"recurrence_month_pattern must be one of {VALID_MONTH_PATTERNS} or null"
        )
    return value


def validate_recurrence_day_of_month(value):
    if value is None:
        return None
    if value == "last":
        return value
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("recurrence_day_of_month must be an integer 1–31, 'last' or null")
    if not (1 <= value <= 31):
        raise ValueError("recurrence_day_of_month must be between 1 and 31")
    return value


def validate_recurrence_nth_week(value):
    if value is None:
        return None
    if value == "last":
        return value
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("recurrence_nth_week must be 1–4, 'last' or null")
    if value not in VALID_NTH_WEEK:
        raise ValueError(f"recurrence_nth_week must be one of {VALID_NTH_WEEK} or null")
    return value


def validate_recurrence_anniversary(value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("recurrence_anniversary must be a 'MM-DD' string or null")
    value = value.strip()
    if not value:
        return None
    if not _MMDD_PATTERN.match(value):
        raise ValueError("recurrence_anniversary must be in MM-DD format")
    month, day = int(value[:2]), int(value[3:5])
    if not (1 <= month <= 12 and 1 <= day <= 31):
        raise ValueError("recurrence_anniversary contains invalid month or day")
    # Reject impossible (month, day) combinations like 02-30 or 04-31, but
    # explicitly allow 02-29 (handled by leap-year clamping at compute time).
    import calendar as _cal
    max_day = _cal.monthrange(2024, month)[1]  # 2024 is a leap year → handles 02-29
    if day > max_day:
        raise ValueError(f"recurrence_anniversary {value} is not a valid calendar date")
    return value


def validate_recurrence_weekdays(value):
    if not isinstance(value, list):
        raise ValueError("recurrence_weekdays must be a list")
    if not all(isinstance(d, int) and 0 <= d <= 6 for d in value):
        raise ValueError("recurrence_weekdays entries must be integers 0–6")
    return sorted(set(value))


def validate_recurrence_end_type(value):
    if value not in ("none", "date", "count"):
        raise ValueError("recurrence_end_type must be 'none', 'date', or 'count'")
    return value


def validate_recurrence_max_count(value):
    if value is not None and (not isinstance(value, int) or value < 1):
        raise ValueError("recurrence_max_count must be a positive integer or null")
    return value


def validate_recurrence_remaining_count(value):
    if value is not None and (not isinstance(value, int) or value < 0):
        raise ValueError("recurrence_remaining_count must be a non-negative integer or null")
    return value


def validate_assigned_person(value):
    if value is not None and (not isinstance(value, str) or len(value) > MAX_TITLE_LENGTH):
        raise ValueError("assigned_person must be a string entity_id or null")
    return value


def validate_tags(value):
    if not isinstance(value, list):
        raise ValueError("tags must be a list")
    if len(value) > MAX_TAGS_PER_TASK:
        raise ValueError(f"Maximum of {MAX_TAGS_PER_TASK} tags allowed")
    cleaned: list[str] = []
    seen: set[str] = set()
    for tag in value:
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
    return cleaned


def validate_reminders(value):
    if not isinstance(value, list):
        raise ValueError("reminders must be a list")
    if len(value) > MAX_REMINDERS_PER_TASK:
        raise ValueError(f"Maximum of {MAX_REMINDERS_PER_TASK} reminders allowed")
    if not all(isinstance(r, int) and 0 <= r <= MAX_REMINDER_OFFSET_MINUTES for r in value):
        raise ValueError(f"Each reminder must be an integer between 0 and {MAX_REMINDER_OFFSET_MINUTES}")
    return sorted(set(value))


# Mapping field name → validator function. Used by both stores' update paths.
_FIELD_VALIDATORS = {
    "notes": validate_notes,
    "priority": validate_priority,
    "completed": validate_completed,
    "recurrence_unit": validate_recurrence_unit,
    "recurrence_value": validate_recurrence_value,
    "recurrence_enabled": validate_recurrence_enabled,
    "recurrence_type": validate_recurrence_type,
    "recurrence_weekdays": validate_recurrence_weekdays,
    "recurrence_month_pattern": validate_recurrence_month_pattern,
    "recurrence_day_of_month": validate_recurrence_day_of_month,
    "recurrence_nth_week": validate_recurrence_nth_week,
    "recurrence_anniversary": validate_recurrence_anniversary,
    "recurrence_end_type": validate_recurrence_end_type,
    "recurrence_max_count": validate_recurrence_max_count,
    "recurrence_remaining_count": validate_recurrence_remaining_count,
    "assigned_person": validate_assigned_person,
    "tags": validate_tags,
    "reminders": validate_reminders,
    "due_time": validate_time,
}


def apply_field_validators(kwargs: dict) -> None:
    """Run each validator on its field if present in kwargs (in-place)."""
    for field, validator in _FIELD_VALIDATORS.items():
        if field in kwargs:
            kwargs[field] = validator(kwargs[field])
    # Date fields use named validators with field_name kwarg
    if "due_date" in kwargs:
        kwargs["due_date"] = validate_date(kwargs["due_date"])
        if kwargs["due_date"] is None:
            kwargs["due_time"] = None  # clear time when date is cleared
    if "recurrence_start_date" in kwargs:
        kwargs["recurrence_start_date"] = validate_date(
            kwargs["recurrence_start_date"], "recurrence_start_date"
        )
    if "recurrence_end_date" in kwargs:
        kwargs["recurrence_end_date"] = validate_date(
            kwargs["recurrence_end_date"], "recurrence_end_date"
        )


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
            self._migrate_v1_to_v2()

    def _migrate_v1_to_v2(self) -> None:
        """Add external sync fields (v1 → v2)."""
        for task in self._data.get("tasks", []):
            task.setdefault("external_id", None)
            task.setdefault("sync_source", None)

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
            # Normalise legacy "weekdays" mode to interval+weeks (UI no longer
            # distinguishes the two; reopen logic now drives the weekday filter
            # off recurrence_weekdays alone).
            if task.get("recurrence_type") == "weekdays":
                task["recurrence_type"] = "interval"
                task["recurrence_unit"] = "weeks"
                task.setdefault("recurrence_value", 1)
            task.setdefault("priority", None)
            task.setdefault("due_time", None)
            task.setdefault("reminders", [])
            task.setdefault("recurrence_value", 1)
            task.setdefault("recurrence_unit", None)
            task.setdefault("recurrence_enabled", False)
            task.setdefault("recurrence_type", "interval")
            task.setdefault("recurrence_weekdays", [])
            task.setdefault("recurrence_start_date", None)
            task.setdefault("recurrence_time", None)
            task.setdefault("recurrence_end_type", "none")
            task.setdefault("recurrence_end_date", None)
            task.setdefault("recurrence_max_count", None)
            task.setdefault("recurrence_remaining_count", None)
            task.setdefault("recurrence_month_pattern", None)
            task.setdefault("recurrence_day_of_month", None)
            task.setdefault("recurrence_nth_week", None)
            task.setdefault("recurrence_anniversary", None)
            task.setdefault("completed_at", None)
            task.setdefault("assigned_person", None)
            task.setdefault("tags", [])
            task.setdefault("history", [])

    async def _async_save(self) -> None:
        """Save data to disk."""
        await self._store.async_save(self._data)
        for listener in self._listeners:
            listener()

    @property
    def tasks(self) -> list[dict]:
        """Return all tasks sorted by order."""
        return sorted(self._data["tasks"], key=lambda t: t["sort_order"])

    async def async_add_task(self, title: str, actor: str | None = None) -> dict:
        """Add a task."""
        title = validate_text(title, MAX_TITLE_LENGTH, "Task title")
        if len(self._data["tasks"]) >= MAX_TASKS_PER_LIST:
            raise ValueError(f"Maximum number of tasks ({MAX_TASKS_PER_LIST}) reached")
        max_order = max((t["sort_order"] for t in self._data["tasks"]), default=-1)
        created_entry: dict = {"ts": datetime.now(timezone.utc).isoformat(), "action": "created"}
        if actor:
            created_entry["by"] = actor
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
            "recurrence_start_date": None,
            "recurrence_time": None,
            "recurrence_end_type": "none",
            "recurrence_end_date": None,
            "recurrence_max_count": None,
            "recurrence_remaining_count": None,
            "recurrence_month_pattern": None,
            "recurrence_day_of_month": None,
            "recurrence_nth_week": None,
            "recurrence_anniversary": None,
            "completed_at": None,
            "assigned_person": None,
            "tags": [],
            "history": [created_entry],
            "external_id": None,
            "sync_source": None,
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

    _UPDATABLE_FIELDS = (
        "title", "completed", "notes", "due_date", "due_time", "priority",
        "reminders", "recurrence_value", "recurrence_unit", "recurrence_enabled",
        "recurrence_type", "recurrence_weekdays", "recurrence_start_date",
        "recurrence_time", "recurrence_end_type", "recurrence_end_date",
        "recurrence_max_count", "recurrence_remaining_count",
        "recurrence_month_pattern", "recurrence_day_of_month",
        "recurrence_nth_week", "recurrence_anniversary",
        "assigned_person", "tags",
    )

    async def async_update_task(self, task_id: str, actor: str | None = None, **kwargs) -> dict:
        """Update a task's fields."""
        task = self.get_task(task_id)
        self._validate_update_kwargs(kwargs)
        snapshot = self._snapshot_task(task)
        self._apply_field_updates(task, kwargs)
        self._handle_completion_transition(task, snapshot, kwargs)
        if any(k in kwargs for k in _HISTORY_FIELDS) or "completed" in kwargs:
            self._record_history(task, snapshot, kwargs, actor)
        self._fire_update_callbacks(task, snapshot)
        await self._async_save()
        return task

    @staticmethod
    def _validate_update_kwargs(kwargs: dict) -> None:
        """Validate every field present in kwargs and normalise list values in-place."""
        if "title" in kwargs:
            kwargs["title"] = validate_text(kwargs["title"], MAX_TITLE_LENGTH, "Task title")
        if "recurrence_time" in kwargs:
            kwargs["recurrence_time"] = validate_time(kwargs["recurrence_time"])
        apply_field_validators(kwargs)

    @staticmethod
    def _snapshot_task(task: dict) -> dict:
        """Capture pre-update field values for diffing in callbacks/history."""
        return {
            "completed": task.get("completed", False),
            "assigned_person": task.get("assigned_person"),
            "due_date": task.get("due_date"),
            "due_time": task.get("due_time"),
            "reminders": task.get("reminders", []),
            "title": task.get("title", ""),
            "priority": task.get("priority"),
            "tags": list(task.get("tags", [])),
            "notes": task.get("notes", ""),
            "recurrence_enabled": task.get("recurrence_enabled", False),
        }

    def _apply_field_updates(self, task: dict, kwargs: dict) -> None:
        """Copy validated kwargs into the task dict (whitelisted fields only)."""
        for key, value in kwargs.items():
            if key in self._UPDATABLE_FIELDS:
                task[key] = value
        # When max_count is set without an explicit remaining override, reset remaining to match
        if "recurrence_max_count" in kwargs and "recurrence_remaining_count" not in kwargs:
            task["recurrence_remaining_count"] = task.get("recurrence_max_count")

    def _handle_completion_transition(self, task: dict, snapshot: dict, kwargs: dict) -> None:
        """Update completed_at, decrement remaining recurrence count, fire callbacks."""
        was_completed = snapshot["completed"]
        is_completed = task.get("completed", False)
        if is_completed and not was_completed:
            task["completed_at"] = datetime.now(timezone.utc).isoformat()
            # Decrement remaining recurrence count
            if task.get("recurrence_end_type") == "count" and task.get("recurrence_remaining_count") is not None:
                remaining = task["recurrence_remaining_count"] - 1
                task["recurrence_remaining_count"] = max(0, remaining)
                if remaining <= 0:
                    task["recurrence_enabled"] = False
            # Notify: fires event + schedules recurrence (no-op if recurrence not configured)
            if self.on_task_completed:
                self.on_task_completed(task)
        elif not is_completed and was_completed:
            task["completed_at"] = None
            if self.on_task_reopened:
                self.on_task_reopened(task)

    # Field name → format of the history entry it should produce when changed.
    #   "from_to": include both from and to values
    #   "to_only": include only to (used for booleans like recurrence_enabled)
    #   "marker":  include neither (used when the actual value is sensitive, e.g. notes)
    _HISTORY_ENTRY_FORMATS = {
        "title": "from_to",
        "due_date": "from_to",
        "due_time": "from_to",
        "priority": "from_to",
        "assigned_person": "from_to",
        "tags": "from_to",
        "notes": "marker",
        "recurrence_enabled": "to_only",
    }

    @classmethod
    def _record_history(cls, task: dict, snapshot: dict, kwargs: dict, actor: str | None) -> None:
        """Append history entries for any fields that actually changed."""
        _now = datetime.now(timezone.utc).isoformat()
        _by = {"by": actor} if actor else {}
        new_hist: list[dict] = []

        for field, fmt in cls._HISTORY_ENTRY_FORMATS.items():
            if field not in kwargs:
                continue
            new_value = task.get(field)
            old_value = snapshot[field]
            # tags need a list copy for accurate diffing
            if field == "tags":
                new_value = list(new_value or [])
            if new_value == old_value:
                continue
            entry = {"ts": _now, "action": "updated", "field": field, **_by}
            if fmt == "from_to":
                entry["from"] = old_value
                entry["to"] = new_value
            elif fmt == "to_only":
                entry["to"] = new_value
            new_hist.append(entry)

        was_completed = snapshot["completed"]
        is_completed = task.get("completed", False)
        if is_completed and not was_completed:
            new_hist.append({"ts": _now, "action": "completed", **_by})
        elif not is_completed and was_completed:
            new_hist.append({"ts": _now, "action": "reopened", "by": actor or "user"})

        if new_hist:
            hist = task.setdefault("history", [])
            hist.extend(new_hist)
            _trim_history(hist)

    def _fire_update_callbacks(self, task: dict, snapshot: dict) -> None:
        """Fire reminder/assignment callbacks when their fields changed."""
        if self.on_reminders_changed and (
            task.get("due_date") != snapshot["due_date"]
            or task.get("due_time") != snapshot["due_time"]
            or task.get("reminders", []) != snapshot["reminders"]
        ):
            self.on_reminders_changed(task)

        new_person = task.get("assigned_person")
        if new_person != snapshot["assigned_person"] and self.on_task_assigned:
            self.on_task_assigned(task, snapshot["assigned_person"])

    async def async_reopen_task(
        self,
        task_id: str,
        actor: str | None = None,
        new_due_date: str | None = None,
        new_due_time: object = _REOPEN_UNCHANGED,
    ) -> dict:
        """Reopen a completed task and reset its sub-tasks.

        actor=None means triggered by the recurrence scheduler.
        actor="name" means triggered by a user or automation.
        new_due_date: if set, update the task's due_date.
        new_due_time: if not _REOPEN_UNCHANGED, update the task's due_time.
        """
        task = self.get_task(task_id)
        if not task.get("completed"):
            return task  # already open, nothing to do

        task["completed"] = False
        task["completed_at"] = None
        if new_due_date is not None:
            task["due_date"] = new_due_date
        if new_due_time is not _REOPEN_UNCHANGED:
            task["due_time"] = new_due_time
        for sub in task.get("sub_items", []):
            sub["completed"] = False
        _rec_entry = {"ts": datetime.now(timezone.utc).isoformat(), "action": "reopened", "by": actor or "recurrence"}
        hist = task.setdefault("history", [])
        hist.append(_rec_entry)
        _trim_history(hist)
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
