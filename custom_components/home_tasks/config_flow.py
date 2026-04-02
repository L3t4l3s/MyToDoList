"""Config flow for Home Tasks integration."""

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, MAX_LIST_NAME_LENGTH


class HomeTasksConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Home Tasks."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Let the user choose between creating a native list or linking an external one."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["native", "external"],
        )

    async def async_step_native(self, user_input=None):
        """Handle creating a new native task list."""
        errors = {}

        if user_input is not None:
            name = user_input["name"].strip()
            if not name:
                errors["name"] = "empty_name"
            elif len(name) > MAX_LIST_NAME_LENGTH:
                errors["name"] = "name_too_long"
            else:
                for entry in self._async_current_entries():
                    if entry.data.get("name", "").lower() == name.lower():
                        errors["name"] = "duplicate_name"
                        break

            if not errors:
                return self.async_create_entry(
                    title=name,
                    data={"name": name},
                )

        return self.async_show_form(
            step_id="native",
            data_schema=vol.Schema(
                {vol.Required("name"): str}
            ),
            errors=errors,
        )

    async def async_step_external(self, user_input=None):
        """Handle linking an external todo entity."""
        errors = {}

        if user_input is not None:
            entity_id = user_input.get("entity_id", "").strip()
            if not entity_id:
                errors["entity_id"] = "empty_entity"
            else:
                # Check not already linked
                for entry in self._async_current_entries():
                    if entry.data.get("entity_id") == entity_id:
                        errors["entity_id"] = "already_linked"
                        break

            if not errors:
                # Derive a friendly name from the entity
                entity_reg = er.async_get(self.hass)
                entity_entry = entity_reg.async_get(entity_id)
                name = (
                    entity_entry.name
                    or entity_entry.original_name
                    or entity_id
                ) if entity_entry else entity_id

                return self.async_create_entry(
                    title=f"{name} (External)",
                    data={
                        "type": "external",
                        "entity_id": entity_id,
                        "name": name,
                    },
                )

        # Build list of available external todo entities
        entity_reg = er.async_get(self.hass)
        our_entries = {e.entry_id for e in self._async_current_entries()}
        already_linked = {
            e.data.get("entity_id")
            for e in self._async_current_entries()
            if e.data.get("type") == "external"
        }

        options = {}
        for entity_entry in entity_reg.entities.values():
            if entity_entry.domain != "todo":
                continue
            if entity_entry.config_entry_id in our_entries:
                continue
            if entity_entry.entity_id in already_linked:
                continue
            label = (
                entity_entry.name
                or entity_entry.original_name
                or entity_entry.entity_id
            )
            options[entity_entry.entity_id] = label

        if not options:
            return self.async_abort(reason="no_external_entities")

        return self.async_show_form(
            step_id="external",
            data_schema=vol.Schema(
                {vol.Required("entity_id"): vol.In(options)}
            ),
            errors=errors,
        )
