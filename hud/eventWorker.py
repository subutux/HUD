'''
Handles events from UI back to home assistant and is just
a simple threaded queue handler
'''
from queue import Queue
import threading
import logging
import homeassistant.const as hasconst
import requests
import tempfile
log = logging.getLogger('HUD.HAEventWorker')
log.addHandler(logging.NullHandler())

Q = Queue()


def do(action, data):
    Q.put((action, data))


def Handle(q, api):
    while True:
        log.debug("Waiting for a Task")
        action, params = q.get()
        if action == "toggle_event":
            log.debug("Handling task {}".format(action))
            if params.state == hasconst.STATE_OFF:

                api.call_service("homeassistant", 'turn_on', {
                    'entity_id': params.entity_id
                })
            else:
                api.call_service("homeassistant", 'turn_off', {
                    'entity_id': params.entity_id
                })
        if action == "call_service":
            log.debug("Handling task {}".format(action))
            service, param = params
            api.call_service(service, params)
        elif action == "callback":
            log.debug("Handling task {}".format(action))
            callback, args = params
            try:
                callback(args)
            except Exception as e:
                log.exception(e)
        elif action == "download":
            log.debug("Handling task download")
            callback, args = params
            url = "{}://{}:{}{}"
            s = api.settings
            url = url.format("https" if s["ssl"] else "http",
                             s["host"], s["port"], args)
            resp = requests.get(url)
            tmp = tempfile.NamedTemporaryFile()

            for chunk in resp:
                tmp.write(chunk)
            try:
                callback(tmp.name)
            except Exception as e:
                log.exception(e)

        q.task_done()


def start(num_threads, eventHandler):
    for i in range(num_threads):
        log.debug("Starting eventWorker-{}".format(i))
        worker = threading.Thread(target=Handle,
                                  args=(Q, eventHandler),
                                  name="eventWorker-{}".format(i))
        worker.setDaemon(True)
        worker.start()


def stop():
    log.debug("Waiting for workers to complete...")
    Q.join()
