import time
import tracemalloc
import shared_objects
import os
import json
import client_api
import gps_utils
import modem_utils


tasks = {}
task = lambda f: tasks.setdefault(f.__name__, f)


def system_info_object():
    current, peak = tracemalloc.get_traced_memory()
    return {
        "current_memory": current,
        "peak_memory": peak,
        "os": "{}, release: {}, version: {}".format(os.uname().sysname, os.uname().release, os.uname().version),
        "start_time": shared_objects.get_start_time(),
        "running_time": shared_objects.get_uptime(),
        "id": shared_objects.config["uuid"]["id"],
        "name": shared_objects.config["uuid"]["name"],
        "description": shared_objects.config["uuid"]["description"],
        "sensors": shared_objects.config["sensors"],
        "interval": shared_objects.config["interval"],
        "system": shared_objects.config["system"]
    }


def run(request, gpsp=None):
    response = {}
    try:
        completed = False
        for t in tasks:
            if t == request["cmd"].replace("-", "_") and not completed:
                request["ts"] = time.perf_counter()
                response = tasks[t](request, gpsp)
                completed = True
        if not completed:
            response.update({
                "message": "Unknown command {}".format(request["cmd"]),
                "status": 1
            })
    except KeyError as e:
        response.update({
            "message": "{}".format(e),
            "status": 1
        })

    response.update({
        "cmd": request["cmd"],
        "uuid": request["uuid"],
        "broadcast_response": True,
        "recipient": request["sender"],
        "sender": request["sender"],
        "ts": (time.perf_counter() - request["ts"]) if "ts" in request else 0,
        "request": request,
    })
    return response


@task
def get_system_info(request, gpsp=None):
    return {
        "data": {
            "data": {**system_info_object(), **gps_utils.get_gps(gpsp)["value"]},
            "message": "OK",
            "status": 0
        },
        "message": "OK",
        "status": 0
    }


@task
def get_client_online_status(request, gpsp=None):
    return {
        "data": {
            "online": 1,
            "message": "",
            "status": 0
        },
        "message": "",
        "status": 0
    }


@task
def set_system_info(request, gpsp=None):
    # iterate through the request[metadata] keys
    for key0 in request["metadata"].keys():
        value0 = request["metadata"][key0]
        if isinstance(value0, dict):
            for key1 in request["metadata"][key0].keys():
                value1 = request["metadata"][key0][key1]
                shared_objects.config[key0].update({key1: value1})
                shared_objects.log.trace("updating client info - {}.{} = {}".format(key0, key1, value1))
        else:
            shared_objects.config.update({key0: value0})
            shared_objects.log.trace("updating client info - {} = {}".format(key0, value0))

    shared_objects.save_config()

    # update client name and description on server
    client_api.update_client_name_description(shared_objects.get_websocket(), shared_objects.config["uuid"])

    return {
        "data": {
            "data": system_info_object(),
            "message": "OK",
            "status": 0
        },
        "message": "OK",
        "status": 0
    }


@task
def get_modem_info(request, gpsp=None):
    modem = shared_objects.config["modem"]
    return {
        "data": {
            "data": {**modem_utils.get_modem_status(modem, shared_objects.config["modem"]["vnstat"])},
            "message": "OK",
            "status": 0
        },
        "message": "OK",
        "status": 0
    }


@task
def get_gps_info(request, gpsp=None):
    return {
        "data": {
            "data": gps_utils.get_gps_report(gpsp),
            "message": "OK",
            "status": 0
        },
        "message": "OK",
        "status": 0
    }
