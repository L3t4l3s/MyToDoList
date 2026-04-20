"""Tests for provider_adapters module."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.home_tasks.provider_adapters import (
    GenericAdapter,
    ProviderCapabilities,
    TodoistAdapter,
    detect_provider_type,
    get_adapter,
    get_todoist_token,
    priority_from_todoist,
    priority_to_todoist,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
#  Priority mapping
# ---------------------------------------------------------------------------


class TestPriorityMapping:
    """Priority mapping between Home Tasks (None/1-3) and Todoist (1-4)."""

    def test_to_todoist_none(self):
        assert priority_to_todoist(None) == 1

    def test_to_todoist_low(self):
        assert priority_to_todoist(1) == 2

    def test_to_todoist_medium(self):
        assert priority_to_todoist(2) == 3

    def test_to_todoist_high(self):
        assert priority_to_todoist(3) == 4

    def test_from_todoist_normal(self):
        assert priority_from_todoist(1) is None

    def test_from_todoist_low(self):
        assert priority_from_todoist(2) == 1

    def test_from_todoist_medium(self):
        assert priority_from_todoist(3) == 2

    def test_from_todoist_urgent(self):
        assert priority_from_todoist(4) == 3

    def test_roundtrip_none(self):
        assert priority_from_todoist(priority_to_todoist(None)) is None

    def test_roundtrip_1(self):
        assert priority_from_todoist(priority_to_todoist(1)) == 1

    def test_roundtrip_2(self):
        assert priority_from_todoist(priority_to_todoist(2)) == 2

    def test_roundtrip_3(self):
        assert priority_from_todoist(priority_to_todoist(3)) == 3


# ---------------------------------------------------------------------------
#  Provider detection
# ---------------------------------------------------------------------------


class TestDetectProviderType:
    """detect_provider_type resolves entity_id -> integration domain."""

    def test_todoist_entity(self):
        hass = MagicMock()
        entity_entry = MagicMock()
        entity_entry.config_entry_id = "cfg_todoist"
        config_entry = MagicMock()
        config_entry.domain = "todoist"

        entity_reg = MagicMock()
        entity_reg.async_get.return_value = entity_entry
        hass.config_entries.async_get_entry.return_value = config_entry

        with patch(
            "custom_components.home_tasks.provider_adapters.er.async_get",
            return_value=entity_reg,
        ):
            assert detect_provider_type(hass, "todo.todoist_shopping") == "todoist"

    def test_caldav_entity(self):
        hass = MagicMock()
        entity_entry = MagicMock()
        entity_entry.config_entry_id = "cfg_caldav"
        config_entry = MagicMock()
        config_entry.domain = "caldav"

        entity_reg = MagicMock()
        entity_reg.async_get.return_value = entity_entry
        hass.config_entries.async_get_entry.return_value = config_entry

        with patch(
            "custom_components.home_tasks.provider_adapters.er.async_get",
            return_value=entity_reg,
        ):
            assert detect_provider_type(hass, "todo.nextcloud_tasks") == "caldav"

    def test_unknown_entity(self):
        hass = MagicMock()
        entity_reg = MagicMock()
        entity_reg.async_get.return_value = None

        with patch(
            "custom_components.home_tasks.provider_adapters.er.async_get",
            return_value=entity_reg,
        ):
            assert detect_provider_type(hass, "todo.nonexistent") == "generic"


# ---------------------------------------------------------------------------
#  Token access
# ---------------------------------------------------------------------------


class TestGetTodoistToken:
    """get_todoist_token reads the API token from the Todoist config entry."""

    def test_token_found(self):
        hass = MagicMock()
        entity_entry = MagicMock()
        entity_entry.config_entry_id = "cfg_todoist"
        config_entry = MagicMock()
        config_entry.domain = "todoist"
        config_entry.data = {"token": "abc123"}

        entity_reg = MagicMock()
        entity_reg.async_get.return_value = entity_entry
        hass.config_entries.async_get_entry.return_value = config_entry

        with patch(
            "custom_components.home_tasks.provider_adapters.er.async_get",
            return_value=entity_reg,
        ):
            assert get_todoist_token(hass, "todo.todoist_shopping") == "abc123"

    def test_no_entity(self):
        hass = MagicMock()
        entity_reg = MagicMock()
        entity_reg.async_get.return_value = None

        with patch(
            "custom_components.home_tasks.provider_adapters.er.async_get",
            return_value=entity_reg,
        ):
            assert get_todoist_token(hass, "todo.nonexistent") is None

    def test_wrong_domain(self):
        hass = MagicMock()
        entity_entry = MagicMock()
        entity_entry.config_entry_id = "cfg_caldav"
        config_entry = MagicMock()
        config_entry.domain = "caldav"
        config_entry.data = {}

        entity_reg = MagicMock()
        entity_reg.async_get.return_value = entity_entry
        hass.config_entries.async_get_entry.return_value = config_entry

        with patch(
            "custom_components.home_tasks.provider_adapters.er.async_get",
            return_value=entity_reg,
        ):
            assert get_todoist_token(hass, "todo.nextcloud_tasks") is None


# ---------------------------------------------------------------------------
#  Adapter factory
# ---------------------------------------------------------------------------


class TestGetAdapter:
    """get_adapter returns the correct adapter class."""

    def test_generic_config(self):
        hass = MagicMock()
        adapter = get_adapter(hass, "todo.nextcloud", {"provider_type": "generic"})
        assert isinstance(adapter, GenericAdapter)
        assert adapter.provider_type == "generic"

    def test_todoist_with_token(self):
        hass = MagicMock()
        entity_entry = MagicMock()
        entity_entry.config_entry_id = "cfg_todoist"
        config_entry = MagicMock()
        config_entry.domain = "todoist"
        config_entry.data = {"token": "test_token"}

        entity_reg = MagicMock()
        entity_reg.async_get.return_value = entity_entry
        hass.config_entries.async_get_entry.return_value = config_entry

        with patch(
            "custom_components.home_tasks.provider_adapters.er.async_get",
            return_value=entity_reg,
        ):
            adapter = get_adapter(
                hass,
                "todo.todoist_shopping",
                {"provider_type": "todoist"},
            )
            assert isinstance(adapter, TodoistAdapter)
            assert adapter.provider_type == "todoist"

    def test_todoist_without_token_falls_back(self):
        hass = MagicMock()
        entity_reg = MagicMock()
        entity_reg.async_get.return_value = None

        with patch(
            "custom_components.home_tasks.provider_adapters.er.async_get",
            return_value=entity_reg,
        ):
            adapter = get_adapter(
                hass,
                "todo.todoist_shopping",
                {"provider_type": "todoist"},
            )
            assert isinstance(adapter, GenericAdapter)

    def test_missing_provider_type_defaults_generic(self):
        hass = MagicMock()
        adapter = get_adapter(hass, "todo.something", {})
        assert isinstance(adapter, GenericAdapter)


# ---------------------------------------------------------------------------
#  Capabilities
# ---------------------------------------------------------------------------


class TestProviderCapabilities:
    """ProviderCapabilities dataclass."""

    def test_default_all_false(self):
        caps = ProviderCapabilities()
        d = caps.to_dict()
        assert all(v is False for v in d.values())

    def test_todoist_capabilities(self):
        hass = MagicMock()
        adapter = TodoistAdapter(hass, "todo.todoist_test", {}, "fake_token")
        caps = adapter.capabilities
        assert caps.can_sync_priority is True
        assert caps.can_sync_labels is True
        assert caps.can_sync_order is True
        assert caps.can_sync_sub_items is True
        assert caps.can_sync_assignee is True
        assert caps.can_sync_recurrence is True
        assert caps.can_sync_reminders is True

    def test_generic_capabilities(self):
        caps = GenericAdapter.capabilities
        assert caps.can_sync_priority is False
        assert caps.can_sync_labels is False


# ---------------------------------------------------------------------------
#  Recurrence mapping
# ---------------------------------------------------------------------------


class TestRecurrenceMapping:
    """TodoistAdapter recurrence string ↔ structured fields."""

    def test_build_daily(self):
        fields = {
            "recurrence_enabled": True,
            "recurrence_type": "interval",
            "recurrence_value": 1,
            "recurrence_unit": "days",
        }
        assert TodoistAdapter._build_recurrence_string(fields) == "every day"

    def test_build_every_3_days(self):
        fields = {
            "recurrence_enabled": True,
            "recurrence_type": "interval",
            "recurrence_value": 3,
            "recurrence_unit": "days",
        }
        assert TodoistAdapter._build_recurrence_string(fields) == "every 3 days"

    def test_build_weekly(self):
        fields = {
            "recurrence_enabled": True,
            "recurrence_type": "interval",
            "recurrence_value": 1,
            "recurrence_unit": "weeks",
        }
        assert TodoistAdapter._build_recurrence_string(fields) == "every week"

    def test_build_weekdays(self):
        fields = {
            "recurrence_enabled": True,
            "recurrence_type": "weekdays",
            "recurrence_weekdays": [0, 2, 4],
        }
        result = TodoistAdapter._build_recurrence_string(fields)
        assert result == "every mon, wed, fri"

    def test_build_with_time(self):
        fields = {
            "recurrence_enabled": True,
            "recurrence_type": "interval",
            "recurrence_value": 1,
            "recurrence_unit": "days",
            "recurrence_time": "14:30",
        }
        assert TodoistAdapter._build_recurrence_string(fields) == "every day at 14:30"

    def test_build_with_start_and_end(self):
        fields = {
            "recurrence_enabled": True,
            "recurrence_type": "interval",
            "recurrence_value": 1,
            "recurrence_unit": "days",
            "recurrence_start_date": "2026-04-10",
            "recurrence_end_date": "2026-12-31",
        }
        result = TodoistAdapter._build_recurrence_string(fields)
        assert "starting 2026-04-10" in result
        assert "ending 2026-12-31" in result

    def test_build_disabled_returns_none(self):
        fields = {"recurrence_enabled": False}
        assert TodoistAdapter._build_recurrence_string(fields) is None

    def test_parse_every_day(self):
        due = MagicMock()
        due.is_recurring = True
        due.string = "every day"
        result = TodoistAdapter._parse_recurrence_from_due(due)
        assert result["recurrence_enabled"] is True
        assert result["recurrence_type"] == "interval"
        assert result["recurrence_value"] == 1
        assert result["recurrence_unit"] == "days"

    def test_parse_every_3_weeks(self):
        due = MagicMock()
        due.is_recurring = True
        due.string = "every 3 weeks"
        result = TodoistAdapter._parse_recurrence_from_due(due)
        assert result["recurrence_value"] == 3
        assert result["recurrence_unit"] == "weeks"

    def test_parse_weekdays(self):
        due = MagicMock()
        due.is_recurring = True
        due.string = "every mon, wed, fri"
        result = TodoistAdapter._parse_recurrence_from_due(due)
        assert result["recurrence_type"] == "weekdays"
        assert result["recurrence_weekdays"] == [0, 2, 4]

    def test_parse_with_time(self):
        due = MagicMock()
        due.is_recurring = True
        due.string = "every day at 14:30"
        result = TodoistAdapter._parse_recurrence_from_due(due)
        assert result["recurrence_time"] == "14:30"

    def test_parse_non_recurring(self):
        due = MagicMock()
        due.is_recurring = False
        result = TodoistAdapter._parse_recurrence_from_due(due)
        assert result["recurrence_enabled"] is False

    def test_parse_none(self):
        result = TodoistAdapter._parse_recurrence_from_due(None)
        assert result["recurrence_enabled"] is False


# ---------------------------------------------------------------------------
#  TodoistAdapter CRUD (with mocked _api)
# ---------------------------------------------------------------------------


def _make_todoist_adapter_with_mock_api():
    """Create a TodoistAdapter with a fully mocked _api so we don't hit Todoist."""
    hass = MagicMock()
    hass.states = MagicMock()
    adapter = TodoistAdapter(hass, "todo.todoist_test", {}, "fake_token")
    api = MagicMock()
    api.get_tasks = AsyncMock(return_value=[])
    api.add_task = AsyncMock()
    api.update_task = AsyncMock()
    api.delete_task = AsyncMock()
    api.complete_task = AsyncMock()
    api.uncomplete_task = AsyncMock()
    api.get_reminders = AsyncMock(return_value=[])
    api.add_reminder = AsyncMock()
    api.delete_reminder = AsyncMock()
    api.get_task = AsyncMock()
    adapter._api = api
    adapter._project_id = "PROJ-1"  # skip _resolve_project_id in _ensure_api
    return adapter, api


class TestTodoistAdapterReadTasks:
    """async_read_tasks fetches main tasks + sub-tasks and parses fields."""

    async def test_read_tasks_empty(self):
        adapter, api = _make_todoist_adapter_with_mock_api()
        result = await adapter.async_read_tasks()
        assert result == []
        api.get_tasks.assert_awaited_once()

    async def test_read_tasks_main_and_sub(self):
        adapter, api = _make_todoist_adapter_with_mock_api()

        # Main task
        main = MagicMock()
        main.id = "task-1"
        main.parent_id = None
        main.content = "Buy groceries"
        main.is_completed = False
        main.priority = 3  # Todoist medium → home_tasks 2
        main.labels = ["shopping", "urgent"]
        main.order = 0
        main.description = "Weekly grocery run"
        main.due = None

        # Sub-task
        sub = MagicMock()
        sub.id = "sub-1"
        sub.parent_id = "task-1"
        sub.content = "Apples"
        sub.is_completed = False
        sub.order = 1

        api.get_tasks = AsyncMock(return_value=[main, sub])

        result = await adapter.async_read_tasks()
        assert len(result) == 1
        t = result[0]
        assert t["uid"] == "task-1"
        assert t["summary"] == "Buy groceries"
        assert t["status"] == "needs_action"
        assert t["priority"] == 2
        assert t["labels"] == ["shopping", "urgent"]
        assert t["description"] == "Weekly grocery run"
        assert len(t["sub_items"]) == 1
        assert t["sub_items"][0]["title"] == "Apples"

    async def test_read_tasks_completed(self):
        adapter, api = _make_todoist_adapter_with_mock_api()
        main = MagicMock()
        main.id = "t1"
        main.parent_id = None
        main.content = "Done"
        main.is_completed = True
        main.priority = 1
        main.labels = []
        main.order = 0
        main.description = ""
        main.due = None
        api.get_tasks = AsyncMock(return_value=[main])

        result = await adapter.async_read_tasks()
        assert result[0]["status"] == "completed"


class TestTodoistAdapterCreateTask:
    """async_create_task forwards to api.add_task with mapped fields."""

    async def test_create_basic(self):
        adapter, api = _make_todoist_adapter_with_mock_api()
        new_task = MagicMock()
        new_task.id = "new-1"
        api.add_task = AsyncMock(return_value=new_task)

        uid = await adapter.async_create_task({"title": "Test create"})
        assert uid == "new-1"
        api.add_task.assert_awaited_once()
        kwargs = api.add_task.await_args.kwargs
        assert kwargs["content"] == "Test create"
        assert kwargs["project_id"] == "PROJ-1"

    async def test_create_with_priority_and_labels(self):
        adapter, api = _make_todoist_adapter_with_mock_api()
        new_task = MagicMock()
        new_task.id = "new-2"
        api.add_task = AsyncMock(return_value=new_task)

        await adapter.async_create_task({
            "title": "With fields",
            "priority": 3,  # high → Todoist 4
            "tags": ["a", "b"],
            "notes": "Some notes",
        })
        kwargs = api.add_task.await_args.kwargs
        assert kwargs["priority"] == 4
        assert kwargs["labels"] == ["a", "b"]
        assert kwargs["description"] == "Some notes"

    async def test_create_with_reminders(self):
        adapter, api = _make_todoist_adapter_with_mock_api()
        new_task = MagicMock()
        new_task.id = "new-3"
        api.add_task = AsyncMock(return_value=new_task)

        await adapter.async_create_task({"title": "Reminder", "reminders": [15, 60]})
        # Each reminder triggers an add_reminder call
        assert api.add_reminder.await_count == 2


class TestTodoistAdapterUpdateTask:
    """async_update_task routes fields to api vs overlay."""

    async def test_update_title_and_priority(self):
        adapter, api = _make_todoist_adapter_with_mock_api()
        unsynced = await adapter.async_update_task("t1", {"title": "Renamed", "priority": 1})
        api.update_task.assert_awaited_once()
        kwargs = api.update_task.await_args.kwargs
        assert kwargs["content"] == "Renamed"
        assert kwargs["priority"] == 2  # home_tasks 1 → Todoist 2
        # Neither field is unsynced
        assert "title" not in unsynced
        assert "priority" not in unsynced

    async def test_update_completed_calls_complete(self):
        adapter, api = _make_todoist_adapter_with_mock_api()
        await adapter.async_update_task("t1", {"completed": True})
        api.complete_task.assert_awaited_once_with("t1")

    async def test_update_uncompleted_calls_uncomplete(self):
        adapter, api = _make_todoist_adapter_with_mock_api()
        await adapter.async_update_task("t1", {"completed": False})
        api.uncomplete_task.assert_awaited_once_with("t1")

    async def test_update_unsynced_field_returned(self):
        adapter, api = _make_todoist_adapter_with_mock_api()
        # recurrence_end_type is always overlay-only
        unsynced = await adapter.async_update_task(
            "t1", {"recurrence_end_type": "date"}
        )
        assert unsynced.get("recurrence_end_type") == "date"

    async def test_update_clear_due_date(self):
        adapter, api = _make_todoist_adapter_with_mock_api()
        await adapter.async_update_task("t1", {"due_date": None})
        kwargs = api.update_task.await_args.kwargs
        assert kwargs.get("due_string") == "no date"


class TestTodoistAdapterDeleteAndReorder:
    """async_delete_task and async_reorder_tasks forward to api."""

    async def test_delete(self):
        adapter, api = _make_todoist_adapter_with_mock_api()
        await adapter.async_delete_task("t1")
        api.delete_task.assert_awaited_once_with("t1")

    async def test_reorder_success(self):
        adapter, api = _make_todoist_adapter_with_mock_api()
        result = await adapter.async_reorder_tasks(["a", "b", "c"])
        assert result is True
        # Three update_task calls with child_order 0, 1, 2
        assert api.update_task.await_count == 3

    async def test_reorder_failure(self):
        adapter, api = _make_todoist_adapter_with_mock_api()
        api.update_task = AsyncMock(side_effect=Exception("boom"))
        result = await adapter.async_reorder_tasks(["a", "b"])
        assert result is False


class TestTodoistAdapterSubTasks:
    """Sub-task CRUD via the Todoist API."""

    async def test_add_sub_task(self):
        adapter, api = _make_todoist_adapter_with_mock_api()
        new_sub = MagicMock()
        new_sub.id = "sub-99"
        api.add_task = AsyncMock(return_value=new_sub)

        sub_id = await adapter.async_add_sub_task("parent-1", "Sub title")
        assert sub_id == "sub-99"
        kwargs = api.add_task.await_args.kwargs
        assert kwargs["content"] == "Sub title"
        assert kwargs["parent_id"] == "parent-1"

    async def test_update_sub_task_title(self):
        adapter, api = _make_todoist_adapter_with_mock_api()
        ok = await adapter.async_update_sub_task("sub-1", title="Renamed sub")
        assert ok is True
        kwargs = api.update_task.await_args.kwargs
        assert kwargs["content"] == "Renamed sub"

    async def test_update_sub_task_complete(self):
        adapter, api = _make_todoist_adapter_with_mock_api()
        await adapter.async_update_sub_task("sub-1", completed=True)
        api.complete_task.assert_awaited_once_with("sub-1")

    async def test_delete_sub_task(self):
        adapter, api = _make_todoist_adapter_with_mock_api()
        ok = await adapter.async_delete_sub_task("sub-1")
        assert ok is True
        api.delete_task.assert_awaited_once_with("sub-1")

    async def test_reorder_sub_tasks(self):
        adapter, api = _make_todoist_adapter_with_mock_api()
        ok = await adapter.async_reorder_sub_tasks("parent", ["s1", "s2"])
        assert ok is True
        assert api.update_task.await_count == 2


class TestTodoistAdapterReminderSync:
    """_sync_reminders performs delta sync against the Todoist API."""

    async def test_sync_creates_new(self):
        adapter, api = _make_todoist_adapter_with_mock_api()
        api.get_reminders = AsyncMock(return_value=[])
        # add_reminder returns a dict-like result so the rollback path
        # in _sync_reminders can read its "id".
        api.add_reminder = AsyncMock(side_effect=[
            {"id": "new-r1"}, {"id": "new-r2"},
        ])
        await adapter._sync_reminders("t1", [30, 60])
        assert api.add_reminder.await_count == 2

    async def test_sync_deletes_removed(self):
        adapter, api = _make_todoist_adapter_with_mock_api()
        api.get_reminders = AsyncMock(return_value=[
            {"id": "r1", "minute_offset": 30},
            {"id": "r2", "minute_offset": 60},
        ])
        await adapter._sync_reminders("t1", [30])
        # r2 (60 min) should be deleted; r1 unchanged
        api.delete_reminder.assert_awaited_once_with("r2")
        api.add_reminder.assert_not_called()

    async def test_sync_no_change(self):
        adapter, api = _make_todoist_adapter_with_mock_api()
        api.get_reminders = AsyncMock(return_value=[{"id": "r1", "minute_offset": 15}])
        await adapter._sync_reminders("t1", [15])
        api.delete_reminder.assert_not_called()
        api.add_reminder.assert_not_called()

    async def test_sync_aborts_on_premium_only_without_deleting_existing(self):
        """REGRESSION: Free tier rejects offset reminders → don't delete the
        existing implicit reminder; roll back any partial creates."""
        from custom_components.home_tasks.todoist_api import TodoistAPIError

        adapter, api = _make_todoist_adapter_with_mock_api()
        # Existing implicit reminder (offset=0) that Todoist auto-creates
        api.get_reminders = AsyncMock(return_value=[
            {"id": "implicit-1", "minute_offset": 0},
        ])
        # Adds will fail with PREMIUM_ONLY
        api.add_reminder = AsyncMock(
            side_effect=TodoistAPIError(403, 32, "Premium only feature")
        )

        await adapter._sync_reminders("t1", [60, 1440])

        # The existing implicit reminder must NOT have been deleted
        api.delete_reminder.assert_not_called()

    async def test_sync_rolls_back_partial_creates_on_premium_error(self):
        """REGRESSION: If first add succeeds but second fails, the first
        must be rolled back (delete the partially-created reminder)."""
        from custom_components.home_tasks.todoist_api import TodoistAPIError

        adapter, api = _make_todoist_adapter_with_mock_api()
        api.get_reminders = AsyncMock(return_value=[])
        api.add_reminder = AsyncMock(side_effect=[
            {"id": "created-1"},
            TodoistAPIError(403, 32, "Premium only feature"),
        ])

        await adapter._sync_reminders("t1", [30, 60])

        # The first reminder should have been rolled back via delete_reminder
        api.delete_reminder.assert_awaited_once_with("created-1")


# ---------------------------------------------------------------------------
#  GenericAdapter — exercises the actual hass.services.async_call paths
# ---------------------------------------------------------------------------


def _make_generic_adapter(supported_features: int = 0):
    """Build a GenericAdapter with a minimal mocked HA hass + entity state."""
    hass = MagicMock()
    state = MagicMock()
    state.attributes = {"supported_features": supported_features}
    hass.states.get = MagicMock(return_value=state)
    hass.services.async_call = AsyncMock()
    return GenericAdapter(hass, "todo.test_entity", {}), hass


class TestGenericAdapterCreateTask:
    """async_create_task forwards to todo.add_item with mapped fields."""

    async def test_basic_title_only(self):
        adapter, hass = _make_generic_adapter()
        result = await adapter.async_create_task({"title": "Buy milk"})
        assert result is None  # Generic adapter doesn't return uid
        hass.services.async_call.assert_awaited_once()
        args, kwargs = hass.services.async_call.await_args
        assert args[0] == "todo"
        assert args[1] == "add_item"
        assert args[2]["item"] == "Buy milk"

    async def test_with_due_date_only_no_datetime_support(self):
        adapter, hass = _make_generic_adapter(supported_features=0)
        await adapter.async_create_task({
            "title": "T", "due_date": "2027-05-15"
        })
        service_data = hass.services.async_call.await_args.args[2]
        assert service_data["due_date"] == "2027-05-15"
        assert "due_datetime" not in service_data

    async def test_with_due_date_and_time_with_datetime_support(self):
        adapter, hass = _make_generic_adapter(supported_features=32)
        await adapter.async_create_task({
            "title": "T", "due_date": "2027-05-15", "due_time": "09:30"
        })
        service_data = hass.services.async_call.await_args.args[2]
        assert service_data["due_datetime"] == "2027-05-15 09:30:00"
        assert "due_date" not in service_data

    async def test_with_due_time_but_no_datetime_support_falls_back(self):
        adapter, hass = _make_generic_adapter(supported_features=0)
        await adapter.async_create_task({
            "title": "T", "due_date": "2027-05-15", "due_time": "09:30"
        })
        service_data = hass.services.async_call.await_args.args[2]
        # No datetime support → only due_date is sent
        assert service_data["due_date"] == "2027-05-15"
        assert "due_datetime" not in service_data

    async def test_with_notes(self):
        adapter, hass = _make_generic_adapter()
        await adapter.async_create_task({"title": "T", "notes": "Some notes"})
        service_data = hass.services.async_call.await_args.args[2]
        assert service_data["description"] == "Some notes"


class TestGenericAdapterUpdateTask:
    """async_update_task routes fields to either the API or the unsynced dict."""

    async def test_title_rename(self):
        adapter, hass = _make_generic_adapter()
        unsynced = await adapter.async_update_task("uid-1", {"title": "Renamed"})
        kwargs = hass.services.async_call.await_args.args[2]
        assert kwargs["item"] == "uid-1"
        assert kwargs["rename"] == "Renamed"
        assert "title" not in unsynced

    async def test_completed_true(self):
        adapter, hass = _make_generic_adapter()
        await adapter.async_update_task("uid-1", {"completed": True})
        kwargs = hass.services.async_call.await_args.args[2]
        assert kwargs["status"] == "completed"

    async def test_completed_false(self):
        adapter, hass = _make_generic_adapter()
        await adapter.async_update_task("uid-1", {"completed": False})
        kwargs = hass.services.async_call.await_args.args[2]
        assert kwargs["status"] == "needs_action"

    async def test_notes_update(self):
        adapter, hass = _make_generic_adapter()
        await adapter.async_update_task("uid-1", {"notes": "New notes"})
        kwargs = hass.services.async_call.await_args.args[2]
        assert kwargs["description"] == "New notes"

    async def test_clear_due_date(self):
        adapter, hass = _make_generic_adapter()
        await adapter.async_update_task("uid-1", {"due_date": None})
        kwargs = hass.services.async_call.await_args.args[2]
        assert kwargs["due_date"] is None

    async def test_due_date_only_no_datetime_support(self):
        adapter, hass = _make_generic_adapter(supported_features=0)
        await adapter.async_update_task(
            "uid-1", {"due_date": "2027-06-01"}
        )
        kwargs = hass.services.async_call.await_args.args[2]
        assert kwargs["due_date"] == "2027-06-01"

    async def test_due_date_with_time_with_datetime_support(self):
        adapter, hass = _make_generic_adapter(supported_features=32)
        await adapter.async_update_task(
            "uid-1", {"due_date": "2027-06-01", "due_time": "14:30"}
        )
        kwargs = hass.services.async_call.await_args.args[2]
        assert kwargs["due_datetime"] == "2027-06-01 14:30:00"

    async def test_clear_due_time_only_with_datetime_support(self):
        """Clearing only due_time (date kept) downgrades to midnight datetime."""
        adapter, hass = _make_generic_adapter(supported_features=32)
        await adapter.async_update_task(
            "uid-1", {"due_date": "2027-06-01", "due_time": None}
        )
        kwargs = hass.services.async_call.await_args.args[2]
        assert kwargs["due_datetime"] == "2027-06-01 00:00:00"

    async def test_due_time_alone_goes_to_unsynced(self):
        """due_time without due_date can't be sent to provider — overlay only."""
        adapter, hass = _make_generic_adapter(supported_features=32)
        unsynced = await adapter.async_update_task(
            "uid-1", {"due_time": "10:00"}
        )
        assert unsynced.get("due_time") == "10:00"

    async def test_unknown_field_routed_to_unsynced(self):
        adapter, hass = _make_generic_adapter()
        unsynced = await adapter.async_update_task(
            "uid-1", {"priority": 2, "tags": ["a"]}
        )
        assert unsynced["priority"] == 2
        assert unsynced["tags"] == ["a"]

    async def test_no_api_call_when_only_unsynced_fields(self):
        adapter, hass = _make_generic_adapter()
        await adapter.async_update_task("uid-1", {"priority": 1})
        # Only "item" key would be in service_data → no API call
        hass.services.async_call.assert_not_awaited()


class TestGenericAdapterDeleteTask:
    async def test_delete(self):
        adapter, hass = _make_generic_adapter()
        await adapter.async_delete_task("uid-1")
        args = hass.services.async_call.await_args.args
        assert args[1] == "remove_item"
        assert args[2]["item"] == "uid-1"


class TestGenericAdapterReorderTasks:
    """async_reorder_tasks uses todo.move_item when MOVE_TODO_ITEM is supported."""

    async def test_reorder_unsupported_returns_false(self):
        """Without MOVE_TODO_ITEM (8) feature, returns False (caller uses overlay)."""
        adapter, hass = _make_generic_adapter(supported_features=0)
        result = await adapter.async_reorder_tasks(["a", "b", "c"])
        assert result is False
        hass.services.async_call.assert_not_awaited()

    async def test_reorder_supported_calls_move_item(self):
        """With MOVE_TODO_ITEM, calls todo.move_item once per task."""
        adapter, hass = _make_generic_adapter(supported_features=8)
        result = await adapter.async_reorder_tasks(["a", "b", "c"])
        assert result is True
        # 3 calls, one per item
        assert hass.services.async_call.await_count == 3
        # First call: no previous_uid (first task has nothing before it)
        first_call = hass.services.async_call.await_args_list[0]
        assert first_call.args[0] == "todo"
        assert first_call.args[1] == "move_item"
        first_data = first_call.args[2]
        assert first_data["uid"] == "a"
        assert "previous_uid" not in first_data  # not passed for the first task
        # Second call: previous_uid="a"
        second_data = hass.services.async_call.await_args_list[1].args[2]
        assert second_data["uid"] == "b"
        assert second_data["previous_uid"] == "a"

    async def test_reorder_failure_returns_false(self):
        adapter, hass = _make_generic_adapter(supported_features=8)
        hass.services.async_call = AsyncMock(side_effect=Exception("boom"))
        result = await adapter.async_reorder_tasks(["a", "b"])
        assert result is False


# ---------------------------------------------------------------------------
#  TodoistAdapter — pure helper functions
# ---------------------------------------------------------------------------


class TestTodoistDueExtractors:
    """_extract_date and _extract_time on TodoistDue objects."""

    def test_extract_date_none(self):
        assert TodoistAdapter._extract_date(None) is None

    def test_extract_date_simple(self):
        due = MagicMock()
        due.date = "2027-05-15"
        assert TodoistAdapter._extract_date(due) == "2027-05-15"

    def test_extract_date_with_iso_datetime(self):
        due = MagicMock()
        due.date = "2027-05-15T14:30:00"
        result = TodoistAdapter._extract_date(due)
        assert result == "2027-05-15"

    def test_extract_date_no_date_attr(self):
        due = MagicMock()
        due.date = None
        assert TodoistAdapter._extract_date(due) is None

    def test_extract_time_none(self):
        assert TodoistAdapter._extract_time(None) is None

    def test_extract_time_no_T_in_date(self):
        due = MagicMock()
        due.date = "2027-05-15"  # date only, no time component
        assert TodoistAdapter._extract_time(due) is None

    def test_extract_time_with_iso_datetime(self):
        due = MagicMock()
        due.date = "2027-05-15T09:30:00"
        result = TodoistAdapter._extract_time(due)
        # Must be a HH:MM string (timezone conversion may shift hour)
        assert result is not None
        assert len(result) == 5 and result[2] == ":"


class TestTodoistMatchCollaborator:
    """_match_person_to_collaborator finds Todoist user IDs from HA person entities."""

    def _build_adapter(self, person_name=None, collaborators=None):
        hass = MagicMock()
        if person_name is None:
            hass.states.get = MagicMock(return_value=None)
        else:
            state = MagicMock()
            state.attributes = {"friendly_name": person_name}
            hass.states.get = MagicMock(return_value=state)
        adapter = TodoistAdapter(hass, "todo.test", {}, "tok")
        adapter._collaborators = collaborators or []
        return adapter

    def _make_collab(self, name, collab_id):
        c = MagicMock()
        c.name = name
        c.id = collab_id
        return c

    def test_no_state_returns_none(self):
        adapter = self._build_adapter(person_name=None)
        assert adapter._match_person_to_collaborator("person.alice") is None

    def test_no_friendly_name_returns_none(self):
        adapter = self._build_adapter(person_name="")
        assert adapter._match_person_to_collaborator("person.alice") is None

    def test_exact_match(self):
        adapter = self._build_adapter(
            person_name="Alice", collaborators=[self._make_collab("Alice", "123")]
        )
        assert adapter._match_person_to_collaborator("person.alice") == "123"

    def test_case_insensitive_match(self):
        adapter = self._build_adapter(
            person_name="ALICE", collaborators=[self._make_collab("alice", "123")]
        )
        assert adapter._match_person_to_collaborator("person.alice") == "123"

    def test_substring_match(self):
        adapter = self._build_adapter(
            person_name="Alice",
            collaborators=[self._make_collab("Alice Wonderland", "456")],
        )
        assert adapter._match_person_to_collaborator("person.alice") == "456"

    def test_no_match(self):
        adapter = self._build_adapter(
            person_name="Alice", collaborators=[self._make_collab("Bob", "789")]
        )
        assert adapter._match_person_to_collaborator("person.alice") is None


class TestTodoistBuildDueParams:
    """_build_due_params maps structured fields to Todoist API parameters."""

    def _adapter(self):
        adapter, _api = _make_todoist_adapter_with_mock_api()
        return adapter

    def test_due_date_only(self):
        params = self._adapter()._build_due_params({"due_date": "2027-05-15"})
        assert params == {"due_date": "2027-05-15"}

    def test_due_date_and_time(self):
        params = self._adapter()._build_due_params(
            {"due_date": "2027-05-15", "due_time": "09:30"}
        )
        assert params == {"due_datetime": "2027-05-15T09:30:00"}

    def test_clear_due_date_explicitly(self):
        params = self._adapter()._build_due_params({"due_date": None})
        assert params == {"due_string": "no date"}

    def test_recurrence_disabled_with_due_date(self):
        params = self._adapter()._build_due_params({
            "recurrence_enabled": False, "due_date": "2027-05-15"
        })
        assert params == {"due_date": "2027-05-15"}

    def test_recurrence_disabled_no_due_clears(self):
        params = self._adapter()._build_due_params({"recurrence_enabled": False})
        assert params == {"due_string": "no date"}

    def test_recurrence_enabled_daily(self):
        params = self._adapter()._build_due_params({
            "recurrence_enabled": True, "recurrence_unit": "days",
            "recurrence_value": 1,
        })
        assert "due_string" in params
        assert "every day" in params["due_string"]

    def test_recurrence_with_due_time_inserted(self):
        params = self._adapter()._build_due_params({
            "recurrence_enabled": True, "recurrence_unit": "days",
            "recurrence_value": 1, "due_time": "09:30",
        })
        assert "at 09:30" in params["due_string"]

    def test_recurrence_hourly_no_time_appended(self):
        params = self._adapter()._build_due_params({
            "recurrence_enabled": True, "recurrence_unit": "hours",
            "recurrence_value": 2, "due_time": "09:30",
        })
        # Hourly intervals must not append "at HH:MM" (Todoist 400)
        assert "at 09:30" not in params["due_string"]


class TestTodoistMergeDueFields:
    """_merge_due_fields fetches current task state when fields are partial."""

    async def test_complete_fields_skip_fetch(self):
        adapter, api = _make_todoist_adapter_with_mock_api()
        full_fields = {
            "recurrence_enabled": True,
            "recurrence_type": "interval",
            "recurrence_value": 1,
            "recurrence_unit": "days",
            "recurrence_weekdays": [],
            "recurrence_start_date": None,
            "recurrence_time": None,
            "due_date": "2027-05-15",
        }
        result = await adapter._merge_due_fields(api, "t1", full_fields)
        assert result == full_fields
        api.get_task.assert_not_called()

    async def test_partial_fields_fetch_and_merge(self):
        adapter, api = _make_todoist_adapter_with_mock_api()
        current = MagicMock()
        current.due = MagicMock()
        current.due.is_recurring = True
        current.due.string = "every 2 days"
        current.due.date = "2027-05-15"
        api.get_task = AsyncMock(return_value=current)

        result = await adapter._merge_due_fields(
            api, "t1", {"recurrence_start_date": "2027-06-01"}
        )
        # New start_date present + fields from current state filled in
        assert result["recurrence_start_date"] == "2027-06-01"
        assert result["recurrence_enabled"] is True

    async def test_fetch_failure_returns_fields_unchanged(self):
        adapter, api = _make_todoist_adapter_with_mock_api()
        api.get_task = AsyncMock(side_effect=Exception("network down"))
        fields = {"recurrence_start_date": "2027-06-01"}
        result = await adapter._merge_due_fields(api, "t1", fields)
        assert result == fields


class TestTodoistResolveProjectId:
    """_resolve_project_id picks the right project from a list by name."""

    async def test_exact_match_by_entity_data_name(self):
        hass = MagicMock()
        adapter = TodoistAdapter(hass, "todo.shopping", {"name": "Shopping"}, "tok")
        adapter._api = MagicMock()
        proj_a = MagicMock()
        proj_a.id = "id-a"
        proj_a.name = "Other"
        proj_b = MagicMock()
        proj_b.id = "id-b"
        proj_b.name = "Shopping"
        adapter._api.get_projects = AsyncMock(return_value=[proj_a, proj_b])

        await adapter._resolve_project_id()
        assert adapter._project_id == "id-b"

    async def test_match_by_entity_id_suffix(self):
        hass = MagicMock()
        adapter = TodoistAdapter(hass, "todo.my_list", {}, "tok")
        adapter._api = MagicMock()
        proj = MagicMock()
        proj.id = "id-x"
        proj.name = "my list"  # matches normalized entity_id
        adapter._api.get_projects = AsyncMock(return_value=[proj])

        await adapter._resolve_project_id()
        assert adapter._project_id == "id-x"

    async def test_no_match_leaves_id_unset(self):
        hass = MagicMock()
        adapter = TodoistAdapter(hass, "todo.unknown", {}, "tok")
        adapter._api = MagicMock()
        proj = MagicMock()
        proj.id = "x"
        proj.name = "Other"
        adapter._api.get_projects = AsyncMock(return_value=[proj])

        await adapter._resolve_project_id()
        assert adapter._project_id is None
