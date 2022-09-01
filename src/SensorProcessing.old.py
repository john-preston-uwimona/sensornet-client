import threading
import shared_objects
import client_api
import time


class SensorProcessing(threading.Thread):

    def __init__(self, wsock, sensor):
        threading.Thread.__init__(self)
        self.wsock = wsock
        self.sensor = sensor
        self.running = True

    def stop_thread(self):
        self.running = False

    def run(self):
        shared_objects.log.debug("starting up sensor processing thread")
        while self.running:
            client_api.update_gps(self.wsock, shared_objects.config["uuid"]["id"])
            client_api.send_sensor(self.wsock, shared_objects.config["uuid"]["id"], self.sensor)
            time.sleep(int(shared_objects.config["interval"]))

        shared_objects.log.debug("shutting down {} sensor processing thread".format(self.sensor))

