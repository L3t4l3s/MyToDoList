"""The My ToDo List integration."""

import logging

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .store import MyToDoListStore
from .websocket_api import async_register_websocket_commands

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["todo"]
CARD_URL = "/my_todo_list/my-todo-list-card.js"
DATA_SETUP_DONE = f"{DOMAIN}_setup_done"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the My ToDo List component."""
    hass.data.setdefault(DOMAIN, {})
    await _async_register_card(hass)
    return True


async def _async_register_card(hass: HomeAssistant) -> None:
    """Register websocket commands and serve static files (once)."""
    if hass.data.get(DATA_SETUP_DONE):
        return
    hass.data[DATA_SETUP_DONE] = True

    async_register_websocket_commands(hass)

    comp_path = hass.config.path(f"custom_components/{DOMAIN}")
    static_paths = [
        StaticPathConfig(
            CARD_URL,
            f"{comp_path}/www/my-todo-list-card.js",
            cache_headers=False,
        ),
        StaticPathConfig(
            f"/brands/{DOMAIN}/icon.png",
            f"{comp_path}/icon.png",
            cache_headers=True,
        ),
        StaticPathConfig(
            f"/brands/{DOMAIN}/icon@2x.png",
            f"{comp_path}/icon@2x.png",
            cache_headers=True,
        ),
        StaticPathConfig(
            f"/brands/{DOMAIN}/logo.png",
            f"{comp_path}/icon.png",
            cache_headers=True,
        ),
    ]
    try:
        await hass.http.async_register_static_paths(static_paths)
    except RuntimeError:
        pass

    # NOTE: The card JS must be added as a Lovelace resource manually:
    # URL: /my_todo_list/my-todo-list-card.js  Type: JavaScript Module
    _LOGGER.info(
        "My ToDo List card served at %s - ensure it is added as a "
        "Lovelace resource (JavaScript Module)",
        CARD_URL,
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up My ToDo List from a config entry."""
    await _async_register_card(hass)

    store = MyToDoListStore(hass, entry.entry_id)
    await store.async_load()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = store

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
