import sensor_utils
import json
import os
import shared_objects
import gps_utils


def send(ws, message):
    if ws is not None and ws.sock:
        shared_objects.log.trace(message)
        ws.send(message)


def ping(ws):
    send(ws, json.dumps({
        "cmd": "ping"
    }))


def register_client(ws, uuid):
    uname = os.uname()
    send(ws, json.dumps({
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
    }))


def update_client_name_description(ws, uuid):
    send(ws, json.dumps({
        "cmd": "update_client_name_description",
        "uuid": uuid["id"],
        "name": uuid["name"],
        "description": uuid["description"],
    }))


def send_sensor(ws, client, sensor, dht_device=None, gpsp=None, co2_device=None):
    reading = sensor_utils.get_sensor_reading(sensor, dht_device=dht_device, gpsp=gpsp, co2_device=co2_device)
    if "value" in reading and reading["value"] is not None:
        send(ws, json.dumps({
            "cmd": "put_sensor_reading",
            "client": client,
            "sensor": sensor,
            "reading": reading
        }))


def update_gps(ws, client, gpsp=None):
    send(ws, json.dumps({
        "cmd": "update_client_gps",
        "client": client,
        "reading": gps_utils.get_gps(gpsp)
    }))
