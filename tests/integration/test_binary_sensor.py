"""Tests for the overdue binary sensor platform."""
from __future__ import annotations

import pytest
from freezegun import freeze_time
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

DOMAIN = "home_tasks"

pytestmark = pytest.mark.integration


def _get_binary_sensor_entity_id(hass: HomeAssistant, unique_id: str) -> str | None:
    """Look up a binary sensor entity_id by its unique_id."""
    reg = er.async_get(hass)
    return reg.async_get_entity_id("binary_sensor", DOMAIN, unique_id)


async def test_binary_sensor_registered(hass: HomeAssistant, mock_config_entry) -> None:
    """An overdue binary sensor is registered for the native list."""
    entity_id = _get_binary_sensor_entity_id(hass, f"{mock_config_entry.entry_id}_overdue")
    assert entity_id is not None


@freeze_time("2026-04-03")
async def test_binary_sensor_off_when_no_overdue_tasks(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """Binary sensor is OFF when no tasks are overdue."""
    await store.async_add_task("Future task")
    await store.async_update_task(
        (await store.async_add_task("Future"))["id"], due_date="2026-04-10"
    )
    await hass.async_block_till_done()

    entity_id = _get_binary_sensor_entity_id(hass, f"{mock_config_entry.entry_id}_overdue")
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "off"


@freeze_time("2026-04-03")
async def test_binary_sensor_on_when_task_overdue(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """Binary sensor is ON when a task is past its due date."""
    task = await store.async_add_task("Overdue task")
    await store.async_update_task(task["id"], due_date="2026-04-01")
    await hass.async_block_till_done()

    entity_id = _get_binary_sensor_entity_id(hass, f"{mock_config_entry.entry_id}_overdue")
    state = hass.states.get(entity_id)
    assert state.state == "on"


@freeze_time("2026-04-03")
async def test_binary_sensor_off_after_completing_overdue_task(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """Binary sensor returns to OFF when the overdue task is completed."""
    task = await store.async_add_task("Was overdue")
    await store.async_update_task(task["id"], due_date="2026-04-01")
    await hass.async_block_till_done()

    entity_id = _get_binary_sensor_entity_id(hass, f"{mock_config_entry.entry_id}_overdue")
    assert hass.states.get(entity_id).state == "on"

    await store.async_update_task(task["id"], completed=True)
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == "off"


@freeze_time("2026-04-03")
async def test_binary_sensor_overdue_tasks_attribute(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """overdue_tasks attribute contains details of each overdue task."""
    task = await store.async_add_task("Late task")
    await store.async_update_task(task["id"], due_date="2026-04-01")
    await hass.async_block_till_done()

    entity_id = _get_binary_sensor_entity_id(hass, f"{mock_config_entry.entry_id}_overdue")
    state = hass.states.get(entity_id)
    overdue_tasks = state.attributes.get("overdue_tasks", [])
    assert len(overdue_tasks) == 1
    assert overdue_tasks[0]["title"] == "Late task"
    assert overdue_tasks[0]["due_date"] == "2026-04-01"


# ---------------------------------------------------------------------------
# External entries should not create binary sensor entities
# ---------------------------------------------------------------------------


async def test_binary_sensor_not_created_for_external_entry(
    hass: HomeAssistant,
) -> None:
    """External entries do not create a binary_sensor entity."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    ext_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"type": "external", "entity_id": "todo.bsensor_ext", "name": "BSensor Ext"},
        title="BSensor Ext (External)",
    )
    ext_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(ext_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = _get_binary_sensor_entity_id(hass, f"{ext_entry.entry_id}_overdue")
    assert entity_id is None
