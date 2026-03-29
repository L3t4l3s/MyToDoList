"""Todo platform for Home Tasks integration."""

from datetime import date

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
        | TodoListEntityFeature.SET_DUE_DATE_ON_ITEM
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
            items.append(
                TodoItem(
                    uid=task["id"],
                    summary=task["title"],
                    status=(
                        TodoItemStatus.COMPLETED
                        if task["completed"]
                        else TodoItemStatus.NEEDS_ACTION
                    ),
                    due=date.fromisoformat(task["due_date"]) if task.get("due_date") else None,
                    description=task.get("notes") or None,
                )
            )
        return items

    async def async_create_todo_item(self, item: TodoItem) -> None:
        """Create a new todo item."""
        task = await self._store.async_add_task(item.summary or "")
        # Apply optional fields
        kwargs = {}
        if item.due:
            kwargs["due_date"] = item.due.isoformat()
        if item.description:
            kwargs["notes"] = item.description
        if item.status == TodoItemStatus.COMPLETED:
            kwargs["completed"] = True
        if kwargs:
            await self._store.async_update_task(task["id"], **kwargs)
        self.async_write_ha_state()

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Update a todo item."""
        if not item.uid:
            return
        kwargs = {}
        if item.summary is not None:
            kwargs["title"] = item.summary
        if item.status is not None:
            kwargs["completed"] = item.status == TodoItemStatus.COMPLETED
        if item.due is not None:
            kwargs["due_date"] = item.due.isoformat()
        elif item.due is None and "due" in (item.__dict__ if hasattr(item, "__dict__") else {}):
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
