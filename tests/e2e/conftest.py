"""Fixtures for E2E flow tests.

E2E tests exercise complete WebSocket command chains against an in-memory
HA instance.  They use the same hass / mock_config_entry fixtures from the
root conftest, plus helpers specific to external-entity flows.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

DOMAIN = "home_tasks"


@pytest.fixture
async def mock_config_entry_with_ws(
    hass: HomeAssistant,
    hass_ws_client,
    mock_config_entry: MockConfigEntry,
):
    """Return (hass_ws_client, list_id) for a fully loaded native list."""
    from custom_components.home_tasks.websocket_api import ws_get_lists

    ws = await hass_ws_client(hass)
    # Resolve list_id
    await ws.send_json({"id": 1, "type": "home_tasks/get_lists"})
    resp = await ws.receive_json()
    lists = resp["result"]["lists"]
    list_id = lists[0]["id"]
    return ws, list_id


def _make_todo_entity(hass: HomeAssistant, entity_id: str, supported_features: int = 0):
    """Register a mock todo entity in hass with the given supported_features."""
    from homeassistant.components.todo import TodoItem, TodoItemStatus

    mock_entity = MagicMock()
    mock_entity.entity_id = entity_id
    mock_entity.todo_items = []
    mock_entity.supported_features = supported_features

    state_attrs = {"supported_features": supported_features, "friendly_name": entity_id}
    hass.states.async_set(entity_id, "0", state_attrs)

    entity_comp = hass.data.setdefault("todo", MagicMock())
    entity_comp.get_entity = MagicMock(return_value=mock_entity)

    return mock_entity
