#!/usr/bin/env python

__author__ = "Bernd Gewehr"

# import python libraries
import signal
import time
import sys
import RPi.GPIO as GPIO

# import libraries
import lib_mqtt as MQTT

DEBUG = False
#DEBUG = True

print 'GPIO daemon starting'

MQTT_TOPIC_IN = "/Gartenwasser/#"
MQTT_TOPIC = "/Gartenwasser"
MQTT_QOS = 0

MONITOR_REFRESH = "/Gartenwasser/refresh"

GPIO_OUTPUT_PINS = []
MONITOR_PINS = []

# Convert the list of strings to a list of ints.
# Also strips any whitespace padding
PINS = []
if MONITOR_PINS:
    PINS = map(int, MONITOR_PINS.split(","))

# Append a column to the list of PINS. This will be used to store state.
for PIN in PINS:
    PINS[PINS.index(PIN)] = [PIN, -1]

def on_message(mosq, obj, msg):
    """
    Handle incoming messages
    """
    if msg.topic == MONITOR_REFRESH:
        refresh()
        return

    topicparts = msg.topic.split("/")
    pin = int(topicparts[len(topicparts) - 1])
    try:
        value = int(float(msg.payload))
    except ValueError:
        value = 0

    if pin not in GPIO_OUTPUT_PINS:
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH)
        GPIO_OUTPUT_PINS.append(pin)
    if value == 1:
        GPIO.output(pin, GPIO.LOW)
    else:
        GPIO.output(pin, GPIO.HIGH)

# End of MQTT callbacks

def cleanup(signum, frame):
    """
    Signal handler to ensure we disconnect cleanly
    in the event of a SIGTERM or SIGINT.
    """
    # Cleanup  modules
    MQTT.cleanup()
    GPIO.cleanup()

    # Exit from application
    print "GPIO daemon stopped"
    sys.exit(signum)

def init_gpio():
    """
    Initialise the GPIO library
    """
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)

    for PIN in PINS:
        index = [y[0] for y in PINS].index(PIN[0])
        pin = PINS[index][0]
        GPIO.setup(pin, GPIO.IN)

def loop():
    """
    The main loop in which we mow the lawn.
    """
    print 'GPIO daemon started'
    while True:
        for PIN in PINS:
            index = [y[0] for y in PINS].index(PIN[0])
            pin = PINS[index][0]
            oldstate = PINS[index][1]
            newstate = GPIO.input(pin)
            if newstate != oldstate:
                mqttc.publish(MQTT_TOPIC_OUT % pin, payload=newstate, qos=MQTT_QOS, retain=MQTT_RETAIN)
                PINS[index][1] = newstate
        time.sleep(.8)


# Use the signal module to handle signals
for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT]:
    signal.signal(sig, cleanup)

# Initialise our libraries
MQTT.init()
print 'MQTT initiated'
MQTT.mqttc.on_message = on_message
MQTT.mqttc.subscribe(MQTT_TOPIC_IN, qos=MQTT_QOS)
init_gpio()
print 'GPIO initiated'

# start main procedure
loop()
