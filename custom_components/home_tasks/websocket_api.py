"""WebSocket API for Home Tasks - extended features (sub-tasks, reorder, external)."""

import logging

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN, MAX_REORDER_IDS, MAX_RECURRENCE_VALUE, MAX_REMINDER_OFFSET_MINUTES, MAX_REMINDERS_PER_TASK, MAX_SUB_TASKS_PER_TASK, MAX_TAGS_PER_TASK, MAX_TITLE_LENGTH, VALID_RECURRENCE_UNITS
from .overlay_store import ExternalTaskOverlayStore, OVERLAY_FIELDS

_LOGGER = logging.getLogger(__name__)

_val_title = vol.All(str, vol.Length(min=1, max=MAX_TITLE_LENGTH))
_val_id = vol.All(str, vol.Length(min=1, max=40))
_val_date = vol.Any(vol.All(str, vol.Match(r"^\d{4}-\d{2}-\d{2}$")), None)
_val_time = vol.Any(vol.All(str, vol.Match(r"^\d{2}:\d{2}$")), None)


@callback
def async_register_websocket_commands(hass: HomeAssistant) -> None:
    """Register WebSocket commands."""
    # Native list commands
    websocket_api.async_register_command(hass, ws_get_lists)
    websocket_api.async_register_command(hass, ws_get_tasks)
    websocket_api.async_register_command(hass, ws_add_task)
    websocket_api.async_register_command(hass, ws_update_task)
    websocket_api.async_register_command(hass, ws_delete_task)
    websocket_api.async_register_command(hass, ws_reorder_tasks)
    websocket_api.async_register_command(hass, ws_add_sub_task)
    websocket_api.async_register_command(hass, ws_update_sub_task)
    websocket_api.async_register_command(hass, ws_delete_sub_task)
    websocket_api.async_register_command(hass, ws_reorder_sub_tasks)
    websocket_api.async_register_command(hass, ws_move_task)
    # External list commands
    websocket_api.async_register_command(hass, ws_get_external_lists)
    websocket_api.async_register_command(hass, ws_get_external_tasks)
    websocket_api.async_register_command(hass, ws_update_external_overlay)
    websocket_api.async_register_command(hass, ws_add_external_sub_task)
    websocket_api.async_register_command(hass, ws_update_external_sub_task)
    websocket_api.async_register_command(hass, ws_delete_external_sub_task)
    websocket_api.async_register_command(hass, ws_reorder_external_sub_tasks)
    websocket_api.async_register_command(hass, ws_delete_external_overlay)


def _get_store(hass, entry_id):
    """Get native HomeTasksStore for a config entry."""
    from .store import HomeTasksStore

    stores = hass.data.get(DOMAIN, {})
    store = stores.get(entry_id)
    if store is None:
        raise ValueError("List not found")
    if not isinstance(store, HomeTasksStore):
        raise ValueError("This command is not supported for external lists")
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
    """Get all lists (native config entries only)."""
    try:
        from .store import HomeTasksStore

        stores = hass.data.get(DOMAIN, {})
        entries = hass.config_entries.async_entries(DOMAIN)
        lists = []
        for entry in entries:
            if entry.data.get("type") == "external":
                continue  # external lists handled by ws_get_external_lists
            store = stores.get(entry.entry_id)
            lists.append({
                "id": entry.entry_id,
                "name": entry.data.get("name", entry.title),
                "task_count": len(store.tasks) if store and isinstance(store, HomeTasksStore) else 0,
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
        actor = connection.user.name if connection.user else None
        task = await store.async_add_task(msg["title"], actor=actor)
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
        vol.Optional("recurrence_start_date"): _val_date,
        vol.Optional("recurrence_time"): _val_time,
        vol.Optional("recurrence_end_type"): vol.In(["none", "date", "count"]),
        vol.Optional("recurrence_end_date"): _val_date,
        vol.Optional("recurrence_max_count"): vol.Any(vol.All(int, vol.Range(min=1)), None),
        vol.Optional("recurrence_remaining_count"): vol.Any(vol.All(int, vol.Range(min=0)), None),
        vol.Optional("assigned_person"): vol.Any(str, None),
        vol.Optional("tags"): vol.All(list, vol.Length(max=MAX_TAGS_PER_TASK)),
    }
)
@websocket_api.async_response
async def ws_update_task(hass, connection, msg):
    """Update a task."""
    try:
        store = _get_store(hass, msg["list_id"])
        actor = connection.user.name if connection.user else None
        kwargs = {}
        for key in ("title", "completed", "notes", "due_date", "due_time", "reminders", "priority", "recurrence_value", "recurrence_unit", "recurrence_enabled", "recurrence_type", "recurrence_weekdays", "recurrence_start_date", "recurrence_time", "recurrence_end_type", "recurrence_end_date", "recurrence_max_count", "recurrence_remaining_count", "assigned_person", "tags"):
            if key in msg:
                kwargs[key] = msg[key]
        task = await store.async_update_task(msg["task_id"], actor=actor, **kwargs)
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


# --- Sub-task commands ---


@websocket_api.websocket_command(
    {
        vol.Required("type"): "home_tasks/add_sub_task",
        vol.Required("list_id"): _val_id,
        vol.Required("task_id"): _val_id,
        vol.Required("title"): _val_title,
    }
)
@websocket_api.async_response
async def ws_add_sub_task(hass, connection, msg):
    """Add a sub-task."""
    try:
        store = _get_store(hass, msg["list_id"])
        sub = await store.async_add_sub_task(msg["task_id"], msg["title"])
        connection.send_result(msg["id"], sub)
    except Exception as err:
        _handle_error(connection, msg["id"], err)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "home_tasks/update_sub_task",
        vol.Required("list_id"): _val_id,
        vol.Required("task_id"): _val_id,
        vol.Required("sub_task_id"): _val_id,
        vol.Optional("title"): _val_title,
        vol.Optional("completed"): bool,
    }
)
@websocket_api.async_response
async def ws_update_sub_task(hass, connection, msg):
    """Update a sub-task."""
    try:
        store = _get_store(hass, msg["list_id"])
        kwargs = {}
        for key in ("title", "completed"):
            if key in msg:
                kwargs[key] = msg[key]
        sub = await store.async_update_sub_task(msg["task_id"], msg["sub_task_id"], **kwargs)
        connection.send_result(msg["id"], sub)
    except Exception as err:
        _handle_error(connection, msg["id"], err)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "home_tasks/delete_sub_task",
        vol.Required("list_id"): _val_id,
        vol.Required("task_id"): _val_id,
        vol.Required("sub_task_id"): _val_id,
    }
)
@websocket_api.async_response
async def ws_delete_sub_task(hass, connection, msg):
    """Delete a sub-task."""
    try:
        store = _get_store(hass, msg["list_id"])
        await store.async_delete_sub_task(msg["task_id"], msg["sub_task_id"])
        connection.send_result(msg["id"])
    except Exception as err:
        _handle_error(connection, msg["id"], err)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "home_tasks/reorder_sub_tasks",
        vol.Required("list_id"): _val_id,
        vol.Required("task_id"): _val_id,
        vol.Required("sub_task_ids"): vol.All([_val_id], vol.Length(max=MAX_SUB_TASKS_PER_TASK)),
    }
)
@websocket_api.async_response
async def ws_reorder_sub_tasks(hass, connection, msg):
    """Reorder sub-tasks within a task."""
    try:
        store = _get_store(hass, msg["list_id"])
        await store.async_reorder_sub_tasks(msg["task_id"], msg["sub_task_ids"])
        connection.send_result(msg["id"])
    except Exception as err:
        _handle_error(connection, msg["id"], err)


# --- Cross-list move ---


@websocket_api.websocket_command(
    {
        vol.Required("type"): "home_tasks/move_task",
        vol.Required("source_list_id"): _val_id,
        vol.Required("target_list_id"): _val_id,
        vol.Required("task_id"): _val_id,
    }
)
@websocket_api.async_response
async def ws_move_task(hass, connection, msg):
    """Move a task from one list to another."""
    try:
        if msg["source_list_id"] == msg["target_list_id"]:
            raise ValueError("source_list_id and target_list_id must be different")
        src = _get_store(hass, msg["source_list_id"])
        tgt = _get_store(hass, msg["target_list_id"])
        task = await src.async_export_task(msg["task_id"])
        await tgt.async_import_task(task)
        connection.send_result(msg["id"])
    except Exception as err:
        _handle_error(connection, msg["id"], err)


# ---------------------------------------------------------------------------
#  External todo entity commands
# ---------------------------------------------------------------------------


def _get_overlay_store(hass, entity_id: str) -> ExternalTaskOverlayStore:
    """Get the overlay store for an external entity_id."""
    stores = hass.data.get(DOMAIN, {})
    for store in stores.values():
        if isinstance(store, ExternalTaskOverlayStore) and store.entity_id == entity_id:
            return store
    raise ValueError(f"No overlay store found for entity: {entity_id}")


def _get_external_todo_items(hass, entity_id: str) -> list[dict]:
    """Read TodoItems from an external HA todo entity and return as dicts."""
    state = hass.states.get(entity_id)
    if state is None:
        raise ValueError(f"Entity not found: {entity_id}")

    # Access the entity via HA's todo EntityComponent
    entity_comp = hass.data.get("todo")
    if entity_comp and hasattr(entity_comp, "get_entity"):
        entity = entity_comp.get_entity(entity_id)
        if entity and hasattr(entity, "todo_items"):
            items = entity.todo_items or []
            from datetime import datetime as dt

            result = []
            for item in items:
                uid = item.uid
                if not uid:
                    continue  # Skip items without a UID — cannot be tracked
                # Split due into date + time (due can be date or datetime)
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


def _merge_tasks_with_overlays(external_items: list[dict], overlay_store: ExternalTaskOverlayStore) -> list[dict]:
    """Merge external todo items with overlay data to produce Home Tasks-compatible dicts."""
    raw_overlays = overlay_store._data.get("overlays", {}) if overlay_store._data else {}
    overlays = overlay_store.get_all_overlays()
    tasks = []
    for idx, item in enumerate(external_items):
        uid = item.get("uid") or ""
        overlay = overlays.get(uid, {})
        # Use provider's original order unless user explicitly reordered in Home Tasks
        raw = raw_overlays.get(uid, {})
        sort_order = raw["sort_order"] if "sort_order" in raw else idx
        completed = item.get("status") == "completed"
        task = {
            "id": uid,
            "title": item.get("summary") or "",
            "completed": completed,
            "notes": item.get("description") or "",
            "due_date": item.get("due"),
            "sort_order": sort_order,
            "sub_items": overlay.get("sub_items", []),
            "priority": overlay.get("priority"),
            "due_time": item.get("due_time") or overlay.get("due_time"),
            "reminders": overlay.get("reminders", []),
            "recurrence_value": overlay.get("recurrence_value", 1),
            "recurrence_unit": overlay.get("recurrence_unit"),
            "recurrence_enabled": overlay.get("recurrence_enabled", False),
            "recurrence_type": overlay.get("recurrence_type", "interval"),
            "recurrence_weekdays": overlay.get("recurrence_weekdays", []),
            "recurrence_start_date": overlay.get("recurrence_start_date"),
            "recurrence_time": overlay.get("recurrence_time"),
            "recurrence_end_type": overlay.get("recurrence_end_type", "none"),
            "recurrence_end_date": overlay.get("recurrence_end_date"),
            "recurrence_max_count": overlay.get("recurrence_max_count"),
            "recurrence_remaining_count": overlay.get("recurrence_remaining_count"),
            "completed_at": overlay.get("completed_at"),
            "assigned_person": overlay.get("assigned_person"),
            "tags": overlay.get("tags", []),
            "history": overlay.get("history", []),
            # Mark as external so the card knows how to route CRUD
            "_external": True,
        }
        tasks.append(task)
    return sorted(tasks, key=lambda t: t["sort_order"])


@websocket_api.websocket_command({vol.Required("type"): "home_tasks/get_external_lists"})
@websocket_api.async_response
async def ws_get_external_lists(hass, connection, msg):
    """List all available external todo entities (from other integrations)."""
    try:
        # Find all todo entities NOT owned by home_tasks
        from homeassistant.helpers import entity_registry as er
        entity_reg = er.async_get(hass)
        our_entries = {e.entry_id for e in hass.config_entries.async_entries(DOMAIN)}

        external = []
        # Also include linked external entries
        linked_entity_ids = set()
        for entry in hass.config_entries.async_entries(DOMAIN):
            if entry.data.get("type") == "external":
                eid = entry.data.get("entity_id")
                if eid:
                    linked_entity_ids.add(eid)

        for entity_entry in entity_reg.entities.values():
            if entity_entry.domain != "todo":
                continue
            if entity_entry.config_entry_id in our_entries:
                continue

            # Read supported_features from entity state attributes
            features = 0
            state = hass.states.get(entity_entry.entity_id)
            if state and state.attributes:
                features = state.attributes.get("supported_features", 0)

            external.append({
                "entity_id": entity_entry.entity_id,
                "name": entity_entry.name or entity_entry.original_name or entity_entry.entity_id,
                "linked": entity_entry.entity_id in linked_entity_ids,
                "supported_features": features,
            })

        connection.send_result(msg["id"], {"external_lists": external})
    except Exception as err:
        _handle_error(connection, msg["id"], err)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "home_tasks/get_external_tasks",
        vol.Required("entity_id"): str,
    }
)
@websocket_api.async_response
async def ws_get_external_tasks(hass, connection, msg):
    """Get tasks from an external todo entity, merged with overlay data."""
    try:
        entity_id = msg["entity_id"]
        overlay_store = _get_overlay_store(hass, entity_id)
        external_items = _get_external_todo_items(hass, entity_id)
        tasks = _merge_tasks_with_overlays(external_items, overlay_store)
        connection.send_result(msg["id"], {"tasks": tasks})
    except Exception as err:
        _handle_error(connection, msg["id"], err)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "home_tasks/update_external_overlay",
        vol.Required("entity_id"): str,
        vol.Required("task_uid"): str,
        vol.Optional("priority"): vol.Any(vol.In([1, 2, 3]), None),
        vol.Optional("due_time"): _val_time,
        vol.Optional("assigned_person"): vol.Any(str, None),
        vol.Optional("tags"): vol.All(list, vol.Length(max=MAX_TAGS_PER_TASK)),
        vol.Optional("reminders"): vol.All(
            list,
            vol.Length(max=MAX_REMINDERS_PER_TASK),
            [vol.All(int, vol.Range(min=0, max=MAX_REMINDER_OFFSET_MINUTES))],
        ),
        vol.Optional("sort_order"): int,
        vol.Optional("recurrence_value"): vol.All(int, vol.Range(min=1, max=MAX_RECURRENCE_VALUE)),
        vol.Optional("recurrence_unit"): vol.Any(vol.In(list(VALID_RECURRENCE_UNITS)), None),
        vol.Optional("recurrence_enabled"): bool,
        vol.Optional("recurrence_type"): vol.In(["interval", "weekdays"]),
        vol.Optional("recurrence_weekdays"): vol.All(list, [vol.All(int, vol.Range(min=0, max=6))]),
        vol.Optional("recurrence_start_date"): _val_date,
        vol.Optional("recurrence_time"): _val_time,
        vol.Optional("recurrence_end_type"): vol.In(["none", "date", "count"]),
        vol.Optional("recurrence_end_date"): _val_date,
        vol.Optional("recurrence_max_count"): vol.Any(vol.All(int, vol.Range(min=1)), None),
        vol.Optional("recurrence_remaining_count"): vol.Any(vol.All(int, vol.Range(min=0)), None),
    }
)
@websocket_api.async_response
async def ws_update_external_overlay(hass, connection, msg):
    """Update overlay fields for an external task."""
    try:
        overlay_store = _get_overlay_store(hass, msg["entity_id"])
        kwargs = {}
        for key in OVERLAY_FIELDS:
            if key in msg:
                kwargs[key] = msg[key]
        overlay = await overlay_store.async_set_overlay(msg["task_uid"], **kwargs)
        connection.send_result(msg["id"], overlay)
    except Exception as err:
        _handle_error(connection, msg["id"], err)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "home_tasks/add_external_sub_task",
        vol.Required("entity_id"): str,
        vol.Required("task_uid"): str,
        vol.Required("title"): _val_title,
    }
)
@websocket_api.async_response
async def ws_add_external_sub_task(hass, connection, msg):
    """Add a sub-task to an external task's overlay."""
    try:
        overlay_store = _get_overlay_store(hass, msg["entity_id"])
        sub = await overlay_store.async_add_sub_task(msg["task_uid"], msg["title"])
        connection.send_result(msg["id"], sub)
    except Exception as err:
        _handle_error(connection, msg["id"], err)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "home_tasks/update_external_sub_task",
        vol.Required("entity_id"): str,
        vol.Required("task_uid"): str,
        vol.Required("sub_task_id"): _val_id,
        vol.Optional("title"): _val_title,
        vol.Optional("completed"): bool,
    }
)
@websocket_api.async_response
async def ws_update_external_sub_task(hass, connection, msg):
    """Update a sub-task in an external task's overlay."""
    try:
        overlay_store = _get_overlay_store(hass, msg["entity_id"])
        kwargs = {}
        for key in ("title", "completed"):
            if key in msg:
                kwargs[key] = msg[key]
        sub = await overlay_store.async_update_sub_task(msg["task_uid"], msg["sub_task_id"], **kwargs)
        connection.send_result(msg["id"], sub)
    except Exception as err:
        _handle_error(connection, msg["id"], err)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "home_tasks/delete_external_sub_task",
        vol.Required("entity_id"): str,
        vol.Required("task_uid"): str,
        vol.Required("sub_task_id"): _val_id,
    }
)
@websocket_api.async_response
async def ws_delete_external_sub_task(hass, connection, msg):
    """Delete a sub-task from an external task's overlay."""
    try:
        overlay_store = _get_overlay_store(hass, msg["entity_id"])
        await overlay_store.async_delete_sub_task(msg["task_uid"], msg["sub_task_id"])
        connection.send_result(msg["id"])
    except Exception as err:
        _handle_error(connection, msg["id"], err)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "home_tasks/reorder_external_sub_tasks",
        vol.Required("entity_id"): str,
        vol.Required("task_uid"): str,
        vol.Required("sub_task_ids"): vol.All([_val_id], vol.Length(max=MAX_SUB_TASKS_PER_TASK)),
    }
)
@websocket_api.async_response
async def ws_reorder_external_sub_tasks(hass, connection, msg):
    """Reorder sub-tasks in an external task's overlay."""
    try:
        overlay_store = _get_overlay_store(hass, msg["entity_id"])
        await overlay_store.async_reorder_sub_tasks(msg["task_uid"], msg["sub_task_ids"])
        connection.send_result(msg["id"])
    except Exception as err:
        _handle_error(connection, msg["id"], err)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "home_tasks/delete_external_overlay",
        vol.Required("entity_id"): str,
        vol.Required("task_uid"): str,
    }
)
@websocket_api.async_response
async def ws_delete_external_overlay(hass, connection, msg):
    """Delete overlay data for an external task (cleanup after deletion)."""
    try:
        overlay_store = _get_overlay_store(hass, msg["entity_id"])
        await overlay_store.async_delete_overlay(msg["task_uid"])
        connection.send_result(msg["id"])
    except Exception as err:
        _handle_error(connection, msg["id"], err)
