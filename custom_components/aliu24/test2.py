from aliu0_protocol import Aliu0_protocol


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

#AliuSwitch.datalink = Aliu0_protocol(NRF_BUS, NRF_CE, NRF_IRQ, HOST_ADDR, SLAVE_BASE)

class AliuSwitch:
    """Representation of an Aliu switch."""
    datalink = None
    def __init__(self, friendly_name, addr, id, timeout):
        """Initialize the switch."""
        from aliu0_protocol import Aliu0_protocol
        self._addr = addr
        self._id = id
        self._timeout = timeout
        self._name = friendly_name
        self._state = False
        self._is_available = False
        #if self.datalink is None:
         #   raise NameError('datalink is none')

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
                print(retry)
                return
        if retry < 1:
            #_LOGGER.error("Error during updating Aliu device state.")
            self._is_available = False
            return  self.update()
        import time
        time.sleep(0.01)
        return self._update(retry-1)

room = AliuSwitch("room", 0x46, 0, 100)
AliuSwitch.datalink = Aliu0_protocol(NRF_BUS, NRF_CE, NRF_IRQ, HOST_ADDR, SLAVE_BASE)
room.update()
print(room.is_on)
