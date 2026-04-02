"""Binary sensor platform for Home Tasks integration."""

from datetime import date
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensor entities from a config entry."""
    if entry.data.get("type") == "external":
        return  # External entries do not get binary sensors
    store = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HomeTasksOverdueBinarySensor(entry, store)])


class HomeTasksOverdueBinarySensor(BinarySensorEntity):
    """Binary sensor that is ON when the list has overdue tasks."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:clock-alert"

    def __init__(self, entry: ConfigEntry, store) -> None:
        """Initialize the binary sensor."""
        self._store = store
        list_name = entry.data.get("name", entry.title)
        self._attr_name = f"{list_name} Overdue"
        self._attr_unique_id = f"{entry.entry_id}_overdue"

    @property
    def is_on(self) -> bool:
        """Return true if there are overdue tasks."""
        today = date.today().isoformat()
        return any(
            not t.get("completed") and t.get("due_date") and t["due_date"] < today
            for t in self._store.tasks
        )

    @property
    def extra_state_attributes(self) -> dict:
        """Return overdue task details."""
        today = date.today().isoformat()
        overdue = [
            t for t in self._store.tasks
            if not t.get("completed") and t.get("due_date") and t["due_date"] < today
        ]
        return {
            "overdue_tasks": [
                {"title": t["title"], "due_date": t["due_date"], "assigned_person": t.get("assigned_person")}
                for t in overdue
            ],
            "overdue_count": len(overdue),
        }

    async def async_added_to_hass(self) -> None:
        """Register store listener."""
        self.async_on_remove(
            self._store.async_add_listener(self._handle_store_update)
        )

    @callback
    def _handle_store_update(self) -> None:
        """React to store data changes."""
        self.async_write_ha_state()
