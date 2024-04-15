"""Light Sync Group integration implementations."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant.components import light
from homeassistant.components.binary_sensor import PLATFORM_SCHEMA
from homeassistant.components.group.light import LightGroup
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_ENTITIES,
    CONF_NAME,
    CONF_UNIQUE_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant, callback, Event
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    EventStateChangedData,
    async_track_state_change_event,
)
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)


DEFAULT_NAME = "Light Sync Group"
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
        vol.Required(CONF_ENTITIES): cv.entities_domain(light.DOMAIN),
    }
)

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Light Sync Group."""
    async_add_entities(
        [
            LightSyncGroup(
                hass,
                config.get(CONF_UNIQUE_ID),
                config[CONF_NAME],
                config[CONF_ENTITIES],
            )
        ]
    )

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize Light Sync Group config entry."""
    registry = er.async_get(hass)
    entities = er.async_validate_entity_ids(
        registry, config_entry.options[CONF_ENTITIES]
    )

    async_add_entities(
        [LightSyncGroup(hass, config_entry.entry_id, config_entry.title, entities)]
    )


class LightSyncGroup(LightGroup):
    """Representation of a light sync group."""

    def __init__(
        self,
        hass: HomeAssistant,
        unique_id: str | None,
        name: str,
        entity_ids: list[str],
    ) -> None:
        """Initialize a light sync group."""
        super().__init__(unique_id, name, entity_ids, True)

        # Install a state event listener to track changes
        unsub = async_track_state_change_event(
            hass, entity_ids, self._watched_entity_change
        )
        self.async_on_remove(unsub)

        self._target_sync_state: str | None = None


    @callback
    async def _watched_entity_change(
        self, event: Event[EventStateChangedData]
    ) -> None:
        nst = event.data["new_state"]
        if nst is not None:
            state = nst.state
            if state in (STATE_ON, STATE_OFF) and state != self._target_sync_state:
                self._target_sync_state = state

                # Call the appropriate service for all the other lights in the group
                data = {
                    ATTR_ENTITY_ID: [
                        entity for entity in self._entity_ids if entity != nst.entity_id
                    ]
                }

                await self.hass.services.async_call(
                    light.DOMAIN,
                    SERVICE_TURN_ON if state == STATE_ON else SERVICE_TURN_OFF,
                    data,
                    blocking=True,
                    context=self._context,
                )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Forward the turn_on command to all lights in the light group."""
        self._target_sync_state = STATE_ON
        await super().async_turn_on(**kwargs)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Forward the turn_off command to all lights in the light group."""
        self._target_sync_state = STATE_ON
        await super().async_turn_off(**kwargs)
