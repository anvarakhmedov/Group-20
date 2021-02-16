import RPi.GPIO as GPIO                                      # used for defining GPIO pins on the Pi
import os
from http.server import BaseHTTPRequestHandler, HTTPServer   # BaseHTTPRequestHandler used for servicing incoming HTTP requests
from time import sleep 
from pydbus import SystemBus                                 # Allows for use of services regardless of what language they are written in
                                                             # Multiple processes using the same bus can communicate with eachother


##############################################################
#
#                Bluetooth Service Setup
#
##############################################################
  
BLUEZ_SERVICE = 'org.bluez'                           # bluetooth service
BLUEZ_DEV_IFACE = 'org.bluez.Device1'
BLUEZ_CHR_IFACE = 'org.bluez.GattCharacteristic1'


class Central:
# def means function in python
    def __init__(self, address):   # function to initialize mac address of bulb. self is an object used for calls and address (MAC) is an input
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


##############################################################
#
#                Python Server Setup
#
##############################################################

host_name = '192.168.0.11'    # Change this to your Raspberry Pi IP address. type 'ip -4 address|grep inet' in terminal
host_port = 8080


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
        
    def _redirect(self, path):
        self.send_response(303)
        self.send_header('Content-type', 'text/html')
        self.send_header('Location', path)
        self.end_headers()
        
    def do_GET(self):
        """ do_GET() can be tested using curl command 
            'curl http://server-ip-address:port' 
        """
        html = '''
            <html>
            <body style="width:960px; margin: 20px auto;">
            <h1>Welcome to my Raspberry Pi</h1>
            <p>Current GPU temperature is {}</p>
            <form action="/" method="POST">
                Turn LED :
                <input type="submit" name="submit" value="On">
                <input type="submit" name="submit" value="Off">
            </form>
            <form action="/" method="POST">
                Choose Brightness : 
                <input type="number" name="quantity">
                <button type="submit"> Submit </button>
            </form>
            </body>
            </html>
        '''
        temp = os.popen("/opt/vc/bin/vcgencmd measure_temp").read()
        self.do_HEAD()
        self.wfile.write(html.format(temp[5:]).encode("utf-8"))

    def do_POST(self):
        """ do_POST() can be tested using curl command 
            'curl -d "submit=On" http://server-ip-address:port' 
        """
        content_length = int(self.headers['Content-Length'])    # Get the size of data
        post_data = self.rfile.read(content_length).decode("utf-8")   # Get the data
        post_data = post_data.split("=")[1]    # Only keep the value
        
        # GPIO setup
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(18,GPIO.OUT)

        if post_data == 'On':
            GPIO.output(18, GPIO.HIGH)
            dev.char_write(light_state , [1])
        elif post_data == 'Off':
            GPIO.output(18, GPIO.LOW)
            dev.char_write(light_state , [0])
        else:
            dev.char_write(brightness_value, [int(format(post_data))])
        print("LED is {}".format(post_data))
        
        self._redirect('/')
        

if __name__ == '__main__':
    http_server = HTTPServer((host_name, host_port), MyServer)
    print("Server Starts - %s:%s" % (host_name, host_port))

    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()
    


