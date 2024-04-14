from typing import Mapping, Any, cast
import voluptuous as vol

from homeassistant.components import light
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaConfigFlowHandler,
    SchemaFlowFormStep,
)
from homeassistant.helpers import selector
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaConfigFlowHandler,
    SchemaFlowFormStep,
)
from homeassistant.const import CONF_ENTITIES

from .const import DOMAIN


OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ENTITIES): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=light.DOMAIN, multiple=True),
        ),
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
            vol.Required("name"): selector.TextSelector(),
            vol.Required(CONF_ENTITIES): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=light.DOMAIN, multiple=True),
            ),
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
