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
tolerance = 0.1 # time between pot readings
stoppedcount = 0
symbolstoptime = 1 # delay allowed between symbols
codestoptime = 2 # delay considered to be the end of entering the code

lastreading = 0
goingup = True
runcounter = 0
waitcount = 0
locked = True # assumed to be locked initially
awaitingattempt = False # True when service has been pushed, but no action taken yet (for timeout)
awaitingsymbol = False # True in above case, and when a symbol entry has timed out (after 1 second
                        # but the next symbol hasn't started being entered yet
sleeping = True # False when service has been pressed until the code entry timeout

symbolslogged = 0
codelog = [] # durations of symbols entered
dirlog = [] # directions of symbols entered
right = 1
left = 0
dialmargin = 3 # by how much must the dial actually move to be considered intentional - for noise reduction
timemargin = 0.5 # by how much can a symbol duration differ from what's required to be considered close enough

class Combination: # hard coded lock combination
    durations = [1, 1, 0.5, 0.5, 1] # in seconds
    directions = [right, left, right, left, right] 

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
    print("Service pushed, awaiting combination code.")
    
    global sleeping
    global awaitingattempt
    global awaitingsymbol
    
    sleeping = False
    awaitingattempt = True
    awaitingsymbol = True
    goingup = True
    
    # reset logs of previous attempt 
    symbolslogged = 0 
    codelog.clear()
    dirlog.clear()
GPIO.add_event_detect(servicepin, GPIO.RISING, service_pushed, delay);

def getreading():
    # read MCP raw input values
    potraw = mcp.read_adc(0)
    pot = round(50*(potraw/1023)) #convert to a resolution of 50 -any finer and pot jitter becomes and issue
    
    return pot  

def unlock():
    # make a happy noise
    # make U-Line high for 2 secs, then send low
    print("Unlocking")
    GPIO.output(unlockpin, 1)
    time.sleep(2)
    GPIO.output(unlockpin, 0)

def lock():
    # make L-Line high for 2 secs, then send low
    print("Locking")
    GPIO.output(lockpin, 1)
    time.sleep(2)
    GPIO.output(lockpin, 0)

def unlockfail():
    print("Combination incorrect, press service button to try again.")
    return
    # make a sad noise
          
def sort (x, y, n): # sort x into an array y of length n from min to max with ARM assembly
    return
    # bleh

def checkcombination(inputdurations, inputdirections): # takes in a combination and checks it against the preset combocode
    correct = True
    global combocode
    global sleeping
    global symbolslogged
    global timemargin

    if (len(combocode.directions) != len(inputdirections)): # rule out attempts with wrong number of symbols
        correct = False
    else:
        for i in range(len(inputdirections)): 
            if (combocode.directions[i] != inputdirections[i] or (abs(combocode.durations[i] - inputdurations[i]) > timemargin)):
                correct = False
    
    print("Checked combination")
    sleeping = True
    return correct

def logsymbol(duration, direction):
    global symbolslogged
    symbolslogged += 1
    
    codelog.append(duration) # add duration of last symbol to log
    dirlog.append(direction) # add direction of last symbol to log
    
    if (direction == 1):
        print("Turned right for " + str(duration) + "s")
    else:
        print("Turned left for " + str(duration) + "s")
    
#try-finally block to handle GPIO cleanup and robust termination
try:
    #loop for programme execution    
    while True: # make the code run until an exception is thrown
        global goingup
        global runcounter
        global awaitingsymbol
        global awaitingattempt
        global sleeping
        global waitcount
        global dialmargin
        
        if not (sleeping): # foil attempts when service button hasn't been pressed
            if not (awaitingsymbol): # only increase run counter when a symbol is actually being entered
                runcounter += 1
            reading = getreading()
        else:
            continue

        if ((reading <= lastreading + dialmargin) and (reading >= lastreading - dialmargin)): # we've stopped (temporarily or otherwise...) [with dialmargin]
            waitcount += 1 

            if (waitcount * tolerance >= codestoptime): # code entering completed
                waitcount = 0
                sleeping = True # put back to sleep, awaiting service button
                if (awaitingattempt): # user never actually entered anything in 2 seconds
                    print("System timed out. Press service button to enter a combination")
                elif (checkcombination(codelog, dirlog)): # check if code entered is correct
                    unlock()
                else:
                    unlockfail()
            
            elif ((waitcount * tolerance >= symbolstoptime) and not (awaitingsymbol)): # consider current symbol to be finished 
                #print("Symbol timed out")
                logsymbol((runcounter-waitcount) * tolerance, goingup) # only count up to when the dial stopped moving
                goingup = True
                awaitingsymbol = True 
                runcounter = 0

        else:
            awaitingattempt = False # the user has done something
            awaitingsymbol = False
            waitcount = 0
        
            if (goingup): # currently in a rightwards symbol (default at start of every symbol)
                if (reading < lastreading): # dial turned left - may be starting attempt with left turn, or ending a right turn    
                    if not (awaitingsymbol): # this isn't a left-starting code entry, we've actually changed direction
                        #print("Turned left to end right symbol")
                        logsymbol(runcounter * tolerance, goingup)
                    goingup = False
                    runcounter = 0
              
            else: # goingup is false - we're in a leftwards symbol
                if (reading > lastreading): # dial turned rightwards - end of left symbol`
                    #print("Turned right to end left symbol")
                    logsymbol(runcounter * tolerance, goingup)
                    goingup = True
                    runcounter = 0

        lastreading = reading
        time.sleep(tolerance)    

finally:
    GPIO.cleanup()