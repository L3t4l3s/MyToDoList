"""WebSocket API for Home Tasks - extended features (sub-items, reorder)."""

import logging

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN, MAX_REORDER_IDS, MAX_RECURRENCE_VALUE, MAX_REMINDER_OFFSET_MINUTES, MAX_REMINDERS_PER_TASK, MAX_TAGS_PER_TASK, MAX_TITLE_LENGTH, VALID_RECURRENCE_UNITS

_LOGGER = logging.getLogger(__name__)

_val_title = vol.All(str, vol.Length(min=1, max=MAX_TITLE_LENGTH))
_val_id = vol.All(str, vol.Length(min=1, max=40))
_val_date = vol.Any(vol.All(str, vol.Match(r"^\d{4}-\d{2}-\d{2}$")), None)
_val_time = vol.Any(vol.All(str, vol.Match(r"^\d{2}:\d{2}$")), None)


@callback
def async_register_websocket_commands(hass: HomeAssistant) -> None:
    """Register WebSocket commands."""
    websocket_api.async_register_command(hass, ws_get_lists)
    websocket_api.async_register_command(hass, ws_get_tasks)
    websocket_api.async_register_command(hass, ws_add_task)
    websocket_api.async_register_command(hass, ws_update_task)
    websocket_api.async_register_command(hass, ws_delete_task)
    websocket_api.async_register_command(hass, ws_reorder_tasks)
    websocket_api.async_register_command(hass, ws_add_sub_item)
    websocket_api.async_register_command(hass, ws_update_sub_item)
    websocket_api.async_register_command(hass, ws_delete_sub_item)


def _get_store(hass, entry_id):
    """Get store for a config entry."""
    stores = hass.data.get(DOMAIN, {})
    store = stores.get(entry_id)
    if store is None:
        raise ValueError("List not found")
    return store


def _handle_error(connection, msg_id, err):
    """Send error without leaking internals."""
    if isinstance(err, ValueError):
        connection.send_error(msg_id, "invalid_request", str(err))
    else:
        _LOGGER.exception("Unexpected error in home_tasks")
        connection.send_error(msg_id, "unknown_error", "An internal error occurred")


# --- List overview (returns config entries as lists) ---


@websocket_api.websocket_command({vol.Required("type"): "home_tasks/get_lists"})
@websocket_api.async_response
async def ws_get_lists(hass, connection, msg):
    """Get all lists (config entries)."""
    try:
        stores = hass.data.get(DOMAIN, {})
        entries = hass.config_entries.async_entries(DOMAIN)
        lists = []
        for entry in entries:
            store = stores.get(entry.entry_id)
            lists.append({
                "id": entry.entry_id,
                "name": entry.data.get("name", entry.title),
                "task_count": len(store.tasks) if store else 0,
            })
        connection.send_result(msg["id"], {"lists": lists})
    except Exception as err:
        _handle_error(connection, msg["id"], err)


# --- Task commands (list_id = entry_id) ---


@websocket_api.websocket_command(
    {
        vol.Required("type"): "home_tasks/get_tasks",
        vol.Required("list_id"): _val_id,
    }
)
@websocket_api.async_response
async def ws_get_tasks(hass, connection, msg):
    """Get all tasks for a list."""
    try:
        store = _get_store(hass, msg["list_id"])
        connection.send_result(msg["id"], {"tasks": store.tasks})
    except Exception as err:
        _handle_error(connection, msg["id"], err)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "home_tasks/add_task",
        vol.Required("list_id"): _val_id,
        vol.Required("title"): _val_title,
    }
)
@websocket_api.async_response
async def ws_add_task(hass, connection, msg):
    """Add a task."""
    try:
        store = _get_store(hass, msg["list_id"])
        task = await store.async_add_task(msg["title"])
        connection.send_result(msg["id"], task)
    except Exception as err:
        _handle_error(connection, msg["id"], err)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "home_tasks/update_task",
        vol.Required("list_id"): _val_id,
        vol.Required("task_id"): _val_id,
        vol.Optional("title"): _val_title,
        vol.Optional("completed"): bool,
        vol.Optional("notes"): vol.All(str, vol.Length(max=5000)),
        vol.Optional("due_date"): _val_date,
        vol.Optional("due_time"): _val_time,
        vol.Optional("reminders"): vol.All(
            list,
            vol.Length(max=MAX_REMINDERS_PER_TASK),
            [vol.All(int, vol.Range(min=0, max=MAX_REMINDER_OFFSET_MINUTES))],
        ),
        vol.Optional("priority"): vol.Any(vol.In([1, 2, 3]), None),
        vol.Optional("recurrence_value"): vol.All(int, vol.Range(min=1, max=MAX_RECURRENCE_VALUE)),
        vol.Optional("recurrence_unit"): vol.Any(vol.In(list(VALID_RECURRENCE_UNITS)), None),
        vol.Optional("recurrence_enabled"): bool,
        vol.Optional("recurrence_type"): vol.In(["interval", "weekdays"]),
        vol.Optional("recurrence_weekdays"): vol.All(list, [vol.All(int, vol.Range(min=0, max=6))]),
        vol.Optional("assigned_person"): vol.Any(str, None),
        vol.Optional("tags"): vol.All(list, vol.Length(max=MAX_TAGS_PER_TASK)),
    }
)
@websocket_api.async_response
async def ws_update_task(hass, connection, msg):
    """Update a task."""
    try:
        store = _get_store(hass, msg["list_id"])
        kwargs = {}
        for key in ("title", "completed", "notes", "due_date", "due_time", "reminders", "priority", "recurrence_value", "recurrence_unit", "recurrence_enabled", "recurrence_type", "recurrence_weekdays", "assigned_person", "tags"):
            if key in msg:
                kwargs[key] = msg[key]
        task = await store.async_update_task(msg["task_id"], **kwargs)
        connection.send_result(msg["id"], task)
    except Exception as err:
        _handle_error(connection, msg["id"], err)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "home_tasks/delete_task",
        vol.Required("list_id"): _val_id,
        vol.Required("task_id"): _val_id,
    }
)
@websocket_api.async_response
async def ws_delete_task(hass, connection, msg):
    """Delete a task."""
    try:
        store = _get_store(hass, msg["list_id"])
        await store.async_delete_task(msg["task_id"])
        connection.send_result(msg["id"])
    except Exception as err:
        _handle_error(connection, msg["id"], err)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "home_tasks/reorder_tasks",
        vol.Required("list_id"): _val_id,
        vol.Required("task_ids"): vol.All([_val_id], vol.Length(max=MAX_REORDER_IDS)),
    }
)
@websocket_api.async_response
async def ws_reorder_tasks(hass, connection, msg):
    """Reorder tasks."""
    try:
        store = _get_store(hass, msg["list_id"])
        await store.async_reorder_tasks(msg["task_ids"])
        connection.send_result(msg["id"])
    except Exception as err:
        _handle_error(connection, msg["id"], err)


# --- Sub-item commands ---


@websocket_api.websocket_command(
    {
        vol.Required("type"): "home_tasks/add_sub_item",
        vol.Required("list_id"): _val_id,
        vol.Required("task_id"): _val_id,
        vol.Required("title"): _val_title,
    }
)
@websocket_api.async_response
async def ws_add_sub_item(hass, connection, msg):
    """Add a sub-item."""
    try:
        store = _get_store(hass, msg["list_id"])
        sub = await store.async_add_sub_item(msg["task_id"], msg["title"])
        connection.send_result(msg["id"], sub)
    except Exception as err:
        _handle_error(connection, msg["id"], err)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "home_tasks/update_sub_item",
        vol.Required("list_id"): _val_id,
        vol.Required("task_id"): _val_id,
        vol.Required("sub_item_id"): _val_id,
        vol.Optional("title"): _val_title,
        vol.Optional("completed"): bool,
    }
)
@websocket_api.async_response
async def ws_update_sub_item(hass, connection, msg):
    """Update a sub-item."""
    try:
        store = _get_store(hass, msg["list_id"])
        kwargs = {}
        for key in ("title", "completed"):
            if key in msg:
                kwargs[key] = msg[key]
        sub = await store.async_update_sub_item(msg["task_id"], msg["sub_item_id"], **kwargs)
        connection.send_result(msg["id"], sub)
    except Exception as err:
        _handle_error(connection, msg["id"], err)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "home_tasks/delete_sub_item",
        vol.Required("list_id"): _val_id,
        vol.Required("task_id"): _val_id,
        vol.Required("sub_item_id"): _val_id,
    }
)
@websocket_api.async_response
async def ws_delete_sub_item(hass, connection, msg):
    """Delete a sub-item."""
    try:
        store = _get_store(hass, msg["list_id"])
        await store.async_delete_sub_item(msg["task_id"], msg["sub_item_id"])
        connection.send_result(msg["id"])
    except Exception as err:
        _handle_error(connection, msg["id"], err)
