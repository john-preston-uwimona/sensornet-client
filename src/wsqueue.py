import json
import os
import sys
import shared_objects
import queue
import threading
import time
import uuid
import SqlStore
import traceback
import sqlite3

from cachetools import TTLCache

# send with caching queue
caqueue = queue.Queue()
# send without caching queue
wsqueue = queue.Queue()
# response queue
rsqueue = queue.Queue()


class WebsocketQueueThread(threading.Thread):

    def __init__(self, name=None, portal=None):
        threading.Thread.__init__(self, name=name)
        self.running = True
        self.portal = portal
        self.cache = None
        self.pending = None

    @staticmethod
    def add_send(message=None, portal=None, cache_message=False):
        if message is not None:
            msg = {"msgid": str(time.time_ns())}
            msg.update(message)
            shared_objects.log.debug(json.dumps(msg))
            # put_sensor_readings message are saved in the cache for processing while
            # all other messages get processed immediately if possible
            if cache_message:
                caqueue.put(msg)
                if portal is not None:
                    portal.broadcast_message(msg)
            else:
                wsqueue.put(msg)
                if portal is not None:
                    portal.broadcast_message(msg)

    @staticmethod
    def add_response(message=None):
        if message is not None:
            # print("ACK", message)
            rsqueue.put(message)

    def clear(self):
        cache.clear()

    def shutdown(self):
        cache.close()
        self.running = False

    def run(self):
        while self.running:
            if self.cache is None:
                shared_objects.log.debug("starting websocket queue thread")
                self.cache = SqlStore.SqlStore('message_store.db', clear=False, debug=False)
                shared_objects.log.debug("initialising WebsocketQueueThread disk based cache - # entries={}".format(len(self.cache)))
            if self.pending is None:
                self.pending = TTLCache(maxsize = 1000, ttl = 60)
            try:
                # copy put_sensor_reading messages in queue to sql store
                count = caqueue.qsize()
                while count > 0:
                    try:
                        message = caqueue.get(block=False)
                        print("%%%% COPYING SEND MESSAGE TO CACHE %%%%", message)
                        self.cache[message['msgid']] = message
                        count -= 1
                    except queue.Empty:
                        count = 0
                # process up to 5 message stored in the non cached send queue
                count = 0
                while count < 5:
                    try:
                        ws = shared_objects.get_websocket()
                        if ws is not None and ws.sock:
                            message = wsqueue.get(block=False)
                            s_message = json.dumps(message)
                            shared_objects.log.debug(s_message)
                            print("%%%% SENDING MESSAGE TO SERVER %%%%", s_message)
                            ws.send(s_message)
                            if self.portal is not None:
                                self.portal.broadcast_message(message)
                            count += 1
                        else:
                            print("%%%% WSOCK IS NONE CANNOT SEND MESSAGE TO SERVER %%%%")
                    except queue.Empty:
                        count = 5
                    count += 1
                # process messages stored in the sql store
                count = 5 - min(5, len(self.cache))
                # process up to 5 messages
                while count < 5:
                    for item in self.cache:
                        if not item['msgid'] in self.pending:
                            ws = shared_objects.get_websocket()
                            if ws is not None and ws.sock:
                                # print("$$$ ITEM $$$ ", item)
                                s_message = {"delayed-send": item['msgid']}
                                s_message.update(item)
                                if self.portal is not None:
                                    self.portal.broadcast_message(s_message)
                                shared_objects.log.debug(s_message)
                                print("%%%% SENDING SQLSTORE MESSAGES TO SERVER %%%%", s_message)
                                try:
                                    ws.send(json.dumps(item))
                                    self.pending[item['msgid']] = '-'
                                except (TimeoutError, BrokenPipeError) as ex:
                                    print("%%% EXCEPTION %%%", ex)
                                count += 1
                                if count > 5:
                                    break
                        count += 1
                # remove some sent messages (stored in the response queue) from the cache.
                count = 200 if rsqueue.qsize() == 0 else 0
                while count < 200:
                    try:
                        message = rsqueue.get(block=False)
                        print("%%%% DELETING MESSAGE FROM SELF.CACHE %%%%", "msgid" in message, message)
                        if "msgid" in message:
                            del self.cache[message["msgid"]]
                            if message["msgid"] in self.pending:
                                del self.pending[message["msgid"]]
                            shared_objects.log.debug("message msgid:{} sent successfully".format(message["msgid"]))
                            print("%%%% MESSAGE SENT SUCCESSFULLY %%%%", message["msgid"])
                        count += 1
                    except queue.Empty:
                        count = 200
                    count += 1
                # sleep a while
                time.sleep(1)
            except sqlite3.Error as e:
                exc_type, exc_value, exc_tb = sys.exc_info()
                print(traceback.format_exception(exc_type, exc_value, exc_tb))
                shared_objects.log.error(traceback.format_exception(exc_type, exc_value, exc_tb))
                #ws = shared_objects.get_websocket()
                #if ws is not None:
                #    ws.close()
                self.cache.close()
                self.cache = None
                
        shared_objects.log.debug("shutting down websocket queue thread")

