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
tolerance = 200 # time between pot readings
started = True
stoppedcount = 0
symbolstoptime = 1 # delay allowed between symbols
codestoptime = 2 # delay considered to be the end of entering the code

lastreading = 0
goingup = True
upwardscount = 0
downwardscount = 0
locked = True # assumed to be locked initially

symbolindex = 0
codelog = [0] * 16 # durations of symbols entered
dirlog = [0] * 16 # directions of symbols entered
up = 1
down = 0

class Combination: # hard coded lock combination
	durations = [500, 500, 250, 250, 500, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] # in milliseconds
	directions = [1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] # 1 is right / up and 0 is left / down

combocode = Combination()

# set pin names
modepin = 19
servicepin = 26
lockpin = 20
unlockpin = 21
CLK = 11
MISO = 9
MOSI = 10
CS = 8

# setup pin modes
GPIO.setup(modepin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(servicepin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(lockpin, GPIO.OUT)
GPIO.setup(unlockpin, GPIO.OUT)
GPIO.setup(MOSI, GPIO.OUT)
GPIO.setup(MISO, GPIO.IN)
GPIO.setup(CLK, GPIO.OUT)
GPIO.setup(CS, GPIO.OUT)

mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, mosi=MOSI, miso=MISO)

# handle service button presses
def service_pushed(channel):
    print("Service pushed")
    
    # reset logs of previous attempt 
    symbolindex = 0 
    codelog.clear()
    dirlog.clear()
GPIO.add_event_detect(servicepin, GPIO.RISING, service_pushed, delay);

def getreading():
    # read MCP raw input values
    potraw = mcp.read_adc(0)
    pot = 3.3*(potraw/1023)
    
    return pot  

def unlock():
	# make a happy noise
	# make U-Line high for 2 secs, then send low
	GPIO.output(unlockpin, 1)
	sleep(2)
	GPIO.output(unlockpin, 0)

def lock():
	# make L-Line high for 2 secs, then send low
	GPIO.output(lockpin, 1)
	sleep(2)
	GPIO.output(lockpin, 0)

def unlockfail():
	# make a sad noise

def sort (x, y, n): # sort x into an array y of length n from min to max with ARM assembly
	# bleh

def checkcombination(inputdurations, inputdirections): # takes in a combination and checks it against the preset combocode
	correct = True
	global combocode

	for index in xrange(0,15):
		if (combocode.directions[index] != inputdirections[index] || combocode.durations[index] != inputdurations[index])
			correct = False

	return correct

def logsymbol(duration, direction):
	codelog[symbolindex] = duration # add duration of last symbol to log
    dirlog[symbolindex] = direction # add direction of last symbol to log

#try-finally block to handle GPIO cleanup and robust termination
try:
    
    #loop for programme execution    
    while True: # make the code run until an exception is thrown
        global goingup
        reading = getreading()
        inc(runcounter)

        if (reading == lastreading): # we've stopped (temporarily or otherwise...)
			inc(waitcount) 

			if (waitcount * tolerance >= codestoptime): # code entering completed
				if (checkcombination(codelog, dirlog)): # check if code entered is correct
					unlock()
				else:
					unlockfail()

			else if (waitcount * tolerance >= symbolstoptime): # consider current symbol to be finished 
				logsymbol(runcounter * tolerance, goingup)
				awaitingattempt = True 
				runcounter = 0

        if (goingup): # currently in a rightwards symbol
        	if (reading >= lastreading): # stopped or still turning right
        		awaitingattempt = False
        	else: # direction changed
        		if (!awaitingattempt): # this isn't a left-starting code entry, we've actually changed direction
        			logsymbol(runcounter * tolerance, goingup)
				
				goingup = False
				runcounter = 0

		else: # in a leftwards symbol
			if (reading <= lastreading): # stopped or still turning left
				awaitingattempt = False
			else:
				logsymbol(runcounter * tolerance, goingup)
				
				goingup = True
				runcounter = 0

		lastreading = reading
        sleep(tolerance)    

finally:
    GPIO.cleanup()