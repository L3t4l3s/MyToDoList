"""Sensor platform for My ToDo List integration."""

from datetime import date
import logging

from homeassistant.components.sensor import SensorEntity, SensorStateClass
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
    """Set up sensor entities from a config entry."""
    store = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MyToDoListOpenTasksSensor(entry, store)])


class MyToDoListOpenTasksSensor(SensorEntity):
    """Sensor that reports the number of open tasks in a list."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "Aufgaben"
    _attr_icon = "mdi:clipboard-list"

    def __init__(self, entry: ConfigEntry, store) -> None:
        """Initialize the sensor."""
        self._store = store
        list_name = entry.data.get("name", entry.title)
        self._attr_name = f"{list_name} Offene Aufgaben"
        self._attr_unique_id = f"{entry.entry_id}_open_tasks"

    @property
    def native_value(self) -> int:
        """Return number of open tasks."""
        return len([t for t in self._store.tasks if not t.get("completed")])

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        today = date.today().isoformat()
        open_tasks = [t for t in self._store.tasks if not t.get("completed")]
        overdue = [t for t in open_tasks if t.get("due_date") and t["due_date"] < today]
        return {
            "open_task_titles": [t["title"] for t in open_tasks],
            "overdue_count": len(overdue),
            "total_tasks": len(self._store.tasks),
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
