'''
Handles events from UI back to home assistant and is just
a simple threaded queue handler
'''
from queue import Queue
import threading
import logging
from . import remote
import homeassistant.const as hasconst
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
        elif action == "callback":
            log.debug("Handling task {}".format(action))
            callback, args = params
            callback(args)
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
