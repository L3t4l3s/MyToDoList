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
        assert caps.can_sync_assignee is False  # False until collaborators loaded
        assert caps.can_sync_recurrence is True
        assert caps.can_sync_reminders is False  # v3.x has no reminder endpoints

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
