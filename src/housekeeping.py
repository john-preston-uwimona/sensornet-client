import sensor_utils
import json
import os
import shared_objects
import gps_utils
import threading
import time


def send(ws, message):
    if ws.sock:
        shared_objects.log.trace(message)
        ws.send(message)


def update_availability(ws, clientid):
    send(ws, json.dumps({
        "cmd": "update_availability",
        "client_id": clientid,
    }))


class HousekeepingThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.value = None
        self.running = True

    def get_value(self):
        return self.value

    def shutdown(self):
        self.running = False

    def run(self):
        shared_objects.log.debug("starting up housekeeping thread")
        while self.running:
            shared_objects.log.debug("update availability record")
            ws = shared_objects.get_websocket()
            if ws is not None:
                update_availability(ws, shared_objects.config["uuid"]["id"])
            time.sleep(int(shared_objects.config["housekeeping"]["interval"]))
        shared_objects.log.debug("shutting down housekeeping thread")
