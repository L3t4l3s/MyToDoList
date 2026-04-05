"""Provider adapters for external todo integrations.

Each adapter encapsulates provider-specific logic for reading, creating, updating,
and deleting tasks.  The *GenericAdapter* uses HA's standard ``todo`` entity
interface (the current behaviour for CalDAV, Google Tasks, etc.).  The
*TodoistAdapter* talks directly to the Todoist REST API via ``todoist-api-python``
to achieve full bidirectional sync for priority, labels, order, sub-tasks,
assignee, recurrence and reminders.
"""

from __future__ import annotations

import asyncio
import logging
import re
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime as dt
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)



# Weekday names used when converting our recurrence weekdays to Todoist strings.
_WEEKDAY_NAMES = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
_VALID_RECURRENCE_UNITS = frozenset({"hours", "days", "weeks", "months"})

# Base fields that the GenericAdapter syncs via HA's todo.update_item service.
_GENERIC_BASE_FIELDS = frozenset({"title", "completed", "notes", "due_date", "due_time"})

# Fields that the TodoistAdapter syncs directly via the Todoist API.
_TODOIST_PROVIDER_FIELDS = frozenset({
    "title", "notes", "priority", "tags", "due_date", "due_time",
    "completed", "reminders", "sort_order",
    "recurrence_enabled", "recurrence_type", "recurrence_value",
    "recurrence_unit", "recurrence_weekdays", "recurrence_start_date",
    "recurrence_time", "recurrence_end_date",
})

# ---------------------------------------------------------------------------
#  Capabilities
# ---------------------------------------------------------------------------


@dataclass
class ProviderCapabilities:
    """Declare per-field sync support for a provider adapter."""

    can_sync_priority: bool = False
    can_sync_labels: bool = False
    can_sync_order: bool = False
    can_sync_due_time: bool = False
    can_sync_description: bool = False
    can_sync_assignee: bool = False
    can_sync_sub_items: bool = False
    can_sync_recurrence: bool = False
    can_sync_reminders: bool = False

    def to_dict(self) -> dict[str, bool]:
        return asdict(self)


# ---------------------------------------------------------------------------
#  Priority mapping helpers (Todoist: 1=normal … 4=urgent)
# ---------------------------------------------------------------------------

def priority_to_todoist(home_tasks_priority: int | None) -> int:
    """Convert Home Tasks priority (1-3 or None) to Todoist (1-4)."""
    return (home_tasks_priority or 0) + 1


def priority_from_todoist(todoist_priority: int) -> int | None:
    """Convert Todoist priority (1-4) to Home Tasks (None or 1-3)."""
    val = todoist_priority - 1
    return val if val >= 1 else None


# ---------------------------------------------------------------------------
#  Detection & factory
# ---------------------------------------------------------------------------

def detect_provider_type(hass: HomeAssistant, entity_id: str) -> str:
    """Return the integration domain that owns *entity_id* (e.g. 'todoist')."""
    entity_reg = er.async_get(hass)
    entity_entry = entity_reg.async_get(entity_id)
    if entity_entry and entity_entry.config_entry_id:
        config_entry = hass.config_entries.async_get_entry(entity_entry.config_entry_id)
        if config_entry:
            return config_entry.domain
    return "generic"


def get_todoist_token(hass: HomeAssistant, entity_id: str) -> str | None:
    """Read the Todoist API token from the existing Todoist config entry."""
    entity_reg = er.async_get(hass)
    entity_entry = entity_reg.async_get(entity_id)
    if not entity_entry or not entity_entry.config_entry_id:
        return None
    config_entry = hass.config_entries.async_get_entry(entity_entry.config_entry_id)
    if config_entry and config_entry.domain == "todoist":
        return config_entry.data.get("token")
    return None


def get_adapter(
    hass: HomeAssistant,
    entity_id: str,
    config_data: dict[str, Any],
) -> ProviderAdapter:
    """Instantiate the correct adapter for *entity_id*."""
    provider_type = config_data.get("provider_type", "generic")
    if provider_type == "todoist":
        token = get_todoist_token(hass, entity_id)
        if token:
            return TodoistAdapter(hass, entity_id, config_data, token)
        _LOGGER.warning(
            "Todoist token not available for %s – falling back to generic adapter",
            entity_id,
        )
    return GenericAdapter(hass, entity_id, config_data)


# ---------------------------------------------------------------------------
#  Base class
# ---------------------------------------------------------------------------


class ProviderAdapter(ABC):
    """Abstract base for provider adapters."""

    provider_type: str = "generic"
    capabilities: ProviderCapabilities = ProviderCapabilities()

    def __init__(
        self,
        hass: HomeAssistant,
        entity_id: str,
        config_data: dict[str, Any],
    ) -> None:
        self._hass = hass
        self._entity_id = entity_id
        self._config_data = config_data

    # -- Task CRUD ----------------------------------------------------------

    @abstractmethod
    async def async_read_tasks(self) -> list[dict]:
        """Read tasks from provider (Home Tasks-compatible dicts)."""

    @abstractmethod
    async def async_create_task(self, fields: dict) -> str | None:
        """Create a task. Return the new UID or *None*."""

    @abstractmethod
    async def async_update_task(self, task_uid: str, fields: dict) -> dict:
        """Update a task. Return dict of *unsynced* fields for the overlay."""

    @abstractmethod
    async def async_delete_task(self, task_uid: str) -> None:
        """Delete a task."""

    @abstractmethod
    async def async_reorder_tasks(self, task_uids: list[str]) -> bool:
        """Reorder tasks. Return *True* if the provider handled it."""

    # -- Sub-task CRUD (default = not supported) ----------------------------

    async def async_add_sub_task(self, parent_uid: str, title: str) -> str | None:
        """Add a sub-task. Return the new sub-task UID or *None*."""
        return None  # handled by overlay

    async def async_update_sub_task(self, sub_task_uid: str, **fields: Any) -> bool:
        """Update a sub-task. Return *True* if handled by the provider."""
        return False  # handled by overlay

    async def async_delete_sub_task(self, sub_task_uid: str) -> bool:
        """Delete a sub-task. Return *True* if handled by the provider."""
        return False  # handled by overlay

    async def async_reorder_sub_tasks(
        self, parent_uid: str, sub_task_uids: list[str]
    ) -> bool:
        """Reorder sub-tasks. Return *True* if handled by the provider."""
        return False  # handled by overlay


# ---------------------------------------------------------------------------
#  Generic adapter (current behaviour – HA todo entity interface)
# ---------------------------------------------------------------------------


class GenericAdapter(ProviderAdapter):
    """Route through HA's standard ``todo`` entity interface."""

    provider_type = "generic"
    capabilities = ProviderCapabilities()  # nothing extra synced

    # -- reads --------------------------------------------------------------

    async def async_read_tasks(self) -> list[dict]:
        return _get_external_todo_items(self._hass, self._entity_id)

    # -- writes -------------------------------------------------------------

    async def async_create_task(self, fields: dict) -> str | None:
        service_data: dict[str, Any] = {"item": fields.get("title", "")}
        if fields.get("due_date"):
            if fields.get("due_time"):
                service_data["due_datetime"] = f"{fields['due_date']} {fields['due_time']}:00"
            else:
                service_data["due_date"] = fields["due_date"]
        if fields.get("notes"):
            service_data["description"] = fields["notes"]
        await self._hass.services.async_call(
            "todo", "add_item", service_data,
            target={"entity_id": self._entity_id},
            blocking=True,
        )
        return None  # UID is assigned by the provider; re-fetch to discover it

    async def async_update_task(self, task_uid: str, fields: dict) -> dict:
        """Send base fields to provider, return everything else as unsynced."""
        service_data: dict[str, Any] = {"item": task_uid}
        unsynced: dict[str, Any] = {}

        if "title" in fields:
            service_data["rename"] = fields["title"]
        if "completed" in fields:
            service_data["status"] = "completed" if fields["completed"] else "needs_action"
        if "notes" in fields:
            service_data["description"] = fields["notes"]
        if "due_date" in fields:
            if fields["due_date"] is None:
                # Explicitly clearing due date
                service_data["due_date"] = None
            elif fields.get("due_time"):
                service_data["due_datetime"] = f"{fields['due_date']} {fields['due_time']}:00"
            else:
                service_data["due_date"] = fields["due_date"]
        elif "due_time" in fields:
            # due_time changed but due_date didn't – treat as unsynced
            unsynced["due_time"] = fields["due_time"]

        for key, value in fields.items():
            if key not in _GENERIC_BASE_FIELDS:
                unsynced[key] = value

        if len(service_data) > 1:  # more than just "item"
            await self._hass.services.async_call(
                "todo", "update_item", service_data,
                target={"entity_id": self._entity_id},
                blocking=True,
            )
        return unsynced

    async def async_delete_task(self, task_uid: str) -> None:
        await self._hass.services.async_call(
            "todo", "remove_item", {"item": task_uid},
            target={"entity_id": self._entity_id},
            blocking=True,
        )

    async def async_reorder_tasks(self, task_uids: list[str]) -> bool:
        features = 0
        state = self._hass.states.get(self._entity_id)
        if state and state.attributes:
            features = state.attributes.get("supported_features", 0)
        if not (features & 8):  # MOVE_TODO_ITEM
            return False  # caller should use overlay sort_order

        for i, uid in enumerate(task_uids):
            try:
                await self._hass.services.async_call(
                    "todo", "item/move",
                    {
                        "entity_id": self._entity_id,
                        "uid": uid,
                        "previous_uid": task_uids[i - 1] if i > 0 else None,
                    },
                    blocking=True,
                )
            except Exception:  # noqa: BLE001
                _LOGGER.warning("Failed to move task %s via todo/item/move", uid)
                return False
        return True


# ---------------------------------------------------------------------------
#  Todoist adapter (direct API access)
# ---------------------------------------------------------------------------


class TodoistAdapter(ProviderAdapter):
    """Full bidirectional sync via the Todoist REST API."""

    provider_type = "todoist"

    def __init__(
        self,
        hass: HomeAssistant,
        entity_id: str,
        config_data: dict[str, Any],
        token: str,
    ) -> None:
        super().__init__(hass, entity_id, config_data)
        self._token = token
        self._api: Any = None  # TodoistAPIClient, lazy-initialised
        self._project_id: str | None = config_data.get("todoist_project_id")
        self._collaborators: list[Any] = []
        self.capabilities = ProviderCapabilities(
            can_sync_priority=True,
            can_sync_labels=True,
            can_sync_order=True,
            can_sync_due_time=True,
            can_sync_description=True,
            can_sync_assignee=False,  # API v1 silently ignores assignee_id
            can_sync_sub_items=True,
            can_sync_recurrence=True,
            can_sync_reminders=True,
        )

    # -- lazy init ----------------------------------------------------------

    async def _ensure_api(self) -> Any:
        """Create the TodoistAPIClient instance on first use."""
        if self._api is not None:
            return self._api
        from .todoist_api import TodoistAPIClient  # noqa: WPS433

        self._api = TodoistAPIClient(self._token)

        if not self._project_id:
            await self._resolve_project_id()
        if not self._collaborators and self._project_id:
            try:
                self._collaborators = await self._api.get_collaborators(self._project_id)
            except Exception:  # noqa: BLE001
                self._collaborators = []
        return self._api

    async def _resolve_project_id(self) -> None:
        """Determine the Todoist project ID from the entity name."""
        projects = await self._api.get_projects()

        entity_name = self._config_data.get("name", "")
        entity_id_suffix = self._entity_id.replace("todo.", "").replace("_", " ")

        for project in projects:
            if project.name.lower() == entity_name.lower():
                self._project_id = project.id
                break
            if project.name.lower().replace(" ", "_") == entity_id_suffix.replace(" ", "_"):
                self._project_id = project.id
                break

        if not self._project_id and projects:
            stripped = entity_id_suffix
            if stripped.startswith("todoist "):
                stripped = stripped[8:]
            for project in projects:
                if project.name.lower() == stripped.lower():
                    self._project_id = project.id
                    break

        if self._project_id:
            _LOGGER.info("Resolved Todoist project ID %s for %s", self._project_id, self._entity_id)
        else:
            _LOGGER.warning("Could not resolve Todoist project ID for %s", self._entity_id)

    def _match_person_to_collaborator(self, person_entity_id: str) -> str | None:
        """Match HA person entity → Todoist collaborator ID by name."""
        state = self._hass.states.get(person_entity_id)
        if not state:
            return None
        name = (state.attributes.get("friendly_name") or "").lower().strip()
        if not name:
            return None
        for c in self._collaborators:
            if c.name.lower().strip() == name:
                return c.id
        for c in self._collaborators:
            cn = c.name.lower().strip()
            if name in cn or cn in name:
                return c.id
        return None

    # -- Recurrence mapping -------------------------------------------------

    @staticmethod
    def _build_recurrence_string(fields: dict) -> str | None:
        """Convert structured recurrence fields to a Todoist due_string."""
        # Recurrence is active if explicitly enabled OR if recurrence detail
        # fields are present (partial update from the card editor).
        _REC_DETAIL_KEYS = {"recurrence_value", "recurrence_unit", "recurrence_weekdays",
                            "recurrence_type", "recurrence_time", "recurrence_start_date",
                            "recurrence_end_date"}
        has_details = any(k in fields for k in _REC_DETAIL_KEYS)
        # If detail fields are present, the user is editing an active recurrence
        # — treat as enabled even if the merged recurrence_enabled says otherwise
        # (can happen due to API timing or parser limitations).
        if fields.get("recurrence_enabled") is False and not has_details:
            return None
        if not fields.get("recurrence_enabled") and not has_details:
            return None

        rtype = fields.get("recurrence_type", "interval")
        value = fields.get("recurrence_value", 1)
        unit = fields.get("recurrence_unit", "days")
        weekdays = fields.get("recurrence_weekdays", [])
        rtime = fields.get("recurrence_time")
        start = fields.get("recurrence_start_date")
        end = fields.get("recurrence_end_date")

        parts: list[str] = []

        if rtype == "weekdays":
            if not weekdays:
                weekdays = [0, 1, 2, 3, 4]  # Default: Mon-Fri
            day_names = [_WEEKDAY_NAMES[d] for d in sorted(weekdays) if 0 <= d <= 6]
            parts.append(f"every {', '.join(day_names)}")
        else:
            # Interval
            unit_str = unit if unit in _VALID_RECURRENCE_UNITS else "days"
            if value == 1:
                # "every day" instead of "every 1 days"
                singular = {"hours": "hour", "days": "day", "weeks": "week", "months": "month"}
                parts.append(f"every {singular.get(unit_str, unit_str)}")
            else:
                parts.append(f"every {value} {unit_str}")

        if rtime:
            parts.append(f"at {rtime}")
        if start:
            parts.append(f"starting {start}")
        if end:
            parts.append(f"ending {end}")

        return " ".join(parts) if parts else None

    @staticmethod
    def _parse_recurrence_from_due(due_obj: Any) -> dict:
        """Parse Todoist due object into Home Tasks recurrence fields."""
        result: dict[str, Any] = {
            "recurrence_enabled": False,
            "recurrence_type": "interval",
            "recurrence_value": 1,
            "recurrence_unit": "days",
            "recurrence_weekdays": [],
            "recurrence_start_date": None,
            "recurrence_time": None,
        }
        if due_obj is None or not getattr(due_obj, "is_recurring", False):
            return result

        result["recurrence_enabled"] = True
        due_string = getattr(due_obj, "string", "") or ""
        lower = due_string.lower().strip()

        # Try to parse "every N unit(s)" pattern
        interval_match = re.match(
            r"every\s+(\d+)\s+(hour|day|week|month)s?", lower
        )
        if interval_match:
            result["recurrence_value"] = int(interval_match.group(1))
            result["recurrence_unit"] = interval_match.group(2) + "s"
            result["recurrence_type"] = "interval"
        elif re.match(r"every\s+(hour|day|week|month)", lower):
            # "every day", "every week" etc.
            unit_match = re.match(r"every\s+(hour|day|week|month)", lower)
            if unit_match:
                result["recurrence_value"] = 1
                result["recurrence_unit"] = unit_match.group(1) + "s"
                result["recurrence_type"] = "interval"
        else:
            # Try to parse weekdays: "every mon, wed, fri"
            weekday_match = re.match(r"every\s+((?:mon|tue|wed|thu|fri|sat|sun)(?:\s*,\s*(?:mon|tue|wed|thu|fri|sat|sun))*)", lower)
            if weekday_match:
                day_str = weekday_match.group(1)
                days = [d.strip() for d in day_str.split(",")]
                indices = []
                for d in days:
                    try:
                        indices.append(_WEEKDAY_NAMES.index(d))
                    except ValueError:
                        pass
                if indices:
                    result["recurrence_type"] = "weekdays"
                    result["recurrence_weekdays"] = sorted(indices)

        # Extract "at HH:MM"
        time_match = re.search(r"at\s+(\d{1,2}):?(\d{2})?\s*(am|pm)?", lower)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            ampm = time_match.group(3)
            if ampm == "pm" and hour < 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0
            result["recurrence_time"] = f"{hour:02d}:{minute:02d}"

        # Extract "starting YYYY-MM-DD"
        start_match = re.search(r"starting\s+(\d{4}-\d{2}-\d{2})", lower)
        if start_match:
            result["recurrence_start_date"] = start_match.group(1)

        # Extract "ending YYYY-MM-DD"
        end_match = re.search(r"ending\s+(\d{4}-\d{2}-\d{2})", lower)
        if end_match:
            result["recurrence_end_date"] = end_match.group(1)
            result["recurrence_end_type"] = "date"

        # Store the original string for read-only display of complex patterns
        result["_todoist_recurrence_string"] = due_string

        return result

    # -- Due date helpers ---------------------------------------------------

    @staticmethod
    def _extract_time(due_obj: Any) -> str | None:
        """Extract HH:MM from a TodoistDue object."""
        if due_obj is None:
            return None
        date_str = getattr(due_obj, "date", None)
        if not date_str or "T" not in str(date_str):
            return None
        try:
            parsed = dt.fromisoformat(str(date_str).replace("Z", "+00:00"))
            local = parsed.astimezone()
            return local.strftime("%H:%M")
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _extract_date(due_obj: Any) -> str | None:
        """Extract YYYY-MM-DD string from a TodoistDue object."""
        if due_obj is None:
            return None
        date_str = getattr(due_obj, "date", None)
        if not date_str:
            return None
        s = str(date_str)
        if "T" in s:
            try:
                parsed = dt.fromisoformat(s.replace("Z", "+00:00"))
                local = parsed.astimezone()
                return local.date().isoformat()
            except (ValueError, TypeError):
                return s[:10]
        return s[:10]  # "YYYY-MM-DD"

    async def _merge_due_fields(self, api: Any, task_uid: str, fields: dict) -> dict:
        """Merge partial recurrence/due fields with the current task state.

        When the card sends e.g. only ``{recurrence_start_date: "2026-04-06"}``,
        we need the existing recurrence_value/unit/weekdays to build a correct
        Todoist due_string.  Fetch the current task and parse its due object.
        """
        _REC_KEYS = {"recurrence_enabled", "recurrence_type", "recurrence_value",
                     "recurrence_unit", "recurrence_weekdays", "recurrence_start_date",
                     "recurrence_time"}
        # If all recurrence keys are present AND we have due_date, no need to fetch
        if _REC_KEYS <= fields.keys() and "due_date" in fields:
            return fields

        try:
            current_task = await api.get_task(task_uid)
        except Exception:  # noqa: BLE001
            return fields

        # Parse existing recurrence from the current due object
        current = self._parse_recurrence_from_due(current_task.due)
        current["due_date"] = self._extract_date(current_task.due)
        current["due_time"] = self._extract_time(current_task.due)

        # Merge: fields from the caller win, fill in blanks from current
        merged = {**current, **fields}
        return merged

    def _build_due_params(self, fields: dict) -> dict[str, Any]:
        """Build Todoist API due parameters from fields."""
        params: dict[str, Any] = {}
        due_date = fields.get("due_date")
        due_time = fields.get("due_time")

        # Check if recurrence is being set or cleared
        recurrence_str = self._build_recurrence_string(fields)
        if recurrence_str:
            if due_time and not fields.get("recurrence_time"):
                params["due_string"] = f"{recurrence_str} at {due_time}"
            else:
                params["due_string"] = recurrence_str
        elif fields.get("recurrence_enabled") is False:
            # Recurrence disabled — set the existing due date as non-recurring
            if due_date:
                if due_time:
                    params["due_datetime"] = f"{due_date}T{due_time}:00"
                else:
                    params["due_date"] = due_date
            else:
                params["due_string"] = "no date"
        elif due_date:
            if due_time:
                params["due_datetime"] = f"{due_date}T{due_time}:00"
            else:
                params["due_date"] = due_date
        elif due_date is None and "due_date" in fields:
            # Explicitly clearing due date
            params["due_string"] = "no date"

        return params

    # -- Task CRUD ----------------------------------------------------------

    async def async_read_tasks(self) -> list[dict]:
        api = await self._ensure_api()
        kwargs: dict[str, Any] = {}
        if self._project_id:
            kwargs["project_id"] = self._project_id

        all_tasks = await api.get_tasks(project_id=self._project_id)

        # Separate main tasks from sub-tasks
        main_tasks = [t for t in all_tasks if not t.parent_id]
        sub_tasks_by_parent: dict[str, list[Any]] = defaultdict(list)
        for t in all_tasks:
            if t.parent_id:
                sub_tasks_by_parent[t.parent_id].append(t)

        result: list[dict] = []
        for task in main_tasks:
            children = sub_tasks_by_parent.get(task.id, [])
            children.sort(key=lambda t: t.order)
            sub_items = [
                {"id": st.id, "title": st.content, "completed": st.is_completed}
                for st in children
            ]

            # Parse recurrence from due object
            recurrence = self._parse_recurrence_from_due(task.due)

            # Read reminders
            raw_reminders = await api.get_reminders(task.id)
            reminders = [
                r["minute_offset"] for r in raw_reminders
                if r.get("minute_offset") is not None
            ]

            result.append({
                "uid": task.id,
                "summary": task.content,
                "status": "completed" if task.is_completed else "needs_action",
                "due": self._extract_date(task.due),
                "due_time": self._extract_time(task.due),
                "description": task.description or "",
                "priority": priority_from_todoist(task.priority),
                "labels": list(task.labels) if task.labels else [],
                "order": task.order,
                "sub_items": sub_items,
                "reminders": reminders,
                **recurrence,
            })

        return result

    async def async_create_task(self, fields: dict) -> str | None:
        api = await self._ensure_api()
        kwargs: dict[str, Any] = {
            "content": fields.get("title", "New task"),
        }
        if self._project_id:
            kwargs["project_id"] = self._project_id
        if fields.get("notes"):
            kwargs["description"] = fields["notes"]
        if fields.get("priority") is not None:
            kwargs["priority"] = priority_to_todoist(fields["priority"])
        if fields.get("tags"):
            kwargs["labels"] = fields["tags"]

        # Due date / recurrence
        due_params = self._build_due_params(fields)
        kwargs.update(due_params)

        # Assignee: send to API (visible in Todoist app) — overlay handles display
        if fields.get("assigned_person"):
            collab_id = self._match_person_to_collaborator(fields["assigned_person"])
            if collab_id:
                kwargs["assignee_id"] = collab_id

        task = await api.add_task(**kwargs)

        # Create reminders
        if fields.get("reminders"):
            for offset in fields["reminders"]:
                await api.add_reminder(task.id, reminder_type="relative", minute_offset=offset)

        return task.id

    async def async_update_task(self, task_uid: str, fields: dict) -> dict:
        api = await self._ensure_api()

        # Step 1: Determine which fields go to the API vs overlay.
        # Overlay fields are ALWAYS returned regardless of API success.
        api_fields: dict[str, Any] = {}
        unsynced: dict[str, Any] = {}

        # --- Fields that go to the Todoist API ---
        if "title" in fields:
            api_fields["content"] = fields["title"]
        if "notes" in fields:
            api_fields["description"] = fields["notes"]
        if "priority" in fields:
            api_fields["priority"] = priority_to_todoist(fields["priority"])
        if "tags" in fields:
            api_fields["labels"] = fields["tags"]

        # Due / recurrence
        _DUE_KEYS = {"due_date", "due_time", "recurrence_enabled", "recurrence_type",
                     "recurrence_value", "recurrence_unit", "recurrence_weekdays",
                     "recurrence_start_date", "recurrence_time", "recurrence_end_date"}
        if _DUE_KEYS & fields.keys():
            merged_due = await self._merge_due_fields(api, task_uid, fields)
            due_params = self._build_due_params(merged_due)
            if due_params:
                api_fields.update(due_params)

        # Assignee: API accepts assignee_id on write (visible in Todoist app)
        # but never returns it on read — so we ALSO store in overlay.
        if "assigned_person" in fields:
            if fields["assigned_person"]:
                collab_id = self._match_person_to_collaborator(fields["assigned_person"])
                if collab_id:
                    api_fields["assignee_id"] = collab_id
            unsynced["assigned_person"] = fields["assigned_person"]

        # --- Fields that ALWAYS go to overlay ---
        _OVERLAY_ALWAYS = {"recurrence_end_type", "recurrence_end_date",
                          "recurrence_max_count", "recurrence_remaining_count"}
        for key in _OVERLAY_ALWAYS:
            if key in fields:
                unsynced[key] = fields[key]

        # All fields NOT handled by the API go to overlay
        for key, value in fields.items():
            if key not in _TODOIST_PROVIDER_FIELDS and key not in unsynced:
                unsynced[key] = value

        # Step 2: Send API updates (errors are logged but don't block overlay).
        try:
            if "completed" in fields:
                if fields["completed"]:
                    await api.complete_task(task_uid)
                else:
                    await api.uncomplete_task(task_uid)
            if api_fields:
                await api.update_task(task_uid, **api_fields)
        except Exception:  # noqa: BLE001
            _LOGGER.warning("Todoist API update failed for task %s", task_uid)

        # Sync reminders via API
        if "reminders" in fields:
            await self._sync_reminders(task_uid, fields["reminders"])

        return unsynced

    async def async_delete_task(self, task_uid: str) -> None:
        api = await self._ensure_api()
        await api.delete_task(task_uid)

    async def async_reorder_tasks(self, task_uids: list[str]) -> bool:
        api = await self._ensure_api()
        try:
            await asyncio.gather(*(
                api.update_task(uid, child_order=i)
                for i, uid in enumerate(task_uids)
            ))
        except Exception:  # noqa: BLE001
            _LOGGER.warning("Failed to reorder Todoist tasks")
            return False
        return True

    # -- Sub-task CRUD ------------------------------------------------------

    async def async_add_sub_task(self, parent_uid: str, title: str) -> str | None:
        api = await self._ensure_api()
        task = await api.add_task(content=title, parent_id=parent_uid)
        return task.id

    async def async_update_sub_task(self, sub_task_uid: str, **fields: Any) -> bool:
        api = await self._ensure_api()
        api_fields: dict[str, Any] = {}
        if "title" in fields:
            api_fields["content"] = fields["title"]
        if "completed" in fields:
            if fields["completed"]:
                await api.complete_task(sub_task_uid)
            else:
                await api.uncomplete_task(sub_task_uid)
        if api_fields:
            await api.update_task(sub_task_uid, **api_fields)
        return True

    async def async_delete_sub_task(self, sub_task_uid: str) -> bool:
        api = await self._ensure_api()
        await api.delete_task(sub_task_uid)
        return True

    async def async_reorder_sub_tasks(
        self, parent_uid: str, sub_task_uids: list[str]
    ) -> bool:
        api = await self._ensure_api()
        try:
            await asyncio.gather(*(
                api.update_task(uid, child_order=i)
                for i, uid in enumerate(sub_task_uids)
            ))
        except Exception:  # noqa: BLE001
            _LOGGER.warning("Failed to reorder Todoist sub-tasks")
            return False
        return True

    # -- Reminder sync ------------------------------------------------------

    async def _sync_reminders(self, task_uid: str, new_offsets: list[int]) -> None:
        """Delta-sync reminder offsets to Todoist."""
        api = self._api
        existing = await api.get_reminders(task_uid)
        existing_map = {
            r.get("minute_offset"): r.get("id")
            for r in existing
            if r.get("minute_offset") is not None
        }
        new_set = set(new_offsets)

        # Delete removed
        for offset, rid in existing_map.items():
            if offset not in new_set:
                await api.delete_reminder(rid)

        # Create added
        for offset in new_offsets:
            if offset not in existing_map:
                await api.add_reminder(task_uid, reminder_type="relative", minute_offset=offset)


# ---------------------------------------------------------------------------
#  Shared helper – also used by GenericAdapter
# ---------------------------------------------------------------------------

def _get_external_todo_items(hass: HomeAssistant, entity_id: str) -> list[dict]:
    """Read TodoItems from an external HA todo entity and return as dicts.

    This is the *existing* logic extracted from websocket_api.py so both
    GenericAdapter and the fallback code can reuse it.
    """
    state = hass.states.get(entity_id)
    if state is None:
        raise ValueError(f"Entity not found: {entity_id}")

    entity_comp = hass.data.get("todo")
    if entity_comp and hasattr(entity_comp, "get_entity"):
        entity = entity_comp.get_entity(entity_id)
        if entity and hasattr(entity, "todo_items"):
            items = entity.todo_items or []
            result: list[dict] = []
            for item in items:
                uid = item.uid
                if not uid:
                    continue
                due_date = None
                due_time = None
                if item.due is not None:
                    if isinstance(item.due, dt):
                        local_due = item.due.astimezone()
                        due_date = local_due.date().isoformat()
                        due_time = local_due.strftime("%H:%M")
                    else:
                        due_date = item.due.isoformat()
                result.append({
                    "uid": uid,
                    "summary": item.summary,
                    "status": item.status.value if item.status else "needs_action",
                    "due": due_date,
                    "due_time": due_time,
                    "description": item.description,
                })
            return result

    raise ValueError(f"Cannot read todo items from entity: {entity_id}")
