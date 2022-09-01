import json
import os
import shared_objects
import gps_utils
import threading
import time
import resource
import commands
import wsqueue


def update_availability(clientid):
    wsqueue.WebsocketQueueThread.add_send({
        "cmd": "update_availability",
        "client_id": clientid,
    })


class HousekeepingThread(threading.Thread):

    def __init__(self, name=None):
        threading.Thread.__init__(self, name=name)
        self.value = None
        self.running = True

    def get_value(self):
        return self.value

    def shutdown(self):
        self.running = False

    def run(self):
        shared_objects.log.debug("starting up housekeeping thread")
        while self.running:
            # log program resource usage
            shared_objects.log.trace("program resource usage: {}".format(resource.getrusage(resource.RUSAGE_SELF)))
            wsqueue.WebsocketQueueThread.add_send({
                "cmd": "system_resource_usage",
                "usage": commands.system_info_object()
            })
            # check if client is connecte to server
            ws = shared_objects.get_websocket()
            wsqueue.WebsocketQueueThread.add_send({
                "cmd": "client_online",
                "status": 1 if ws is not None and ws.sock else 0,
                "start_time": shared_objects.get_start_time(),
                "up_time": shared_objects.get_uptime(),
                "priority": 10
            })
            # update availability record
            shared_objects.log.debug("update availability record")
            update_availability(shared_objects.config["uuid"]["id"])
            time.sleep(int(shared_objects.config["housekeeping"]["interval"]))
        shared_objects.log.debug("shutting down housekeeping thread")

