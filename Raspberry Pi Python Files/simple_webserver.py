import RPi.GPIO as GPIO
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from time import sleep
from pydbus import SystemBus
import cgi
import cgitb

BLUEZ_SERVICE = 'org.bluez'
BLUEZ_DEV_IFACE = 'org.bluez.Device1'
BLUEZ_CHR_IFACE = 'org.bluez.GattCharacteristic1'


class Central:
# def means function in python
    def __init__(self, address):   # initialize mac address of bulb. Similar to a constructor in C++
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
brightness_value = '932c32bd-0003-47a2-835a-a8d455b859dd'    # charactersitic ID for changing brightness (value between 1-254)

GPIO.setmode(GPIO.BCM) # BCM is the numbering system you see on the actual pins


dev = Central(device_address)   # store dev as class Central and pass in the device_address defined above. This argument is passed into the function __init__
dev.connect()                   # use connect() function inside the class Central
#GPIO.setup(18,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)   # setup pin 18 as an input and initialize it to an off state.
#while True:   # indefinite loop
#    motion = GPIO.input(18)
#    if motion==1:
 #       print('Motion Detected!')
#        dev.char_write(light_state , [1])   # write 1 to the characteristic light_state (turns bulb on)
#        sleep(5)                            # wait for 5 seconds
#        dev.char_write(light_state , [0])   # write 0, turns bulb off
#        print(dev.char_read(light_state ))
        #dev.disconnect()
#    else:
#        print('No Motion Detected Yet')
#    sleep(1);
        


host_name = '192.168.0.11'    # Change this to your Raspberry Pi IP address. type 'ip -4 address|grep inet' in terminal
host_port = 8000


class MyServer(BaseHTTPRequestHandler):
    """ A special implementation of BaseHTTPRequestHander for reading data from
        and control GPIO of a Raspberry Pi
    """

    def do_HEAD(self):
        """ do_HEAD() can be tested use curl command 
            'curl -I http://server-ip-address:port' 
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        """ do_GET() can be tested using curl command 
            'curl http://server-ip-address:port' 
        """
        html = '''
            <html>
            <body style="width:960px; margin: 20px auto;">
            <h1>Smart Light Controller</h1>
            <p>Current GPU temperature is {}</p>
            <p>Turn LED: <a href="/on">On</a> <a href="/off">Off</a></p>   
            <label for="tentacles">Choose Brightness (1-254):</label>
            <input type="number" id="brightness" name="brightness" value="200">
            <div> <input type="submit"> </div>
            <div id="led-status"></div>
            <script>
                document.getElementById("led-status").innerHTML="{}";
            </script>
            </body>
            </html>
        '''
        form = cgi.FieldStorage()
        brightness_amount = form.getvalue('brightness')
        temp = os.popen("/opt/vc/bin/vcgencmd measure_temp").read()
        self.do_HEAD()
        status = ''
        if self.path=='/':
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(18, GPIO.OUT)
        elif self.path=='/on':
            GPIO.output(18, GPIO.HIGH)
            status='LED is On'
            dev.char_write(light_state , [1])
            dev.char_write(brightness_value, [200]
                           )   # this works, but need to pass in value entered in the html code
        elif self.path=='/off':
            GPIO.output(18, GPIO.LOW)
            status='LED is Off'
            dev.char_write(light_state , [0])
        self.wfile.write(html.format(temp[5:], status).encode("utf-8"))
        
if __name__ == '__main__':
    http_server = HTTPServer((host_name, host_port), MyServer)
    print("Server Starts - %s:%s" % (host_name, host_port))

    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()
    

