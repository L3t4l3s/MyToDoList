"""The My ToDo List integration."""

import logging
from datetime import datetime, timezone

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_call_later

from .const import DOMAIN, RECURRENCE_UNIT_SECONDS
from .store import MyToDoListStore
from .websocket_api import async_register_websocket_commands

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["todo"]
CARD_URL = "/my_todo_list/my-todo-list-card.js"
DATA_SETUP_DONE = f"{DOMAIN}_setup_done"
DATA_RECURRENCE_TIMERS = f"{DOMAIN}_recurrence_timers"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the My ToDo List component."""
    hass.data.setdefault(DOMAIN, {})
    await _async_register_card(hass)
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
            f"{comp_path}/my-todo-list-card.js",
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

    # NOTE: The card JS must be added as a Lovelace resource manually:
    # URL: /my_todo_list/my-todo-list-card.js  Type: JavaScript Module
    _LOGGER.info(
        "My ToDo List card served at %s - ensure it is added as a "
        "Lovelace resource (JavaScript Module)",
        CARD_URL,
    )


def _schedule_recurrence(hass: HomeAssistant, entry_id: str, task: dict, delay_seconds: float | None = None) -> None:
    """Schedule a task to reopen after its recurrence interval."""
    timers = hass.data.setdefault(DATA_RECURRENCE_TIMERS, {})
    task_id = task["id"]

    # Cancel any existing timer for this task
    _cancel_recurrence(hass, task_id)

    unit = task.get("recurrence_unit")
    value = task.get("recurrence_value", 1)
    if not unit or unit not in RECURRENCE_UNIT_SECONDS:
        return

    if delay_seconds is None:
        delay_seconds = float(RECURRENCE_UNIT_SECONDS[unit] * value)

    def _reopen_task(_now):
        """Reopen the task after recurrence interval."""
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
        return  # Task was deleted

    if not task.get("recurrence_enabled"):
        return  # Recurrence was disabled while waiting

    # Reopen task without triggering the completion callback again
    task["completed"] = False
    task["completed_at"] = None
    # Reset sub-items
    for sub in task.get("sub_items", []):
        sub["completed"] = False
    await store._async_save()

    # Update HA entity state
    hass.bus.async_fire(f"{DOMAIN}_task_reopened", {"entry_id": entry_id, "task_id": task_id})
    _LOGGER.info("Recurring task '%s' reopened", task.get("title", task_id))


def _cancel_recurrence(hass: HomeAssistant, task_id: str) -> None:
    """Cancel a pending recurrence timer."""
    timers = hass.data.get(DATA_RECURRENCE_TIMERS, {})
    cancel = timers.pop(task_id, None)
    if cancel:
        cancel()


def _recover_recurrence_timers(hass: HomeAssistant, entry_id: str, store: MyToDoListStore) -> None:
    """On startup, recover timers for tasks that were completed with recurrence enabled."""
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
            # Should have reopened already — do it now
            hass.async_create_task(_async_reopen_task(hass, entry_id, task["id"]))
        else:
            _schedule_recurrence(hass, entry_id, task, delay_seconds=remaining)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up My ToDo List from a config entry."""
    await _async_register_card(hass)

    store = MyToDoListStore(hass, entry.entry_id)
    await store.async_load()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = store

    # Wire up recurrence callbacks
    store.on_task_completed = lambda task: _schedule_recurrence(hass, entry.entry_id, task)
    store.on_task_deleted = lambda task_id: _cancel_recurrence(hass, task_id)

    # Recover any pending recurrence timers from before restart
    _recover_recurrence_timers(hass, entry.entry_id, store)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Cancel all recurrence timers for this entry's tasks
    store = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if store:
        for task in store.tasks:
            _cancel_recurrence(hass, task["id"])

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
