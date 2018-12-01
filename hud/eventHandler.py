import homeassistant.core as ha
from sseclient import SSEClient
import requests
import threading
import json
import logging
import websocket
import time
from . import eventWorker
log = logging.getLogger('HUD.HAEventHandler')
log.addHandler(logging.NullHandler())


class HAWebsocketEventHandler(threading.Thread):
    """
    A Home Assistant Websocket actionner
    """
    callbacks = {}
    daemon = True
    connected = False
    authenticated = False
    requestCallbacks = {}
    lastId = 1

    def __init__(self, group=None, target=None, name=None,
                 settings={}, kwargs=None, verbose=None):
        self.url = "wss://{}:{}/api/websocket".format(settings["host"],
                                                      settings["port"])
        self.ws = websocket.WebSocketApp(self.url,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close)
        self.password = settings["key"]
        name = "Thread-websocket-client"
        threading.Thread.__init__(self, group=group, target=target, name=name)

    def run(self):
        log.info("Starting WebSocket")
        self.ws.run_forever()

    def stop(self):
        log.info("Closing WebSocket")
        self.ws.close()

    def on_open(self):
        self.connected = True

    def on_message(self, message):
        msg = json.loads(message)
        Id = msg["id"] if "id" in msg else None
        Type = msg["type"] if "type" in msg else None
        log.debug("Got message {} ({}): {}".format(Id, Type, message))

        if Type and Type == "result":
            if Id and Id in self.requestCallbacks:
                log.debug("Executing callback for id %i", Id)
                try:
                    eventWorker.do("callback",
                                   (self.requestCallbacks[Id], msg))
                except Exception as e:
                    log.exception(e)
        if Type and Type == "event":
            try:
                self._handleEvent(msg)
            except Exception as e:
                log.exception(e)

        if Type and Type.startswith("auth"):
            self._handleAuth(msg)

    def on_error(self, error):
        log.debug("Got error", error)
        self.stop()

    def on_close(self):
        self.connected = False
        self.authenticated = False

    def after_auth(self):
        self.request({
            "type": "subscribe_events",
            "event_type": "state_changed",
            "id": 2
        })

    def request(self, data, response=None):
        if self.authenticated:
            self.lastId = self.lastId + 1
            data["id"] = self.lastId
            json_data = json.dumps(data)
            log.debug("Sending request with data {}".format(json_data))
            if response:
                self._register(self.lastId, response)
            self.ws.send(json_data)
        else:
            log.warning("Not authenticated!")

    def call_service(self, domain, service,
                     service_data={}):
        self.request({
            "type": "call_service",
            "domain": domain,
            "service": service,
            "service_data": service_data
        })

    def _register(self, Id, cb):
        self.requestCallbacks[Id] = cb

    def _handleAuth(self, msg):
        if msg["type"] == "auth_ok":
            log.info("Login successfull")
            self.authenticated = True
            self.after_auth()
        elif msg["type"] == "auth_required":
            log.debug("Sending credentials")
            self.ws.send(json.dumps({
                "type": "auth",
                "api_password": self.password
            }))
        elif msg["type"] == "auth_invalid":
            log.debug("Cannot connect to Home Assistant. Invalid Auth.")
            self.stop()

    def _handleEvent(self, msg):
        data = msg["event"]
        if data["event_type"] == "state_changed":
            state = ha.State.from_dict(data["data"]["new_state"])
            if state.entity_id in self.callbacks:
                for cb in self.callbacks[state.entity_id]:
                    eventWorker.do("callback", (cb, state))

    def add_listener(self, entity, callback):
        log.debug("Adding listener for {} to callback {}".format(
            str(entity), str(callback.__name__)))
        if entity in self.callbacks:
            log.debug(
                "Found existsing listeners for {}. Adding this one to it."
                .format(str(entity)))
            self.callbacks[entity].append(callback)
        else:
            self.callbacks[entity] = [callback]


class HAEventHandler(threading.Thread):
    """
    Quick and dirty eventHandler
    """

    def __init__(self, api=None, group=None, target=None, name=None,
                 settings={}, kwargs=None, verbose=None):

        log.debug("Setup eventHandler")
        if api is not None:
            log.warning("'api' parameter is depricated. Remove it.")
        self.api = api
        self.callbacks = {}
        self.states = []
        self._stopEvent = threading.Event()
        self.settings = settings
        self.sse = None
        close_url = "{}:{}/api/stream?api_password={}&restrict=state_changed,HUD-SSECLIENT-CLOSE"  # nopep8
        if self.settings["ssl"]:
            self.url = "https://" + close_url
        else:
            self.url = "http://" + close_url
        self.url = self.url.format(
            self.settings["host"], self.settings["port"], self.settings["key"])
        threading.Thread.__init__(self, group=group, target=target, name=name)

    def add_listener(self, entity, callback):
        log.debug("Adding listener for {} to callback {}".format(
            str(entity), str(callback.__name__)))
        if entity in self.callbacks:
            log.debug(
                "Found existsing listeners for {}. Adding this one to it."
                .format(str(entity)))
            self.callbacks[entity].append(callback)
        else:
            cbs = []
            cbs.append(callback)
            self.callbacks[entity] = cbs

    def _handleEvent(self, msg):
        if hasattr(msg, "data") and msg.data != "ping":
            data = json.loads(msg.data)
            if data["event_type"] == "state_changed":
                state = ha.State.from_dict(data["data"]["new_state"])
                if state.entity_id in self.callbacks:
                    for cb in self.callbacks[state.entity_id]:
                        log.info("Event: {}".format(str(state)))
                        cb(state)

    def run(self):
        try:
            self.sse = SSEClient(self.url)
            log.info("Started SSEClient")
            for msg in self.sse:
                log.debug("MSG:{}".format(str(msg)))
                if not self._stopEvent.isSet():
                    self._handleEvent(msg)
                else:

                    log.info("Closing SSEClient")
                    break
        except Exception as e:
            log.error("Got Exception: {}! Exitting thread.".format(str(e)))
            self.stop()

    def sendClosingEvent(self):
        """
        This is bit of a hack. We can't immediatly close our SSEClient
        connection, until we got an event.
        We simply send a custom event to HA allowing us to close the
        connection.

        Source: http://somnambulistic-monkey.blogspot.be/2016/07/
        home-assistant-custom-events-and-amazon.html
        """
        log.debug("Sending Event \"HUD-SSECLIENT-CLOSE\"")
        url = "{}:{}/api/events/HUD-SSECLIENT-CLOSE?api_password={}"
        if self.settings["ssl"]:
            url = "https://" + url
        else:
            url = "http://" + url
        url = url.format(
            self.settings["host"], self.settings["port"], self.settings["key"])
        requests.post(url)

    def stop(self):

        log.info("Stopping SSEClient")
        log.debug("Stopping SSEClient->_stopEvent.set()")
        self._stopEvent.set()
        log.info("Waiting for an Event to close ...")
        self.sendClosingEvent()

    def isStopped(self):
        return self._stopEvent.isSet()
