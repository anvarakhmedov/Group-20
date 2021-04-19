from http.server import BaseHTTPRequestHandler, HTTPServer   # BaseHTTPRequestHandler used for servicing incoming HTTP requests
import RPi.GPIO as GPIO                                      # used for defining GPIO pins on the Pi
import csv
import os
from lightbulb import lightbulb
import datetime
import socket
from string import Template
import board
import busio
import adafruit_veml7700
import _thread
from time import sleep


from sensor_data import sensor_class

# # GPIO setup
# GPIO.setmode(GPIO.BCM)
# GPIO.setwarnings(False)
# GPIO.setup(24,GPIO.IN) # motion sensor, labelled #24 on breakout board
# GPIO.setup(27,GPIO.IN) # touch sensor, labelled #27 on breakout board
# 
# # Light Sensor Module Setup. Use veml7700.light to output ambient light levels and veml7700.lux to output light in lux
# 
# i2c = busio.I2C(board.SCL, board.SDA)
# veml7700 = adafruit_veml7700.VEML7700(i2c)
# light = int(veml7700.lux)
GPIO.setup(22,GPIO.OUT)
GPIO.output(22,GPIO.HIGH)

hostname = socket.gethostname()
host_name = socket.gethostbyname(hostname)   # type 'ip -4 address|grep inet' in terminal to retrieve device IP address
#host_name = '130.108.226.76'    # Anthony's Testing IP
#host_name = '10.16.164.10'
host_port = 8080

#  Connect to bulb ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
device_address = 'C9:F0:78:8D:F2:F9'  # MAC Address of the Hue Bulb
bulb = lightbulb(device_address)   # store bulb as class lightbulb and pass in the device_address defined above. This argument is passed into the function __init__
bulb.connect()                   # use connect() function inside the class lightbulb
bulb.turnOff

# Assign classifier to sensor_data module
sensor = sensor_class()
brightness = 0


#Handle History and Ststus File IO ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def writeHistory(status, method, brightness):
    with open('history.csv', 'a', newline='') as f:
        time = datetime.datetime.now() 
        writer = csv.writer(f)
        writer.writerow([time, status, method, brightness])
        
def setBrightness(brightness):
    with open('history.csv', 'a', newline='') as f:
        time = datetime.datetime.now() 
        writer = csv.writer(f)
        writer.writerow([time, status, method, brightness])
        
def getBrightness():
    with open('history.csv', 'r', newline='') as f:
        time = datetime.datetime.now() 
        writer = csv.writer(f)
        writer.writerow([time, status, method, brightness])
        

class server(BaseHTTPRequestHandler):
    bulb.turnOff
                
    def defineLocals(self):
        self.brightness = 0
    
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
        html = open('html/index.html', 'r').read()
        
        self.do_HEAD()
        
        #  Insert all necessary variable into the HTML
        html = html%(brightness)
        
        self.wfile.write(html.encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])    # Get the size of data
        post_data1 = self.rfile.read(content_length).decode("utf-8")   # Get the data
        post_data = post_data1.split("=")[1]    # Only keep the value
        print("post data: ",post_data)
        if post_data == 'On':
            current_brightness = bulb.turnOn()
            writeHistory('on', 'application', current_brightness)
            print("post data: ",current_brightness)
        elif post_data == 'Off': 
            current_brightness = bulb.turnOff()
            writeHistory('off', 'application', current_brightness)
            print("post data: ",current_brightness)
        elif post_data == 'Motion':
            current_brightness = bulb.turnOn()
        else:
            brightness = int(format(post_data))
            bulb.setBrightness(brightness)
            writeHistory('brightness change', 'application', brightness)  # TODO: UnboundLocalError: local variable 'brightness' referenced before assignment
            print("post data: ",brightness)

        self._redirect('/')
    
    def sensor_control():
        current_state = [0]
        while True:
            light_state_id = bulb.light_state      # declare variable to hold light state characteristic id
            lightstate = bulb.char_read(light_state_id)  # read actual light state of bulb. Data type is list
            sensor.read_sensor_data()    # call read_sensor_data() method from sensor_data.py
            #sleep(1)
            #print("lightstate is", lightstate)
            #print("current_state is", current_state)
            #post_data = self.post_data1 
            current_state = lightstate
            #print("post data: ",post_data)
            if sensor.is_touch == 1 and current_state == [0]:# and lightstate == [0]:  #TODO: web page bulb on/off functions interfere with this state machine
                current_brightness = bulb.turnOn()
                #current_state = [1]
                GPIO.output(22,GPIO.LOW)
                sleep(1)
                GPIO.output(22,GPIO.HIGH)
            elif sensor.is_touch == 1 and current_state == [1]: #and lightstate == [1]:
                current_brightness = bulb.turnOff()
                #current_state = [0]
                GPIO.output(22,GPIO.LOW)
                sleep(1)
                GPIO.output(22,GPIO.HIGH)
            #elif post_data == 'Motion' and sensor.is_motion == 1 and lightstate == [0]:
                #current_brightness = bulb.turnOn()
#_thread.start_new_thread(sensor.read_sensor_data,())   # start a new thread and run the sensors() function in the server class to read sensor data.
_thread.start_new_thread(server.sensor_control,())   # start a new thread and run the sensors() function in the server class to read sensor data.

if __name__ == '__main__':
    http_server = HTTPServer((host_name, host_port), server)
    print("Server Starts - %s:%s" % (host_name, host_port))
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()

     





















