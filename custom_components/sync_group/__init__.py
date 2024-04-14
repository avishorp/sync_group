"""Platform allowing several lights to be grouped into one light."""
from homeassistant.const import Platform

DOMAIN = "sync_group"
PLATFORMS = [Platform.LIGHT]
