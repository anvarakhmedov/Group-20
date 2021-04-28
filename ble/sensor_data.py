import RPi.GPIO as GPIO                                      # used for defining GPIO pins on the Pi
import os
from time import sleep
                                                             # Multiple processes using the same bus can communicate with eachother
# Light Sensor Module Libraries
import board
import busio
import adafruit_veml7700
import _thread
from lightbulb import lightbulb
import math

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(24,GPIO.IN) # motion sensor, labelled #24 on breakout board
GPIO.setup(23,GPIO.IN) # motion sensor, labelled #24 on breakout board
GPIO.setup(25,GPIO.IN) # motion sensor, labelled #24 on breakout board
GPIO.setup(27,GPIO.IN) # touch sensor, labelled #27 on breakout board

# Light Sensor Module Setup. Use veml7700.light to output ambient light levels and veml7700.lux to output light in lux
i2c = busio.I2C(board.SCL, board.SDA)
veml7700 = adafruit_veml7700.VEML7700(i2c)

class sensor_class():

    def read_sensor_data(self):
        self.is_light = int(veml7700.lux)    # measuring light in units of lux 
        #print("Ambient light:", veml7700.light)
        #print("Lux:", veml7700.lux)  
        self.is_motion = GPIO.input(24) or GPIO.input(23) or GPIO.input(25)  # check for motion
        self.is_touch = GPIO.input(27)    # check for touch
        print("motion: ", self.is_motion)
        #print("touch: ", self.is_touch)
        if self.is_light > 100:
            self.is_light = 100
        elif self.is_light < 1:
            self.is_light = 1
        self.is_light = round(2.5*self.is_light - 1.896*math.exp(-14)) # fit to 1-250 range  
        self.brightness = round(-2.5*self.is_light + 250) # interpolation model defined in MATLAB
        if self.brightness < 1:
           self.brightness = 0

