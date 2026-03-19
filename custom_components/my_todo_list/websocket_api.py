"""WebSocket API for My ToDo List."""

import logging

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN, MAX_REORDER_IDS, MAX_TITLE_LENGTH, MAX_LIST_NAME_LENGTH

_LOGGER = logging.getLogger(__name__)

# Voluptuous validators for constrained strings
_val_list_name = vol.All(str, vol.Length(min=1, max=MAX_LIST_NAME_LENGTH))
_val_title = vol.All(str, vol.Length(min=1, max=MAX_TITLE_LENGTH))
_val_id = vol.All(str, vol.Length(min=1, max=40))
_val_date = vol.Any(vol.All(str, vol.Match(r"^\d{4}-\d{2}-\d{2}$")), None)


@callback
def async_register_websocket_commands(hass: HomeAssistant) -> None:
    """Register WebSocket commands."""
    websocket_api.async_register_command(hass, ws_get_lists)
    websocket_api.async_register_command(hass, ws_create_list)
    websocket_api.async_register_command(hass, ws_rename_list)
    websocket_api.async_register_command(hass, ws_delete_list)
    websocket_api.async_register_command(hass, ws_get_tasks)
    websocket_api.async_register_command(hass, ws_add_task)
    websocket_api.async_register_command(hass, ws_update_task)
    websocket_api.async_register_command(hass, ws_delete_task)
    websocket_api.async_register_command(hass, ws_reorder_tasks)
    websocket_api.async_register_command(hass, ws_add_sub_item)
    websocket_api.async_register_command(hass, ws_update_sub_item)
    websocket_api.async_register_command(hass, ws_delete_sub_item)


def _handle_error(connection, msg_id, err):
    """Send a generic error without leaking internal details."""
    if isinstance(err, ValueError):
        # Send the validation message (safe, we control these)
        connection.send_error(msg_id, "invalid_request", str(err))
    else:
        _LOGGER.exception("Unexpected error in my_todo_list")
        connection.send_error(msg_id, "unknown_error", "An internal error occurred")


# --- List commands ---


@websocket_api.websocket_command({vol.Required("type"): "my_todo_list/get_lists"})
@websocket_api.async_response
async def ws_get_lists(hass, connection, msg):
    """Get all lists."""
    try:
        store = hass.data[DOMAIN]
        connection.send_result(msg["id"], {"lists": store.get_lists()})
    except Exception as err:
        _handle_error(connection, msg["id"], err)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "my_todo_list/create_list",
        vol.Required("name"): _val_list_name,
    }
)
@websocket_api.async_response
async def ws_create_list(hass, connection, msg):
    """Create a new list."""
    try:
        store = hass.data[DOMAIN]
        result = await store.async_create_list(msg["name"])
        connection.send_result(msg["id"], result)
    except Exception as err:
        _handle_error(connection, msg["id"], err)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "my_todo_list/rename_list",
        vol.Required("list_id"): _val_id,
        vol.Required("name"): _val_list_name,
    }
)
@websocket_api.async_response
async def ws_rename_list(hass, connection, msg):
    """Rename a list."""
    try:
        store = hass.data[DOMAIN]
        result = await store.async_rename_list(msg["list_id"], msg["name"])
        connection.send_result(msg["id"], result)
    except Exception as err:
        _handle_error(connection, msg["id"], err)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "my_todo_list/delete_list",
        vol.Required("list_id"): _val_id,
    }
)
@websocket_api.async_response
async def ws_delete_list(hass, connection, msg):
    """Delete a list."""
    try:
        store = hass.data[DOMAIN]
        await store.async_delete_list(msg["list_id"])
        connection.send_result(msg["id"])
    except Exception as err:
        _handle_error(connection, msg["id"], err)


# --- Task commands ---


@websocket_api.websocket_command(
    {
        vol.Required("type"): "my_todo_list/get_tasks",
        vol.Required("list_id"): _val_id,
    }
)
@websocket_api.async_response
async def ws_get_tasks(hass, connection, msg):
    """Get all tasks for a list."""
    try:
        store = hass.data[DOMAIN]
        tasks = store.get_tasks(msg["list_id"])
        connection.send_result(msg["id"], {"tasks": tasks})
    except Exception as err:
        _handle_error(connection, msg["id"], err)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "my_todo_list/add_task",
        vol.Required("list_id"): _val_id,
        vol.Required("title"): _val_title,
    }
)
@websocket_api.async_response
async def ws_add_task(hass, connection, msg):
    """Add a task."""
    try:
        store = hass.data[DOMAIN]
        task = await store.async_add_task(msg["list_id"], msg["title"])
        connection.send_result(msg["id"], task)
    except Exception as err:
        _handle_error(connection, msg["id"], err)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "my_todo_list/update_task",
        vol.Required("list_id"): _val_id,
        vol.Required("task_id"): _val_id,
        vol.Optional("title"): _val_title,
        vol.Optional("completed"): bool,
        vol.Optional("notes"): vol.All(str, vol.Length(max=5000)),
        vol.Optional("due_date"): _val_date,
    }
)
@websocket_api.async_response
async def ws_update_task(hass, connection, msg):
    """Update a task."""
    try:
        store = hass.data[DOMAIN]
        kwargs = {}
        for key in ("title", "completed", "notes", "due_date"):
            if key in msg:
                kwargs[key] = msg[key]
        task = await store.async_update_task(msg["list_id"], msg["task_id"], **kwargs)
        connection.send_result(msg["id"], task)
    except Exception as err:
        _handle_error(connection, msg["id"], err)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "my_todo_list/delete_task",
        vol.Required("list_id"): _val_id,
        vol.Required("task_id"): _val_id,
    }
)
@websocket_api.async_response
async def ws_delete_task(hass, connection, msg):
    """Delete a task."""
    try:
        store = hass.data[DOMAIN]
        await store.async_delete_task(msg["list_id"], msg["task_id"])
        connection.send_result(msg["id"])
    except Exception as err:
        _handle_error(connection, msg["id"], err)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "my_todo_list/reorder_tasks",
        vol.Required("list_id"): _val_id,
        vol.Required("task_ids"): vol.All(
            [_val_id], vol.Length(max=MAX_REORDER_IDS)
        ),
    }
)
@websocket_api.async_response
async def ws_reorder_tasks(hass, connection, msg):
    """Reorder tasks."""
    try:
        store = hass.data[DOMAIN]
        await store.async_reorder_tasks(msg["list_id"], msg["task_ids"])
        connection.send_result(msg["id"])
    except Exception as err:
        _handle_error(connection, msg["id"], err)


# --- Sub-item commands ---


@websocket_api.websocket_command(
    {
        vol.Required("type"): "my_todo_list/add_sub_item",
        vol.Required("list_id"): _val_id,
        vol.Required("task_id"): _val_id,
        vol.Required("title"): _val_title,
    }
)
@websocket_api.async_response
async def ws_add_sub_item(hass, connection, msg):
    """Add a sub-item."""
    try:
        store = hass.data[DOMAIN]
        sub = await store.async_add_sub_item(
            msg["list_id"], msg["task_id"], msg["title"]
        )
        connection.send_result(msg["id"], sub)
    except Exception as err:
        _handle_error(connection, msg["id"], err)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "my_todo_list/update_sub_item",
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
        store = hass.data[DOMAIN]
        kwargs = {}
        for key in ("title", "completed"):
            if key in msg:
                kwargs[key] = msg[key]
        sub = await store.async_update_sub_item(
            msg["list_id"], msg["task_id"], msg["sub_item_id"], **kwargs
        )
        connection.send_result(msg["id"], sub)
    except Exception as err:
        _handle_error(connection, msg["id"], err)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "my_todo_list/delete_sub_item",
        vol.Required("list_id"): _val_id,
        vol.Required("task_id"): _val_id,
        vol.Required("sub_item_id"): _val_id,
    }
)
@websocket_api.async_response
async def ws_delete_sub_item(hass, connection, msg):
    """Delete a sub-item."""
    try:
        store = hass.data[DOMAIN]
        await store.async_delete_sub_item(
            msg["list_id"], msg["task_id"], msg["sub_item_id"]
        )
        connection.send_result(msg["id"])
    except Exception as err:
        _handle_error(connection, msg["id"], err)
