import secrets
import sys
import tracemalloc
import websocket
import threading
import time
import shared_objects
import client_api
import housekeeping
import uuid
import json
import sensor_utils
import adafruit_dht
import gps_utils
import co_utils

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from commands import run
from datetime import datetime

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
else:
    shared_objects.log.debug("connecting client {}".format(shared_objects.config["uuid"]))

dhtDevice = adafruit_dht.DHT22(shared_objects.config["sensors"]["temperature"]["device_parameters"]["data_pin"])
# keep_running = True
# housekeeping_running = True
threads = {
    "co2": co_utils.Co2Poller(shared_objects.config["sensors"]["co2"]),
    "gpsp": gps_utils.GpsReader(shared_objects.config["gps"]),
    "sensors": [],
    "housekeeping": housekeeping.HousekeepingThread()
}
for sensor in shared_objects.config["sensors"].keys():
    threads["sensors"].append(sensor_utils.SensorProcessing(sensor, dht_device=dhtDevice,
                                                            gpsp=threads["gpsp"],
                                                            co2_device=threads["co2"]))

# start all threads
for k, th in threads.items():
    if k == "sensors":
        for t in th:
            t.start()
    else:
        th.start()


class ConfigFileChangedHandler(FileSystemEventHandler):
    def on_modified(self, event):
        shared_objects.load_config()
        shared_objects.log.debug("reloading config due to file modification event.")


def on_message(wsock, message):
    try:
        rq = json.loads(message)
        # filter responses
        if "broadcast" in rq:
            # log this message which was sent by the server to the client
            shared_objects.log.info("request: {}".format(json.dumps(rq)))
            # process the request
            response = run(rq, threads["gpsp"])
            # return response
            client_api.send(wsock, json.dumps(response))
            shared_objects.log.info("response {}".format(json.dumps(response)))
        else:
            # log this message which was generated internally
            shared_objects.log.info("local {}".format(json.dumps(rq)))
    except json.decoder.JSONDecodeError as e:
        shared_objects.log.error("{}".format(e))


def on_error(wsock, error):
    shared_objects.log.error("Websocket Error - {}".format(error))


def on_close(wsock, close_status_code, close_msg):
    # update shared websocket object
    shared_objects.set_websocket(None)


def on_open(wsock):
    client_api.register_client(wsock, shared_objects.config["uuid"])
    # wait a while for the registration to be updated
    time.sleep(2)
    # set shared websocket object
    shared_objects.set_websocket(wsock)


if __name__ == "__main__":
    websocket.enableTrace(False)
    while True:
        try:
            event_handler = ConfigFileChangedHandler()
            observer = Observer()
            observer.schedule(event_handler, path=shared_objects.CONFIG_PATH, recursive=False)
            observer.start()

            shared_objects.log.debug("connecting to server {}".format(shared_objects.config["server"]["websocket"]))
            shared_objects.initialise_uptime()
            ws = websocket.WebSocketApp(shared_objects.config["server"]["websocket"],
                                        on_open=on_open,
                                        on_message=on_message,
                                        on_error=on_error,
                                        on_close=on_close)
            ws.run_forever()

            shared_objects.log.error("connection to server {} lost. Waiting {} seconds to reconnect to server.".format(
                shared_objects.config["server"]["websocket"], shared_objects.config["interval"]))

            time.sleep(int(shared_objects.config["interval"]) + 10)
        except KeyboardInterrupt:
            # shutdown all threads
            for k, th in threads.items():
                if k == "sensors":
                    for t in th:
                        t.shutdown()
                else:
                    th.shutdown()
            sys.exit()
