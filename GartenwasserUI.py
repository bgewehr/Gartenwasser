#!/usr/bin/python

__author__ = "Bernd Gewehr"

# import python libraries
import signal
import time
import sys

# import libraries
import lib_mqtt as MQTT

import Adafruit_MPR121.MPR121 as MPR121

import PCF_CharLCD as LCD

# the global debug variable, set true for console output
DEBUG = False
#DEBUG = True

# the MQTT topics and qos setting
MQTT_TOPIC_IN = "/Gartenwasser/#"
MQTT_TOPIC = "/Gartenwasser"
MQTT_QOS = 0

# The VALVE_STATE stores the current states of all valves, 
# the flow and the consumption
# It has five datasets because our keypad has five switches, makes it easier to code
VALVE_STATE = [[0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0]]

# the units of the displaytype state, flow and consumption
UNIT = ['', 'l/h', 'l ']

# the text expression fpr the switchvalues 0 and 1
SWITCHPOS = ['off ', 'on ']

# the time the display backlight will stay on after each switching event
DISPLAYTIME = 50

# the countdown variable for the display backlight
DISPLAYON = DISPLAYTIME

#The DISPLAYTYPE Variable is modified by the 5th button of the keypad
#It decides which data to show: state, flow, consumption60min
DISPLAYTYPE = 0

print 'LCD daemon starting'

def output():
    if DISPLAYTYPE == 0:
        state1 = SWITCHPOS[VALVE_STATE[0][DISPLAYTYPE]] + UNIT[DISPLAYTYPE]
    else:
        state1 = str(VALVE_STATE[0][DISPLAYTYPE]) + UNIT[DISPLAYTYPE]
    state1 = state1.rjust(6)
    if DISPLAYTYPE == 0:
        state2 = SWITCHPOS[VALVE_STATE[1][DISPLAYTYPE]] + UNIT[DISPLAYTYPE]
    else:
        state2 = str(VALVE_STATE[1][DISPLAYTYPE]) + UNIT[DISPLAYTYPE]
    state2 = state2.rjust(6)
    if DISPLAYTYPE == 0:
        state3 = SWITCHPOS[VALVE_STATE[2][DISPLAYTYPE]] + UNIT[DISPLAYTYPE]
    else:
        state3 = str(VALVE_STATE[2][DISPLAYTYPE]) + UNIT[DISPLAYTYPE]
    state3 = state3.rjust(6)
    if DISPLAYTYPE == 0:
        state4 = SWITCHPOS[VALVE_STATE[3][DISPLAYTYPE]] + UNIT[DISPLAYTYPE]
    else:
        state4 = str(VALVE_STATE[3][DISPLAYTYPE]) + UNIT[DISPLAYTYPE]
    state4 = state4.rjust(6)
    Message0 = '1:' + state1 + '2:' + state2
    Message1 = '3:' + state3 + '4:' + state4

    lcd.set_cursor(0,0)
    lcd.message(Message0)
    lcd.set_cursor(0,1)
    lcd.message(Message1)
 

def on_message(mosq, obj, msg):
    """
    Handle incoming messages
    """
    global DISPLAYON
    topicparts = msg.topic.split("/")
    
    if DEBUG:
       print 'Received: ' + msg.topic, msg.payload
       #print 'TOPICPARTS :'
       #print topicparts
       #for i in range(0,len(topicparts)):
       #    print i, topicparts[i]
	
    pin = int(topicparts[len(topicparts) - 1])

    try:
        value = int(float(msg.payload))
    except ValueError:
        if DEBUG: print 'Valueerror on ' + msg.topic, msg.payload
        value = -1

    if topicparts[2] == "in":
        if DEBUG: print "Message type 'in' for pin " + str(pin) + " with value " + str(value)  
        if pin == 29:
            VALVE_STATE[0][0] = value
        if pin == 31:
            VALVE_STATE[1][0] = value
        if pin == 33:
            VALVE_STATE[2][0] = value
        if pin == 35:
            VALVE_STATE[3][0] = value
        if DEBUG: print 'Setting RGB to color ' + str(VALVE_STATE[0][0] + VALVE_STATE[1][0] + VALVE_STATE[2][0] + VALVE_STATE[3][0] + 1)
        time.sleep(.05)
        lcd.set_backlight(True)
        DISPLAYON = DISPLAYTIME

    elif topicparts[2] == "flow":
        if DEBUG: print "Message type 'flow' for pin " + str(pin) + " with value " + str(value)  
        if pin == 29:
            VALVE_STATE[0][1] = value
        if pin == 31:
            VALVE_STATE[1][1] = value
        if pin == 33:
            VALVE_STATE[2][1] = value
        if pin == 35:
            VALVE_STATE[3][1] = value

    elif topicparts[2] == "consumption":
        if DEBUG: print "Message type 'consumption' for pin " + str(pin) + " with value " + str(value)  
        if pin == 29:
            VALVE_STATE[0][2] = value
        if pin == 31:
            VALVE_STATE[1][2] = value
        if pin == 33:
            VALVE_STATE[2][2] = value
        if pin == 35:
            VALVE_STATE[3][2] = value

# End of MQTT callbacks


def cleanup(signum, frame):
    """
    Signal handler to ensure we disconnect cleanly
    in the event of a SIGTERM or SIGINT.
    """
    # Cleanup  modules
    MQTT.cleanup()
    lcd.clear()

    # Exit from application
    print "LCD daemon stopped"
    sys.exit(signum)


def loop():
    """
    The main loop in which we mow the lawn.
    """
    print 'LCD daemon startet'

    last_touched = cap.touched()

    global DISPLAYTYPE, DISPLAYON
    while True:
        time.sleep(0.08)
        output()
        current_touched = cap.touched()
        # Check each pin's last and current state to see if it was pressed or released.
        for i in range(12):
            # Each pin is represented by a bit in the touched value.  A value of 1
            # means the pin is being touched, and 0 means it is not being touched.
            pin_bit = 1 << i
            # First check if transitioned from not touched to touched.
            #if current_touched & pin_bit and not last_touched & pin_bit:
            #    print '{0} touched!'.format(i)
            # Next check if transitioned from touched to not touched.
            #if not current_touched & pin_bit and last_touched & pin_bit:
            #    print '{0} released!'.format(i)
        # Update last state and wait a short period before repeating.
        last_touched = current_touched

        buttonState = current_touched
        if DISPLAYON > 0: 
            DISPLAYON = DISPLAYON -1
        else:
            if DISPLAYON == 0: 
                if (VALVE_STATE[0][0] or VALVE_STATE[1][0] or VALVE_STATE[2][0] or VALVE_STATE[3][0]):
                    DISPLAYON = DISPLAYTIME
                else:
                    lcd.set_backlight(False)
                    DISPLAYON = -1

        for b in btn:
            if (buttonState & (1 << b[0])) != 0:
                if DEBUG: print 'Button pressed for GPIO ' + str(b[1])
                DISPLAYON = DISPLAYTIME
                lcd.set_backlight(True)
                if b[1] > 0: 
                    MQTT.mqttc.publish(MQTT_TOPIC + '/in/' + str(b[1]), abs(VALVE_STATE[b[2]][0]-1), qos=0, retain=True)
                    if DEBUG: print 'Sent ' + MQTT_TOPIC + '/in/' + str(b[1]), abs(VALVE_STATE[b[2]][0]-1)
                else:
                    DISPLAYTYPE = DISPLAYTYPE + 1
                    if DISPLAYTYPE == 3: DISPLAYTYPE = 0
                    lcd.set_cursor(0,0)
                    if DISPLAYTYPE == 0: lcd.message("Display         \nstate           ")
                    if DISPLAYTYPE == 1: lcd.message("Display         \nflow            ")
                    if DISPLAYTYPE == 2: lcd.message("Display         \nconsumption     ")
                    time.sleep(0.5)
                    output()
                time.sleep(.5)
                if DEBUG: print 'DISPLAYTYPE = ' + str(DISPLAYTYPE)
                break

# Use the signal module to handle signals
for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT]:
    signal.signal(sig, cleanup)

# Initialize the LCD
lcd = LCD.PCF_CharLCD(0, address=0x27, busnum=1, cols=16, lines=2)

# Clear display and show greeting, pause 1 sec
lcd.clear()
lcd.set_backlight(True)
lcd.message("Gartenwasser\nstartet...")
time.sleep(1)

# Create MPR121 instance.
cap = MPR121.MPR121()

print 'Adafruit MPR121 Capacitive Touch Sensor started'

# Initialize communication with MPR121 using default I2C bus of device, and
# default I2C address (0x5A).  On BeagleBone Black will default to I2C bus 0.
if not cap.begin():
    print 'Error initializing MPR121.  Check your wiring!'
    sys.exit(1)

# Init MQTT connections
MQTT.init()
print 'MQTT initiated'
MQTT.mqttc.on_message = on_message
MQTT.mqttc.subscribe(MQTT_TOPIC_IN, qos=MQTT_QOS)

# assign GPIO & Status index of VALVA_STATUS
btn = ((11, 29, 0),
       (10, 31, 1),
       (9, 33, 2),
       (8, 35, 3),
       (7, 0, 4))

# Start output of values
output()
# start main procedure
loop()
