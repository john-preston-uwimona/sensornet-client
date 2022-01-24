import os
import shelve
import json
import logging
import humanize
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

config = None
root = None
log = None
cache = None

uptime = datetime.now()
ws = None
CONFIG_PATH = 'config/config.json'


def trace(self, message, *args, **kws):
    if self.isEnabledFor(5):
        self._log(5, message, args, **kws)


def set_websocket(wsock):
    global ws
    ws = wsock


def get_websocket():
    global ws
    return ws


def initialise_uptime():
    global uptime
    uptime = datetime.now()


def get_start_time():
    global uptime
    return uptime.isoformat()


def get_uptime():
    global uptime
    elapsed = datetime.now() - uptime
    return humanize.precisedelta(elapsed.total_seconds())


def get_level_number(level):
    return {
        'trace': 5,
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL,
    }.get(level.lower(), logging.INFO)


def get_level_name(level):
    return {
        5: 'trace',
        logging.DEBUG: 'debug',
        logging.INFO: 'info',
        logging.WARNING: 'warning',
        logging.ERROR: 'error',
        logging.CRITICAL: 'critical',
    }.get(level, "unknown")


def get_root_path():
    global root
    return root


def human_size(bsize, units=[' bytes','KB','MB','GB','TB', 'PB', 'EB']):
    """ Returns a human readable string representation of bytes """
    return str(bsize) + units[0] if bsize < 1024 else human_size(bsize >> 10, units[1:])


def init():
    global config
    global log
    global root
    # define root path
    root = os.path.dirname(os.path.abspath(__file__))
    # load config
    load_config()
    # with open(config_file_path) as json_file:
    #     config = json.load(json_file)
    # add log level
    logging.TRACE = 5  # between NOSET and DEBUG
    logging.addLevelName(logging.TRACE, "TRACE")
    logging.Logger.trace = trace
    log = logging.getLogger('SENSORNET')
    # set default level
    log.setLevel(get_level_number(config["logger"]["level"]))
    # create file handler which logs even debug messages
    fh = TimedRotatingFileHandler(os.path.join(config["logger"]["logDirectory"], config["logger"]["logFile"]),
                                  when="midnight")
    # fh = TimedRotatingFileHandler(os.path.join(config["logger"]["logDirectory"], config["logger"]["logFile"]),
    #                               when="D", backupCount=1000)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.TRACE)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('[%(asctime)s][%(levelname)s][%(module)s][%(funcName)s:%(lineno)d] %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    log.addHandler(fh)
    log.addHandler(ch)
    log.info("****************************************")
    log.info("*** Started logging with level {} ***".format(logging.getLevelName(log.getEffectiveLevel())))
    log.info("****************************************")
    # open/create cache
    global cache
    cache = shelve.open(os.path.join(root, "cache"))


def load_config():
    global config
    # load and parse config
    with open(CONFIG_PATH) as json_file:
        config = json.load(json_file)


def save_config():
    global config
    # save config to disk
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def close_cache():
    global cache
    cache.close()


def get_cache(key, missing_value=None):
    global cache
    if key in cache:
        return cache[key]
    else:
        return missing_value


def put_cache(key, value):
    global cache
    cache[key] = value
    return cache[key]

