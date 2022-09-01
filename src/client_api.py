import sensor_utils
import json
import os
import shared_objects
import gps_utils
import dht_utils
import co_utils
import threading                                                                
import functools                                                                


def synchronized(wrapped):                                                      
    lock = threading.Lock()
    #shared_objects.log.trace("Instantiating re-entrant lock '{}' id {}".format(lock, id(lock)))
    @functools.wraps(wrapped)
    def _wrap(*args, **kwargs):
        with lock:
            shared_objects.log.trace("Calling '{}' with Lock {} from thread {}".format(
                                     wrapped.__name__, id(lock),
                                     threading.current_thread().name))
            result = wrapped(*args, **kwargs)
            shared_objects.log.trace("Done '{}' with Lock {} from thread {}".format(
                                     wrapped.__name__, id(lock),
                                     threading.current_thread().name))
            return result
    return _wrap


@synchronized
def send(message):
    s_message = json.dumps(message)
    ws = shared_objects.get_websocket()
    if ws is not None and ws.sock:
        shared_objects.log.debug(s_message)
        ws.send(s_message)
    else:
        shared_objects.log.debug("** websocket closed ** {}".format(s_message))


def ping():
    send({
        "cmd": "ping"
    })


def register_client(uuid):
    uname = os.uname()
    send({
        "cmd": "register_client",
        "uuid": uuid["id"],
        "name": uuid["name"],
        "description": uuid["description"],
        "reg_ts": uuid["timestamp"],
        "os": "{}, release: {}, version: {}".format(uname.sysname, uname.release, uname.version),
        "easting": uuid["easting"],
        "northing": uuid["northing"],
        "altitude": uuid["altitude"],
        "epsg": uuid["epsg"]
    })


def update_client_name_description(uuid):
    send({
        "cmd": "update_client_name_description",
        "uuid": uuid["id"],
        "name": uuid["name"],
        "description": uuid["description"],
    })


def send_sensor(client, sensor, dhtDevicePin=None, gpsp=None, co2_device=None, portal=None):
    reading = get_sensor_reading(sensor, dhtDevicePin=dhtDevicePin, gpsp=gpsp, co2_device=co2_device)
    if "value" in reading and reading["value"] is not None:
        send({
            "cmd": "put_sensor_reading",
            "client": client,
            "sensor": sensor,
            "reading": reading
        })
        if portal is not None:
            portal.broadcast_message({
                "cmd": "put_sensor_reading",
                "sensor": sensor,
                "reading": reading
            })


def update_gps(client, gpsp=None, portal=None):
    send({
        "cmd": "update_client_gps",
        "client": client,
        "reading": gps_utils.get_gps(gpsp)
    })
    if portal is not None:
        portal.broadcast_message({
            "cmd": "update_client_gps",
            "client": client,
            "reading": gps_utils.get_gps(gpsp)
        })


def get_sensor_reading(sensor, dhtDevicePin=None, gpsp=None, co2_device=None):
    gps = gps_utils.get_gps(gpsp)
    if sensor == "temperature":
        return {**dht_utils.get_temperature(dhtDevicePin), **gps["value"]}
    elif sensor == "humidity":
        return {**dht_utils.get_humidity(dhtDevicePin), **gps["value"]}
    elif sensor == "co2":
        return {**co_utils.get_co2(co2_device), **gps["value"]}


