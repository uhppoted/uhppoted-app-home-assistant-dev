import logging

from homeassistant import core
from homeassistant import config_entries

from .const import DOMAIN
from .const import CONF_BIND_ADDR
from .const import CONF_BROADCAST_ADDR
from .const import CONF_LISTEN_ADDR

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: core.HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, "sensor"))

    return True


async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    defaults = {
        CONF_BIND_ADDR: '0.0.0.0',
        CONF_BROADCAST_ADDR: '255.255.255.255:60000',
        CONF_LISTEN_ADDR: '0.0.0.0:60001',
    }

    if 'sensor' in config:
        for c in config['sensor']:
            if 'platform' in c and c['platform'] == 'uhppoted':
                for v in [CONF_BIND_ADDR, CONF_BROADCAST_ADDR, CONF_LISTEN_ADDR]:
                    if v in c:
                        defaults[v] = c[v]

    _LOGGER.info(f'default bind address {defaults[CONF_BIND_ADDR]}')
    _LOGGER.info(f'default broadcast address {defaults[CONF_BROADCAST_ADDR]}')
    _LOGGER.info(f'default listen address {defaults[CONF_LISTEN_ADDR]}')

    hass.data.setdefault(DOMAIN, defaults)

    return True
