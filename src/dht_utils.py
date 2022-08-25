from datetime import datetime, timedelta
import random
import shared_objects
import Adafruit_DHT


def get_temperature(dhtDevicePin=None):
    temperature_c = "None"
    try:
        humidity, temperature_c = Adafruit_DHT.read(Adafruit_DHT.DHT22, dhtDevicePin)
    except RuntimeError as e:
        shared_objects.log.error("{}".format(e))
    # print(">>>>>>>>  TEMPERATURE  >>>>>>>>", temperature_c)
    # get random number to add to timestamp to avoid sensor 
    # timestamp collision in sensor data database
    ts = datetime.now() + timedelta(milliseconds=random.randint(0,1000))
    return {
        "value": temperature_c,
        "units": shared_objects.config["sensors"]["temperature"]["units"],
        "timestamp": ts.isoformat(),
    }


def get_humidity(dhtDevicePin=None):
    humidity = "None"
    try:
        humidity, temperature_c = Adafruit_DHT.read(Adafruit_DHT.DHT22, dhtDevicePin)
    except RuntimeError as e:
        shared_objects.log.error("{}".format(e))
    # print(">>>>>>>>  HUMIDITY  >>>>>>>>", humidity)
    # get random number to add to timestamp to avoid sensor 
    # timestamp collision in sensor data database
    ts = datetime.now() + timedelta(milliseconds=random.randint(0,1000))
    return {
        "value": humidity,
        "units": shared_objects.config["sensors"]["humidity"]["units"],
        "timestamp": ts.isoformat(),
    }
