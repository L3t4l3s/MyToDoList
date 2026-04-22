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

        uid, unsynced = await adapter.async_create_task({"title": "Test create"})
        assert uid == "new-1"
        assert unsynced == {}
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

    async def test_priority_and_tags_do_not_leak_to_overlay(self):
        """Mirror of the GenericAdapter test: Todoist syncs these natively.

        The generic adapter treats priority/tags as overlay-only because the
        HA todo service schema can't carry them (see
        ``TestGenericAdapterCreateBitGuards.test_non_base_fields_go_to_overlay
        _for_generic_provider``).  Todoist's REST API *does* accept them, so
        the TodoistAdapter must NOT echo them back into ``unsynced`` — that
        would double-write the same value to both the provider and the
        overlay and diverge on subsequent reads.
        """
        adapter, api = _make_todoist_adapter_with_mock_api()
        new_task = MagicMock()
        new_task.id = "new-4"
        api.add_task = AsyncMock(return_value=new_task)

        uid, unsynced = await adapter.async_create_task({
            "title": "Native-synced",
            "priority": 3,
            "tags": ["a", "b"],
        })

        assert uid == "new-4"
        # priority / tags are in _TODOIST_PROVIDER_FIELDS → not in unsynced
        assert "priority" not in unsynced
        assert "tags" not in unsynced
        # And they DO reach the API.
        kwargs = api.add_task.await_args.kwargs
        assert kwargs["priority"] == 4
        assert kwargs["labels"] == ["a", "b"]

    async def test_sub_items_do_not_leak_to_overlay(self):
        """sub_items are handled via separate add_sub_task calls, not overlay.

        Even though the main create call doesn't pass sub_items to the API,
        they must NOT appear in ``unsynced`` — otherwise the overlay would
        hold stale duplicates of what Todoist already stores natively.
        """
        adapter, api = _make_todoist_adapter_with_mock_api()
        new_task = MagicMock()
        new_task.id = "new-5"
        api.add_task = AsyncMock(return_value=new_task)

        uid, unsynced = await adapter.async_create_task({
            "title": "With subs",
            "sub_items": [{"title": "s1"}, {"title": "s2"}],
        })

        assert "sub_items" not in unsynced

    async def test_assigned_person_leaks_to_overlay_by_design(self):
        """assigned_person is the one field that intentionally double-writes.

        Todoist accepts ``assignee_id`` on write (visible in the Todoist app)
        but never returns it on read — so we also store the HA ``person.*``
        entity_id in the overlay to drive the card's display.  The test
        pins this asymmetry so nobody "optimises" it away.
        """
        adapter, api = _make_todoist_adapter_with_mock_api()
        new_task = MagicMock()
        new_task.id = "new-6"
        api.add_task = AsyncMock(return_value=new_task)

        uid, unsynced = await adapter.async_create_task({
            "title": "Assigned",
            "assigned_person": "person.alice",
        })

        assert unsynced.get("assigned_person") == "person.alice", (
            "assigned_person must be mirrored into the overlay because "
            "Todoist's API doesn't return it on read."
        )


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
# NOTE: Full GenericAdapter behaviour (service-call acceptance, reorder via
# entity.async_move_todo_item, etc.) is covered end-to-end by the live tests
# in tests/live/test_provider_*.py — they drive the real ``todo.*`` services
# against a running HA instance and verify the provider-side view via
# todo.get_items.  That prevents MagicMock-style tests from green-lighting
# service names HA would reject (this once hid the Google Tasks reorder bug).
#
# The unit tests below are deliberately scoped: they verify the pure-Python
# *decision logic* that routes fields between ``service_data`` and the
# ``unsynced`` overlay dict based on the entity's ``supported_features``
# bitmap.  They don't assert anything about how HA would interpret the
# service call — only about what the adapter DECIDES to send vs. keep local.
# If you're touching the service call signature, update the live tests.
# ---------------------------------------------------------------------------


# HA TodoListEntityFeature bits — kept inline so tests document the protocol
# contract with HA core.  Cross-check with homeassistant/components/todo/const.py.
_F_CREATE = 1
_F_DELETE = 2
_F_UPDATE = 4
_F_MOVE = 8
_F_SET_DUE_DATE = 16
_F_SET_DUE_DATETIME = 32
_F_SET_DESCRIPTION = 64

# Provider profiles — what HA reports in state.attributes.supported_features.
FEATURES_SHOPPING_LIST = _F_CREATE | _F_UPDATE | _F_DELETE | _F_MOVE  # 15
FEATURES_GOOGLE_TASKS = FEATURES_SHOPPING_LIST | _F_SET_DUE_DATE | _F_SET_DESCRIPTION  # 95
FEATURES_FULL = FEATURES_GOOGLE_TASKS | _F_SET_DUE_DATETIME  # 127


def _make_generic_adapter(
    supported_features: int,
    entity_id: str = "todo.ut_generic",
    existing_uids: list[str] | None = None,
    new_uid: str | None = "new-uid-x",
):
    """Build a GenericAdapter whose hass reports the given feature bitmap.

    The returned ``captured`` dict collects every ``hass.services.async_call``
    invocation so tests can assert on payloads.  ``async_read_tasks`` is
    patched to return a deterministic before/after snapshot so the before/
    after-diff UID discovery is exercised without touching HA's todo
    component state.
    """
    captured: dict = {"calls": []}

    hass = MagicMock()
    state = MagicMock()
    state.attributes = {"supported_features": supported_features}
    hass.states.get = MagicMock(return_value=state)

    async def _record_call(domain, service, service_data=None, target=None, blocking=False):
        captured["calls"].append({
            "domain": domain,
            "service": service,
            "service_data": dict(service_data) if service_data else {},
            "target": dict(target) if target else {},
        })

    hass.services.async_call = AsyncMock(side_effect=_record_call)

    adapter = GenericAdapter(hass, entity_id, {})

    # Patch async_read_tasks to return an explicit before/after snapshot.
    # Before the create call: ``existing_uids``.  After: same plus ``new_uid``
    # (when set) — the adapter's diff should pick ``new_uid`` out.
    before = [{"uid": u, "summary": f"existing-{u}"} for u in (existing_uids or [])]
    after = list(before)
    if new_uid is not None:
        after.append({"uid": new_uid, "summary": "new task"})
    reads = iter([before, after])

    async def _read_tasks():
        try:
            return next(reads)
        except StopIteration:
            return after

    adapter.async_read_tasks = _read_tasks  # type: ignore[method-assign]
    return adapter, captured


# ---------------------------------------------------------------------------
#  GenericAdapter — supported_features bit-guard decision logic
# ---------------------------------------------------------------------------


class TestGenericAdapterCreateBitGuards:
    """async_create_task routes fields by supported_features bits."""

    async def test_shopping_list_profile_routes_notes_and_due_to_overlay(self):
        """No SET_DUE_DATE, no SET_DESCRIPTION → notes + due stay local."""
        adapter, captured = _make_generic_adapter(FEATURES_SHOPPING_LIST)

        uid, unsynced = await adapter.async_create_task({
            "title": "Cheese",
            "notes": "aged cheddar",
            "due_date": "2027-09-15",
            "due_time": "14:00",
        })

        # Only the title reaches HA — the provider can't carry anything else.
        assert len(captured["calls"]) == 1
        call = captured["calls"][0]
        assert call["service"] == "add_item"
        assert call["service_data"] == {"item": "Cheese"}

        # Everything else must live in the overlay.
        assert unsynced == {
            "notes": "aged cheddar",
            "due_date": "2027-09-15",
            "due_time": "14:00",
        }
        # UID discovery must have run — we have overlay data to persist.
        assert uid == "new-uid-x"

    async def test_date_only_profile_sends_date_keeps_time_local(self):
        """SET_DUE_DATE but no SET_DUE_DATETIME → date goes, time stays local."""
        adapter, captured = _make_generic_adapter(FEATURES_GOOGLE_TASKS)

        uid, unsynced = await adapter.async_create_task({
            "title": "Google due time",
            "due_date": "2027-12-10",
            "due_time": "16:45",
        })

        call = captured["calls"][0]
        assert call["service_data"] == {
            "item": "Google due time",
            "due_date": "2027-12-10",
        }
        assert "due_datetime" not in call["service_data"]
        assert unsynced == {"due_time": "16:45"}
        assert uid == "new-uid-x"

    async def test_full_profile_sends_datetime_no_overlay_needed(self):
        """CalDAV-shaped: due_datetime supported → nothing left for overlay."""
        adapter, captured = _make_generic_adapter(FEATURES_FULL)

        uid, unsynced = await adapter.async_create_task({
            "title": "CalDAV task",
            "notes": "body",
            "due_date": "2027-12-10",
            "due_time": "16:45",
        })

        call = captured["calls"][0]
        assert call["service_data"] == {
            "item": "CalDAV task",
            "due_datetime": "2027-12-10 16:45:00",
            "description": "body",
        }
        assert unsynced == {}

    async def test_description_only_profile_keeps_due_local(self):
        """SET_DESCRIPTION but no SET_DUE_DATE → notes go, due stays local."""
        features = FEATURES_SHOPPING_LIST | _F_SET_DESCRIPTION
        adapter, captured = _make_generic_adapter(features)

        uid, unsynced = await adapter.async_create_task({
            "title": "Mixed",
            "notes": "n",
            "due_date": "2027-12-10",
        })

        call = captured["calls"][0]
        assert call["service_data"] == {
            "item": "Mixed",
            "description": "n",
        }
        assert "due_date" not in call["service_data"]
        assert unsynced == {"due_date": "2027-12-10"}

    async def test_non_base_fields_go_to_overlay_for_generic_provider(self):
        """priority / tags / assigned_person are overlay-only for GenericAdapter.

        This is NOT the same for TodoistAdapter — there priority and tags are
        synced via the Todoist REST API (see ``_TODOIST_PROVIDER_FIELDS`` and
        ``TestTodoistAdapterCreateTask``).  GenericAdapter only pushes what HA's
        todo service schema accepts (title/status/notes/due_date/due_datetime);
        everything else stays local.
        """
        adapter, captured = _make_generic_adapter(FEATURES_FULL)

        uid, unsynced = await adapter.async_create_task({
            "title": "Rich task",
            "priority": 3,
            "tags": ["a", "b"],
            "assigned_person": "person.alice",
        })

        call = captured["calls"][0]
        assert call["service_data"] == {"item": "Rich task"}
        assert unsynced == {
            "priority": 3,
            "tags": ["a", "b"],
            "assigned_person": "person.alice",
        }

    async def test_bare_title_skips_uid_discovery(self):
        """No overlay data to persist → no before/after snapshot, uid=None.

        The adapter only pays the cost of UID discovery when it actually
        needs a UID to key overlay data.  A plain title-only create has
        nothing to persist locally, so we skip the extra read.
        """
        captured: dict = {"calls": [], "reads": 0}

        hass = MagicMock()
        state = MagicMock()
        state.attributes = {"supported_features": FEATURES_FULL}
        hass.states.get = MagicMock(return_value=state)

        async def _record_call(*args, **kwargs):
            captured["calls"].append(args)

        hass.services.async_call = AsyncMock(side_effect=_record_call)

        adapter = GenericAdapter(hass, "todo.ut_generic", {})

        async def _read_tasks():
            captured["reads"] += 1
            return []

        adapter.async_read_tasks = _read_tasks  # type: ignore[method-assign]

        uid, unsynced = await adapter.async_create_task({"title": "plain"})

        assert uid is None
        assert unsynced == {}
        assert captured["reads"] == 0  # no snapshot, no re-read

    async def test_uid_discovery_uses_before_after_diff(self):
        """When overlay data exists, the new UID is the one absent from ``before``."""
        adapter, captured = _make_generic_adapter(
            FEATURES_SHOPPING_LIST,
            existing_uids=["pre-1", "pre-2"],
            new_uid="fresh-uid-42",
        )

        uid, unsynced = await adapter.async_create_task({
            "title": "Milk",
            "notes": "2 litres",  # forces UID discovery
        })

        assert uid == "fresh-uid-42"
        assert unsynced == {"notes": "2 litres"}


class TestGenericAdapterUpdateBitGuards:
    """async_update_task routes fields by supported_features bits."""

    async def test_shopping_list_profile_routes_notes_to_overlay(self):
        """UPDATE with notes on a notes-less provider → unsynced, no service call."""
        adapter, captured = _make_generic_adapter(FEATURES_SHOPPING_LIST)

        unsynced = await adapter.async_update_task("uid-1", {"notes": "n"})

        # service_data would only have "item" (the UID) → no update fires.
        assert captured["calls"] == []
        assert unsynced == {"notes": "n"}

    async def test_date_only_profile_sends_date_keeps_time_local(self):
        """due_date + due_time, provider lacks SET_DUE_DATETIME → time stays local."""
        adapter, captured = _make_generic_adapter(FEATURES_GOOGLE_TASKS)

        unsynced = await adapter.async_update_task("uid-1", {
            "due_date": "2027-12-10",
            "due_time": "16:45",
        })

        call = captured["calls"][0]
        assert call["service"] == "update_item"
        assert call["service_data"] == {
            "item": "uid-1",
            "due_date": "2027-12-10",
        }
        assert "due_datetime" not in call["service_data"]
        assert unsynced == {"due_time": "16:45"}

    async def test_full_profile_sends_datetime(self):
        adapter, captured = _make_generic_adapter(FEATURES_FULL)

        unsynced = await adapter.async_update_task("uid-1", {
            "due_date": "2027-12-10",
            "due_time": "16:45",
        })

        call = captured["calls"][0]
        assert call["service_data"] == {
            "item": "uid-1",
            "due_datetime": "2027-12-10 16:45:00",
        }
        assert unsynced == {}

    async def test_clear_due_date_on_dateless_provider_noops(self):
        """due_date=None on a shopping-list-shaped provider must NOT call HA.

        The provider never had a due_date — pushing ``due_date=None`` would
        be rejected with ``Entity does not support setting field 'due_date'``.
        The adapter must silently skip it.
        """
        adapter, captured = _make_generic_adapter(FEATURES_SHOPPING_LIST)

        unsynced = await adapter.async_update_task("uid-1", {"due_date": None})

        assert captured["calls"] == []
        # Nothing to store locally either — due_date was already absent.
        assert unsynced == {}

    async def test_clear_due_date_on_date_capable_provider_sends_none(self):
        """due_date=None on a Google-shaped provider MUST reach HA to unset."""
        adapter, captured = _make_generic_adapter(FEATURES_GOOGLE_TASKS)

        unsynced = await adapter.async_update_task("uid-1", {"due_date": None})

        call = captured["calls"][0]
        assert call["service_data"] == {"item": "uid-1", "due_date": None}
        assert unsynced == {}

    async def test_description_only_profile_sends_notes_keeps_due_local(self):
        """SET_DESCRIPTION but no SET_DUE_DATE → notes go, due stays local."""
        features = FEATURES_SHOPPING_LIST | _F_SET_DESCRIPTION
        adapter, captured = _make_generic_adapter(features)

        unsynced = await adapter.async_update_task("uid-1", {
            "notes": "hello",
            "due_date": "2027-12-10",
            "priority": 3,
        })

        call = captured["calls"][0]
        assert call["service_data"] == {
            "item": "uid-1",
            "description": "hello",
        }
        assert unsynced == {"due_date": "2027-12-10", "priority": 3}


# ---------------------------------------------------------------------------


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
