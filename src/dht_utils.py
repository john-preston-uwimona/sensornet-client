from datetime import datetime
import random
import shared_objects


def get_temperature(dht_device=None):
    temperature_c = "None"
    if dht_device is not None:
        try:
            temperature_c = dht_device.temperature
        except RuntimeError as e:
            shared_objects.log.error("{}".format(e))
    print(">>>>>>>>  TEMPERATURE  >>>>>>>>", temperature_c)
    return {
        "value": temperature_c,
        "units": shared_objects.config["sensors"]["temperature"]["units"],
        "timestamp": datetime.now().isoformat(),
    }


def get_humidity(dht_device=None):
    humidity = "None"
    if dht_device is not None:
        try:
            humidity = dht_device.humidity
        except RuntimeError as e:
            shared_objects.log.error("{}".format(e))
    print(">>>>>>>>  HUMIDITY  >>>>>>>>", humidity)
    return {
        "value": humidity,
        "units": shared_objects.config["sensors"]["humidity"]["units"],
        "timestamp": datetime.now().isoformat(),
    }
