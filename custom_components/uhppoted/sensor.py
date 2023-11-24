from __future__ import annotations

import datetime
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.typing import DiscoveryInfoType
from homeassistant.components.sensor import SensorEntity

from uhppoted import uhppote

_LOGGER = logging.getLogger(__name__)

# Configuration constants
from .const import DOMAIN
from .const import CONF_BIND_ADDR
from .const import CONF_BROADCAST_ADDR
from .const import CONF_LISTEN_ADDR
from .const import CONF_DEBUG
from .const import CONF_CONTROLLER_ID
from .const import CONF_CONTROLLER_NAME
from .const import CONF_CONTROLLER_ADDR
from .const import CONF_DOOR_ID
from .const import CONF_DOOR_NAME

# Attribute constants
from .const import ATTR_ADDRESS
from .const import ATTR_NETMASK
from .const import ATTR_GATEWAY
from .const import ATTR_FIRMWARE


async def async_setup_platform(hass: HomeAssistantType,
                               config: ConfigType,
                               async_add_entities: Callable,
                               discovery_info: DiscoveryInfoType | None = None) -> None:
    async_add_entities([], update_before_add=True)


async def async_setup_entry(hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry, async_add_entities):
    config = hass.data[DOMAIN][config_entry.entry_id]

    id = config[CONF_CONTROLLER_ID]
    name = f'{id}'
    address = ''
    bind = '0.0.0.0'
    broadcast = '255.255.255.255'
    listen = '0.0.0.0:60001'
    debug = False

    door = {'id': 1, 'name': '1'}

    if CONF_CONTROLLER_NAME in config and not config[CONF_CONTROLLER_NAME].strip() == '':
        name = config[CONF_CONTROLLER_NAME].strip()

    if CONF_CONTROLLER_ADDR in config:
        address = config[CONF_CONTROLLER_ADDR]

    if CONF_BIND_ADDR in config:
        bind = config[CONF_BIND_ADDR]

    if CONF_BROADCAST_ADDR in config:
        broadcast = config[CONF_BROADCAST_ADDR]

    if CONF_LISTEN_ADDR in config:
        listen = config[CONF_LISTEN_ADDR]

    if CONF_DEBUG in config:
        debug = config[CONF_DEBUG]

    if CONF_DOOR_ID in config:
        door['id'] = config[CONF_DOOR_ID]
        door['name'] = f"{door['id']}"

    if CONF_DOOR_NAME in config:
        door['name'] = config[CONF_DOOR_NAME]

    u = uhppote.Uhppote(bind, broadcast, listen, debug)

    controller = [
        ControllerID(u, id, name),
        ControllerAddress(u, id, name, address),
        ControllerDateTime(u, id, name),
        ControllerDoor(u, id, name, door['id'], door['name']),
    ]

    async_add_entities(controller, update_before_add=True)


class ControllerID(SensorEntity):
    _attr_device_class = None
    _attr_last_reset = None
    _attr_native_unit_of_measurement = None
    _attr_state_class = None

    def __init__(self, u, id, name):
        super().__init__()

        _LOGGER.debug(f'controller ID:{id}')

        self.uhppote = u
        self.id = id
        self._name = f'{name}.ID'
        self._icon = 'mdi:identifier'
        self._translation_key = 'controller_id'
        self._state = id
        self._attributes: Dict[str, Any] = {
            ATTR_ADDRESS: '',
            ATTR_NETMASK: '',
            ATTR_GATEWAY: '',
            ATTR_FIRMWARE: '',
        }
        self._available = True

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_id(self) -> str:
        return f'{self.id}.ID'

    @property
    def icon(self) -> str:
        return f'{self._icon}'

    @property
    def has_entity_name(self) -> bool:
        return True

    @property
    def translation_key(self) -> str:
        return self._translation_key

    @property
    def available(self) -> bool:
        return self._available

    @property
    def state(self) -> Optional[str]:
        if self._state != None:
            return f'{self._state}'

        return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        return self._attributes

    async def async_update(self):
        _LOGGER.info(f'controller:{self.id}  update info')
        try:
            controller = self.id
            response = self.uhppote.get_controller(controller)

            if response.controller == self.id:
                self._state = response.controller
                self._available = True
                self._attributes[ATTR_ADDRESS] = f'{response.ip_address}'
                self._attributes[ATTR_NETMASK] = f'{response.subnet_mask}'
                self._attributes[ATTR_GATEWAY] = f'{response.gateway}'
                self._attributes[ATTR_FIRMWARE] = f'{response.version} {response.date:%Y-%m-%d}'

        except (Exception):
            self._available = False
            _LOGGER.exception(f'error retrieving controller {self.id} information')


class ControllerAddress(SensorEntity):
    _attr_name = "address"
    _attr_device_class = None
    _attr_last_reset = None
    _attr_native_unit_of_measurement = None
    _attr_state_class = None

    def __init__(self, u, id, name, address):
        super().__init__()

        _LOGGER.debug(f'controller address:{id}  address:{address}')

        self.uhppote = u
        self.id = id
        self._name = f'{name}.address'
        self._icon = 'mdi:ip-network'
        self._state = address
        self._available = False if address == '' else True

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_id(self) -> str:
        return f'{self.id}.address'

    @property
    def icon(self) -> str:
        return f'{self._icon}'

    @property
    def available(self) -> bool:
        return self._available

    @property
    def state(self) -> Optional[str]:
        if self._state != None:
            return f'{self._state}'

        return None

    async def async_update(self):
        _LOGGER.debug(f'controller:{self.id}  update address')
        try:
            controller = self.id
            response = self.uhppote.get_controller(controller)

            if response.controller == self.id:
                self._state = response.ip_address
                self._available = True

        except (Exception):
            self._available = False
            _LOGGER.exception(f'error retrieving controller {self.id} address')


class ControllerDateTime(SensorEntity):
    _attr_name = "datetime"
    _attr_device_class = None
    _attr_last_reset = None
    _attr_native_unit_of_measurement = None
    _attr_state_class = None

    def __init__(self, u, id, name):
        super().__init__()

        _LOGGER.debug(f'controller datetime:{id}')

        self.uhppote = u
        self.id = id
        self._name = f'{name}.date/time'
        self._icon = 'mdi:calendar-clock-outline'
        self._state = None
        self._available = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_id(self) -> str:
        return f'{self.id}.datetime'

    @property
    def icon(self) -> str:
        return f'{self._icon}'

    @property
    def available(self) -> bool:
        return self._available

    @property
    def state(self) -> Optional[str]:
        if self._state != None:
            return f'{self._state:%Y-%m-%d %H:%M:%S}'

        return None

    async def async_update(self):
        _LOGGER.debug(f'controller:{self.id}  update datetime')
        try:
            controller = self.id
            response = self.uhppote.get_time(controller)

            if response.controller == self.id:
                self._state = response.datetime
                self._available = True

        except (Exception):
            self._available = False
            _LOGGER.exception(f'error retrieving controller {self.id} date/time')


class ControllerDoor(SensorEntity):
    _attr_name = "door"
    _attr_device_class = None
    _attr_last_reset = None
    _attr_native_unit_of_measurement = None
    _attr_state_class = None

    def __init__(self, u, id, name, door_id, door):
        super().__init__()

        _LOGGER.debug(f'controller {id}: door:{door_id}')

        self.uhppote = u
        self.id = id
        self.door_id = door_id
        self.door = door

        self._name = f'{name}.door.{door}'
        self._icon = 'mdi:door'
        self._locked = None
        self._open = None
        self._available = False

        match door_id:
            case 1:
                self._mask = 0x01
            case 2:
                self._mask = 0x02
            case 3:
                self._mask = 0x04
            case 4:
                self._mask = 0x08
            case _:
                self._mask = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_id(self) -> str:
        return f'{self.id}.door.{self.door_id}'

    @property
    def icon(self) -> str:
        return f'{self._icon}'

    @property
    def available(self) -> bool:
        return self._available

    @property
    def state(self) -> Optional[str]:
        match (self._unlocked, self._open):
            case (False, False):
                return f'LOCKED, CLOSED'
            case (False, True):
                return f'LOCKED, OPEN'
            case (False, _):
                return f'LOCKED'
            case (True, False):
                return f'UNLOCKED, CLOSED'
            case (True, True):
                return f'UNLOCKED, OPEN'
            case (True, _):
                return f'UNLOCKED'
            case (_, False):
                return f'CLOSED'
            case (_, True):
                return f'OPEN'

        return None

    async def async_update(self):
        _LOGGER.debug(f'controller:{self.id}  update door {self.door_id} state')
        try:
            controller = self.id
            response = self.uhppote.get_status(controller)

            if response.controller == self.id:
                if self.door_id == 1:
                    self._unlocked = response.door_1_open == True
                elif self.door_id == 2:
                    self._unlocked = response.door_2_open == True
                elif self.door_id == 3:
                    self._unlocked = response.door_3_open == True
                elif self.door_id == 4:
                    self._unlocked = response.door_4_open == True
                else:
                    self._unlocked = None

                if self._mask != None:
                    self._open = response.inputs & self._mask != 0x00
                else:
                    self._open = None

                self._available = True

        except (Exception):
            self._available = False
            _LOGGER.exception(f'error retrieving controller {self.id} status')
