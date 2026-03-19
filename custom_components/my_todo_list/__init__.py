"""The My ToDo List integration."""

import logging

from homeassistant.components.frontend import add_extra_js_url
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
    """Register websocket commands and frontend card (once)."""
    if hass.data.get(DATA_SETUP_DONE):
        return
    hass.data[DATA_SETUP_DONE] = True

    async_register_websocket_commands(hass)

    try:
        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(
                    CARD_URL,
                    hass.config.path(
                        f"custom_components/{DOMAIN}/www/my-todo-list-card.js"
                    ),
                    cache_headers=False,
                )
            ]
        )
    except RuntimeError:
        # Route already registered from a previous setup
        pass

    add_extra_js_url(hass, CARD_URL)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up My ToDo List from a config entry."""
    # Ensure card is registered (in case async_setup was not called)
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
