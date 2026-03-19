"""Data store for My ToDo List."""

import logging
import re
import uuid

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import (
    DEFAULT_LIST_NAME,
    MAX_LISTS,
    MAX_NOTES_LENGTH,
    MAX_SUB_ITEMS_PER_TASK,
    MAX_TASKS_PER_LIST,
    MAX_TITLE_LENGTH,
    MAX_LIST_NAME_LENGTH,
    STORAGE_KEY,
    STORAGE_VERSION,
)

_LOGGER = logging.getLogger(__name__)

# ISO 8601 date pattern (YYYY-MM-DD)
_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _validate_text(value: str, max_length: int, field_name: str) -> str:
    """Validate and truncate a text field."""
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    value = value.strip()
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if len(value) > max_length:
        raise ValueError(f"{field_name} exceeds maximum length of {max_length}")
    return value


def _validate_date(value: str | None) -> str | None:
    """Validate a date string (YYYY-MM-DD) or None."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("due_date must be a string or null")
    value = value.strip()
    if not value:
        return None
    if not _DATE_PATTERN.match(value):
        raise ValueError("due_date must be in YYYY-MM-DD format")
    # Validate the date components are reasonable
    try:
        year, month, day = int(value[:4]), int(value[5:7]), int(value[8:10])
        if not (1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31):
            raise ValueError("due_date contains invalid date components")
    except (IndexError, TypeError) as err:
        raise ValueError("due_date must be in YYYY-MM-DD format") from err
    return value


class MyToDoListStore:
    """Manage todo list data persistence."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the store."""
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._data: dict | None = None

    async def async_load(self) -> None:
        """Load data from disk."""
        data = await self._store.async_load()
        if data is None:
            default_list_id = str(uuid.uuid4())
            self._data = {
                "lists": {
                    default_list_id: {
                        "id": default_list_id,
                        "name": DEFAULT_LIST_NAME,
                        "sort_order": 0,
                        "tasks": [],
                    }
                }
            }
            await self._async_save()
        else:
            self._data = data

    async def _async_save(self) -> None:
        """Save data to disk."""
        await self._store.async_save(self._data)

    def _get_list(self, list_id: str) -> dict:
        """Get a list by ID or raise ValueError."""
        lst = self._data["lists"].get(list_id)
        if lst is None:
            raise ValueError("List not found")
        return lst

    def _get_task(self, lst: dict, task_id: str) -> dict:
        """Get a task from a list or raise ValueError."""
        for task in lst["tasks"]:
            if task["id"] == task_id:
                return task
        raise ValueError("Task not found")

    def _get_sub_item(self, task: dict, sub_item_id: str) -> dict:
        """Get a sub-item from a task or raise ValueError."""
        for sub in task["sub_items"]:
            if sub["id"] == sub_item_id:
                return sub
        raise ValueError("Sub-item not found")

    # --- List methods ---

    def get_lists(self) -> list[dict]:
        """Return all lists (without tasks, for overview)."""
        result = []
        for lst in self._data["lists"].values():
            result.append({
                "id": lst["id"],
                "name": lst["name"],
                "sort_order": lst["sort_order"],
                "task_count": len(lst["tasks"]),
            })
        result.sort(key=lambda x: x["sort_order"])
        return result

    async def async_create_list(self, name: str) -> dict:
        """Create a new list."""
        name = _validate_text(name, MAX_LIST_NAME_LENGTH, "List name")
        if len(self._data["lists"]) >= MAX_LISTS:
            raise ValueError(f"Maximum number of lists ({MAX_LISTS}) reached")
        list_id = str(uuid.uuid4())
        max_order = max(
            (lst["sort_order"] for lst in self._data["lists"].values()),
            default=-1,
        )
        new_list = {
            "id": list_id,
            "name": name,
            "sort_order": max_order + 1,
            "tasks": [],
        }
        self._data["lists"][list_id] = new_list
        await self._async_save()
        return {"id": list_id, "name": name, "sort_order": new_list["sort_order"], "task_count": 0}

    async def async_rename_list(self, list_id: str, name: str) -> dict:
        """Rename a list."""
        name = _validate_text(name, MAX_LIST_NAME_LENGTH, "List name")
        lst = self._get_list(list_id)
        lst["name"] = name
        await self._async_save()
        return {"id": list_id, "name": name}

    async def async_delete_list(self, list_id: str) -> None:
        """Delete a list."""
        self._get_list(list_id)  # Validate existence
        del self._data["lists"][list_id]
        await self._async_save()

    # --- Task methods ---

    def get_tasks(self, list_id: str) -> list[dict]:
        """Return all tasks for a list."""
        lst = self._get_list(list_id)
        tasks = sorted(lst["tasks"], key=lambda t: t["sort_order"])
        return tasks

    async def async_add_task(self, list_id: str, title: str) -> dict:
        """Add a task to a list."""
        title = _validate_text(title, MAX_TITLE_LENGTH, "Task title")
        lst = self._get_list(list_id)
        if len(lst["tasks"]) >= MAX_TASKS_PER_LIST:
            raise ValueError(
                f"Maximum number of tasks ({MAX_TASKS_PER_LIST}) reached"
            )
        max_order = max(
            (t["sort_order"] for t in lst["tasks"]),
            default=-1,
        )
        task = {
            "id": str(uuid.uuid4()),
            "title": title,
            "completed": False,
            "notes": "",
            "due_date": None,
            "sort_order": max_order + 1,
            "sub_items": [],
        }
        lst["tasks"].append(task)
        await self._async_save()
        return task

    async def async_update_task(
        self, list_id: str, task_id: str, **kwargs
    ) -> dict:
        """Update a task's fields."""
        lst = self._get_list(list_id)
        task = self._get_task(lst, task_id)

        # Validate each field
        if "title" in kwargs:
            kwargs["title"] = _validate_text(
                kwargs["title"], MAX_TITLE_LENGTH, "Task title"
            )
        if "notes" in kwargs:
            notes = kwargs["notes"]
            if not isinstance(notes, str):
                raise ValueError("Notes must be a string")
            if len(notes) > MAX_NOTES_LENGTH:
                raise ValueError(
                    f"Notes exceed maximum length of {MAX_NOTES_LENGTH}"
                )
            kwargs["notes"] = notes
        if "due_date" in kwargs:
            kwargs["due_date"] = _validate_date(kwargs["due_date"])
        if "completed" in kwargs:
            if not isinstance(kwargs["completed"], bool):
                raise ValueError("completed must be a boolean")

        for key, value in kwargs.items():
            if key in ("title", "completed", "notes", "due_date"):
                task[key] = value

        await self._async_save()
        return task

    async def async_delete_task(self, list_id: str, task_id: str) -> None:
        """Delete a task."""
        lst = self._get_list(list_id)
        self._get_task(lst, task_id)  # Validate existence
        lst["tasks"] = [t for t in lst["tasks"] if t["id"] != task_id]
        await self._async_save()

    async def async_reorder_tasks(
        self, list_id: str, task_ids: list[str]
    ) -> None:
        """Reorder tasks by providing ordered list of task IDs."""
        lst = self._get_list(list_id)
        # Limit size to prevent DoS
        actual_count = len(lst["tasks"])
        if len(task_ids) > actual_count:
            raise ValueError("Too many task IDs provided")
        task_map = {t["id"]: t for t in lst["tasks"]}
        for index, tid in enumerate(task_ids):
            if tid in task_map:
                task_map[tid]["sort_order"] = index
        await self._async_save()

    # --- Sub-item methods ---

    async def async_add_sub_item(
        self, list_id: str, task_id: str, title: str
    ) -> dict:
        """Add a sub-item to a task."""
        title = _validate_text(title, MAX_TITLE_LENGTH, "Sub-item title")
        lst = self._get_list(list_id)
        task = self._get_task(lst, task_id)
        if len(task["sub_items"]) >= MAX_SUB_ITEMS_PER_TASK:
            raise ValueError(
                f"Maximum number of sub-items ({MAX_SUB_ITEMS_PER_TASK}) reached"
            )
        sub_item = {
            "id": str(uuid.uuid4()),
            "title": title,
            "completed": False,
        }
        task["sub_items"].append(sub_item)
        await self._async_save()
        return sub_item

    async def async_update_sub_item(
        self, list_id: str, task_id: str, sub_item_id: str, **kwargs
    ) -> dict:
        """Update a sub-item."""
        lst = self._get_list(list_id)
        task = self._get_task(lst, task_id)
        sub = self._get_sub_item(task, sub_item_id)

        if "title" in kwargs:
            kwargs["title"] = _validate_text(
                kwargs["title"], MAX_TITLE_LENGTH, "Sub-item title"
            )
        if "completed" in kwargs:
            if not isinstance(kwargs["completed"], bool):
                raise ValueError("completed must be a boolean")

        for key, value in kwargs.items():
            if key in ("title", "completed"):
                sub[key] = value

        await self._async_save()
        return sub

    async def async_delete_sub_item(
        self, list_id: str, task_id: str, sub_item_id: str
    ) -> None:
        """Delete a sub-item."""
        lst = self._get_list(list_id)
        task = self._get_task(lst, task_id)
        self._get_sub_item(task, sub_item_id)  # Validate existence
        task["sub_items"] = [
            s for s in task["sub_items"] if s["id"] != sub_item_id
        ]
        await self._async_save()
