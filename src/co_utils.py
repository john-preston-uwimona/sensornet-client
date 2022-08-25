import serial
import threading
import shared_objects
import random
from datetime import datetime, timedelta
import serial.tools.list_ports


class Co2Poller(threading.Thread):

    def __init__(self, name=None, config={}):
        threading.Thread.__init__(self, name=name)
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
            self.ser = None
        self.current_value = 0
        self.running = True

    def get_port(self, location, default_port):
        ports = serial.tools.list_ports.comports()
        for p in ports:
            if location in p.hwid:
                shared_objects.log.info("connecting to port {} for CO2 device ".format(p.device))
                return p.device
        shared_objects.log.info("connecting to default port {} for CO2 device ".format(default_port))
        return default_port

    def get_current_value(self):
        return self.current_value

    def shutdown(self):
        self.running = False

    def run(self):
        while self.running:
            try:
                ser_bytes = self.ser.readline()
                # print(str(ser_bytes.decode()))
                # print(str(ser_bytes.decode()).split(" "))
                values = (str(ser_bytes.decode()).split(" "))
                if len(values) > 3:
                    self.current_value = int(str(ser_bytes.decode()).split(" ")[2])
            except ConnectionRefusedError as e:
                print("+++++++ ConnectionRefusedError")
                pass


def get_co2(co2p):
    co2_value = co2p.get_current_value()
    print("@@@@@@ CO2_VALUE @@@@", co2_value)
    # get random number to add to timestamp to avoid sensor 
    # timestamp collision in sensor data database
    ts = datetime.now() + timedelta(milliseconds=random.randint(0,1000))
    return {
        "value": co2_value,
        "units": shared_objects.config["sensors"]["co2"]["units"],
        "timestamp": ts.isoformat(),
    }
