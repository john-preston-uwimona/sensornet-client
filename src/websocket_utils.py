import threading
import shared_objects
import websocket
import json
import time
import sys
import os
import wsqueue

from commands import run


class WebsocketThread(threading.Thread):

    def __init__(self, name=None):
        threading.Thread.__init__(self, name=name)
        self.running = True
        self.ws = None
        self.threads = None

    def setThreads(self, threads):
        self.threads = threads

    def shutdown(self):
        self.running = False

    def on_message(self, wsock, message):
        try:
            rq = json.loads(message)
            # filter responses
            if "broadcast" in rq:
                # log this message which was sent by the server to the client
                shared_objects.log.info("request: {}".format(json.dumps(rq)))
                # process the request
                response = run(rq, self.threads["gpsp"])
                # return response
                wsock.send(json.dumps(response))
                shared_objects.log.info("response {}".format(json.dumps(response)))
            else:
                wsqueue.WebsocketQueueThread.add_response(rq)
        except json.decoder.JSONDecodeError as e:
            shared_objects.log.error("{}".format(e))

    def on_error(self, wsock, error):
        shared_objects.log.error("Websocket Error, Closing socket - {}".format(error))
        # raise RuntimeError from error
        # self.running = False
        # sys.exit()
        wsock.close()

    def on_close(self, wsock, close_status_code, close_msg):
        # update shared websocket object
        shared_objects.set_websocket(None)

    def on_open(self, wsock):
        shared_objects.log.debug("connecton to server established.")
        # send these messages before telling the threads that the connection is good
        uuid = shared_objects.config["uuid"]
        uname = os.uname()
        msg = {
            "cmd": "register_client",
            "msgid": str(time.time_ns()),
            "uuid": uuid["id"],
            "name": uuid["name"],
            "description": uuid["description"],
            "reg_ts": uuid["timestamp"],
            "os": "{}, release: {}, version: {}".format(uname.sysname, uname.release, uname.version),
            "easting": uuid["easting"],
            "northing": uuid["northing"],
            "altitude": uuid["altitude"],
            "epsg": uuid["epsg"]
        }
        shared_objects.log.debug(json.dumps(msg))
        wsock.send(json.dumps(msg))

        # signal online status
        msg = {
            "cmd": "client_online",
            "msgid": str(time.time_ns()),
            "status": 1,
            "start_time": shared_objects.get_start_time(),
            "up_time": shared_objects.get_uptime()
        }
        shared_objects.log.debug(json.dumps(msg))
        wsock.send(json.dumps(msg))
        # set shared websocket object
        shared_objects.set_websocket(wsock)

    def run(self):
        shared_objects.log.debug("starting up websocket client connection to server thread")
        websocket.enableTrace(False)
        while self.running:
            try:
                shared_objects.log.debug("connecting to server {}".format(shared_objects.config["server"]["websocket"]))
                shared_objects.initialise_uptime()
                self.ws = websocket.WebSocketApp(shared_objects.config["server"]["websocket"],
                                                 on_open=self.on_open,
                                                 on_message=self.on_message,
                                                 on_error=self.on_error,
                                                 on_close=self.on_close)
                self.ws.run_forever()

                shared_objects.log.error("connection to server {} lost. Waiting {} seconds to reconnect to server.".format(
                    shared_objects.config["server"]["websocket"], shared_objects.config["interval"]))

                time.sleep(int(shared_objects.config["interval"]) + 10)
            except KeyboardInterrupt:
                pass
                # shutdown all threads
            #except Exception as ex:
            #    shared_objects.log.error("WebsocketApp Error - {}".format(ex))
