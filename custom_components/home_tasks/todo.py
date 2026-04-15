"""Todo platform for Home Tasks integration."""

from datetime import date, datetime, timezone

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up todo list entity from a config entry."""
    if entry.data.get("type") == "external":
        return  # External entries do not get a todo entity (managed by other integration)
    store = hass.data[DOMAIN][entry.entry_id]
    entity = HomeTasksEntity(entry, store)
    async_add_entities([entity])


class HomeTasksEntity(TodoListEntity):
    """A todo list entity backed by our custom store."""

    _attr_has_entity_name = True
    _attr_supported_features = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
        | TodoListEntityFeature.MOVE_TODO_ITEM
        | TodoListEntityFeature.SET_DUE_DATE_ON_ITEM
        | TodoListEntityFeature.SET_DUE_DATETIME_ON_ITEM
        | TodoListEntityFeature.SET_DESCRIPTION_ON_ITEM
    )

    def __init__(self, entry: ConfigEntry, store) -> None:
        """Initialize the entity."""
        self._entry = entry
        self._store = store
        self._attr_name = entry.data.get("name", entry.title)
        self._attr_unique_id = entry.entry_id

    async def async_added_to_hass(self) -> None:
        """Register store listener so state updates on any data change."""
        self.async_on_remove(
            self._store.async_add_listener(self._handle_store_update)
        )

    @callback
    def _handle_store_update(self) -> None:
        """React to store data changes."""
        self.async_write_ha_state()

    @property
    def todo_items(self) -> list[TodoItem]:
        """Return the todo items."""
        items = []
        for task in self._store.tasks:
            # due: expose as datetime when due_time is set, date otherwise
            due = None
            if task.get("due_date"):
                if task.get("due_time"):
                    local_tz = datetime.now().astimezone().tzinfo
                    h, m = int(task["due_time"][:2]), int(task["due_time"][3:5])
                    due = datetime(
                        *map(int, task["due_date"].split("-")),
                        h, m, tzinfo=local_tz,
                    )
                else:
                    due = date.fromisoformat(task["due_date"])

            # completed: expose the completion timestamp if available
            completed_dt = None
            if task.get("completed") and task.get("completed_at"):
                try:
                    completed_dt = datetime.fromisoformat(task["completed_at"])
                    if completed_dt.tzinfo is None:
                        completed_dt = completed_dt.replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    pass

            items.append(
                TodoItem(
                    uid=task["id"],
                    summary=task["title"],
                    status=(
                        TodoItemStatus.COMPLETED
                        if task["completed"]
                        else TodoItemStatus.NEEDS_ACTION
                    ),
                    due=due,
                    description=task.get("notes") or None,
                    completed=completed_dt,
                )
            )
        return items

    async def async_create_todo_item(self, item: TodoItem) -> None:
        """Create a new todo item."""
        task = await self._store.async_add_task(item.summary or "")
        # Apply optional fields
        kwargs = {}
        if item.due:
            kwargs["due_date"] = (
                item.due.date().isoformat()
                if isinstance(item.due, datetime)
                else item.due.isoformat()
            )
            if isinstance(item.due, datetime):
                kwargs["due_time"] = item.due.strftime("%H:%M")
        if item.description:
            kwargs["notes"] = item.description
        if item.status == TodoItemStatus.COMPLETED:
            kwargs["completed"] = True
        if kwargs:
            await self._store.async_update_task(task["id"], **kwargs)
        self.async_write_ha_state()

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Update a todo item.

        HA always passes a complete TodoItem (existing fields + changes).
        We update all standard fields unconditionally.
        """
        if not item.uid:
            return
        kwargs = {}
        if item.summary is not None:
            kwargs["title"] = item.summary
        if item.status is not None:
            kwargs["completed"] = item.status == TodoItemStatus.COMPLETED
        # due can be a date, datetime, or None (cleared)
        if isinstance(item.due, datetime):
            kwargs["due_date"] = item.due.date().isoformat()
            kwargs["due_time"] = item.due.strftime("%H:%M")
        elif isinstance(item.due, date):
            kwargs["due_date"] = item.due.isoformat()
            kwargs["due_time"] = None
        else:
            kwargs["due_date"] = None
        if item.description is not None:
            kwargs["notes"] = item.description
        if kwargs:
            await self._store.async_update_task(item.uid, **kwargs)
        self.async_write_ha_state()

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        """Delete todo items."""
        for uid in uids:
            await self._store.async_delete_task(uid)
        self.async_write_ha_state()

    async def async_move_todo_item(
        self, uid: str, previous_uid: str | None = None
    ) -> None:
        """Re-order a todo item by placing it after previous_uid (or first if None)."""
        current_ids = [t["id"] for t in sorted(
            self._store.tasks, key=lambda t: t.get("sort_order", 0)
        )]
        if uid not in current_ids:
            return
        current_ids.remove(uid)
        if previous_uid is None:
            current_ids.insert(0, uid)
        else:
            try:
                idx = current_ids.index(previous_uid)
                current_ids.insert(idx + 1, uid)
            except ValueError:
                current_ids.append(uid)
        await self._store.async_reorder_tasks(current_ids)
        self.async_write_ha_state()
