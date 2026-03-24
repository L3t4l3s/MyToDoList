"""The Home Tasks integration."""

import logging
from datetime import date, datetime, timedelta, timezone

import voluptuous as vol

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_call_later, async_track_time_interval

from .const import DOMAIN, RECURRENCE_UNIT_SECONDS
from .store import HomeTasksStore
from .websocket_api import async_register_websocket_commands

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["todo", "sensor", "binary_sensor"]
CARD_URL = "/home_tasks/home-tasks-card.js"
DATA_SETUP_DONE = f"{DOMAIN}_setup_done"
DATA_RECURRENCE_TIMERS = f"{DOMAIN}_recurrence_timers"
DATA_DUE_CHECK_UNSUB = f"{DOMAIN}_due_check_unsub"
DATA_DUE_FIRED = f"{DOMAIN}_due_fired"

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
    if task.get("assigned_person"):
        data["assigned_person"] = task["assigned_person"]
    if task.get("due_date"):
        data["due_date"] = task["due_date"]
    return data


def _on_task_completed(hass: HomeAssistant, entry_id: str, task: dict) -> None:
    """Handle task completion: fire event and schedule recurrence."""
    hass.bus.async_fire(f"{DOMAIN}_task_completed", _build_event_data(entry_id, task))
    _schedule_recurrence(hass, entry_id, task)


def _on_task_created(hass: HomeAssistant, entry_id: str, task: dict) -> None:
    """Fire event when a task is created."""
    hass.bus.async_fire(f"{DOMAIN}_task_created", _build_event_data(entry_id, task))


def _on_task_deleted(hass: HomeAssistant, task_id: str) -> None:
    """Handle task deletion: cancel recurrence and clean due-fired cache."""
    _cancel_recurrence(hass, task_id)
    hass.data.get(DATA_DUE_FIRED, {}).pop(task_id, None)


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
    unsub = async_track_time_interval(hass, _async_check_due_dates, DUE_CHECK_INTERVAL)
    hass.data[DATA_DUE_CHECK_UNSUB] = unsub
    # Also run once on startup
    hass.async_create_task(_async_check_due_dates(hass))


async def _async_check_due_dates(hass: HomeAssistant, _now=None) -> None:
    """Check all tasks for due/overdue and fire events once per day per task."""
    today = date.today().isoformat()
    fired = hass.data.setdefault(DATA_DUE_FIRED, {})
    stores = hass.data.get(DOMAIN, {})

    for entry_id, store in stores.items():
        if not isinstance(store, HomeTasksStore):
            continue
        for task in store.tasks:
            if task.get("completed"):
                continue
            dd = task.get("due_date")
            if not dd:
                continue
            task_id = task["id"]
            task_fired = fired.setdefault(task_id, {})

            event_data = _build_event_data(entry_id, task)

            if dd == today and task_fired.get("due") != today:
                hass.bus.async_fire(f"{DOMAIN}_task_due", event_data)
                task_fired["due"] = today
            elif dd < today and task_fired.get("overdue") != today:
                hass.bus.async_fire(f"{DOMAIN}_task_overdue", event_data)
                task_fired["overdue"] = today


# ---------------------------------------------------------------------------
#  Recurrence scheduling
# ---------------------------------------------------------------------------

def _schedule_recurrence(hass: HomeAssistant, entry_id: str, task: dict, delay_seconds: float | None = None) -> None:
    """Schedule a task to reopen after its recurrence interval."""
    timers = hass.data.setdefault(DATA_RECURRENCE_TIMERS, {})
    task_id = task["id"]

    _cancel_recurrence(hass, task_id)

    unit = task.get("recurrence_unit")
    value = task.get("recurrence_value", 1)
    if not unit or unit not in RECURRENCE_UNIT_SECONDS:
        return

    if delay_seconds is None:
        delay_seconds = float(RECURRENCE_UNIT_SECONDS[unit] * value)

    def _reopen_task(_now):
        timers.pop(task_id, None)
        hass.async_create_task(_async_reopen_task(hass, entry_id, task_id))

    cancel = async_call_later(hass, delay_seconds, _reopen_task)
    timers[task_id] = cancel
    _LOGGER.debug("Scheduled recurrence for task %s in %s seconds", task_id, delay_seconds)


async def _async_reopen_task(hass: HomeAssistant, entry_id: str, task_id: str) -> None:
    """Reopen a recurring task and reset its sub-items."""
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

    task["completed"] = False
    task["completed_at"] = None
    for sub in task.get("sub_items", []):
        sub["completed"] = False
    await store._async_save()

    event_data = _build_event_data(entry_id, task)
    hass.bus.async_fire(f"{DOMAIN}_task_reopened", event_data)
    _LOGGER.info("Recurring task '%s' reopened", task.get("title", task_id))


def _cancel_recurrence(hass: HomeAssistant, task_id: str) -> None:
    """Cancel a pending recurrence timer."""
    timers = hass.data.get(DATA_RECURRENCE_TIMERS, {})
    cancel = timers.pop(task_id, None)
    if cancel:
        cancel()


def _recover_recurrence_timers(hass: HomeAssistant, entry_id: str, store: HomeTasksStore) -> None:
    """On startup, recover timers for completed recurring tasks."""
    now = datetime.now(timezone.utc)
    for task in store.tasks:
        if not task.get("completed") or not task.get("recurrence_enabled") or not task.get("recurrence_unit"):
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

        unit_seconds = RECURRENCE_UNIT_SECONDS.get(task.get("recurrence_unit"), 0)
        interval_seconds = unit_seconds * task.get("recurrence_value", 1)
        if interval_seconds <= 0:
            continue

        elapsed = (now - completed_at).total_seconds()
        remaining = interval_seconds - elapsed

        if remaining <= 0:
            hass.async_create_task(_async_reopen_task(hass, entry_id, task["id"]))
        else:
            _schedule_recurrence(hass, entry_id, task, delay_seconds=remaining)


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


def _async_register_services(hass: HomeAssistant) -> None:
    """Register integration services (once globally)."""
    if hass.services.has_service(DOMAIN, "add_task"):
        return

    async def async_handle_add_task(call: ServiceCall) -> None:
        entry_id, store = _resolve_store(hass, call.data)
        task = await store.async_add_task(call.data["title"])
        kwargs = {}
        if "assigned_person" in call.data:
            kwargs["assigned_person"] = call.data["assigned_person"]
        if "due_date" in call.data:
            kwargs["due_date"] = call.data["due_date"]
        if kwargs:
            await store.async_update_task(task["id"], **kwargs)

    async def async_handle_complete_task(call: ServiceCall) -> None:
        _entry_id, store = _resolve_store(hass, call.data)
        task = _resolve_task(store, call.data)
        if not task.get("completed"):
            await store.async_update_task(task["id"], completed=True)

    async def async_handle_assign_task(call: ServiceCall) -> None:
        _entry_id, store = _resolve_store(hass, call.data)
        task = _resolve_task(store, call.data)
        await store.async_update_task(task["id"], assigned_person=call.data["person"])

    hass.services.async_register(
        DOMAIN, "add_task", async_handle_add_task,
        schema=vol.Schema({
            vol.Optional("entry_id"): cv.string,
            vol.Optional("list_name"): cv.string,
            vol.Required("title"): cv.string,
            vol.Optional("assigned_person"): cv.string,
            vol.Optional("due_date"): cv.string,
        }),
    )
    hass.services.async_register(
        DOMAIN, "complete_task", async_handle_complete_task,
        schema=vol.Schema({
            vol.Optional("entry_id"): cv.string,
            vol.Optional("list_name"): cv.string,
            vol.Optional("task_id"): cv.string,
            vol.Optional("task_title"): cv.string,
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
    _LOGGER.info("Home Tasks services registered")


# ---------------------------------------------------------------------------
#  Config entry lifecycle
# ---------------------------------------------------------------------------

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Home Tasks from a config entry."""
    await _async_register_card(hass)
    _async_register_services(hass)

    store = HomeTasksStore(hass, entry.entry_id)
    await store.async_load()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = store

    # Wire up callbacks
    store.on_task_completed = lambda task: _on_task_completed(hass, entry.entry_id, task)
    store.on_task_created = lambda task: _on_task_created(hass, entry.entry_id, task)
    store.on_task_deleted = lambda task_id: _on_task_deleted(hass, task_id)
    store.on_task_assigned = lambda task, prev: _fire_assignment_event(hass, entry.entry_id, task, prev)

    # Recover any pending recurrence timers from before restart
    _recover_recurrence_timers(hass, entry.entry_id, store)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    store = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if store:
        for task in store.tasks:
            _cancel_recurrence(hass, task["id"])

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
