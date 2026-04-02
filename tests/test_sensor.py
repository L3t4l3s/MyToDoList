"""Tests for the open tasks sensor platform."""
from __future__ import annotations

import pytest
from freezegun import freeze_time
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

DOMAIN = "home_tasks"


def _get_sensor_entity_id(hass: HomeAssistant, unique_id: str) -> str | None:
    """Look up a sensor entity_id by its unique_id."""
    reg = er.async_get(hass)
    return reg.async_get_entity_id("sensor", DOMAIN, unique_id)


async def test_sensor_registered(hass: HomeAssistant, mock_config_entry) -> None:
    """An open-tasks sensor is registered for the native list."""
    entity_id = _get_sensor_entity_id(hass, f"{mock_config_entry.entry_id}_open_tasks")
    assert entity_id is not None


async def test_sensor_counts_open_tasks(hass: HomeAssistant, mock_config_entry, store) -> None:
    """Sensor state equals the number of incomplete tasks."""
    await store.async_add_task("Task 1")
    await store.async_add_task("Task 2")
    await hass.async_block_till_done()

    entity_id = _get_sensor_entity_id(hass, f"{mock_config_entry.entry_id}_open_tasks")
    state = hass.states.get(entity_id)
    assert state is not None
    assert int(state.state) == 2


async def test_sensor_decrements_on_completion(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """Sensor decrements by one when a task is completed."""
    task = await store.async_add_task("Sole task")
    await hass.async_block_till_done()

    entity_id = _get_sensor_entity_id(hass, f"{mock_config_entry.entry_id}_open_tasks")
    assert int(hass.states.get(entity_id).state) == 1

    await store.async_update_task(task["id"], completed=True)
    await hass.async_block_till_done()
    assert int(hass.states.get(entity_id).state) == 0


async def test_sensor_open_task_titles_attribute(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """open_task_titles attribute lists titles of incomplete tasks only."""
    await store.async_add_task("Open one")
    task2 = await store.async_add_task("Open two")
    await store.async_update_task(task2["id"], completed=True)
    await hass.async_block_till_done()

    entity_id = _get_sensor_entity_id(hass, f"{mock_config_entry.entry_id}_open_tasks")
    state = hass.states.get(entity_id)
    titles = state.attributes.get("open_task_titles", [])
    assert "Open one" in titles
    assert "Open two" not in titles


@freeze_time("2026-04-03")
async def test_sensor_overdue_count_attribute(
    hass: HomeAssistant, mock_config_entry, store
) -> None:
    """overdue_count attribute reflects tasks with due_date before today."""
    task = await store.async_add_task("Overdue task")
    await store.async_update_task(task["id"], due_date="2026-04-01")
    await hass.async_block_till_done()

    entity_id = _get_sensor_entity_id(hass, f"{mock_config_entry.entry_id}_open_tasks")
    state = hass.states.get(entity_id)
    assert state.attributes.get("overdue_count") == 1
