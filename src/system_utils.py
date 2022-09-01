import subprocess
import json


def get_system_status():
    # getting system status
    useless_cat_call = subprocess.Popen(["/usr/local/bin/rpi-health.sh"],
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, text=True)
    output1, errors1 = useless_cat_call.communicate()
    useless_cat_call.wait()
    print("RPI-HEALTH>>", output1)
    print(">>", errors1)

    # getting system battery status
    useless_cat_call = subprocess.Popen(["/usr/bin/python3.9", "/usr/local/bin/x708.py"],
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, text=True)
    output2, errors2 = useless_cat_call.communicate()
    useless_cat_call.wait()
    print("BATTERY>>", output2)
    print(">>", errors2)

    return {"system": {**json.loads(output1), **json.loads(output2)}}

def get_wpa_status():
    # getting wpa status
    wpa = {"networks": [], "current_network": "", "ip": "", "mac": "", "key_mgmt": "", "wpa_state": "", "freq": 0}
    useless_cat_call = subprocess.Popen(["/usr/sbin/wpa_cli", "list_networks"],
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, text=True)
    output1, errors1 = useless_cat_call.communicate()
    useless_cat_call.wait()
    # print("WPA>>", output1)
    # print(">>", errors1)
    for line in output1.split("\n"):
        if line.rstrip()[0:1].isdigit():
            p = line.rstrip().split("\t")
            wpa["networks"].append(p[1])
            if len(p) > 3 and "current" in p[3].lower():
                wpa["current_network"] = p[1]


    # getting system battery status
    useless_cat_call = subprocess.Popen(["/usr/sbin/wpa_cli", "-i", "wlan0", "status"],
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, text=True)
    output2, errors2 = useless_cat_call.communicate()
    useless_cat_call.wait()
    # print("BATTERY>>", output2)
    # print(">>", errors2)
    for line in output2.split("\n"):
        if "=" in line:
            p = line.split("=")
            if p[0] == "ssid":
                wpa["current_network"] = p[1]
            elif p[0] == "ip_address":
                wpa["ip"] = p[1]
            elif p[0] == "address":
                wpa["mac"] = p[1]
            elif p[0] == "key_mgmt":
                wpa["key_mgmt"] = p[1]
            elif p[0] == "wpa_state":
                wpa["wpa_state"] = p[1]
            elif p[0] == "freq":
                wpa["freq"] = int(p[1])

    return {"wpa": {**wpa}}
