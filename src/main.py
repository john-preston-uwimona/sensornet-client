import secrets
import sys
import tracemalloc
import websocket
import threading
import time
import shared_objects
import housekeeping
import wsqueue
import uuid
import json
import sensor_utils
import Adafruit_DHT
import gps_utils
import co_utils
import portal
import websocket_utils

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Event
from datetime import datetime
from threading import Event

tracemalloc.start()

# initialise shared objects
shared_objects.init()

if not shared_objects.config["uuid"]["id"]:
    shared_objects.config["uuid"].update(
        {"id": "{}-{}".format(shared_objects.config["uuid"]["prefix"], secrets.token_hex(8))})
    shared_objects.config["uuid"].update({"timestamp": datetime.now().isoformat()})
    if not shared_objects.config["uuid"]["name"]:
        shared_objects.config["uuid"].update({"name": "default"})
    if not shared_objects.config["uuid"]["description"]:
        shared_objects.config["uuid"].update({"description": "-"})
    if not shared_objects.config["uuid"]["easting"]:
        shared_objects.config["uuid"].update({"easting":
                                             shared_objects.config["gps"]["fixed_location_value"]["lon"]
                                             if shared_objects.config["gps"]["fixed_location"] == "true" else "0"})
    if not shared_objects.config["uuid"]["northing"]:
        shared_objects.config["uuid"].update({"northing":
                                              shared_objects.config["gps"]["fixed_location_value"]["lat"]
                                              if shared_objects.config["gps"]["fixed_location"] == "true" else "0"})
    if not shared_objects.config["uuid"]["altitude"]:
        shared_objects.config["uuid"].update({"altitude":
                                              shared_objects.config["gps"]["fixed_location_value"]["alt"]
                                              if shared_objects.config["gps"]["fixed_location"] == "true" else "0"})
    shared_objects.log.debug("initialising new client {}".format(shared_objects.config["uuid"]))

    shared_objects.save_config()

# Portal
portal = portal.Portal()
#
wsq = wsqueue.WebsocketQueueThread(name="WEBSOCKET_SEND_QUEUE", portal=portal)
wsq.daemon = True
wsq.start()

# dhtDevice = Adafruit_DHT.DHT22(Adafruit_DHT.DHT22, shared_objects.config["sensors"]["temperature"]["device_parameters"]["data_pin"])
dhtDevicePin = None
#shared_objects.config["sensors"]["temperature"]["device_parameters"]["data_pin"]

threads = {}
threads["co2"] = co_utils.Co2Poller(name="CO2", config=shared_objects.config["sensors"]["co2"])
threads["gpsp"] = gps_utils.GpsReader(name="GPSP", config=shared_objects.config["gps"])
threads["sensors"] = sensor_utils.SensorProcessing(name="SENSORS",
                                                   dhtDevicePin=dhtDevicePin,
                                                   gpsp=threads["gpsp"],
                                                   co2_device=threads["co2"],
                                                   portal=portal)
threads["housekeeping"] = housekeeping.HousekeepingThread(name="HOUSEKEEPING",)
threads["websocket"] = websocket_utils.WebsocketThread(name="WEBSOCKET")

threads["websocket"].setThreads(threads)
portal.setThreads(threads)
# for sensor in shared_objects.config["sensors"].keys():
#    threads["sensors"].append(sensor_utils.SensorProcessing(sensor, dhtDevicePin=dhtDevicePin,
#                                                            gpsp=threads["gpsp"],
#                                                            co2_device=threads["co2"],
#                                                            portal=portal))

# start all threads
for k, th in threads.items():
    th.daemon = True
    th.start()


class ConfigFileChangedHandler(FileSystemEventHandler):
    def on_modified(self, event):
        shared_objects.load_config()
        shared_objects.log.debug("reloading config due to file modification event.")

event_handler = ConfigFileChangedHandler()
observer = Observer()
observer.schedule(event_handler, path=shared_objects.CONFIG_PATH, recursive=False)
observer.start()


if __name__ == "__main__":
    while True:
        try:
            Event().wait()
        except KeyboardInterrupt:
            # shutdown all threads
            for k, th in threads.items():
                if k == "sensors":
                    for t in th:
                        t.shutdown()
                else:
                    th.shutdown()
        finally:
            sys.exit()

