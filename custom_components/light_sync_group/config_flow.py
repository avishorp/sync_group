"""Config flow for Light Sync Group integration."""
from collections.abc import Mapping
from typing import Any, cast

import voluptuous as vol

from homeassistant.core import callback, HomeAssistant
from homeassistant.components import light
from homeassistant.const import CONF_ENTITIES
from homeassistant.helpers import entity_registry as er, selector
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaConfigFlowHandler,
    SchemaFlowFormStep,
)
from homeassistant.components.group.const import CONF_HIDE_MEMBERS

from .const import DOMAIN


OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ENTITIES): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=light.DOMAIN, multiple=True),
        ),
        vol.Required(CONF_HIDE_MEMBERS, default=False): selector.BooleanSelector(),
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
            vol.Required("name"): selector.TextSelector(),
            vol.Required(CONF_ENTITIES): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=light.DOMAIN, multiple=True),
            ),
            vol.Required(CONF_HIDE_MEMBERS, default=False): selector.BooleanSelector(),            
    }
)

CONFIG_FLOW = {
    "user": SchemaFlowFormStep(CONFIG_SCHEMA),
}

OPTIONS_FLOW = {
    "init": SchemaFlowFormStep(OPTIONS_SCHEMA),
}

class ConfigFlowHandler(SchemaConfigFlowHandler, domain=DOMAIN):
    """Handle a config or options flow for Integration."""

    config_flow = CONFIG_FLOW
    options_flow = OPTIONS_FLOW

    def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
        """Return config entry title."""
        return cast(str, options["name"])

    @callback
    def async_config_flow_finished(self, options: Mapping[str, Any]) -> None:
        """Hide the group members if requested."""
        if options[CONF_HIDE_MEMBERS]:
            _async_hide_members(
                self.hass, options[CONF_ENTITIES], er.RegistryEntryHider.INTEGRATION
            )

    @callback
    @staticmethod
    def async_options_flow_finished(
        hass: HomeAssistant, options: Mapping[str, Any]
    ) -> None:
        """Hide or unhide the group members as requested."""
        hidden_by = (
            er.RegistryEntryHider.INTEGRATION if options[CONF_HIDE_MEMBERS] else None
        )
        _async_hide_members(hass, options[CONF_ENTITIES], hidden_by)

def _async_hide_members(
    hass: HomeAssistant, members: list[str], hidden_by: er.RegistryEntryHider | None
) -> None:
    """Hide or unhide group members."""
    registry = er.async_get(hass)
    for member in members:
        if not (entity_id := er.async_resolve_entity_id(registry, member)):
            continue
        if entity_id not in registry.entities:
            continue
        registry.async_update_entity(entity_id, hidden_by=hidden_by)
