"""Support for Aliu devices."""
from datetime import timedelta
import logging
import time

import voluptuous as vol

from homeassistant.components.switch import (
    ENTITY_ID_FORMAT, PLATFORM_SCHEMA, SwitchDevice)
from homeassistant.const import (
    CONF_COMMAND_OFF, CONF_COMMAND_ON, CONF_NAME, CONF_HOST, CONF_MAC,
    CONF_SWITCHES, CONF_TIMEOUT, CONF_TYPE, STATE_ON)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.restore_state import RestoreEntity

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'Aliu switch'
DEFAULT_TIMEOUT = 10

CONF_ADDR = "addr"
CONF_ID = "id"

NRF_BUS = 0
NRF_CE = 5
NRF_IRQ = 6
HOST_ADDR = [0x19, 0x93, 0x10, 0x24, 0x26]
SLAVE_BASE = [0x20, 0x17, 0x09, 0x14]


SWITCH_TYPES = ['2cmds']

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_ADDR): cv.positive_int,
    vol.Required(CONF_ID): cv.positive_int,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_TYPE, default=SWITCH_TYPES[0]): vol.In(SWITCH_TYPES),
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Aliu switches."""
    _LOGGER.info("setup platform switch.aliu...")

    from custom_components.aliu24.aliu0_protocol import Aliu0_protocol

    name = config.get(CONF_NAME)
    addr = config.get(CONF_ADDR)
    id = config.get(CONF_ID)
    timeout = config.get(CONF_TIMEOUT)
    switch_type = config.get(CONF_TYPE)

    switches = [AliuSwitch(name, addr, id, timeout)]
    if AliuSwitch.datalink is None:
        AliuSwitch.datalink = Aliu0_protocol(NRF_BUS, NRF_CE, NRF_IRQ, HOST_ADDR, SLAVE_BASE)
    add_entities(switches)


class AliuSwitch(SwitchDevice, RestoreEntity):
    """Representation of an Aliu switch."""
    datalink = None

    def __init__(self, name, addr, id, timeout):
        """Initialize the switch."""

        #self.entity_id = ENTITY_ID_FORMAT.format(slugify(friendly_name))
        self._addr = addr
        self._id = id
        self._timeout = timeout
        self._name = name
        self._state = False
        self._is_available = False

    async def async_added_to_hass(self):
        """Call when entity about to be added to hass."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state:
            self._state = state.state == STATE_ON

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def assumed_state(self):
        """Return true if unable to access real state of entity."""
        return True

    @property
    def available(self):
        """Return True if entity is available."""
        return not self.should_poll or self._is_available

    @property
    def should_poll(self):
        """Return the polling state."""
        return False

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    def turn_on(self, **kwargs):
        """Turn the device on."""
        if self.datalink.set_on(self._addr, self._id):
            self._state = True
            self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """Turn the device off."""
        if self.datalink.set_off(self._addr, self._id):
            self._state = False
            self.schedule_update_ha_state()

    def update(self):
        """Synchronize state with switch."""
        self.datalink.request(self._addr, self._id)
        self._update()

    def _update(self, retry=20):
        """Update the state of the device."""
        status = self.datalink.get_data()
        if status[0]:
            if status[1] == self._addr and status[2] == self._id:
                self._state = status[3]
                self._is_available = True
                return
        if retry < 1:
            _LOGGER.error("Error during updating Aliu device state.")
            self._is_available = False
            return
        time.sleep(0.01)
        return self._update(retry-1)

