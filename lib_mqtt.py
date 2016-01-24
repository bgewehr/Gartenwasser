#!/usr/bin/env python

__author__ = "Ben Jones and Bernd Gewehr"
__copyright__ = "Copyright (C) Ben Jones"

import logging
import os
import signal
import sys
import time
import paho.mqtt.client as mqtt
import random

# Initialize variables
APPNAME = os.path.splitext(os.path.basename(__file__))[0]
LOGFILE = os.getenv('LOGFILE', APPNAME + '.log')

DEBUG = False

MQTT_HOST = "localhost"
MQTT_PORT = 1883
# MQTT_CLIENT_ID = "RPiMower"
MQTT_CLIENT_ID = APPNAME + "_%d" % os.getpid()
MQTT_QOS = 0
MQTT_RETAIN = False
MQTT_CLEAN_SESSION = True
MQTT_LWT = "/clients/RPiMower"

# Create the MQTT client
def init():
    global mqttc
    mqttc = mqtt.Client(MQTT_CLIENT_ID, clean_session=MQTT_CLEAN_SESSION)
    connect()

# MQTT callbacks
def on_connect(mosq, obj, result_code):
    """
    Handle connections (or failures) to the broker.
    This is called after the client has received a CONNACK message
    from the broker in response to calling connect().
    The parameter rc is an integer giving the return code:

    0: Success
    1: Refused . unacceptable protocol version
    2: Refused . identifier rejected
    3: Refused . server unavailable
    4: Refused . bad user name or password (MQTT v3.1 broker only)
    5: Refused . not authorised (MQTT v3.1 broker only)
    """
    if result_code == 0:
        logging.info("Connected to %s:%s" % (MQTT_HOST, MQTT_PORT))

        # Subscribe to our incoming topic
        #  mqttc.subscribe(MQTT_TOPIC_IN, qos=MQTT_QOS)
        
        # Publish retained LWT as per http://stackoverflow.com/questions/19057835/how-to-find-connected-mqtt-client-details/19071979#19071979
        # See also the will_set function in connect() below
        mqttc.publish(MQTT_LWT, "1", qos=0, retain=True)

    elif result_code == 1:
        logging.info("Connection refused - unacceptable protocol version")
    elif result_code == 2:
        logging.info("Connection refused - identifier rejected")
    elif result_code == 3:
        logging.info("Connection refused - server unavailable")
    elif result_code == 4:
        logging.info("Connection refused - bad user name or password")
    elif result_code == 5:
        logging.info("Connection refused - not authorised")
    else:
        logging.warning("Connection failed - result code %d" % (result_code))

def on_disconnect(mosq, obj, result_code):
    """
    Handle disconnections from the broker
    """
    if result_code == 0:
        logging.info("Clean disconnection from broker")
    else:
        logging.info("Broker connection lost. Retrying in 5s...")
        time.sleep(5)

# End of MQTT callbacks

def cleanup():
    """
    Ensure we disconnect cleanly
    """
    # Publish our LWT and cleanup the MQTT connection
    logging.info("Disconnecting from broker...")
    mqttc.publish(MQTT_LWT, "0", qos=0, retain=True)
    mqttc.disconnect()
    mqttc.loop_stop()

def connect():
    """
    Connect to the broker, define the callbacks, and subscribe
    This will also set the Last Will and Testament (LWT)
    The LWT will be published in the event of an unclean or
    unexpected disconnection.
    """
    # Add the callbacks
    mqttc.on_connect = on_connect
    mqttc.on_disconnect = on_disconnect

    # Set the Last Will and Testament (LWT) *before* connecting
    mqttc.will_set(MQTT_LWT, payload="0", qos=0, retain=True)

    # Attempt to connect
    logging.debug("Connecting to %s:%d..." % (MQTT_HOST, MQTT_PORT))
    try:
        mqttc.connect(MQTT_HOST, MQTT_PORT, 60)
    except Exception, e:
        logging.error("Error connecting to %s:%d: %s" % (MQTT_HOST, MQTT_PORT, str(e)))
        sys.exit(2)

    # Let the connection run forever
    mqttc.loop_start()
