import sys
import time
import shared_objects
import json

from commands import run
from websocket_server import WebsocketServer
from datetime import datetime

class Portal():
    def __init__(self, port=9001):
        self.threads = None
        shared_objects.log.debug("starting up portal websocket server thread {}:{}".format("localhost", port))
        self.server = WebsocketServer(host="0.0.0.0", port=port)
        self.server.set_fn_new_client(self.new_client)
        self.server.set_fn_client_left(self.client_left)
        self.server.set_fn_message_received(self.message_received)
        self.server.run_forever(threaded=True)

    def setThreads(self, threads):
        self.threads = threads

    def shutdown(self):
        shared_objects.log.debug("shutting down portal websocket server thread")

      # Called for every client connecting (after handshake)
    def new_client(self, client, server):
        shared_objects.log.trace("New portal client connected with id {}".format(client['id']))


    # Called for every client disconnecting
    def client_left(self, client, server):
        shared_objects.log.trace("Client {} disconnected.".format(client['id']))


    # Called when a client sends a message
    def message_received(self, client, server, message):
        try:
            rq = json.loads(message)
            rq["ts"] = 0
            rq["recipient"] = ""
            rq["sender"] = "",
            # log this message
            shared_objects.log.info("portal request: {}".format(json.dumps(rq)))
            # process the request
            response = run(rq, self.threads["gpsp"])
            # return response
            self.server.send_message(client, json.dumps(response))
            shared_objects.log.info("portal response {}".format(json.dumps(response)))
        except json.decoder.JSONDecodeError as e:
            shared_objects.log.error("{}".format(e))

    def broadcast_message(self, message):
        self.server.send_message_to_all(json.dumps(message))

