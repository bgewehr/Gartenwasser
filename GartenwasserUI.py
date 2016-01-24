#!/usr/bin/python

__author__ = "Bernd Gewehr"

# import python libraries
import signal
import time
import sys

# import libraries
import lib_mqtt as MQTT
from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate

sys.sterr = sys.stdout

DEBUG = False
#DEBUG = True

MQTT_TOPIC_IN = "/Gartenwasser/#"
MQTT_TOPIC = "/Gartenwasser"
MQTT_QOS = 0

VALVE_STATE = [0, 0, 0, 0, 0]

def on_message(mosq, obj, msg):
    """
    Handle incoming messages
    """
    topicparts = msg.topic.split("/")
    
    if DEBUG:
       print msg.topic
       print topicparts
       for i in range(0,len(topicparts)):
           print i, topicparts[i]
       print msg.payload
	
    pin = int('0' + topicparts[len(topicparts) - 1])
    value = int(msg.payload)

    if topicparts[2] == "in":
        if pin == 29:
            VALVE_STATE[0] = value
        if pin == 31:
            VALVE_STATE[1] = value
        if pin == 33:
            VALVE_STATE[2] = value
        if pin == 35:
            VALVE_STATE[3] = value

    Message = 'V1: ' + str(VALVE_STATE[0]) + ' V2: ' + str(VALVE_STATE[1]) + '\nV3: ' + str(VALVE_STATE[2]) + ' V4: ' + str(VALVE_STATE[3])
    lcd.clear()
    lcd.message(Message)


# End of MQTT callbacks


def cleanup(signum, frame):
    """
    Signal handler to ensure we disconnect cleanly
    in the event of a SIGTERM or SIGINT.
    """
    # Cleanup  modules
    MQTT.cleanup()
    lcd.stop()

    # Exit from application
    sys.exit(signum)


def loop():
    """
    The main loop in which we mow the lawn.
    """
    while True:
        time.sleep(0.08)
        buttonState = lcd.buttons()
        for b in btn:
            if (buttonState & (1 << b[0])) != 0:
                if DEBUG: print 'Button pressed for GPIO ' + str(b[1])
                if b[1] > 0: MQTT.mqttc.publish(MQTT_TOPIC + '/in/' + str(b[1]), abs(VALVE_STATE[b[2]]-1), qos=0, retain=True)
                time.sleep(.5)
                break



# Use the signal module to handle signals
for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT]:
    signal.signal(sig, cleanup)

# Initialise our libraries
lcd = Adafruit_CharLCDPlate()
lcd.backlight(True)

MQTT.init()
MQTT.mqttc.on_message = on_message
MQTT.mqttc.subscribe(MQTT_TOPIC_IN, qos=MQTT_QOS)

# Clear display and show greeting, pause 1 sec
lcd.clear()
lcd.message("Gartenwasser\nstartet...")
time.sleep(1)
Message = 'V1: ' + str(VALVE_STATE[0]) + ' V2: ' + str(VALVE_STATE[1]) + '\nV3: ' + str(VALVE_STATE[2]) + ' V4: ' + str(VALVE_STATE[3])
lcd.clear()
lcd.message(Message)

# Cycle through backlight colors
#col = (lcd.RED, lcd.YELLOW, lcd.GREEN, lcd.TEAL,
#       lcd.BLUE, lcd.VIOLET, lcd.WHITE, lcd.OFF)
#for c in col:
#    lcd.ledRGB(c)
#   sleep(.5)

# assign GPIO & Status index of VALVA_STATUS

btn = ((lcd.LEFT, 29, 0),
       (lcd.UP, 31, 1),
       (lcd.DOWN, 33, 2),
       (lcd.RIGHT, 35, 3),
       (lcd.SELECT, 0, 4))

# start main procedure
loop()
