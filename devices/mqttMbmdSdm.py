""" Eastron SDM120 / SDM 220 for solaredge_meterproxy

    This file is intended to be used with https://github.com/nmakel/solaredge_meterproxy
    and is to be stored in the devices folder.

    It consumes MQTT messages which are provided via mbmd, see https://github.com/volkszaehler/mbmd
    Only for SDM120 / SDM220 so far. Feel free to extend it.

    Note: The sensor must be installed as counting the attached inverter as a load, not as a source.
    The grid must be connected on 1, the inverter on 2.
"""

import logging
import time

import paho.mqtt.client as mqtt

lastValues = {}
logger = logging.getLogger()
reconnect_delay = 10 # count of seconds between connection retries

def on_connect(client, userdata, flags, rc):
    logger.info(f"Connected to MQTT: {userdata['host']}:{userdata['port']}/{userdata['topic']}/{userdata['sensorname']}")
    client.subscribe(userdata["topic"]+"/status")
    client.subscribe(userdata["topic"]+"/"+userdata["sensorname"]+"/#")

def on_message(client, userdata, message):
    global lastValues

    logger.debug(f"MQTT message received: {message.topic}:{message.payload.decode('utf-8')}")

    topicmap = userdata['topicmap']
    if message.topic == userdata['topic']+"/status":
        if message.payload.decode("utf-8") == "connected":
            logger.debug(f"Logger Status is online")
        else:
            logger.debug(f"Logger Status is not online, setting power vlaues to 0")
            lastValues["power_active"] = 0
            lastValues["l1_power_active"] = 0
            lastValues["l1_current"] = 0
    elif message.topic in topicmap:
        logger.debug(f"message {message.topic} is in map")
        for entry in topicmap[message.topic]:
            lastValues[entry[0]] = float(message.payload) * entry[1]
            if "/Sum" in message.topic or "/Export" in message.topic:
                lastValues[entry[0]] += userdata["energy_offset"]
    else:
        logger.debug(f"MQTT ignored unknown topic {message.topic}")


def on_disconnect(client, userdata, rc):
    if rc != 0:
        logger.warning(f"MQTT disconnected unexpectedly: {rc}, trying to reconnect")
    while True:
        time.sleep(reconnect_delay)
        try:
            client.reconnect()
            logger.info(f"MQTT reconnected")
            return
        except Exception as err:
            logger.warning("MQTT reconnect failed (%s), retrying...", err)


def device(config):

    # Configuration parameters:
    #
    # host              ip or hostname of MQTT server
    # port              port of MQTT server
    # keepalive         keepalive time in seconds for MQTT server
    # topic             base topic of mbmd
    # sensorname        name of the sensor within mbmd (e.g. sdm2201-1 for the first sensor, tpye SDM220, bus id 1)
    # energy_offset     offset in kWh of the generated sensor (e.g. if the sensor and/or the inverter is used)

    host = config.get("host", fallback="localhost")
    port = config.getint("port", fallback=1883)
    keepalive = config.getint("keepalive", fallback=60)
    topic = config.get("topic", fallback="mbmd")
    sensorname = config.get("sensorname", fallback="sdm2201-1")
    energy_offset = float(config.get("energy_offset", fallback=float(0)))

    """ The topicmap is used for mapping the mbmd names to the one within the proxy.
        Per MQTT topic an array of proxy keys has to be given. The array entries are arrays again.
        The first value of the array is the name within the proxy, the second vlaue is a scaling
        factor. Set it to -1 to negate something. Currently not really needed, but who knows.
    """
    userdata = {
        "host": host,
        "port": port,
        "topic": topic,
        "sensorname": sensorname,
        "energy_offset": energy_offset,
        "topicmap":  {
            f"{topic}/{sensorname}/ApparentPower": [ ["power_apparent", 1] ],
            f"{topic}/{sensorname}/Current": [ ["l1_current", 1] ],
            f"{topic}/{sensorname}/Frequency": [ ["frequency", 1] ],
            f"{topic}/{sensorname}/Export": [ ["import_energy_active", 1], [ "l1_import_energy_active", 1] ],
            f"{topic}/{sensorname}/Power": [ ["power_active", -1], ["l1_power_active", -1] ],
            f"{topic}/{sensorname}/ReactivePower": [ ["power_reactive", -1 ] ],
            f"{topic}/{sensorname}/Sum": [ ["energy_active", 1], ["l1_energy_active", 1], ],
            f"{topic}/{sensorname}/Voltage": [ ["voltage_ln", 1], ["l1n_voltage", 1] ],
        }
    }

    connected = False
    while not connected:
        try:
            client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1, userdata=userdata)
            client.on_connect = on_connect
            client.on_message = on_message
            client.on_disconnect = on_disconnect

            client.connect(host, port, keepalive)
            client.loop_start()
            connected = True
        except Exception as err:
            logger.error(f"MQTT connection failed: {host}:{port}/{topic} ({err=}). Retrying in {reconnect_delay}s.")
            time.sleep(reconnect_delay)

    return {
        "client": client,
        "host": host,
        "port": port,
        "keepalive": keepalive,
        "topic": topic,
    }


def values(device):
    if not device:
        return {}

    return lastValues

    #  MQTT input is a json with one or more of the below elements
    # "energy_active"
    # "import_energy_active"
    # "power_active"
    # "l1_power_active"
    # "l2_power_active"
    # "l3_power_active"
    # "voltage_ln"
    # "l1n_voltage"
    # "l2n_voltage"
    # "l3n_voltage"
    # "voltage_ll"
    # "l12_voltage"
    # "l23_voltage"
    # "l31_voltage"
    # "frequency"
    # "l1_energy_active"
    # "l2_energy_active"
    # "l3_energy_active"
    # "l1_import_energy_active"
    # "l2_import_energy_active"
    # "l3_import_energy_active"
    # "export_energy_active"
    # "l1_export_energy_active"
    # "l2_export_energy_active"
    # "l3_export_energy_active"
    # "energy_reactive"
    # "l1_energy_reactive"
    # "l2_energy_reactive"
    # "l3_energy_reactive"
    # "energy_apparent"
    # "l1_energy_apparent"
    # "l2_energy_apparent"
    # "l3_energy_apparent"
    # "power_factor"
    # "l1_power_factor"
    # "l2_power_factor"
    # "l3_power_factor"
    # "power_reactive"
    # "l1_power_reactive"
    # "l2_power_reactive"
    # "l3_power_reactive"
    # "power_apparent"
    # "l1_power_apparent"
    # "l2_power_apparent"
    # "l3_power_apparent"
    # "l1_current"
    # "l2_current"
    # "l3_current"
    # "demand_power_active"
    # "minimum_demand_power_active"
    # "maximum_demand_power_active"
    # "demand_power_apparent"
    # "l1_demand_power_active"
    # "l2_demand_power_active"
    # "l3_demand_power_active"
