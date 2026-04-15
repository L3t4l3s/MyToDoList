"""The Home Tasks integration."""

import calendar
import logging
from datetime import date, datetime, timedelta, timezone

import voluptuous as vol

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HassJob, HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_call_later, async_track_time_interval
from homeassistant.util import dt as dt_util

from .const import DOMAIN, RECURRENCE_UNIT_SECONDS

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
from .overlay_store import ExternalTaskOverlayStore
from .store import HomeTasksStore
from .websocket_api import async_register_websocket_commands

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["todo", "sensor", "binary_sensor", "calendar"]
CARD_URL = "/home_tasks/home-tasks-card.js"
DATA_SETUP_DONE = f"{DOMAIN}_setup_done"
DATA_RECURRENCE_TIMERS = f"{DOMAIN}_recurrence_timers"
DATA_REMINDER_TIMERS = f"{DOMAIN}_reminder_timers"
DATA_DUE_CHECK_UNSUB = f"{DOMAIN}_due_check_unsub"
DATA_DUE_FIRED = f"{DOMAIN}_due_fired"
DATA_DUE_STARTUP_DONE = f"{DOMAIN}_due_startup_done"

DUE_CHECK_INTERVAL = timedelta(hours=1)


# ---------------------------------------------------------------------------
#  Setup
# ---------------------------------------------------------------------------

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Home Tasks component."""
    hass.data.setdefault(DOMAIN, {})
    await _async_register_card(hass)
    _async_register_services(hass)
    _async_register_due_checker(hass)
    return True


async def _async_register_card(hass: HomeAssistant) -> None:
    """Register websocket commands and serve static files (once)."""
    if hass.data.get(DATA_SETUP_DONE):
        return
    hass.data[DATA_SETUP_DONE] = True

    async_register_websocket_commands(hass)

    comp_path = hass.config.path(f"custom_components/{DOMAIN}")
    static_paths = [
        StaticPathConfig(
            CARD_URL,
            f"{comp_path}/home-tasks-card.js",
            cache_headers=False,
        ),
        StaticPathConfig(
            f"/brands/{DOMAIN}/icon.png",
            f"{comp_path}/icon.png",
            cache_headers=True,
        ),
        StaticPathConfig(
            f"/brands/{DOMAIN}/icon@2x.png",
            f"{comp_path}/icon@2x.png",
            cache_headers=True,
        ),
        StaticPathConfig(
            f"/brands/{DOMAIN}/logo.png",
            f"{comp_path}/icon.png",
            cache_headers=True,
        ),
    ]
    try:
        await hass.http.async_register_static_paths(static_paths)
    except RuntimeError:
        pass

    # Auto-register card JS so users don't need to add a Lovelace resource manually
    add_extra_js_url(hass, CARD_URL)
    _LOGGER.info("Home Tasks card served at %s", CARD_URL)


# ---------------------------------------------------------------------------
#  Events
# ---------------------------------------------------------------------------

def _build_event_data(entry_id: str, task: dict) -> dict:
    """Build common event data dict."""
    data = {
        "entry_id": entry_id,
        "task_id": task["id"],
        "task_title": task.get("title", ""),
    }
    if task.get("_entity_id"):
        data["entity_id"] = task["_entity_id"]
    if task.get("assigned_person"):
        data["assigned_person"] = task["assigned_person"]
    if task.get("due_date"):
        data["due_date"] = task["due_date"]
    if task.get("tags"):
        data["tags"] = task["tags"]
    return data


def _on_task_completed(hass: HomeAssistant, entry_id: str, task: dict) -> None:
    """Handle task completion: fire event, schedule recurrence, cancel reminders."""
    hass.bus.async_fire(f"{DOMAIN}_task_completed", _build_event_data(entry_id, task))
    _schedule_recurrence(hass, entry_id, task)
    _cancel_reminders(hass, task["id"])


def _on_task_created(hass: HomeAssistant, entry_id: str, task: dict) -> None:
    """Fire event when a task is created."""
    hass.bus.async_fire(f"{DOMAIN}_task_created", _build_event_data(entry_id, task))


def _on_task_deleted(hass: HomeAssistant, task_id: str) -> None:
    """Handle task deletion: cancel recurrence, reminders, and clean due-fired cache."""
    _cancel_recurrence(hass, task_id)
    _cancel_reminders(hass, task_id)
    hass.data.get(DATA_DUE_FIRED, {}).pop(task_id, None)


def _on_task_reopened(hass: HomeAssistant, entry_id: str, task: dict) -> None:
    """Fire event when a task is reopened and reschedule its reminders."""
    hass.bus.async_fire(f"{DOMAIN}_task_reopened", _build_event_data(entry_id, task))
    _schedule_reminders(hass, entry_id, task)


def _fire_assignment_event(
    hass: HomeAssistant, entry_id: str, task: dict, previous_person: str | None
) -> None:
    """Fire an event when a task's assigned person changes."""
    data = _build_event_data(entry_id, task)
    data["previous_person"] = previous_person
    hass.bus.async_fire(f"{DOMAIN}_task_assigned", data)


# ---------------------------------------------------------------------------
#  Due-date checker (hourly)
# ---------------------------------------------------------------------------

def _async_register_due_checker(hass: HomeAssistant) -> None:
    """Register the periodic due-date checker (once globally)."""
    if hass.data.get(DATA_DUE_CHECK_UNSUB):
        return

    @callback
    def _periodic_check(_now=None) -> None:
        hass.async_create_task(_async_check_due_dates(hass))

    unsub = async_track_time_interval(hass, _periodic_check, DUE_CHECK_INTERVAL, cancel_on_shutdown=True)
    hass.data[DATA_DUE_CHECK_UNSUB] = unsub
    _LOGGER.debug("Due-date checker registered, interval=%s", DUE_CHECK_INTERVAL)


def _schedule_startup_due_check(hass: HomeAssistant) -> None:
    """Schedule a single delayed due-date check after startup (once globally).

    Delayed by 120s so external todo entities from other integrations have time
    to finish loading before we try to read their tasks.
    """
    if hass.data.get(DATA_DUE_STARTUP_DONE):
        return
    hass.data[DATA_DUE_STARTUP_DONE] = True

    @callback
    def _delayed_check(_now):
        hass.async_create_task(_async_check_due_dates(hass))

    async_call_later(hass, 120, HassJob(_delayed_check, "startup_due_check", cancel_on_shutdown=True))
    _LOGGER.debug("Startup due-date check scheduled in 120s")


async def _async_check_due_dates(hass: HomeAssistant, _now=None) -> None:
    """Check all tasks for due/overdue and fire events once per day per task."""
    today = date.today().isoformat()
    fired = hass.data.setdefault(DATA_DUE_FIRED, {})
    stores = hass.data.get(DOMAIN, {})
    store_count = sum(1 for s in stores.values() if isinstance(s, HomeTasksStore))
    _LOGGER.debug("Due-date check: today=%s, stores=%d", today, store_count)

    for entry_id, store in stores.items():
        if not isinstance(store, HomeTasksStore):
            continue
        for task in store.tasks:
            _check_task_due(hass, entry_id, task, today, fired)

    # Also check external entities for due dates
    _check_external_due_dates(hass, today, fired)


def _check_task_due(hass: HomeAssistant, entry_id: str, task: dict, today: str, fired: dict) -> None:
    """Check a single task for due/overdue and fire events."""
    if task.get("completed"):
        return
    dd = task.get("due_date")
    if not dd:
        return
    task_id = task["id"]
    task_fired = fired.setdefault(task_id, {})

    event_data = _build_event_data(entry_id, task)

    if dd == today and task_fired.get("due") != today:
        _LOGGER.info("Firing task_due for '%s' (due=%s)", task.get("title"), dd)
        hass.bus.async_fire(f"{DOMAIN}_task_due", event_data)
        task_fired["due"] = today
    elif dd < today and task_fired.get("overdue") != today:
        _LOGGER.info("Firing task_overdue for '%s' (due=%s)", task.get("title"), dd)
        hass.bus.async_fire(f"{DOMAIN}_task_overdue", event_data)
        task_fired["overdue"] = today
    else:
        _LOGGER.debug(
            "Skipping task '%s': due=%s, fired=%s",
            task.get("title"), dd, task_fired,
        )


def _check_external_due_dates(hass: HomeAssistant, today: str, fired: dict) -> None:
    """Check external todo entities for due/overdue tasks."""
    stores = hass.data.get(DOMAIN, {})
    for entry_id, store in stores.items():
        if not isinstance(store, ExternalTaskOverlayStore):
            continue
        entity_id = store.entity_id
        # Read tasks from the external entity via HA state
        try:
            from .provider_adapters import _get_external_todo_items
            from .websocket_api import _merge_tasks_with_overlays
            external_items = _get_external_todo_items(hass, entity_id)
            tasks = _merge_tasks_with_overlays(external_items, store)
            for task in tasks:
                # Inject entity_id so events carry the external entity reference
                task["_entity_id"] = entity_id
                _check_task_due(hass, entry_id, task, today, fired)
        except (ValueError, Exception) as err:
            _LOGGER.debug("Could not check due dates for external entity %s: %s", entity_id, err)


# ---------------------------------------------------------------------------
#  Recurrence scheduling
# ---------------------------------------------------------------------------

def _parse_rec_time(task: dict) -> tuple[int, int]:
    """Return (hour, minute) for recurrence_time, defaulting to midnight."""
    rec_time = task.get("recurrence_time")
    if rec_time and isinstance(rec_time, str) and len(rec_time) == 5:
        try:
            return int(rec_time[:2]), int(rec_time[3:5])
        except ValueError:
            pass
    return 0, 0


def _check_end_date(task: dict, target: datetime) -> bool:
    """Return True if target exceeds the recurrence end date (meaning: stop).

    Comparison uses local date because end_date is user-specified in local time.
    """
    if task.get("recurrence_end_type") != "date":
        return False
    end_date_str = task.get("recurrence_end_date")
    if not end_date_str:
        return False
    try:
        end_date = date.fromisoformat(end_date_str)
        return target.astimezone(dt_util.DEFAULT_TIME_ZONE).date() > end_date
    except ValueError:
        return False


def _apply_start_date(task: dict, target: datetime) -> datetime:
    """Advance target to recurrence_start_date if target falls before it.

    Comparison uses local date because start_date is user-specified in local time.
    """
    start_date_str = task.get("recurrence_start_date")
    if not start_date_str:
        return target
    try:
        start_date = date.fromisoformat(start_date_str)
        local_target = target.astimezone(dt_util.DEFAULT_TIME_ZONE)
        if local_target.date() < start_date:
            t_h, t_m = _parse_rec_time(task)
            return local_target.replace(
                year=start_date.year, month=start_date.month, day=start_date.day,
                hour=t_h, minute=t_m, second=0, microsecond=0,
            )
    except ValueError:
        pass
    return target


def _compute_reopen_delay(task: dict, completed_at: datetime) -> float | None:
    """Compute seconds from now until the task should reopen.

    - hours: exact elapsed-based interval (e.g. every 3 h → reopen 3 h after completion)
    - days / weeks / months / weekdays: recurrence_time (or midnight) of the target day
    Returns None if recurrence is not configured or end conditions are met.
    """
    rec_type = task.get("recurrence_type", "interval")
    now = datetime.now(timezone.utc)
    t_h, t_m = _parse_rec_time(task)

    if rec_type == "weekdays":
        weekdays = task.get("recurrence_weekdays", [])
        if not weekdays:
            return None
        local_completed = completed_at.astimezone(dt_util.DEFAULT_TIME_ZONE)
        completed_weekday = local_completed.weekday()  # local weekday, not UTC
        min_days = min((w - completed_weekday) % 7 or 7 for w in weekdays)
        target = (local_completed + timedelta(days=min_days)).replace(
            hour=t_h, minute=t_m, second=0, microsecond=0
        )
        if _check_end_date(task, target):
            return None
        target = _apply_start_date(task, target)
        return (target.astimezone(timezone.utc) - now).total_seconds()

    unit = task.get("recurrence_unit")
    value = task.get("recurrence_value", 1)
    if not unit or unit not in RECURRENCE_UNIT_SECONDS:
        return None

    if unit == "hours":
        reopen_at = completed_at + timedelta(seconds=RECURRENCE_UNIT_SECONDS["hours"] * value)
        if _check_end_date(task, reopen_at):
            return None
        reopen_at = _apply_start_date(task, reopen_at)
        return (reopen_at.astimezone(timezone.utc) - now).total_seconds()

    # days / weeks / months / years → recurrence_time (or midnight) of target day in local timezone
    local_completed = completed_at.astimezone(dt_util.DEFAULT_TIME_ZONE)
    if unit == "days":
        target_local = local_completed + timedelta(days=value)
    elif unit == "weeks":
        target_local = local_completed + timedelta(weeks=value)
    elif unit == "years":
        year = local_completed.year + value
        day = min(local_completed.day, calendar.monthrange(year, local_completed.month)[1])
        target_local = local_completed.replace(year=year, day=day)
    else:  # months
        m = local_completed.month - 1 + value
        year = local_completed.year + m // 12
        month = m % 12 + 1
        day = min(local_completed.day, calendar.monthrange(year, month)[1])
        target_local = local_completed.replace(year=year, month=month, day=day)

    target_time = target_local.replace(hour=t_h, minute=t_m, second=0, microsecond=0)
    if _check_end_date(task, target_time):
        return None
    target_time = _apply_start_date(task, target_time)
    return (target_time.astimezone(timezone.utc) - now).total_seconds()


def _schedule_recurrence(hass: HomeAssistant, entry_id: str, task: dict, completed_at: datetime | None = None) -> None:
    """Schedule a task to reopen based on its recurrence settings."""
    timers = hass.data.setdefault(DATA_RECURRENCE_TIMERS, {})
    task_id = task["id"]

    _cancel_recurrence(hass, task_id)

    if completed_at is None:
        completed_at = datetime.now(timezone.utc)

    delay = _compute_reopen_delay(task, completed_at)
    if delay is None:
        return
    delay = max(0.0, delay)

    @callback
    def _reopen_task(_now):
        timers.pop(task_id, None)
        hass.async_create_task(_async_reopen_task(hass, entry_id, task_id))

    cancel = async_call_later(hass, delay, _reopen_task)
    timers[task_id] = cancel
    _LOGGER.debug("Scheduled recurrence for task %s in %.0f seconds", task_id, delay)


async def _async_reopen_task(hass: HomeAssistant, entry_id: str, task_id: str) -> None:
    """Reopen a recurring task and reset its sub-tasks."""
    stores = hass.data.get(DOMAIN, {})
    store = stores.get(entry_id)
    if store is None:
        return
    try:
        task = store.get_task(task_id)
    except ValueError:
        return

    if not task.get("recurrence_enabled"):
        return

    await store.async_reopen_task(task_id)
    _LOGGER.info("Recurring task '%s' reopened", task.get("title", task_id))


def _cancel_recurrence(hass: HomeAssistant, task_id: str) -> None:
    """Cancel a pending recurrence timer."""
    timers = hass.data.get(DATA_RECURRENCE_TIMERS, {})
    cancel = timers.pop(task_id, None)
    if cancel:
        cancel()


# ---------------------------------------------------------------------------
#  Reminder scheduling
# ---------------------------------------------------------------------------

def _compute_due_datetime(task: dict) -> datetime | None:
    """Return timezone-aware datetime for the task's due moment (local time).

    - due_date + due_time → exact datetime
    - due_date only → midnight of that day (local time)
    - no due_date → None
    """
    due_date = task.get("due_date")
    if not due_date:
        return None
    try:
        d = date.fromisoformat(due_date)
    except (ValueError, TypeError):
        return None
    due_time_str = task.get("due_time")
    if due_time_str:
        try:
            h, m = int(due_time_str[:2]), int(due_time_str[3:5])
        except (ValueError, TypeError, IndexError):
            h, m = 0, 0
    else:
        h, m = 0, 0
    return datetime(d.year, d.month, d.day, h, m, 0, tzinfo=dt_util.DEFAULT_TIME_ZONE)


def _schedule_reminders(hass: HomeAssistant, entry_id: str, task: dict) -> None:
    """Schedule async_call_later timers for all reminder offsets of a task."""
    task_id = task["id"]
    _cancel_reminders(hass, task_id)

    if task.get("completed"):
        return

    due_dt = _compute_due_datetime(task)
    if due_dt is None:
        return

    reminders = task.get("reminders", [])
    if not reminders:
        return

    timers = hass.data.setdefault(DATA_REMINDER_TIMERS, {})
    now = datetime.now(timezone.utc)

    for offset in reminders:
        target = due_dt - timedelta(minutes=offset)
        delay = (target.astimezone(timezone.utc) - now).total_seconds()
        if delay <= 0:
            continue  # already past — silent miss

        @callback
        def _fire_reminder(_now, _task=task, _offset=offset):
            key = f"{_task['id']}_r{_offset}"
            hass.data.get(DATA_REMINDER_TIMERS, {}).pop(key, None)
            event_data = {
                **_build_event_data(entry_id, _task),
                "reminder_offset_minutes": _offset,
            }
            hass.bus.async_fire(f"{DOMAIN}_task_reminder", event_data)

        cancel = async_call_later(hass, delay, _fire_reminder)
        timers[f"{task_id}_r{offset}"] = cancel
        _LOGGER.debug(
            "Scheduled reminder for task %s (offset %d min) in %.0f s",
            task_id, offset, delay,
        )


def _cancel_reminders(hass: HomeAssistant, task_id: str) -> None:
    """Cancel all pending reminder timers for a task."""
    timers = hass.data.get(DATA_REMINDER_TIMERS, {})
    prefix = f"{task_id}_r"
    keys = [k for k in list(timers) if k.startswith(prefix)]
    for key in keys:
        cancel = timers.pop(key, None)
        if cancel:
            cancel()


def _recover_reminder_timers(hass: HomeAssistant, entry_id: str, store: HomeTasksStore) -> None:
    """On startup, reschedule reminder timers for open tasks with due dates."""
    for task in store.tasks:
        if task.get("completed"):
            continue
        if not task.get("reminders"):
            continue
        if not task.get("due_date"):
            continue
        _schedule_reminders(hass, entry_id, task)


def _recover_recurrence_timers(hass: HomeAssistant, entry_id: str, store: HomeTasksStore) -> None:
    """On startup, recover timers for completed recurring tasks."""
    for task in store.tasks:
        if not task.get("completed") or not task.get("recurrence_enabled"):
            continue

        completed_at_str = task.get("completed_at")
        if not completed_at_str:
            continue
        try:
            completed_at = datetime.fromisoformat(completed_at_str)
            if completed_at.tzinfo is None:
                completed_at = completed_at.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue

        delay = _compute_reopen_delay(task, completed_at)
        if delay is None:
            continue

        if delay <= 0:
            hass.async_create_task(_async_reopen_task(hass, entry_id, task["id"]))
        else:
            _schedule_recurrence(hass, entry_id, task, completed_at=completed_at)


# ---------------------------------------------------------------------------
#  Services
# ---------------------------------------------------------------------------

def _resolve_store(hass: HomeAssistant, data: dict) -> tuple[str, HomeTasksStore]:
    """Find the store by entry_id or list_name."""
    entry_id = data.get("entry_id")
    list_name = data.get("list_name")

    if entry_id:
        store = hass.data.get(DOMAIN, {}).get(entry_id)
        if store is None or not isinstance(store, HomeTasksStore):
            raise vol.Invalid(f"No list found with entry_id: {entry_id}")
        return entry_id, store

    if list_name:
        entries = hass.config_entries.async_entries(DOMAIN)
        for entry in entries:
            name = entry.data.get("name", entry.title)
            if name.lower() == list_name.lower():
                store = hass.data.get(DOMAIN, {}).get(entry.entry_id)
                if store and isinstance(store, HomeTasksStore):
                    return entry.entry_id, store
        raise vol.Invalid(f"No list found with name: {list_name}")

    raise vol.Invalid("Either entry_id or list_name must be provided")


def _resolve_task(store: HomeTasksStore, data: dict) -> dict:
    """Find a task by task_id or task_title."""
    task_id = data.get("task_id")
    task_title = data.get("task_title")

    if task_id:
        return store.get_task(task_id)

    if task_title:
        matches = [t for t in store.tasks if t["title"].lower() == task_title.lower()]
        if not matches:
            raise ValueError(f"No task found with title: {task_title}")
        incomplete = [t for t in matches if not t.get("completed")]
        return incomplete[0] if incomplete else matches[0]

    raise ValueError("Either task_id or task_title must be provided")


async def _resolve_actor(hass: HomeAssistant, call: ServiceCall) -> str | None:
    """Resolve the actor name from a service call context (user or automation)."""
    user_id = call.context.user_id
    if not user_id:
        return None
    try:
        user = await hass.auth.async_get_user(user_id)
        return user.name if user else None
    except Exception:  # noqa: BLE001
        return None


def _async_register_services(hass: HomeAssistant) -> None:
    """Register integration services (once globally)."""
    if hass.services.has_service(DOMAIN, "add_task"):
        return

    async def async_handle_add_task(call: ServiceCall) -> None:
        entry_id, store = _resolve_store(hass, call.data)
        actor = await _resolve_actor(hass, call)
        task = await store.async_add_task(call.data["title"], actor=actor)
        kwargs = {}
        if "assigned_person" in call.data:
            kwargs["assigned_person"] = call.data["assigned_person"]
        if "due_date" in call.data:
            kwargs["due_date"] = call.data["due_date"]
        if "tags" in call.data:
            raw = call.data["tags"]
            kwargs["tags"] = [t.strip() for t in raw.split(",") if t.strip()]
        if kwargs:
            await store.async_update_task(task["id"], actor=actor, **kwargs)

    async def async_handle_complete_task(call: ServiceCall) -> None:
        _entry_id, store = _resolve_store(hass, call.data)
        actor = await _resolve_actor(hass, call)
        tag = call.data.get("tag")

        if tag:
            tag = tag.strip().lower()
            for task in store.tasks:
                if (
                    not task.get("completed")
                    and tag in (t.lower() for t in task.get("tags", []))
                ):
                    await store.async_update_task(task["id"], actor=actor, completed=True)
        else:
            task = _resolve_task(store, call.data)
            if not task.get("completed"):
                await store.async_update_task(task["id"], actor=actor, completed=True)

    async def async_handle_assign_task(call: ServiceCall) -> None:
        _entry_id, store = _resolve_store(hass, call.data)
        actor = await _resolve_actor(hass, call)
        task = _resolve_task(store, call.data)
        await store.async_update_task(task["id"], actor=actor, assigned_person=call.data["person"])

    async def async_handle_reopen_task(call: ServiceCall) -> None:
        _entry_id, store = _resolve_store(hass, call.data)
        actor = await _resolve_actor(hass, call)
        task_id = call.data.get("task_id")
        task_title = call.data.get("task_title")
        assigned_person = call.data.get("assigned_person")
        tag = call.data.get("tag")

        if task_id or task_title:
            # Reopen a single task
            task = _resolve_task(store, call.data)
            if task.get("completed"):
                await store.async_reopen_task(task["id"], actor=actor)
        elif assigned_person or tag:
            # Reopen completed tasks matching person and/or tag
            for task in store.tasks:
                if not task.get("completed"):
                    continue
                if assigned_person and task.get("assigned_person") != assigned_person:
                    continue
                if tag and tag.strip().lower() not in (
                    t.lower() for t in task.get("tags", [])
                ):
                    continue
                await store.async_reopen_task(task["id"], actor=actor)
        else:
            raise vol.Invalid(
                "Either task_id, task_title, assigned_person, or tag must be provided"
            )

    hass.services.async_register(
        DOMAIN, "add_task", async_handle_add_task,
        schema=vol.Schema({
            vol.Optional("entry_id"): cv.string,
            vol.Optional("list_name"): cv.string,
            vol.Required("title"): cv.string,
            vol.Optional("assigned_person"): cv.string,
            vol.Optional("due_date"): cv.string,
            vol.Optional("tags"): cv.string,
        }),
    )
    hass.services.async_register(
        DOMAIN, "complete_task", async_handle_complete_task,
        schema=vol.Schema({
            vol.Optional("entry_id"): cv.string,
            vol.Optional("list_name"): cv.string,
            vol.Optional("task_id"): cv.string,
            vol.Optional("task_title"): cv.string,
            vol.Optional("tag"): cv.string,
        }),
    )
    hass.services.async_register(
        DOMAIN, "assign_task", async_handle_assign_task,
        schema=vol.Schema({
            vol.Optional("entry_id"): cv.string,
            vol.Optional("list_name"): cv.string,
            vol.Optional("task_id"): cv.string,
            vol.Optional("task_title"): cv.string,
            vol.Required("person"): cv.string,
        }),
    )
    hass.services.async_register(
        DOMAIN, "reopen_task", async_handle_reopen_task,
        schema=vol.Schema({
            vol.Optional("entry_id"): cv.string,
            vol.Optional("list_name"): cv.string,
            vol.Optional("task_id"): cv.string,
            vol.Optional("task_title"): cv.string,
            vol.Optional("assigned_person"): cv.string,
            vol.Optional("tag"): cv.string,
        }),
    )
    _LOGGER.info("Home Tasks services registered")


# ---------------------------------------------------------------------------
#  Config entry lifecycle
# ---------------------------------------------------------------------------

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Home Tasks from a config entry."""
    await _async_register_card(hass)
    _async_register_services(hass)

    if entry.data.get("type") == "external":
        return await _async_setup_external_entry(hass, entry)

    return await _async_setup_native_entry(hass, entry)


async def _async_setup_native_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a native Home Tasks list from a config entry."""
    store = HomeTasksStore(hass, entry.entry_id)
    await store.async_load()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = store

    # Wire up callbacks
    store.on_task_completed = lambda task: _on_task_completed(hass, entry.entry_id, task)
    store.on_task_created = lambda task: _on_task_created(hass, entry.entry_id, task)
    store.on_task_deleted = lambda task_id: _on_task_deleted(hass, task_id)
    store.on_task_assigned = lambda task, prev: _fire_assignment_event(hass, entry.entry_id, task, prev)
    store.on_task_reopened = lambda task: _on_task_reopened(hass, entry.entry_id, task)
    store.on_reminders_changed = lambda task: _schedule_reminders(hass, entry.entry_id, task)

    # Recover any pending timers from before restart
    _recover_recurrence_timers(hass, entry.entry_id, store)
    _recover_reminder_timers(hass, entry.entry_id, store)

    # Schedule a delayed due-date check (120s) to let all integrations finish loading.
    # This ensures external todo entities are available when we check their tasks.
    _schedule_startup_due_check(hass)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_setup_external_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a linked external todo entity with an overlay store."""
    entity_id = entry.data.get("entity_id")
    if not entity_id:
        _LOGGER.error("External entry %s has no entity_id", entry.entry_id)
        return False

    overlay_store = ExternalTaskOverlayStore(hass, entity_id)
    await overlay_store.async_load()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = overlay_store

    # Instantiate the provider adapter.
    # Detect provider_type on the fly if missing (pre-1.7 entries) — do NOT call
    # async_update_entry here because that triggers a config entry reload which
    # would abort this setup mid-flight and cause transient "overlay not found" errors.
    from .provider_adapters import detect_provider_type, get_adapter  # noqa: WPS433

    config_data = dict(entry.data)
    if "provider_type" not in config_data:
        config_data["provider_type"] = detect_provider_type(hass, entity_id)
        _LOGGER.info("Detected provider_type '%s' for %s", config_data["provider_type"], entity_id)

    adapter = get_adapter(hass, entity_id, config_data)
    hass.data.setdefault(f"{DOMAIN}_adapters", {})[entity_id] = adapter

    _LOGGER.info(
        "Linked external todo entity: %s (provider: %s)",
        entity_id,
        adapter.provider_type,
    )
    # External entries do NOT forward to platforms (todo/sensor/binary_sensor)
    # because those entities are already managed by the external integration.

    _schedule_startup_due_check(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if entry.data.get("type") == "external":
        # External entries don't have platforms to unload
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        eid = entry.data.get("entity_id")
        if eid:
            hass.data.get(f"{DOMAIN}_adapters", {}).pop(eid, None)
        return True

    store = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if store and isinstance(store, HomeTasksStore):
        fired = hass.data.get(DATA_DUE_FIRED, {})
        for task in store.tasks:
            _cancel_recurrence(hass, task["id"])
            _cancel_reminders(hass, task["id"])
            fired.pop(task["id"], None)

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
