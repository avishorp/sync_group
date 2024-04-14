"""Light Sync Group integration implementations."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant.components import light
from homeassistant.components.binary_sensor import PLATFORM_SCHEMA
from homeassistant.components.group.light import FORWARDED_ATTRIBUTES, LightGroup
from homeassistant.components.light import ATTR_TRANSITION, ColorMode
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
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    EventStateChangedData,
    async_track_state_change_event,
)
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType, EventType

_LOGGER = logging.getLogger(__name__)


DEFAULT_NAME = "Sync Group"
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

    _attr_available = False
    _attr_icon = "mdi:lightbulb-group"
    _attr_max_color_temp_kelvin = 6500
    _attr_min_color_temp_kelvin = 2000
    _attr_should_poll = False

    def __init__(
        self,
        hass: HomeAssistant,
        unique_id: str | None,
        name: str,
        entity_ids: list[str],
    ) -> None:
        """Initialize a light sync group."""
        self._entity_ids = entity_ids

        self._attr_name = name
        self._attr_extra_state_attributes = {ATTR_ENTITY_ID: entity_ids}
        self._attr_unique_id = unique_id
        self.mode = all   # Sync group always works in "all" mode

        self._attr_color_mode = ColorMode.UNKNOWN
        self._attr_supported_color_modes = {ColorMode.ONOFF}

        # Only install the state listener if synchronization is enabled
        unsub = async_track_state_change_event(
            hass, entity_ids, self._watched_entity_change
        )
        self.async_on_remove(unsub)

        self._target_sync_state: str | None = None

    @callback
    def async_update_group_state(self) -> None:
        """Query all members and determine the light group state."""
        states = [
            state
            for entity_id in self._entity_ids
            if (state := self.hass.states.get(entity_id)) is not None
        ]
        on_states = [state for state in states if state.state == STATE_ON]

        valid_state = all(
            state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE) for state in states
        )

        if not valid_state:
            # Set as unknown if any / all member is unknown or unavailable
            self._attr_is_on = None
        else:
            # Set as ON if any / all member is ON
            self._attr_is_on = all(state.state == STATE_ON for state in states)

        self._attr_available = any(state.state != STATE_UNAVAILABLE for state in states)
        # self._attr_brightness = reduce_attribute(on_states, ATTR_BRIGHTNESS)

        # self._attr_hs_color = reduce_attribute(
        #     on_states, ATTR_HS_COLOR, reduce=mean_tuple
        # )
        # self._attr_rgb_color = reduce_attribute(
        #     on_states, ATTR_RGB_COLOR, reduce=mean_tuple
        # )
        # self._attr_rgbw_color = reduce_attribute(
        #     on_states, ATTR_RGBW_COLOR, reduce=mean_tuple
        # )
        # self._attr_rgbww_color = reduce_attribute(
        #     on_states, ATTR_RGBWW_COLOR, reduce=mean_tuple
        # )
        # self._attr_xy_color = reduce_attribute(
        #     on_states, ATTR_XY_COLOR, reduce=mean_tuple
        # )

        # self._attr_color_temp_kelvin = reduce_attribute(
        #     on_states, ATTR_COLOR_TEMP_KELVIN
        # )
        # self._attr_min_color_temp_kelvin = reduce_attribute(
        #     states, ATTR_MIN_COLOR_TEMP_KELVIN, default=2000, reduce=min
        # )
        # self._attr_max_color_temp_kelvin = reduce_attribute(
        #     states, ATTR_MAX_COLOR_TEMP_KELVIN, default=6500, reduce=max
        # )

        # self._attr_effect_list = None
        # all_effect_lists = list(find_state_attributes(states, ATTR_EFFECT_LIST))
        # if all_effect_lists:
        #     # Merge all effects from all effect_lists with a union merge.
        #     self._attr_effect_list = list(set().union(*all_effect_lists))
        #     self._attr_effect_list.sort()
        #     if "None" in self._attr_effect_list:
        #         self._attr_effect_list.remove("None")
        #         self._attr_effect_list.insert(0, "None")

        # self._attr_effect = None
        # all_effects = list(find_state_attributes(on_states, ATTR_EFFECT))
        # if all_effects:
        #     # Report the most common effect.
        #     effects_count = Counter(itertools.chain(all_effects))
        #     self._attr_effect = effects_count.most_common(1)[0][0]

        # supported_color_modes = {ColorMode.ONOFF}
        # all_supported_color_modes = list(
        #     find_state_attributes(states, ATTR_SUPPORTED_COLOR_MODES)
        # )
        # if all_supported_color_modes:
        #     # Merge all color modes.
        #     supported_color_modes = filter_supported_color_modes(
        #         cast(set[ColorMode], set().union(*all_supported_color_modes))
        #     )
        # self._attr_supported_color_modes = supported_color_modes

        # self._attr_color_mode = ColorMode.UNKNOWN
        # all_color_modes = list(find_state_attributes(on_states, ATTR_COLOR_MODE))
        # if all_color_modes:
        #     # Report the most common color mode, select brightness and onoff last
        #     color_mode_count = Counter(itertools.chain(all_color_modes))
        #     if ColorMode.ONOFF in color_mode_count:
        #         if ColorMode.ONOFF in supported_color_modes:
        #             color_mode_count[ColorMode.ONOFF] = -1
        #         else:
        #             color_mode_count.pop(ColorMode.ONOFF)
        #     if ColorMode.BRIGHTNESS in color_mode_count:
        #         if ColorMode.BRIGHTNESS in supported_color_modes:
        #             color_mode_count[ColorMode.BRIGHTNESS] = 0
        #         else:
        #             color_mode_count.pop(ColorMode.BRIGHTNESS)
        #     if color_mode_count:
        #         self._attr_color_mode = color_mode_count.most_common(1)[0][0]
        #     else:
        #         self._attr_color_mode = next(iter(supported_color_modes))

        # self._attr_supported_features = LightEntityFeature(0)
        # for support in find_state_attributes(states, ATTR_SUPPORTED_FEATURES):
        #     # Merge supported features by emulating support for every feature
        #     # we find.
        #     self._attr_supported_features |= support
        # # Bitwise-and the supported features with the GroupedLight's features
        # # so that we don't break in the future when a new feature is added.
        # self._attr_supported_features &= SUPPORT_GROUP_LIGHT

    @callback
    async def _watched_entity_change(
        self, event: EventType[EventStateChangedData]
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
        data = {
            key: value for key, value in kwargs.items() if key in FORWARDED_ATTRIBUTES
        }
        data[ATTR_ENTITY_ID] = self._entity_ids
        self._target_sync_state = STATE_ON

        _LOGGER.debug("Forwarded turn_on command: %s", data)

        await self.hass.services.async_call(
            light.DOMAIN,
            SERVICE_TURN_ON,
            data,
            blocking=True,
            context=self._context,
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Forward the turn_off command to all lights in the light group."""
        data = {ATTR_ENTITY_ID: self._entity_ids}
        self._target_sync_state = STATE_OFF

        if ATTR_TRANSITION in kwargs:
            data[ATTR_TRANSITION] = kwargs[ATTR_TRANSITION]

        await self.hass.services.async_call(
            light.DOMAIN,
            SERVICE_TURN_OFF,
            data,
            blocking=True,
            context=self._context,
        )
