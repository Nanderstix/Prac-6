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
lightmax = 898 # maximum expected LDR value
time_start = time.time() # reference time to calculate timer value
freq_arr = [0.5,1,2] # array of delay time values in seconds
time_delay = 0.5 # default delay is 500ms
started = True
stoppedcount = 0
stoppedcache = ""

# set pin names
resetpin = 19
freqpin = 16
stoppin = 20
displaypin = 21
CLK = 11
MISO = 9
MOSI = 10
CS = 8

# setup pin modes
GPIO.setup(resetpin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(freqpin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(stoppin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(displaypin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(MOSI, GPIO.OUT)
GPIO.setup(MISO, GPIO.IN)
GPIO.setup(CLK, GPIO.OUT)
GPIO.setup(CS, GPIO.OUT)

mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, mosi=MOSI, miso=MISO)

# handle reset button presses
def reset_pushed(channel):
    global time_start
    time_start = time.time() # reset time of timer
    print("\033c", end='') #clears the console, but only when running from terminal. No way to clear IDE shell
    print("Reset pushed")
    # print header line
    print ('{:10}{:10}{:8}{:8}{:8}'.format("Time", "Timer", "Pot", "Temp", "Light"))
GPIO.add_event_detect(resetpin, GPIO.RISING, reset_pushed, delay);

# handle freq button presses
def freq_pushed(channel):
    global time_delay
    index = freq_arr.index(time_delay) 
    if (index==2): index=0  
    else: index +=1 
    time_delay = freq_arr[index] # iterate to next delay value
    
    print("Frequency pushed")
    print("Time delay = " + str(time_delay) + "s")
GPIO.add_event_detect(freqpin, GPIO.RISING, freq_pushed, delay);

# handle stop button presses
def stop_pushed(channel):
    global started
    started = not(started)
    if (started): print("Start pushed")
    else:  print("Stop pushed")
    
    # reset the stopped cache for use by the Display button
    global stoppedcache
    stoppedcache = ""
    global stoppedcount
    stoppedcount = 0
GPIO.add_event_detect(stoppin, GPIO.RISING, stop_pushed, delay);

# handle display button presses
def display_pushed(channel):
    global stoppedcache
    print("Display pushed")
    print(stoppedcache)
GPIO.add_event_detect(displaypin, GPIO.RISING, display_pushed, delay);

def getreadings():
    # read MCP raw input values
    tempraw = mcp.read_adc(0)
    lightraw = mcp.read_adc(1)
    potraw = mcp.read_adc(2)
    
    # convert raw values to meaningful output numbers
    current_ticks = time.time() # current number of seconds since 1978
    timer_seconds = round(current_ticks - time_start) # value of timer
    
    timer = str(datetime.timedelta(seconds=timer_seconds)) # Convert seconds to correct format
    actualtime = datetime.datetime.fromtimestamp(current_ticks).strftime('%H:%M:%S') # Get the current device time
    tempvolt = 3.3*(tempraw/1023) # convert raw value to voltage for use in formula
    temp = (tempvolt-0.5)/(0.01)
    light = 100*(lightraw/lightmax)
    pot = 3.3*(potraw/1023)
    
    readings = '{:10}{:6}{:6.1f} V {:4.0f} C {:4.0f}%'.format(actualtime, timer, pot, temp, light)
    return readings

def wait():
    time_corrector = (time.time()-time_start)%time_delay # account for function run time.
    time.sleep(time_delay-time_corrector) # delay for time delay value   

#try-finally block to handle GPIO cleanup and robust termination
try:
    # print header line
    print ('{:10}{:10}{:8}{:8}{:8}'.format("Time", "Timer", "Pot", "Temp", "Light"))
    
    #loop for programme execution    
    while True: # make the code run until an exception is thrown
        readings = getreadings();
        
        if (started):
            # Display values
            print (readings)
        else:
            if (stoppedcount < 5) :
                # add current set of readings to cache
                stoppedcache = stoppedcache + readings
                if (stoppedcount < 4): stoppedcache += "\n"
                stoppedcount += 1
                
        wait()     

finally:
    GPIO.cleanup()