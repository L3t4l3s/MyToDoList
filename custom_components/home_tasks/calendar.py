"""Calendar platform for Home Tasks integration.

Creates a calendar entity per native list that shows all tasks with a due
date as calendar events.  Tasks with due_time become timed events; tasks
with only due_date become all-day events.  Completed tasks are excluded.
"""

from datetime import date, datetime, timedelta, timezone

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.util import dt as dt_util

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up calendar entity from a config entry."""
    if entry.data.get("type") == "external":
        return  # External entries are managed by their own integration
    store = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HomeTasksCalendarEntity(entry, store)])


class HomeTasksCalendarEntity(CalendarEntity):
    """Calendar view of tasks with due dates in a Home Tasks list."""

    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry, store) -> None:
        self._entry = entry
        self._store = store
        self._attr_name = f"{entry.data.get('name', entry.title)} Calendar"
        self._attr_unique_id = f"{entry.entry_id}_calendar"

    async def async_added_to_hass(self) -> None:
        """Register store listener so calendar updates on any data change."""
        self.async_on_remove(
            self._store.async_add_listener(self._handle_store_update)
        )

    @callback
    def _handle_store_update(self) -> None:
        self.async_write_ha_state()

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event (used for the entity state)."""
        now = datetime.now(timezone.utc)
        today = now.date()
        best: CalendarEvent | None = None
        best_key = None

        for task in self._store.tasks:
            if task.get("completed") or not task.get("due_date"):
                continue
            evt = self._task_to_event(task)
            if evt is None:
                continue
            # Sort key: timed events by their start datetime, all-day by date
            if isinstance(evt.start, datetime):
                key = evt.start
            else:
                key = datetime.combine(evt.start, datetime.min.time(), tzinfo=timezone.utc)
            # Only consider events not yet past
            if isinstance(evt.end, datetime):
                if evt.end < now:
                    continue
            elif isinstance(evt.end, date):
                if evt.end <= today:
                    continue
            if best_key is None or key < best_key:
                best = evt
                best_key = key

        return best

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Return all task events in the given time range."""
        events: list[CalendarEvent] = []
        for task in self._store.tasks:
            if task.get("completed") or not task.get("due_date"):
                continue
            evt = self._task_to_event(task)
            if evt is None:
                continue
            # Check overlap with the requested range
            if isinstance(evt.start, datetime):
                evt_start = evt.start
                evt_end = evt.end
            else:
                # All-day: convert to datetimes for comparison
                evt_start = datetime.combine(evt.start, datetime.min.time(), tzinfo=start_date.tzinfo)
                evt_end = datetime.combine(evt.end, datetime.min.time(), tzinfo=start_date.tzinfo)
            if evt_end > start_date and evt_start < end_date:
                events.append(evt)
        return events

    @staticmethod
    def _task_to_event(task: dict) -> CalendarEvent | None:
        """Convert a task dict to a CalendarEvent."""
        due_date_str = task.get("due_date")
        if not due_date_str:
            return None
        try:
            due_date = date.fromisoformat(due_date_str)
        except (ValueError, TypeError):
            return None

        due_time_str = task.get("due_time")
        summary = task.get("title", "")
        description = HomeTasksCalendarEntity._build_description(task)
        uid = task.get("id")

        if due_time_str:
            try:
                h, m = int(due_time_str[:2]), int(due_time_str[3:5])
                local_tz = dt_util.DEFAULT_TIME_ZONE
                start = datetime(due_date.year, due_date.month, due_date.day,
                                 h, m, tzinfo=local_tz)
                end = start + timedelta(hours=1)
                return CalendarEvent(
                    start=start, end=end,
                    summary=summary, description=description, uid=uid,
                )
            except (ValueError, TypeError, IndexError):
                pass

        # All-day event
        return CalendarEvent(
            start=due_date,
            end=due_date + timedelta(days=1),
            summary=summary, description=description, uid=uid,
        )

    @staticmethod
    def _build_description(task: dict) -> str | None:
        """Build a rich description from notes + task metadata."""
        parts: list[str] = []

        # Notes first (the primary content)
        if task.get("notes"):
            parts.append(task["notes"])

        # Metadata lines
        meta: list[str] = []
        pri = task.get("priority")
        if pri:
            label = {1: "Low", 2: "Medium", 3: "High"}.get(pri, str(pri))
            meta.append(f"⚡ Priority: {label}")

        person = task.get("assigned_person")
        if person:
            meta.append(f"👤 {person}")

        tags = task.get("tags")
        if tags:
            meta.append(" ".join(f"#{t}" for t in tags))

        subs = task.get("sub_items") or []
        if subs:
            done = sum(1 for s in subs if s.get("completed"))
            meta.append(f"☑ Sub-tasks: {done}/{len(subs)}")

        reminders = task.get("reminders") or []
        if reminders:
            labels = []
            for r in reminders:
                if r == 0:
                    labels.append("at due time")
                elif r < 60:
                    labels.append(f"{r} min before")
                elif r == 60:
                    labels.append("1h before")
                elif r < 1440:
                    labels.append(f"{r // 60}h before")
                else:
                    labels.append(f"{r // 1440}d before")
            meta.append(f"⏰ {', '.join(labels)}")

        if not parts and not meta:
            return None
        if meta:
            parts.append("\n".join(meta))
        return "\n\n".join(parts)
