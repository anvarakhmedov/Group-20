#from http.server import BaseHTTPRequestHandler, HTTPServer   # BaseHTTPRequestHandler used for servicing incoming HTTP requests
import RPi.GPIO as GPIO                                      # used for defining GPIO pins on the Pi
from time import sleep 
from pydbus import SystemBus                                 # Allows for use of services regardless of what language they are written in
                                                             # Multiple processes using the same bus can communicate with eachother
import importlib

BLUEZ_SERVICE = 'org.bluez'                           # bluetooth service
BLUEZ_DEV_IFACE = 'org.bluez.Device1'
BLUEZ_CHR_IFACE = 'org.bluez.GattCharacteristic1'

class lightbulb():

    light_state = '932c32bd-0002-47a2-835a-a8d455b859dd'   # Attribute ID for toggling light on/off
    brightness_value = '932c32bd-0003-47a2-835a-a8d455b859dd'    # Attribute ID for changing brightness (value between 1-254)


    def __init__(self, address):   # function to initialize mac address of bulb. self is an object used for calls and address (MAC) is an input
        
        self.bus = SystemBus()
        self.mngr = self.bus.get(BLUEZ_SERVICE, '/')
        self.dev_path = self._from_device_address(address)
        self.device = self.bus.get(BLUEZ_SERVICE, self.dev_path)
        self.chars = {}
             
        print('Connecting to bulb at ' + address)

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
        # Read value of given GATT characteristic UUID
        if uuid.casefold() in self.chars:
            return self.chars[uuid.casefold()].ReadValue({})
        else:
            raise KeyError(f'UUID {uuid} not found')


    #~~~~~~~~~~~~~~~~~~~~~~ Bulb Controlling Functions ~~~~~~~~~~~~~~~~~~~~~~~~~~

    def turnOn(self):
        print('Light turning on')
        self.char_write(light_state , [1])
        sleep(0.5)
        current_brightness = self.char_read(brightness_value)[0]
        lightstate = self.char_read(light_state)
        print('Light State is' + (str)(lightstate))
        print('Brightness is currently set to ' + (str)(current_brightness))
        return current_brightness
        
    def turnOff(self):
        print('Light turning off')
        self.char_write(light_state , [0])
        current_brightness = 0
        lightstate = self.char_read(light_state)
        print('Light State is' + (str)(lightstate))
        print('Brightness is currently set to ' + (str)(current_brightness))
        return current_brightness

    def setBrightness(self, brightness):
        print('Set brightess to ' + (str)(brightness))
        if brightness == 0:
            self.char_write(light_state, [0])
        else:
            self.char_write(light_state, [1])
            self.char_write(brightness_value, [brightness])
            sleep(0.5)
            stored_brightness = self.char_read(brightness_value)
            print('Stored Brightness is ' + (str)(stored_brightness))
        
    #~~~~~~~~~~~~~~~~~~~~~ END Bulb Controlling Functions ~~~~~~~~~~~~~~~~~~~~~~~ 
       



