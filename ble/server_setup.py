#!/usr/bin/env python
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
import time
from sensor_data import sensor_class
import math
import matplotlib.pyplot as plt
import pandas as pd


GPIO.setup(22,GPIO.OUT)
GPIO.output(22,GPIO.HIGH)

hostname = socket.gethostname()
host_name = socket.gethostbyname(hostname)   # type 'ip -4 address | grep inet' in terminal to retrieve device IP address
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
        
def graphHistory():
    data = pd.read_csv('history.csv')
    data = data.iloc[-20:]  # get last 20 entries

    x = data["time"]
    y = data["brightness"]

    xAxis = []

    for i in x: 
        xAxis.append(i[5:16]) 

    plt.bar(x,y, 1)
    plt.xticks(x, xAxis)
    plt.yticks(range(0,257,32))
    plt.grid(axis='y', linestyle='--')
    plt.xlabel('Date')
    plt.ylabel('Brightness')
    plt.title('Activation History')
    plt.xticks(rotation = -45)
    plt.savefig('html/images/history.png', bbox_inches = "tight")
    plt.clf()

    # <img src="html/images/history.png" alt="Lightbulb Activation Data">
        

class server(BaseHTTPRequestHandler):
    bulb.turnOff
                
    def defineLocals(self):
        self.brightness = 0
    
    def do_HEAD(self):
        """ do_HEAD() can be tested use curl command 
            'curl -I http://server-ip-address:port' 
        """
        if self.path.endswith(".png"):
            #print(elf.path)
            f = open("/home/pi/Desktop/ble" + self.path, 'rb')
            self.send_response(200)
            self.send_header('Content-type', 'image/png')
            self.end_headers()
            self.wfile.write(f.read())
            f.close()
            return
        elif self.path.endswith(".jpg"):
            #print(elf.path)
            f = open("/home/pi/Desktop/ble" + self.path, 'rb')
            self.send_response(200)
            self.send_header('Content-type', 'image/jpg')
            self.end_headers()
            self.wfile.write(f.read())
            f.close()
            return
        elif self.path.endswith(".ico"):
            #print(elf.path)
            f = open("/home/pi/Desktop/ble" + self.path, 'rb')
            self.send_response(200)
            self.send_header('Content-type', 'image/ico')
            self.end_headers()
            self.wfile.write(f.read())
            f.close()
            return
        
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
        
    global post_data
    global motion_valid
    global last_light_input
    global last_motion_input
    motion_valid = 0
    last_light_input = 'Undefined'
    last_motion_input = 'Undefined'
    post_data = 'Undefined'
    print("motion_valid ", motion_valid)
    
    def do_POST(self):
        global post_data
        global last_light_input
        global last_motion_input
        global motion_valid
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
            motion_valid = 0
            writeHistory('off', 'application', current_brightness)
            print("post data: ",current_brightness)
        elif post_data == 'Motion':
            last_motion_input = 'Motion'
        elif post_data == 'Light':
            last_light_input = 'Light'
        elif post_data == 'Neither':
            last_motion_input = 'Undefined'
            last_light_input = 'Undefined'
        else:
            brightness = int(format(post_data))
            bulb.setBrightness(brightness)
            writeHistory('brightness change', 'application', brightness)  
            print("post data: ",brightness)
        graphHistory()
        print("post data is: ", post_data)
        self._redirect('/')
    
    def sensor_control():
        light_valid = 1
        global motion_valid
        while True:
            light_state_id = bulb.light_state      # declare variable to hold light state characteristic id
            lightstate = bulb.char_read(light_state_id)  # read actual light state of bulb. Data type is list
            sensor.read_sensor_data()    # call read_sensor_data() method from sensor_data.py
            print("motion_valid = ", motion_valid)
            print("motion = ", sensor.is_motion)
            print("light_valid =", light_valid)
            if sensor.is_touch == 1 and lightstate == [0]: # lightstate is on/off state of bulb
                current_brightness = bulb.turnOn()
                print("Turned on by touch sensor")
                light_valid = 1
                GPIO.output(22,GPIO.LOW)  # reset touch sensor output
                sleep(1)
                GPIO.output(22,GPIO.HIGH)
            elif sensor.is_touch == 1 and lightstate == [1]: 
                current_brightness = bulb.turnOff()
                print("Turned off by touch sensor")
                light_valid = 0
                GPIO.output(22,GPIO.LOW)  # reset touch sensor output
                sleep(1)
                GPIO.output(22,GPIO.HIGH)
            elif last_light_input == 'Light' and post_data != 'Off' and post_data != 'Motion': #or light_valid == 1:# and lightstate == [1]:
                sleep(0.5)
                set_brightness = sensor.brightness 
                print("brightness = ", set_brightness)
                bulb.setBrightness(set_brightness)
                print("actual light = ",sensor.is_light)
            elif last_motion_input == 'Motion' and post_data != 'Light' and sensor.is_motion == 1 and lightstate == [0]:
                sleep(0.5)
                if (post_data == 'Off' and motion_valid == 0) or light_valid == 0: #and motion_valid == 0:
                    motion_valid = 1
                    light_valid = 1
                    print("in the loop")
                    sleep(10)
                else:
                    current_brightness = bulb.turnOn()

_thread.start_new_thread(server.sensor_control,())
    


if __name__ == '__main__':
    http_server = HTTPServer((host_name, host_port), server)
    print("Server Starts - %s:%s" % (host_name, host_port))
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()
