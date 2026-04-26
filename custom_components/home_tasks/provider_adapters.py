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
from datetime import date as _date_cls, datetime as dt, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)



# Weekday names used when converting our recurrence weekdays to Todoist strings.
_WEEKDAY_NAMES = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
_WEEKDAY_LONG = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
_VALID_RECURRENCE_UNITS = frozenset({"hours", "days", "weeks", "months", "years"})

# Base fields that the GenericAdapter syncs via HA's todo.update_item service.
_GENERIC_BASE_FIELDS = frozenset({"title", "completed", "notes", "due_date", "due_time"})

# Fields that the TodoistAdapter syncs directly via the Todoist API.
# Note: ``sub_items`` is synced via the provider too, but through separate
# ``async_add_sub_task``/``async_update_sub_task`` calls rather than the
# main task's create/update payload — we list it here so the create/update
# loops don't mistakenly divert it to the overlay.
_TODOIST_PROVIDER_FIELDS = frozenset({
    "title", "notes", "priority", "tags", "due_date", "due_time",
    "completed", "reminders", "sort_order", "sub_items",
    "recurrence_enabled", "recurrence_type", "recurrence_value",
    "recurrence_unit", "recurrence_weekdays", "recurrence_start_date",
    "recurrence_time", "recurrence_end_date",
    "recurrence_month_pattern", "recurrence_day_of_month",
    "recurrence_nth_week", "recurrence_anniversary",
})

# Month name lookup for Todoist's natural-language due_string parsing.
_MONTH_NAMES = ("jan", "feb", "mar", "apr", "may", "jun",
                "jul", "aug", "sep", "oct", "nov", "dec")
_NTH_WORDS = {"1st": 1, "first": 1, "2nd": 2, "second": 2,
              "3rd": 3, "third": 3, "4th": 4, "fourth": 4}


def _ordinal(n: int) -> str:
    """Return e.g. '1st', '2nd', '3rd', '24th' for an integer day/index."""
    if 10 <= (n % 100) <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _month_index(name: str) -> int | None:
    """Return 1–12 for an English month abbreviation/name, or None."""
    name = name.lower()[:3]
    try:
        return _MONTH_NAMES.index(name) + 1
    except ValueError:
        return None


def _parse_ordinal_token(token: str) -> int | None:
    """Convert '24th', '2nd', 'second', 'last' etc. into an int day or None."""
    if token == "last":
        return None
    if token in _NTH_WORDS:
        return _NTH_WORDS[token]
    m = re.match(r"^(\d+)(?:st|nd|rd|th)?$", token)
    if m:
        return int(m.group(1))
    return None


def _parse_monthly_token(token: str, second: str | None, value: int) -> dict:
    """Parse the head of a monthly Todoist phrase into structured fields.

    Returns a dict with recurrence fields set, or with recurrence_unit absent
    if the token can't be interpreted as a monthly pattern.
    """
    out: dict = {}
    # "last day" — special "last" day-of-month
    if token == "last" and second == "day":
        out.update({
            "recurrence_value": value,
            "recurrence_unit": "months",
            "recurrence_type": "interval",
            "recurrence_month_pattern": "day_of_month",
            "recurrence_day_of_month": "last",
        })
        return out
    # "last <weekday>" — nth-weekday with nth=last
    if token == "last" and second:
        try:
            wd_idx = _WEEKDAY_NAMES.index(second[:3])
        except ValueError:
            return out
        out.update({
            "recurrence_value": value,
            "recurrence_unit": "months",
            "recurrence_type": "interval",
            "recurrence_month_pattern": "nth_weekday",
            "recurrence_nth_week": "last",
            "recurrence_weekdays": [wd_idx],
        })
        return out
    # "Nth <weekday>" — nth-weekday with explicit n
    if second and second != "day":
        try:
            wd_idx = _WEEKDAY_NAMES.index(second[:3])
        except ValueError:
            return out
        n = _parse_ordinal_token(token)
        if n is None or not (1 <= n <= 4):
            return out
        out.update({
            "recurrence_value": value,
            "recurrence_unit": "months",
            "recurrence_type": "interval",
            "recurrence_month_pattern": "nth_weekday",
            "recurrence_nth_week": n,
            "recurrence_weekdays": [wd_idx],
        })
        return out
    # "<Nth>" alone — day_of_month with the literal day
    n = _parse_ordinal_token(token)
    if n is not None and 1 <= n <= 31:
        out.update({
            "recurrence_value": value,
            "recurrence_unit": "months",
            "recurrence_type": "interval",
            "recurrence_month_pattern": "day_of_month",
            "recurrence_day_of_month": n,
        })
    return out


def _extract_aux(lower: str, result: dict) -> None:
    """Extract 'at HH:MM', 'starting YYYY-MM-DD', 'ending YYYY-MM-DD' tokens."""
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
    start_match = re.search(r"starting\s+(\d{4}-\d{2}-\d{2})", lower)
    if start_match:
        result["recurrence_start_date"] = start_match.group(1)
    end_match = re.search(r"ending\s+(\d{4}-\d{2}-\d{2})", lower)
    if end_match:
        result["recurrence_end_date"] = end_match.group(1)
        result["recurrence_end_type"] = "date"


def _store_original(due_string: str, result: dict) -> None:
    """Store the original Todoist string for read-only display fallback."""
    result["_todoist_recurrence_string"] = due_string

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
    async def async_create_task(self, fields: dict) -> tuple[str | None, dict]:
        """Create a task.

        Returns ``(uid, unsynced)``:
        - ``uid``  — the provider's new task UID, or *None* if it can't be
          determined synchronously.
        - ``unsynced`` — fields that the adapter could not push to the
          provider (because the provider lacks the capability or doesn't
          support the feature bit).  The caller writes these to the
          overlay keyed on ``uid``.  If ``uid`` is *None*, overlay data
          cannot be stored and the caller must surface this to the user.
        """

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

    async def async_create_task(self, fields: dict) -> tuple[str | None, dict]:
        state = self._hass.states.get(self._entity_id)
        features = (
            state.attributes.get("supported_features", 0)
            if state and state.attributes else 0
        )
        supports_datetime = bool(features & 32)  # SET_DUE_DATETIME_ON_ITEM
        supports_due_date = bool(features & 16)  # SET_DUE_DATE_ON_ITEM
        supports_description = bool(features & 64)  # SET_DESCRIPTION_ON_ITEM

        # Snapshot existing UIDs so we can identify the new task afterwards.
        # Only needed when we have overlay data to persist against the new UID;
        # otherwise the caller doesn't care about the UID (always None today).
        before_uids: set[str] = set()
        need_uid = False  # flip to True as we accumulate unsynced fields

        service_data: dict[str, Any] = {"item": fields.get("title", "")}
        unsynced: dict[str, Any] = {}

        # due_date / due_time — three branches:
        #   1. datetime supported + both given  → due_datetime
        #   2. only date supported              → due_date
        #   3. provider can't hold a due at all → overlay
        if fields.get("due_date"):
            if fields.get("due_time") and supports_datetime:
                service_data["due_datetime"] = f"{fields['due_date']} {fields['due_time']}:00"
            elif supports_due_date:
                service_data["due_date"] = fields["due_date"]
                # due_time alone (without datetime support) stays local
                if fields.get("due_time"):
                    unsynced["due_time"] = fields["due_time"]
                    need_uid = True
            else:
                unsynced["due_date"] = fields["due_date"]
                if fields.get("due_time"):
                    unsynced["due_time"] = fields["due_time"]
                need_uid = True
        elif fields.get("due_time"):
            unsynced["due_time"] = fields["due_time"]
            need_uid = True

        # notes / description
        if fields.get("notes"):
            if supports_description:
                service_data["description"] = fields["notes"]
            else:
                unsynced["notes"] = fields["notes"]
                need_uid = True

        # Everything not in the base field set → overlay
        for key, value in fields.items():
            if key not in _GENERIC_BASE_FIELDS and key not in unsynced:
                unsynced[key] = value
                need_uid = True

        if need_uid:
            try:
                before_uids = {item["uid"] for item in await self.async_read_tasks()}
            except Exception:  # noqa: BLE001
                _LOGGER.debug("Could not snapshot pre-create UIDs for %s", self._entity_id)

        await self._hass.services.async_call(
            "todo", "add_item", service_data,
            target={"entity_id": self._entity_id},
            blocking=True,
        )

        new_uid: str | None = None
        if need_uid:
            try:
                after_items = await self.async_read_tasks()
            except Exception:  # noqa: BLE001
                _LOGGER.warning(
                    "Could not re-read %s after create to discover new UID; "
                    "overlay fields may be lost", self._entity_id,
                )
                return None, unsynced
            new_candidates = [
                item["uid"] for item in after_items
                if item["uid"] not in before_uids
            ]
            if len(new_candidates) == 1:
                new_uid = new_candidates[0]
            elif new_candidates:
                # Fall back to title match when multiple new tasks appear
                # (race with another actor creating in parallel).
                title_lower = (fields.get("title") or "").lower()
                for item in reversed(after_items):
                    if (
                        item["uid"] in new_candidates
                        and (item.get("summary") or "").lower() == title_lower
                    ):
                        new_uid = item["uid"]
                        break
        return new_uid, unsynced

    async def async_update_task(self, task_uid: str, fields: dict) -> dict:
        """Send supported base fields to provider, return everything else as unsynced."""
        service_data: dict[str, Any] = {"item": task_uid}
        unsynced: dict[str, Any] = {}

        # Feature bits — the HA todo service layer rejects writes that the
        # entity's integration hasn't declared support for.  Route unsupported
        # fields to the overlay instead of letting the service call crash.
        state = self._hass.states.get(self._entity_id)
        features = (
            state.attributes.get("supported_features", 0)
            if state and state.attributes else 0
        )
        supports_datetime = bool(features & 32)   # SET_DUE_DATETIME_ON_ITEM
        supports_due_date = bool(features & 16)   # SET_DUE_DATE_ON_ITEM
        supports_description = bool(features & 64)  # SET_DESCRIPTION_ON_ITEM

        if "title" in fields:
            service_data["rename"] = fields["title"]
        if "completed" in fields:
            service_data["status"] = "completed" if fields["completed"] else "needs_action"
        if "notes" in fields:
            if supports_description:
                service_data["description"] = fields["notes"]
            else:
                unsynced["notes"] = fields["notes"]

        if "due_date" in fields:
            if fields["due_date"] is None:
                # Explicitly clearing due date — only push if provider can
                # carry a due date at all; otherwise drop silently (it was
                # never there).
                if supports_due_date or supports_datetime:
                    service_data["due_date"] = None
            elif fields.get("due_time") and supports_datetime:
                service_data["due_datetime"] = f"{fields['due_date']} {fields['due_time']}:00"
            elif "due_time" in fields and fields["due_time"] is None and supports_datetime:
                # Time explicitly cleared while date remains — set date at midnight
                # to force CalDAV to downgrade from due_datetime to due_date.
                service_data["due_datetime"] = f"{fields['due_date']} 00:00:00"
            elif supports_due_date:
                service_data["due_date"] = fields["due_date"]
                # due_time alone without datetime support → overlay
                if fields.get("due_time"):
                    unsynced["due_time"] = fields["due_time"]
            else:
                # Provider has no due-date concept — keep it all local
                unsynced["due_date"] = fields["due_date"]
                if "due_time" in fields:
                    unsynced["due_time"] = fields["due_time"]
        elif "due_time" in fields:
            # due_time changed but due_date didn't – treat as unsynced
            unsynced["due_time"] = fields["due_time"]

        for key, value in fields.items():
            if key not in _GENERIC_BASE_FIELDS and key not in unsynced:
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

        # HA's todo platform exposes MOVE as a WebSocket command `todo/item/move`,
        # NOT as a regular service — so `hass.services.async_call("todo", "move_item")`
        # fails with ServiceNotFound.  Instead we look up the TodoListEntity and
        # call `async_move_todo_item` directly, mirroring what HA's own WS handler
        # does in homeassistant/components/todo/__init__.py::websocket_handle_move.
        entity_component = self._hass.data.get("todo")
        if entity_component is None:
            _LOGGER.warning(
                "Cannot reorder %s: todo entity component not loaded",
                self._entity_id,
            )
            return False

        entity = entity_component.get_entity(self._entity_id)
        if entity is None:
            _LOGGER.warning(
                "Cannot reorder %s: entity not found in todo component",
                self._entity_id,
            )
            return False

        for i, uid in enumerate(task_uids):
            try:
                previous_uid = task_uids[i - 1] if i > 0 else None
                await entity.async_move_todo_item(
                    uid=uid, previous_uid=previous_uid
                )
            except Exception:  # noqa: BLE001
                _LOGGER.warning(
                    "Failed to move task %s via entity.async_move_todo_item",
                    uid, exc_info=True,
                )
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
            can_sync_assignee=True,
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
    def _build_monthly_phrase(pattern: str, dom, nth, weekdays, value: int) -> str | None:
        """Build the Todoist phrase for a monthly sub-pattern, or None if invalid."""
        if pattern == "day_of_month":
            if dom is None:
                return None
            day_token = "last day" if dom == "last" else _ordinal(int(dom))
            if value == 1:
                return f"every {day_token}"
            return f"every {value} months on the {day_token}"
        if pattern == "nth_weekday":
            if nth is None or not weekdays:
                return None
            wd_idx = weekdays[0]
            if not (0 <= wd_idx <= 6):
                return None
            nth_token = "last" if nth == "last" else _ordinal(int(nth))
            # Todoist's NL parser rejects compound nth-weekday + month-interval
            # phrases ("every 2 months on the last wednesday" → 400 Invalid
            # date format), so we always emit the simple form.  The custom
            # value > 1 stays in the overlay; the local compute honours it.
            return f"every {nth_token} {_WEEKDAY_NAMES[wd_idx]}"
        return None

    @staticmethod
    def _build_yearly_phrase(anniversary: str, value: int) -> str | None:
        """Build the Todoist phrase for a yearly anniversary anchor."""
        if not anniversary or len(anniversary) != 5 or anniversary[2] != "-":
            return None
        try:
            month = int(anniversary[:2])
            day = int(anniversary[3:5])
        except ValueError:
            return None
        if not (1 <= month <= 12 and 1 <= day <= 31):
            return None
        month_name = _MONTH_NAMES[month - 1]
        if value == 1:
            return f"every {day} {month_name}"
        return f"every {value} years on {day} {month_name}"

    @staticmethod
    def _build_recurrence_string(fields: dict) -> str | None:
        """Convert structured recurrence fields to a Todoist due_string."""
        # Recurrence is active if explicitly enabled OR if recurrence detail
        # fields are present (partial update from the card editor).
        _REC_DETAIL_KEYS = {"recurrence_value", "recurrence_unit", "recurrence_weekdays",
                            "recurrence_type", "recurrence_time", "recurrence_start_date",
                            "recurrence_end_date", "recurrence_month_pattern",
                            "recurrence_day_of_month", "recurrence_nth_week",
                            "recurrence_anniversary"}
        has_details = any(k in fields for k in _REC_DETAIL_KEYS)
        # Explicit disable always wins, even if detail fields are present
        # (the recurrence toggle sends all fields alongside enabled=false).
        if fields.get("recurrence_enabled") is False:
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
        month_pattern = fields.get("recurrence_month_pattern")
        dom = fields.get("recurrence_day_of_month")
        nth = fields.get("recurrence_nth_week")
        anniversary = fields.get("recurrence_anniversary")

        parts: list[str] = []

        # ---- Monthly sub-patterns -----------------------------------------
        if rtype != "weekdays" and unit == "months" and month_pattern:
            head = TodoistAdapter._build_monthly_phrase(
                month_pattern, dom, nth, weekdays, value,
            )
            if head:
                parts.append(head)
            else:
                # Fall back to plain "every N months" if the pattern is broken.
                parts.append("every month" if value == 1 else f"every {value} months")
        # ---- Yearly anchor (anniversary) ----------------------------------
        elif rtype != "weekdays" and unit == "years" and anniversary:
            head = TodoistAdapter._build_yearly_phrase(anniversary, value)
            if head:
                parts.append(head)
            else:
                parts.append("every year" if value == 1 else f"every {value} years")
        elif rtype == "weekdays":
            if not weekdays:
                weekdays = [0, 1, 2, 3, 4]  # Default: Mon-Fri
            day_names = [_WEEKDAY_NAMES[d] for d in sorted(weekdays) if 0 <= d <= 6]
            parts.append(f"every {', '.join(day_names)}")
        elif unit == "weeks" and weekdays:
            # New: weekly with weekday filter (replaces legacy "weekdays" mode).
            day_names = [_WEEKDAY_NAMES[d] for d in sorted(weekdays) if 0 <= d <= 6]
            if value == 1:
                parts.append(f"every {', '.join(day_names)}")
            elif len(day_names) == 1:
                parts.append(f"every {value} weeks on {day_names[0]}")
            else:
                # Todoist doesn't natively express "every 2 weeks on mon, fri".
                # Fall back to a simpler phrase + retain structured fields locally.
                parts.append(f"every {value} weeks")
        else:
            # Interval (hours/days/weeks/months/years without sub-pattern)
            unit_str = unit if unit in _VALID_RECURRENCE_UNITS else "days"
            if value == 1:
                singular = {"hours": "hour", "days": "day", "weeks": "week", "months": "month", "years": "year"}
                parts.append(f"every {singular.get(unit_str, unit_str)}")
            else:
                parts.append(f"every {value} {unit_str}")

        # Append "at HH:MM" only when meaningful:
        # - Skip for hourly intervals (Todoist returns 400)
        # - Skip "00:00" (card's default, not a deliberate choice)
        if rtime and rtime != "00:00" and unit != "hours":
            parts.append(f"at {rtime}")
        if start:
            parts.append(f"starting {start}")
        if end:
            # Safety: Todoist nullifies the entire due object when the end
            # date is before the next occurrence.  Compute a safe minimum.
            try:
                end_d = _date_cls.fromisoformat(end)
                today = _date_cls.today()
                if unit == "years":
                    min_end = today + timedelta(days=365 * value)
                elif unit == "months":
                    # Approximate: 31 days per month × value
                    min_end = today + timedelta(days=31 * value)
                elif unit == "weeks":
                    min_end = today + timedelta(weeks=value)
                elif unit == "hours":
                    min_end = today + timedelta(days=1)
                else:  # days
                    min_end = today + timedelta(days=value)
                if end_d < min_end:
                    end = min_end.isoformat()
                    _LOGGER.debug("Clamped recurrence end date to %s (before next occurrence ~%s)", end, min_end)
                parts.append(f"ending {end}")
            except ValueError:
                pass

        result = " ".join(parts) if parts else None
        return result

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
            "recurrence_month_pattern": None,
            "recurrence_day_of_month": None,
            "recurrence_nth_week": None,
            "recurrence_anniversary": None,
        }
        if due_obj is None or not getattr(due_obj, "is_recurring", False):
            return result

        result["recurrence_enabled"] = True
        due_string = getattr(due_obj, "string", "") or ""
        lower = due_string.lower().strip()

        # ---- Monthly: "every 2 months on the 24th" / "...on the last sat" --
        m_compound = re.match(
            r"every\s+(\d+)\s+months?\s+on\s+the\s+([\w-]+)(?:\s+(mon|tue|wed|thu|fri|sat|sun))?",
            lower,
        )
        if m_compound:
            value = int(m_compound.group(1))
            token = m_compound.group(2)
            wd = m_compound.group(3)
            parsed = _parse_monthly_token(token, wd, value)
            if parsed.get("recurrence_unit") == "months":
                result.update(parsed)
                _extract_aux(lower, result)
                _store_original(due_string, result)
                return result

        # ---- Yearly anniversary: "every 24 dec" / "every 2 years on 24 dec" --
        # Runs BEFORE monthly_simple so "every 24 dec" isn't misread as a
        # day-of-month pattern.
        y_compound = re.match(
            r"every\s+(\d+)\s+years?\s+on\s+(\d{1,2})\s+([a-z]{3,9})", lower
        )
        if y_compound:
            value = int(y_compound.group(1))
            day = int(y_compound.group(2))
            month_idx = _month_index(y_compound.group(3))
            if month_idx is not None:
                result["recurrence_value"] = value
                result["recurrence_unit"] = "years"
                result["recurrence_anniversary"] = f"{month_idx:02d}-{day:02d}"
                _extract_aux(lower, result)
                _store_original(due_string, result)
                return result

        y_simple = re.match(r"every\s+(\d{1,2})\s+([a-z]{3,9})\b", lower)
        if y_simple and not re.match(r"every\s+\d+\s+(hour|day|week|month|year)", lower):
            day = int(y_simple.group(1))
            month_idx = _month_index(y_simple.group(2))
            if month_idx is not None:
                result["recurrence_value"] = 1
                result["recurrence_unit"] = "years"
                result["recurrence_anniversary"] = f"{month_idx:02d}-{day:02d}"
                _extract_aux(lower, result)
                _store_original(due_string, result)
                return result

        # ---- "every N unit(s)" generic interval -----------------------------
        # Runs BEFORE monthly_simple so "every 2 days" isn't read as a
        # day-of-month=2 pattern.
        interval_match = re.match(
            r"every\s+(\d+)\s+(hour|day|week|month|year)s?\b", lower
        )
        plain_unit_match = re.match(r"every\s+(hour|day|week|month|year)\b", lower)

        if interval_match or plain_unit_match:
            pass  # handled below
        else:
            # ---- Monthly: "every 24th" / "every last day" / "every 2nd saturday" /
            # ---- "every last wednesday" --------------------------------------
            m_simple = re.match(
                r"every\s+([\w-]+)(?:\s+(mon|tue|wed|thu|fri|sat|sun|monday|tuesday|wednesday|thursday|friday|saturday|sunday|day))?",
                lower,
            )
            if m_simple:
                token = m_simple.group(1)
                second = m_simple.group(2)
                parsed = _parse_monthly_token(token, second, 1)
                if parsed.get("recurrence_unit") == "months":
                    result.update(parsed)
                    _extract_aux(lower, result)
                    _store_original(due_string, result)
                    return result

        if interval_match:
            result["recurrence_value"] = int(interval_match.group(1))
            result["recurrence_unit"] = interval_match.group(2) + "s"
            result["recurrence_type"] = "interval"
            # "every 2 weeks on <weekday>" — preserve the weekday filter so
            # the structured fields round-trip back to the card unchanged.
            if interval_match.group(2) == "week":
                wd_after = re.search(
                    r"on\s+((?:mon|tue|wed|thu|fri|sat|sun)(?:\s*,\s*(?:mon|tue|wed|thu|fri|sat|sun))*)",
                    lower,
                )
                if wd_after:
                    days = [d.strip() for d in wd_after.group(1).split(",")]
                    indices = []
                    for d in days:
                        try:
                            indices.append(_WEEKDAY_NAMES.index(d))
                        except ValueError:
                            pass
                    if indices:
                        result["recurrence_weekdays"] = sorted(indices)
        elif plain_unit_match:
            unit_match = re.match(r"every\s+(hour|day|week|month|year)", lower)
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
                    # Treat as weekly with weekday filter (interval+weeks).
                    result["recurrence_type"] = "interval"
                    result["recurrence_unit"] = "weeks"
                    result["recurrence_value"] = 1
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
            local = parsed.astimezone(dt_util.DEFAULT_TIME_ZONE)
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
                local = parsed.astimezone(dt_util.DEFAULT_TIME_ZONE)
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
        # When disabling recurrence, the API may have lost the time component.
        # Fall back to recurrence_time if due_time is missing.
        rec_time_fb = fields.get("recurrence_time")
        if not due_time and rec_time_fb and rec_time_fb != "00:00":
            due_time = rec_time_fb

        # Check if recurrence is being set or cleared
        recurrence_str = self._build_recurrence_string(fields)
        if recurrence_str:
            # Append due_time only if the recurrence string doesn't already
            # contain a meaningful time, and the unit is not "hours".
            # Treat "00:00" as "no time set" — it's the card's default.
            unit = fields.get("recurrence_unit", "days")
            rec_time = fields.get("recurrence_time")
            has_rec_time = rec_time and rec_time != "00:00"
            if due_time and due_time != "00:00" and unit != "hours" and not has_rec_time:
                # Insert "at HH:MM" before "ending"/"starting" — Todoist
                # ignores time tokens that appear after these keywords.
                if " ending " in recurrence_str:
                    params["due_string"] = recurrence_str.replace(" ending ", f" at {due_time} ending ", 1)
                elif " starting " in recurrence_str:
                    params["due_string"] = recurrence_str.replace(" starting ", f" at {due_time} starting ", 1)
                else:
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

            # Read reminders — best-effort, swallow API errors here so a
            # single failed reminders call doesn't break the whole task list.
            try:
                from .todoist_api import TodoistAPIError  # noqa: WPS433
                raw_reminders = await api.get_reminders(task.id)
            except TodoistAPIError as err:
                _LOGGER.debug("Could not read reminders for task %s: %s", task.id, err.message)
                raw_reminders = []
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

    async def async_create_task(self, fields: dict) -> tuple[str | None, dict]:
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

        # Todoist syncs nearly every field via the API; the caller still
        # writes the remaining overlay-only fields (recurrence_end_type,
        # recurrence_max_count, recurrence_remaining_count, assigned_person
        # display, …) via its own logic keyed on the returned UID.
        unsynced: dict[str, Any] = {}
        for key, value in fields.items():
            if key not in _TODOIST_PROVIDER_FIELDS:
                unsynced[key] = value
        # Monthly/yearly sub-patterns are emitted as a simplified Todoist
        # phrase (Todoist's NL parser rejects compound month-interval +
        # nth-weekday phrases), so the value must also live in overlay to
        # round-trip correctly.
        if (fields.get("recurrence_month_pattern") or fields.get("recurrence_anniversary")) \
                and "recurrence_value" in fields:
            unsynced["recurrence_value"] = fields["recurrence_value"]
        return task.id, unsynced

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
        if "due_date" in fields and fields["due_date"] is None:
            # Explicitly clearing due date — bypass merge to avoid recurrence overriding
            api_fields["due_string"] = "no date"
        elif _DUE_KEYS & fields.keys():
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
            else:
                # Unassign: explicitly clear assignee in Todoist
                api_fields["assignee_id"] = None
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
        # See async_create_task: monthly/yearly sub-pattern uses a simplified
        # Todoist phrase, so recurrence_value must live in overlay too.
        if (fields.get("recurrence_month_pattern") or fields.get("recurrence_anniversary")) \
                and "recurrence_value" in fields:
            unsynced["recurrence_value"] = fields["recurrence_value"]

        # Step 2: Send API updates.
        # When due changes, Todoist deletes all reminders.  Snapshot them
        # BEFORE the update so we can restore them afterwards.
        has_due_change = "due_string" in api_fields or "due_date" in api_fields or "due_datetime" in api_fields
        saved_reminders: list[int] | None = None
        if has_due_change:
            try:
                existing = await api.get_reminders(task_uid)
                saved_reminders = [r["minute_offset"] for r in existing if r.get("minute_offset") is not None]
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Could not snapshot reminders for %s: %s", task_uid, err)

        if "completed" in fields:
            try:
                if fields["completed"]:
                    await api.complete_task(task_uid)
                else:
                    await api.uncomplete_task(task_uid)
            except Exception:  # noqa: BLE001
                _LOGGER.warning("Todoist complete/uncomplete failed for %s", task_uid)
        if api_fields:
            await api.update_task(task_uid, **api_fields)

        # Sync reminders via API.  If the caller specified reminders, use
        # those.  Otherwise restore the snapshot we took before the due change.
        reminder_offsets: list[int] | None = None
        if "reminders" in fields:
            reminder_offsets = fields["reminders"]
        elif saved_reminders:
            reminder_offsets = saved_reminders
        if reminder_offsets is not None:
            await self._sync_reminders(task_uid, reminder_offsets)

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
        """Delta-sync reminder offsets to Todoist.

        Free Todoist accounts cannot create reminders with non-zero
        minute_offset (Premium-only feature).  We try to add the new
        reminders FIRST so that, if the API rejects them, we don't end
        up deleting the existing ones and leaving the task with nothing.
        """
        from .todoist_api import TodoistAPIError  # noqa: WPS433

        api = self._api
        try:
            existing = await api.get_reminders(task_uid)
        except TodoistAPIError as err:
            _LOGGER.warning(
                "Cannot read reminders for task %s: %s — skipping sync",
                task_uid, err.message,
            )
            return

        existing_map = {
            r.get("minute_offset"): r.get("id")
            for r in existing
            if r.get("minute_offset") is not None
        }
        new_set = set(new_offsets)

        # Step 1: try to ADD new reminders first.  If the API rejects any
        # of them (e.g. PREMIUM_ONLY for non-zero offsets on Free accounts),
        # abort the whole sync so we don't delete the existing reminders.
        offsets_to_add = [o for o in new_offsets if o not in existing_map]
        added_ids: list[str] = []
        for offset in offsets_to_add:
            try:
                result = await api.add_reminder(
                    task_uid, reminder_type="relative", minute_offset=offset
                )
                if result and result.get("id"):
                    added_ids.append(result["id"])
            except TodoistAPIError as err:
                if err.is_premium_only:
                    _LOGGER.warning(
                        "Todoist rejected reminder offset=%d for task %s: %s. "
                        "Reminders with non-zero offsets require Todoist Premium. "
                        "Aborting reminder sync to preserve existing reminders.",
                        offset, task_uid, err.message,
                    )
                else:
                    _LOGGER.warning(
                        "Todoist rejected reminder offset=%d for task %s: %s. "
                        "Aborting reminder sync.",
                        offset, task_uid, err.message,
                    )
                # Roll back: delete any reminders we just created in this call
                for rid in added_ids:
                    try:
                        await api.delete_reminder(rid)
                    except TodoistAPIError:
                        pass
                return

        # Step 2: all adds succeeded, now safe to delete the obsolete ones.
        for offset, rid in existing_map.items():
            if offset not in new_set:
                try:
                    await api.delete_reminder(rid)
                except TodoistAPIError as err:
                    _LOGGER.warning(
                        "Failed to delete obsolete reminder %s for task %s: %s",
                        rid, task_uid, err.message,
                    )


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
                        local_due = item.due.astimezone(dt_util.DEFAULT_TIME_ZONE)
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
