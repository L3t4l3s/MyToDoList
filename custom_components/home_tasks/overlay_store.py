"""Overlay store for external todo entities.

Stores Home Tasks extra fields (priority, tags, sub_items, etc.) that external
providers (CalDAV, Google Tasks, Microsoft ToDo) do not support.  The overlay
is keyed by the external task's UID and persisted locally via HA's Store helper.
"""

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
    MAX_TITLE_LENGTH,
    VALID_RECURRENCE_UNITS,
)
from .store import apply_field_validators, validate_date, validate_text, validate_time

_LOGGER = logging.getLogger(__name__)

OVERLAY_STORAGE_VERSION = 1

# Fields that the overlay store manages (not provided by external providers).
OVERLAY_FIELDS = (
    "priority",
    "due_date",
    "due_time",
    "notes",
    "assigned_person",
    "tags",
    "reminders",
    "sub_items",
    "sort_order",
    "recurrence_enabled",
    "recurrence_type",
    "recurrence_value",
    "recurrence_unit",
    "recurrence_weekdays",
    "recurrence_start_date",
    "recurrence_time",
    "recurrence_end_type",
    "recurrence_end_date",
    "recurrence_max_count",
    "recurrence_remaining_count",
    "recurrence_month_pattern",
    "recurrence_day_of_month",
    "recurrence_nth_week",
    "recurrence_anniversary",
    "history",
    "completed_at",
)

_MAX_HISTORY = 50


def _empty_overlay() -> dict:
    """Return a fresh overlay with default values for all extra fields."""
    return {
        "priority": None,
        "due_date": None,
        "due_time": None,
        "notes": None,
        "assigned_person": None,
        "tags": [],
        "reminders": [],
        "sub_items": [],
        "sort_order": 0,
        "recurrence_enabled": False,
        "recurrence_type": "interval",
        "recurrence_value": 1,
        "recurrence_unit": None,
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
        "history": [],
        "completed_at": None,
    }


def _trim_history(hist: list) -> None:
    """Trim history in-place."""
    if len(hist) > _MAX_HISTORY:
        del hist[:-_MAX_HISTORY]


class ExternalTaskOverlayStore:
    """Manage overlay data for tasks belonging to an external todo entity."""

    def __init__(self, hass: HomeAssistant, entity_id: str) -> None:
        """Initialize the overlay store."""
        # Sanitise entity_id for use in the storage filename.
        # Strip everything except alphanumerics and underscores to prevent
        # path traversal (e.g. ../../etc/passwd) or filesystem-special chars.
        safe_id = re.sub(r"[^a-zA-Z0-9_]", "_", entity_id)
        self._store = Store(hass, OVERLAY_STORAGE_VERSION, f"home_tasks_overlay_{safe_id}")
        self._data: dict | None = None
        self._listeners: list[Callable[[], None]] = []
        self.entity_id = entity_id

    # -- listener support (mirrors HomeTasksStore) --

    def async_add_listener(self, callback: Callable[[], None]) -> Callable[[], None]:
        """Add a listener for data changes. Returns a removal callable."""
        self._listeners.append(callback)
        return lambda: self._listeners.remove(callback) if callback in self._listeners else None

    # -- persistence --

    async def async_load(self) -> None:
        """Load overlay data from disk."""
        data = await self._store.async_load()
        if data is None:
            self._data = {"overlays": {}}
            await self._async_save()
        else:
            self._data = data
            self._strip_default_overlays()

    def _strip_default_overlays(self) -> None:
        """Remove fields from stored overlays that match _empty_overlay() defaults.

        Earlier versions stored all defaults on every overlay write.  This
        migration strips them so only user-set values remain, allowing the
        merge logic to distinguish explicit values from defaults.
        """
        defaults = _empty_overlay()
        overlays = self._data.get("overlays", {})
        to_delete = []
        for uid, overlay in overlays.items():
            keys_to_remove = [
                k for k, v in list(overlay.items())
                if k in defaults and v == defaults[k] and k != "sub_items"
            ]
            for k in keys_to_remove:
                del overlay[k]
            # Remove empty overlays entirely
            if not overlay:
                to_delete.append(uid)
        for uid in to_delete:
            del overlays[uid]

    async def _async_save(self) -> None:
        """Save overlay data to disk."""
        await self._store.async_save(self._data)
        for listener in self._listeners:
            listener()

    # -- read --

    def get_overlay(self, task_uid: str) -> dict:
        """Return the overlay for *task_uid*, creating a blank one if needed."""
        overlays = self._data.setdefault("overlays", {})
        if task_uid not in overlays:
            return _empty_overlay()
        return {**_empty_overlay(), **overlays[task_uid]}

    def get_all_overlays(self) -> dict[str, dict]:
        """Return all overlays keyed by task UID."""
        result = {}
        for uid, data in self._data.get("overlays", {}).items():
            result[uid] = {**_empty_overlay(), **data}
        return result

    # -- write --

    async def async_set_overlay(self, task_uid: str, **kwargs) -> dict:
        """Create or update the overlay for *task_uid*.

        Only fields listed in OVERLAY_FIELDS are accepted.  Validation mirrors
        the rules in HomeTasksStore.async_update_task.
        """
        self._validate_overlay_fields(kwargs)

        overlays = self._data.setdefault("overlays", {})
        if task_uid not in overlays:
            overlays[task_uid] = {}
        overlay = overlays[task_uid]

        for key, value in kwargs.items():
            if key in OVERLAY_FIELDS:
                overlay[key] = value

        await self._async_save()
        return {**_empty_overlay(), **overlay}

    async def async_delete_overlay(self, task_uid: str) -> None:
        """Remove the overlay for *task_uid*."""
        self._data.get("overlays", {}).pop(task_uid, None)
        await self._async_save()

    # -- sub-tasks (stored entirely in overlay) --

    async def async_add_sub_task(self, task_uid: str, title: str) -> dict:
        """Add a sub-task to the overlay of *task_uid*."""
        title = validate_text(title, MAX_TITLE_LENGTH, "Sub-task title")
        overlays = self._data.setdefault("overlays", {})
        if task_uid not in overlays:
            overlays[task_uid] = {}
        overlay = overlays[task_uid]
        subs = overlay.setdefault("sub_items", [])
        if len(subs) >= MAX_SUB_TASKS_PER_TASK:
            raise ValueError(f"Maximum number of sub-tasks ({MAX_SUB_TASKS_PER_TASK}) reached")
        sub = {"id": str(uuid.uuid4()), "title": title, "completed": False}
        subs.append(sub)
        await self._async_save()
        return sub

    async def async_update_sub_task(self, task_uid: str, sub_task_id: str, **kwargs) -> dict:
        """Update a sub-task in the overlay."""
        overlay = self._data.get("overlays", {}).get(task_uid)
        if overlay is None:
            raise ValueError("Overlay not found")
        for sub in overlay.get("sub_items", []):
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

    async def async_delete_sub_task(self, task_uid: str, sub_task_id: str) -> None:
        """Delete a sub-task from the overlay."""
        overlay = self._data.get("overlays", {}).get(task_uid)
        if overlay is None:
            raise ValueError("Overlay not found")
        subs = overlay.get("sub_items", [])
        original_len = len(subs)
        overlay["sub_items"] = [s for s in subs if s["id"] != sub_task_id]
        if len(overlay["sub_items"]) == original_len:
            raise ValueError("Sub-task not found")
        await self._async_save()

    async def async_reorder_sub_tasks(self, task_uid: str, sub_task_ids: list[str]) -> None:
        """Reorder sub-tasks within the overlay."""
        overlay = self._data.get("overlays", {}).get(task_uid)
        if overlay is None:
            raise ValueError("Overlay not found")
        id_to_sub = {s["id"]: s for s in overlay.get("sub_items", [])}
        overlay["sub_items"] = [id_to_sub[sid] for sid in sub_task_ids if sid in id_to_sub]
        await self._async_save()

    # -- validation helpers --

    @staticmethod
    def _validate_overlay_fields(kwargs: dict) -> None:
        """Validate incoming overlay fields (same rules as HomeTasksStore)."""
        if "recurrence_time" in kwargs:
            kwargs["recurrence_time"] = validate_time(kwargs["recurrence_time"])
        apply_field_validators(kwargs)
