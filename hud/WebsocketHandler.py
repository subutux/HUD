import homeassistant.core as ha
import threading
import json
import logging
import websocket
from . import eventWorker
log = logging.getLogger('HUD.HAWebsocketEventHandler')
log.addHandler(logging.NullHandler())


class HAWebsocketEventHandler(object):
    """
    A Home Assistant Websocket actionner
    """
    callbacks = {}
    daemon = True
    connected = False
    authenticated = False
    requestCallbacks = {}
    lastId = 1
    worker = None

    def __init__(self, group=None, target=None, name=None,
                 settings={}, kwargs=None, verbose=None):
        self.settings = settings
        protocol = "wss" if settings["ssl"] else "ws"
        self.url = "{}://{}:{}/api/websocket".format(protocol,
                                                     settings["host"],
                                                     settings["port"])
        self.ws = websocket.WebSocketApp(self.url,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close)
        self.password = settings["key"]

    def start(self):
        log.info("Starting WebSocket")
        self.worker = threading.Thread(target=self.ws.run_forever,
                                       name="Thread-websocket-client")
        self.worker.setDaemon(True)
        self.worker.start()

    def stop(self):
        log.info("Closing WebSocket")
        self.ws.close()

    def on_open(self):
        log.info("Started WebSocket")
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
