"""Shared pytest fixtures for home_tasks integration tests."""
from __future__ import annotations

import asyncio
import pathlib
import sys

# ---------------------------------------------------------------------------
# Import `custom_components` as a namespace package from the project root
# BEFORE anything else can import it from pytest-hacc's testing_config
# (which has a regular-package __init__.py that would shadow our directory).
# _async_mount_config_dir adds testing_config to sys.path and imports
# custom_components; by importing it here first (at collection time, before
# any fixtures run), we ensure __path__ points at the project root.
# ---------------------------------------------------------------------------
_PROJECT_ROOT = str(pathlib.Path(__file__).parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
import custom_components as _cc  # noqa: E402 — must come before any HA fixture
# Ensure our project's custom_components directory is in __path__
_CC_DIR = str(pathlib.Path(_PROJECT_ROOT) / "custom_components")
if _CC_DIR not in _cc.__path__:
    _cc.__path__.insert(0, _CC_DIR)

import pytest
from unittest.mock import patch

# ---------------------------------------------------------------------------
# Windows fix: aiohttp's default resolver (aiodns / AsyncResolver) requires
# SelectorEventLoop or winloop, but pytest-hacc forces ProactorEventLoop on
# Windows. Force aiohttp to use ThreadedResolver (plain socket) instead so
# that hass_ws_client's aiohttp TestClient can connect on Windows.
# ---------------------------------------------------------------------------
if sys.platform == "win32":
    import aiohttp.resolver as _aiohttp_resolver
    import aiohttp.connector as _aiohttp_connector
    from aiohttp.resolver import ThreadedResolver as _ThreadedResolver
    _aiohttp_resolver.DefaultResolver = _ThreadedResolver
    _aiohttp_connector.DefaultResolver = _ThreadedResolver

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

DOMAIN = "home_tasks"

# ---------------------------------------------------------------------------
# Frontend mock: the HA `frontend` component's async_setup tries to import
# hass_frontend (the compiled bundle, not installed in tests) and register
# hundreds of static files. Mock the entire async_setup to avoid this while
# still initialising the data keys that add_extra_js_url expects.
# ---------------------------------------------------------------------------
import homeassistant.components.frontend as _frontend_module


async def _mock_frontend_async_setup(hass, config):
    """Lightweight frontend setup that skips hass_frontend entirely."""
    from homeassistant.components.frontend import (
        DATA_EXTRA_JS_URL_ES5,
        DATA_EXTRA_MODULE_URL,
    )
    hass.data.setdefault(DATA_EXTRA_JS_URL_ES5, set())
    hass.data.setdefault(DATA_EXTRA_MODULE_URL, set())
    return True


_frontend_module.async_setup = _mock_frontend_async_setup

# ---------------------------------------------------------------------------
# Windows fix: asyncio event loops need socket.socketpair() internally, but
# pytest-hacc calls pytest_socket.disable_socket() in pytest_runtest_setup,
# which blocks ALL AF_INET socket creation — breaking event loop setup on Windows.
#
# Fix: at conftest import time (before any sockets are guarded), save a reference
# to the real socket.socket class, then replace socket.socketpair with a version
# that uses that saved reference so it still works after disable_socket() patches
# socket.socket with a GuardedSocket.
# ---------------------------------------------------------------------------
if sys.platform == "win32":
    import socket as _socket_module

    # Save real socket.socket and socket.socketpair BEFORE pytest-socket patches them.
    # pytest-hacc disables sockets in pytest_runtest_setup (runs before fixtures), but
    # asyncio event loops need socketpair() internally on Windows.
    _real_socket_class = _socket_module.socket
    _real_socketpair = _socket_module.socketpair

    def _unguarded_socketpair(
        family: int = _socket_module.AF_INET,
        type: int = _socket_module.SOCK_STREAM,
        proto: int = 0,
    ):
        """socket.socketpair that temporarily restores real socket.socket."""
        guarded = _socket_module.socket
        _socket_module.socket = _real_socket_class
        try:
            return _real_socketpair(family, type, proto)
        finally:
            _socket_module.socket = guarded

    _socket_module.socketpair = _unguarded_socketpair


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading custom integrations defined in this repo."""
    return


if sys.platform == "win32":
    @pytest.fixture
    def expected_lingering_tasks() -> bool:
        """Windows ProactorEventLoop IOCP accept tasks from the HTTP server
        don't get cancelled cleanly when hass.async_stop() is called.
        Suppress the pytest-hacc fail-on-lingering-tasks check on Windows."""
        return True


@pytest.fixture(autouse=True)
def patch_add_extra_js_url():
    """Patch add_extra_js_url to prevent frontend data key errors in tests.

    Patch the name both at the source (for first import, where `from X import Y`
    binds the name into the module) and in the module namespace (for subsequent
    tests where the module is already cached in sys.modules).
    """
    import sys
    ht_mod = sys.modules.get("custom_components.home_tasks")
    if ht_mod is not None:
        # Module already loaded — patch its local reference directly
        with patch.object(ht_mod, "add_extra_js_url"):
            yield
    else:
        # Module not yet loaded — patch the source so the first import picks up the mock
        with patch("homeassistant.components.frontend.add_extra_js_url"):
            yield


@pytest.fixture
async def mock_config_entry(hass: HomeAssistant, patch_add_extra_js_url) -> MockConfigEntry:
    """Create and fully load a native Home Tasks config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"name": "Test List"},
        title="Test List",
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


@pytest.fixture
async def store(hass: HomeAssistant, mock_config_entry: MockConfigEntry):
    """Return the HomeTasksStore for the test config entry."""
    from custom_components.home_tasks.store import HomeTasksStore
    s = hass.data[DOMAIN][mock_config_entry.entry_id]
    assert isinstance(s, HomeTasksStore)
    return s
