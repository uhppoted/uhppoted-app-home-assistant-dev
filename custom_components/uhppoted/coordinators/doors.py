from __future__ import annotations

import concurrent.futures
import threading
import datetime
import logging
import async_timeout

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed

from uhppoted import uhppote

_LOGGER = logging.getLogger(__name__)
_INTERVAL = datetime.timedelta(seconds=30)

from ..const import CONF_DOOR_ID
from ..const import CONF_CONTROLLER_SERIAL_NUMBER
from ..const import CONF_DOOR_NUMBER

from ..const import ATTR_AVAILABLE
from ..const import ATTR_DOOR_DELAY
from ..const import ATTR_DOOR_MODE
from ..const import ATTR_DOOR_BUTTON
from ..const import ATTR_DOOR_LOCK
from ..const import ATTR_DOOR_OPEN

from ..config import configure_driver
from ..config import get_configured_doors
from ..config import resolve_door
from ..config import resolve_door_by_name


class DoorsCoordinator(DataUpdateCoordinator):
    _state: Dict[str, Dict]

    def __init__(self, hass, options, poll, db):
        interval = _INTERVAL if poll == None else poll

        super().__init__(hass, _LOGGER, name="doors", update_interval=interval)

        self._uhppote = configure_driver(options)
        self._options = options
        self._db = db
        self._state = {}
        self._initialised = False

        _LOGGER.info(f'doors coordinator initialised ({interval.total_seconds():.0f}s)')

    def __del__(self):
        self.unload()

    def unload(self):
        pass

    def set_door_mode(self, controller, door, mode):
        api = self._uhppote['api']

        response = api.get_door_control(controller, door)
        if response.controller == controller and response.door == door:
            delay = response.delay
            response = api.set_door_control(controller, door, mode, delay)

            if response.controller != controller or response.door != door:
                raise ValueError(f'invalid response to set-door-control')
            else:
                return response

        return None

    def set_door_delay(self, controller, door, delay):
        api = self._uhppote['api']

        response = api.get_door_control(controller, door)
        if response.controller == controller and response.door == door:
            mode = response.mode
            response = api.set_door_control(controller, door, mode, delay)

            if response.controller != controller or response.door != door:
                raise ValueError(f'invalid response to set-door-control')
            else:
                return response

        return None

    def unlock_door(self, controller, door) -> None:
        api = self._uhppote['api']
        response = api.open_door(controller, door)

        if response.controller != controller:
            raise ValueError(f'invalid response to open-door')
        else:
            return response

    def unlock_door_by_name(self, door):
        record = resolve_door_by_name(self._options, door)
        if record:
            controller = record[CONF_CONTROLLER_SERIAL_NUMBER]
            doorno = record[CONF_DOOR_NUMBER]
            response = self.unlock_door(controller, doorno)
            return response.opened

        return False

    async def _async_update_data(self):
        try:
            contexts = set(self.async_contexts())
            doors = get_configured_doors(self._options)

            if not self._initialised:
                contexts.update(doors)
                self._initialised = True

            async with async_timeout.timeout(2.5):
                return await self._get_doors(contexts)
        except Exception as err:
            raise UpdateFailed(f"uhppoted API error {err}")

    async def _get_doors(self, contexts):
        api = self._uhppote['api']
        lock = threading.Lock()

        for v in contexts:
            if not v in self._state:
                self._state[v] = {
                    ATTR_AVAILABLE: False,
                }

        controllers = set()
        doors = {}
        for idx in contexts:
            door = resolve_door(self._options, idx)
            if door:
                controllers.add(door[CONF_CONTROLLER_SERIAL_NUMBER])
                doors[idx] = door

        state = {}
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                executor.map(lambda controller: self._get_controller(api, lock, state, controller),
                             controllers,
                             timeout=1)

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                executor.map(lambda idx: self._get_door(api, lock, idx, doors[idx], state), contexts, timeout=1)
        except Exception as err:
            _LOGGER.error(f'error retrieving controller {controller} door information ({err})')

        self._db.doors = self._state

        return self._db.doors

    def _get_controller(self, api, lock, state, controller):
        info = None

        try:
            response = api.get_status(controller)
            if response.controller == controller:
                info = {
                    1: {
                        'open': response.door_1_open == True,
                        'button': response.door_1_button == True,
                        'locked': response.relays & 0x01 == 0x00,
                    },
                    2: {
                        'open': response.door_2_open == True,
                        'button': response.door_2_button == True,
                        'locked': response.relays & 0x02 == 0x00,
                    },
                    3: {
                        'open': response.door_3_open == True,
                        'button': response.door_3_button == True,
                        'locked': response.relays & 0x04 == 0x00,
                    },
                    4: {
                        'open': response.door_4_open == True,
                        'button': response.door_4_button == True,
                        'locked': response.relays & 0x08 == 0x00,
                    }
                }
        except Exception as err:
            _LOGGER.error(f'error retrieving controller {controller} door state ({err})')

        with lock:
            state[controller] = info

    def _get_door(self, api, lock, idx, door, state):
        info = {
            ATTR_AVAILABLE: False,
            ATTR_DOOR_MODE: None,
            ATTR_DOOR_DELAY: None,
            ATTR_DOOR_OPEN: None,
            ATTR_DOOR_BUTTON: None,
            ATTR_DOOR_LOCK: None,
        }

        try:
            name = door[CONF_DOOR_ID]
            controller = door[CONF_CONTROLLER_SERIAL_NUMBER]
            door_id = door[CONF_DOOR_NUMBER]

            _LOGGER.debug(f'fetch door {name} information')

            mode = None
            delay = None

            response = api.get_door_control(controller, door_id)
            if response.controller == controller and response.door == door_id and controller in state and state[
                    controller] != None:
                mode = response.mode
                delay = response.delay

                info = {
                    ATTR_DOOR_MODE: mode,
                    ATTR_DOOR_DELAY: delay,
                    ATTR_DOOR_OPEN: state[controller][door_id]['open'],
                    ATTR_DOOR_BUTTON: state[controller][door_id]['button'],
                    ATTR_DOOR_LOCK: state[controller][door_id]['locked'],
                    ATTR_AVAILABLE: True,
                }

        except Exception as err:
            _LOGGER.error(f'error retrieving door {door["door_id"]} information ({err})')

        with lock:
            self._state[idx].update(info)
