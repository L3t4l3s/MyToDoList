"""Fixtures and skip-logic for live tests.

Live tests require credentials and dedicated test lists. Each test is
auto-skipped if the env vars it needs are missing, so partial setups still
run cleanly (e.g. only Todoist configured → only Todoist tests run).
"""
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
import pytest_socket

from .config import CONFIG, LiveConfig
from .ws_client import HAWebSocketClient


# pytest-homeassistant-custom-component disables all sockets in
# pytest_runtest_setup, but live tests need real network access.
# Restore the original socket class AND the original connect method,
# both of which pytest-socket replaces.
import socket as _socket_module  # noqa: E402

_REAL_SOCKET = pytest_socket._true_socket
_REAL_CONNECT = pytest_socket._true_connect


@pytest.fixture(autouse=True)
def _enable_sockets_for_live_tests():
    _socket_module.socket = _REAL_SOCKET
    _socket_module.socket.connect = _REAL_CONNECT
    yield


# ---------------------------------------------------------------------------
# Skip-logic — auto-skip live tests when required env vars are missing
# ---------------------------------------------------------------------------

# Each marker → list of CONFIG attributes that must be set
_MARKER_REQUIREMENTS: dict[str, list[str]] = {
    "live_websocket": ["ha_url", "ha_token", "native_list_name"],
    "live_websocket_two_lists": [
        "ha_url", "ha_token", "native_list_name", "native_list_name_secondary",
    ],
    "live_todoist": ["ha_url", "ha_token", "todoist_entity"],
    "live_google_tasks": ["ha_url", "ha_token", "google_tasks_entity"],
    "live_caldav": ["ha_url", "ha_token", "caldav_entity"],
    "live_local_todo": ["ha_url", "ha_token", "local_todo_entity"],
    "live_bring": ["ha_url", "ha_token", "bring_entity"],
}


def pytest_collection_modifyitems(config, items):
    """Skip live tests whose env vars are missing."""
    for item in items:
        for marker in item.iter_markers():
            required = _MARKER_REQUIREMENTS.get(marker.name)
            if required is None:
                continue
            missing = [
                attr for attr in required
                if getattr(CONFIG, attr, None) in (None, "")
            ]
            if missing:
                env_names = ", ".join(_attr_to_env(a) for a in missing)
                item.add_marker(pytest.mark.skip(
                    reason=f"live test: missing env vars ({env_names})"
                ))


def _attr_to_env(attr: str) -> str:
    """Map a CONFIG attribute name back to its env var name."""
    mapping = {
        "ha_url": "HT_HA_URL",
        "ha_token": "HT_HA_TOKEN",
        "native_list_name": "HT_NATIVE_LIST_NAME",
        "native_list_name_secondary": "HT_NATIVE_LIST_NAME_2",
        "todoist_entity": "HT_TODOIST_TEST_ENTITY",
        "google_tasks_entity": "HT_GOOGLE_TASKS_TEST_ENTITY",
        "caldav_entity": "HT_CALDAV_TEST_ENTITY",
        "local_todo_entity": "HT_LOCAL_TODO_TEST_ENTITY",
        "bring_entity": "HT_BRING_TEST_ENTITY",
    }
    return mapping.get(attr, attr.upper())


# ---------------------------------------------------------------------------
# CalDAV availability helper
# ---------------------------------------------------------------------------


async def ensure_caldav_available(ws: HAWebSocketClient, entity_id: str) -> None:
    """Reload the CalDAV integration if the entity is unavailable.

    The CalDAV server (e.g. Nextcloud on SQLite) is often slow to respond
    after an HA restart.  Instead of skipping, reload the config entry once
    and wait for the entity to come back.
    """
    states = await ws.get_states()
    state = next((s for s in states if s["entity_id"] == entity_id), None)
    if state and state.get("state") != "unavailable":
        return  # already available

    # Find the caldav config entry and reload it via the HA service
    entries = await ws.send_command("config_entries/get")
    caldav_entry = next(
        (e for e in entries if e["domain"] == "caldav"),
        None,
    )
    if caldav_entry:
        print(f"[caldav] Entity {entity_id} unavailable — reloading config entry '{caldav_entry.get('title')}'")
        try:
            await ws.call_service(
                "homeassistant", "reload_config_entry",
                {"entry_id": caldav_entry["entry_id"]},
            )
        except Exception as err:
            print(f"[caldav] Reload failed: {err}")

    # Wait for the entity to become available (up to 15s)
    for attempt in range(15):
        await asyncio.sleep(1)
        states = await ws.get_states()
        state = next((s for s in states if s["entity_id"] == entity_id), None)
        if state and state.get("state") != "unavailable":
            print(f"[caldav] Entity available after {attempt + 1}s")
            return

    pytest.skip(f"{entity_id} still unavailable after CalDAV reload + 15s wait")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def live_config() -> LiveConfig:
    return CONFIG


@pytest_asyncio.fixture
async def ws_client() -> AsyncIterator[HAWebSocketClient]:
    """Open a fresh WebSocket connection per test, close at teardown."""
    if not CONFIG.ha_url or not CONFIG.ha_token:
        pytest.skip("HT_HA_URL or HT_HA_TOKEN not set")
    client = HAWebSocketClient(CONFIG.ha_url, CONFIG.ha_token)
    await client.connect()
    try:
        yield client
    finally:
        await client.close()


@pytest_asyncio.fixture
async def native_list_id(ws_client: HAWebSocketClient) -> str:
    """Resolve the configured native list name to its entry_id."""
    if not CONFIG.native_list_name:
        pytest.skip("HT_NATIVE_LIST_NAME not set")
    result = await ws_client.send_command("home_tasks/get_lists")
    target = CONFIG.native_list_name.lower()
    for lst in result.get("lists", []):
        if lst.get("name", "").lower() == target:
            return lst["id"]
    pytest.skip(
        f"Native list '{CONFIG.native_list_name}' not found in HA — "
        f"create it via Settings → Integrations → Home Tasks"
    )


@pytest_asyncio.fixture
async def native_list_id_secondary(ws_client: HAWebSocketClient) -> str:
    """Resolve the secondary native list name (for move_task tests)."""
    if not CONFIG.native_list_name_secondary:
        pytest.skip("HT_NATIVE_LIST_NAME_2 not set")
    result = await ws_client.send_command("home_tasks/get_lists")
    target = CONFIG.native_list_name_secondary.lower()
    for lst in result.get("lists", []):
        if lst.get("name", "").lower() == target:
            return lst["id"]
    pytest.skip(
        f"Secondary native list '{CONFIG.native_list_name_secondary}' not found"
    )


@pytest_asyncio.fixture
async def clean_native_list(
    ws_client: HAWebSocketClient, native_list_id: str
) -> AsyncIterator[str]:
    """Wipe the native test list before each test.  Returns the list_id.

    Safety: aborts if the list contains more than CONFIG.max_existing_items
    so we never accidentally delete a real list's data.
    """
    await _wipe_native_list(ws_client, native_list_id)
    yield native_list_id


async def _wipe_native_list(ws_client: HAWebSocketClient, list_id: str) -> None:
    """Delete every task in the given native list (with safety check)."""
    result = await ws_client.send_command("home_tasks/get_tasks", list_id=list_id)
    tasks = result.get("tasks", [])
    if len(tasks) > CONFIG.max_existing_items:
        raise RuntimeError(
            f"Refusing to wipe list {list_id}: contains {len(tasks)} tasks "
            f"(> max_existing_items={CONFIG.max_existing_items}). "
            f"Did you point HT_NATIVE_LIST_NAME at a non-test list?"
        )
    for task in tasks:
        await ws_client.send_command(
            "home_tasks/delete_task", list_id=list_id, task_id=task["id"]
        )


@pytest_asyncio.fixture
async def clean_external_list_factory(ws_client: HAWebSocketClient):
    """Returns a function that wipes a given external entity_id's tasks.

    Used by per-provider tests as: `await clean_external_list_factory(entity_id)`.
    """
    async def _wipe(entity_id: str) -> None:
        result = await ws_client.send_command(
            "home_tasks/get_external_tasks", entity_id=entity_id
        )
        tasks = result.get("tasks", [])
        if len(tasks) > CONFIG.max_existing_items:
            raise RuntimeError(
                f"Refusing to wipe {entity_id}: {len(tasks)} tasks > max"
            )
        for task in tasks:
            try:
                # delete via todo.remove_item service (works for all generic providers)
                await ws_client.call_service(
                    "todo", "remove_item",
                    {"entity_id": entity_id, "item": task["id"]},
                )
            except Exception as err:  # noqa: BLE001
                print(f"[live cleanup] failed to remove {task.get('id')} from {entity_id}: {err}")
    return _wipe
