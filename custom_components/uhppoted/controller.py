from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity

_LOGGER = logging.getLogger(__name__)

# Attribute constants
from .const import ATTR_ADDRESS
from .const import ATTR_NETMASK
from .const import ATTR_GATEWAY
from .const import ATTR_FIRMWARE

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
        self._name = f'uhppoted.{name}.ID'
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
        self._name = f'uhppoted.{name}.address'
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
        self._name = f'uhppoted.{name}.date/time'
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


