import threading
import shared_objects
import time
import gps_utils
import dht_utils
import co_utils
import wsqueue


class SensorProcessing(threading.Thread):
    def __init__(self, name=None, dhtDevicePin=None, gpsp=None, co2_device=None, portal=None):
        threading.Thread.__init__(self, name=name)
        self.running = True
        self.dhtDevicePin = dhtDevicePin
        self.gpsp = gpsp
        self.co2 = co2_device
        self.portal = portal

    def shutdown(self):
        self.running = False

    def run(self):
        shared_objects.log.debug("starting up sensor processing thread")
        while self.running:
            client = shared_objects.config["uuid"]["id"]
            wsqueue.WebsocketQueueThread.add_send({
                "cmd": "update_client_gps",
                "client": client,
                "reading": gps_utils.get_gps(self.gpsp)
            }, portal=self.portal, cache_message=True)

            for sensor in shared_objects.config["sensors"].keys():
                reading = self.get_sensor_reading(sensor, dhtDevicePin=self.dhtDevicePin, gpsp=self.gpsp, co2_device=self.co2)
                if reading is not None and "value" in reading and reading["value"] is not None:
                    wsqueue.WebsocketQueueThread.add_send({
                        "cmd": "put_sensor_reading",
                        "client": client,
                        "sensor": sensor,
                        "reading": reading
                    }, portal=self.portal, cache_message=True)
            time.sleep(int(shared_objects.config["interval"]))

        shared_objects.log.debug("shutting down sensor processing thread")

    def get_sensor_reading(self, sensor, dhtDevicePin=None, gpsp=None, co2_device=None):
        gps = gps_utils.get_gps(gpsp)
        if sensor == "temperature":
            return {**dht_utils.get_temperature(dhtDevicePin), **gps["value"]}
        elif sensor == "humidity":
            return {**dht_utils.get_humidity(dhtDevicePin), **gps["value"]}
        elif sensor == "co2":
            return {**co_utils.get_co2(co2_device), **gps["value"]}


