from datetime import datetime
from gps import *
import threading
import shared_objects
import serial
import serial.tools.list_ports


# session = None


class GpsReader(threading.Thread):

    def __init__(self, name=None, config={}):
        threading.Thread.__init__(self, name=name)
        self.current_value = None
        self.current_gpgga = None
        self.running = True
        self.fixed_location = False
        self.config = config
        if config["fixed_location"] == "true":
            self.fixed_location = True
            self.current_value = config["fixed_location_value"]
        else:
            try:
                self.ser = serial.Serial(
                    self.get_port(config["device_parameters"]["location"], config["device_parameters"]["port"]),
                    baudrate=config["device_parameters"]["baudrate"],
                    bytesize=config["device_parameters"]["bytesize"],
                    parity=config["device_parameters"]["parity"],
                    stopbits=config["device_parameters"]["stopbits"],
                    timeout=None,
                    xonxoff=True if config["device_parameters"]["xonxoff"] == "true" else False)
                self.ser.flushInput()
            except ConnectionRefusedError as e:
                print(e)

    def get_port(self, location, default_port):
        ports = serial.tools.list_ports.comports()
        for p in ports:
            if location in p.hwid:
                shared_objects.log.info("connecting to port {} for GPS device ".format(p.device))
                return p.device
        shared_objects.log.info("connecting to default port {} for GPS device ".format(default_port))
        return default_port

    def get_current_value(self):
        return self.current_value

    def get_current_record(self):
        return self.current_value if self.config["fixed_location"] == "true" else self.current_gpgga

    def shutdown(self):
        self.running = False

    def dms2dd(self, degrees, minutes, seconds, direction):
        dd = float(degrees) + float(minutes) / 60 + (float(seconds) * 60) / 60
        if direction == 'W' or direction == 'S':
            dd *= -1
        return dd

    def parse_ggga_record(self, record):
        rec_dict = {}
        # parse latitude
        rec_dict["lat"] = self.dms2dd(record[2][0:2], record[2][2:4], record[2][4:], record[3])
        # parse longitude
        rec_dict["lon"] = self.dms2dd(record[4][0:3], record[4][3:5], record[4][5:], record[5])
        # parse altitude
        rec_dict["alt"] = float(record[9])
        return rec_dict

    def run(self):
        while self.running:
            if self.fixed_location:
                time.sleep(2)
            else:
                try:
                    ser_bytes = self.ser.readline()
                    print("+++++", str(ser_bytes))
                    print("-----", str(ser_bytes.decode()).split(","))
                    values = (str(ser_bytes.decode()).split(","))
                    # values = "$GPGGA,200053.000,1800.1861,N,07645.6552,W,2,05,2.2,174.2,M,-23.7,M,2.0,0000".split(",")
                    if values[0] == "$GPGGA":
                        self.current_gpgga = values
                        # first choice record
                        # r = str(ser_bytes.decode()).split(",")
                        print(">>>", values)
                        # only accept a valid record
                        if values[6] != "0":
                            gpgga = self.parse_ggga_record(values)
                            print("%%% GPGGA %%%", gpgga)
                            self.current_value = gpgga
                    # elif values[0] == "$GPRMC":
                    #     # second choice record
                    #     # r = str(ser_bytes.decode()).split(",")
                    #     print(">>>", values)
                    #     # only accept a valid record
                    #     if values[2] == "A":
                    #         pass
                except ConnectionRefusedError as e:
                    print("+++++++ ConnectionRefusedError")
                    pass


class GpsPoller(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        try:
            self.session = gps(mode=WATCH_ENABLE)
        except ConnectionRefusedError as e:
            print(e)
            self.session = None
        self.current_value = None
        self.running = True

    def get_current_value(self):
        return self.current_value

    def shutdown(self):
        self.running = False

    def run(self):
        while self.running:
            try:
                self.session = gps(mode=WATCH_ENABLE)
                while True:
                    report = self.session.next()
                    print(">>>>>>>>>>", report)
                    if report["class"] == "DEVICE":
                        self.session.close()
                        self.session = gps(mode=WATCH_ENABLE)
                    elif report["class"] == "TPV":
                        self.current_value = report
            except StopIteration as s:
                print("+++++++ StopIteration")
            except ConnectionRefusedError as e:
                print("+++++++ ConnectionRefusedError")


def get_gps_report(gpsp):
    report = gpsp.get_current_record()
    return {
        "report": {} if report is None else report,
        "timestamp": datetime.now().isoformat()
    }


def get_gps(gpsp):
    report = gpsp.get_current_value()
    shared_objects.log.info("GPS report {}".format(report))
    # print("@@@@@@ CACHE(lon) REPORT @@@@@@", shared_objects.get_cache("lon"))
    # print("@@@@@@ CACHE(lat) REPORT @@@@@@", shared_objects.get_cache("lat"))
    # print("@@@@@@ CACHE(alt) REPORT @@@@@@", shared_objects.get_cache("alt"))

    # save in cache
    if report is not None:
        shared_objects.put_cache('lon', report["lon"] if "lon" in report else 0)
        shared_objects.put_cache('lat', report["lat"] if "lat" in report else 0)
        shared_objects.put_cache('alt', report["alt"] if "alt" in report else 0)

    return {
        "value": {
            "easting": report["lon"] if report is not None else shared_objects.get_cache("lon", 0),
            "northing": report["lat"] if report is not None else shared_objects.get_cache("lat", 0),
            "altitude": report["alt"] if report is not None else shared_objects.get_cache("alt", 0),
            "cachedgps": 0 if report is not None else 1 if shared_objects.get_cache("lon", None) is not None else 0,
            "epsg": "wgs84"
        },
        "timestamp": datetime.now().isoformat()
    }


