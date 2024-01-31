from __future__ import annotations

import datetime
import logging

_LOGGER = logging.getLogger(__name__)

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from uhppoted import uhppote

from .const import DOMAIN
from .const import CONF_BIND_ADDR
from .const import CONF_BROADCAST_ADDR
from .const import CONF_LISTEN_ADDR
from .const import CONF_DEBUG

from .const import ATTR_CONTROLLER_ADDRESS
from .const import ATTR_NETMASK
from .const import ATTR_GATEWAY
from .const import ATTR_FIRMWARE

from .config import configure_doors
from .door import DoorUnlock


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    options = entry.options

    bind = options[CONF_BIND_ADDR]
    broadcast = options[CONF_BROADCAST_ADDR]
    listen = options[CONF_LISTEN_ADDR]
    debug = options[CONF_DEBUG]

    u = uhppote.Uhppote(bind, broadcast, listen, debug)
    entities = []

    def g(unique_id, controller, serial_no, door, door_no):
        entities.extend([
            DoorUnlock(u, unique_id, controller, serial_no, door, door_no),
        ])

    configure_doors(options, g)
    async_add_entities(entities, update_before_add=True)
