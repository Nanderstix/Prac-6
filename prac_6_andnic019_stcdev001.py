#!/usr/bin/python
# created by STCDEV001 & ANDNIC019, 01/09/2018

import RPi.GPIO as GPIO
import time
import datetime
import Adafruit_MCP3008
import os
GPIO.setwarnings(False)

# init variables & constants
GPIO.setmode(GPIO.BCM) # use GPIO pin numbering
delay = 300 # button debounce time
resolution = 200 # time between pot readings
started = True
stoppedcount = 0
symbolstop = 1 # delay allowed between symbols
codestop = 2 # delay considered to be the end of entering the code
lastreading = 0
goingup = True
upwardscount = 0
downwardscount = 0

# set pin names
servicepin = 19
CLK = 11
MISO = 9
MOSI = 10
CS = 8

# setup pin modes
GPIO.setup(servicepin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(MOSI, GPIO.OUT)
GPIO.setup(MISO, GPIO.IN)
GPIO.setup(CLK, GPIO.OUT)
GPIO.setup(CS, GPIO.OUT)

mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, mosi=MOSI, miso=MISO)

# handle service button presses
def service_pushed(channel):
    print("Service pushed")
GPIO.add_event_detect(servicepin, GPIO.RISING, service_pushed, delay);

def getreading():
    # read MCP raw input values
    potraw = mcp.read_adc(0)
    pot = 3.3*(potraw/1023)
    
    return pot  

#try-finally block to handle GPIO cleanup and robust termination
try:
    
    #loop for programme execution    
    while True: # make the code run until an exception is thrown
        reading = getreading();
        
        if (goingup):
        	if (reading >= lastreading):
        		inc(upwardscount)

        sleep(resolution)    

finally:
    GPIO.cleanup()