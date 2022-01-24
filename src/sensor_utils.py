import gps_utils
import dht_utils
import co_utils
import threading
import shared_objects
import client_api
import time


class SensorProcessing(threading.Thread):
    def __init__(self, sensor, dht_device=None, gpsp=None, co2_device=None):
        threading.Thread.__init__(self)
        self.sensor = sensor
        self.running = True
        self.dht_device = dht_device
        self.gpsp = gpsp
        self.co2 = co2_device

    def shutdown(self):
        self.running = False

    def run(self):
        shared_objects.log.debug("starting up {} sensor processing thread".format(self.sensor))
        while self.running:
            wsock = shared_objects.get_websocket()
            if wsock is not None:
                client_api.update_gps(wsock, shared_objects.config["uuid"]["id"], gpsp=self.gpsp)
                client_api.send_sensor(wsock, shared_objects.config["uuid"]["id"],
                                       self.sensor, dht_device=self.dht_device, gpsp=self.gpsp,
                                       co2_device=self.co2)
            time.sleep(int(shared_objects.config["sensors"][self.sensor]["interval"]))

        shared_objects.log.debug("shutting down {} sensor processing thread".format(self.sensor))


def get_sensor_reading(sensor, dht_device=None, gpsp=None, co2_device=None):
    gps = gps_utils.get_gps(gpsp)
    if sensor == "temperature":
        return {**dht_utils.get_temperature(dht_device), **gps["value"]}
    elif sensor == "humidity":
        return {**dht_utils.get_humidity(dht_device), **gps["value"]}
    elif sensor == "co2":
        return {**co_utils.get_co2(co2_device), **gps["value"]}
