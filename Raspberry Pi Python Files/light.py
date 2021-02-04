from time import sleep
from pydbus import SystemBus
import RPi.GPIO as GPIO

BLUEZ_SERVICE = 'org.bluez'
BLUEZ_DEV_IFACE = 'org.bluez.Device1'
BLUEZ_CHR_IFACE = 'org.bluez.GattCharacteristic1'


class Central:
# def means function in python
    def __init__(self, address):
        self.bus = SystemBus()
        self.mngr = self.bus.get(BLUEZ_SERVICE, '/')
        self.dev_path = self._from_device_address(address)
        self.device = self.bus.get(BLUEZ_SERVICE, self.dev_path)
        self.chars = {}

    def _from_device_address(self, addr):
        """Look up D-Bus object path from device address"""
        mng_objs = self.mngr.GetManagedObjects()
        for path in mng_objs:
            dev_addr = mng_objs[path].get(BLUEZ_DEV_IFACE, {}).get('Address', '')
            if addr.casefold() == dev_addr.casefold():
                return path

    def _get_device_chars(self):
        mng_objs = self.mngr.GetManagedObjects()
        for path in mng_objs:
            chr_uuid = mng_objs[path].get(BLUEZ_CHR_IFACE, {}).get('UUID')
            if path.startswith(self.dev_path) and chr_uuid:
                self.chars[chr_uuid] = self.bus.get(BLUEZ_SERVICE, path)


    def connect(self):
        """
        Connect to device.
        Wait for GATT services to be resolved before returning
        """
        self.device.Connect()
        while not self.device.ServicesResolved:
            sleep(0.5)
        self._get_device_chars()

    def disconnect(self):
        """Disconnect from device"""
        self.device.Disconnect()

    def char_write(self, uuid, value):
        """Write value to given GATT characteristic UUID"""
        if uuid.casefold() in self.chars:
            self.chars[uuid.casefold()].WriteValue(value, {})
        else:
            raise KeyError(f'UUID {uuid} not found')

    def char_read(self, uuid):
        """Read value of given GATT characteristic UUID"""
        if uuid.casefold() in self.chars:
            return self.chars[uuid.casefold()].ReadValue({})
        else:
            raise KeyError(f'UUID {uuid} not found')


device_address = 'C9:F0:78:8D:F2:F9'  # MAC Address of the Hue Bulb
light_state = '932c32bd-0002-47a2-835a-a8d455b859dd'   # characteristic ID for toggling light on/off

GPIO.setmode(GPIO.BCM) # BCM is the numbering system you see on the actual pins


dev = Central(device_address )
dev.connect()
GPIO.setup(18,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)   # setup pin 18 as an input and initialize it to an off state.
while True:   # indefinite loop
    motion = GPIO.input(18)
    if motion==1:
        print('Motion Detected!')
        dev.char_write(light_state , [1])   # write 1 to the characteristic light_state (turns bulb on)
        sleep(5)                            # wait for 5 seconds
        dev.char_write(light_state , [0])   # write 0, turns bulb off
        print(dev.char_read(light_state ))
        #dev.disconnect()
    else:
        print('No Motion Detected Yet')
    sleep(1);
        
