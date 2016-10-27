import homeassistant.remote as remote
import homeassistant.core as ha
from sseclient import SSEClient
import requests
import threading
import time
import json
import logging
log = logging.getLogger('HUD.HAEventHandler')
log.addHandler(logging.NullHandler())
class HAEventHandler(threading.Thread):
	"""
	Quick and dirty eventHandler
	"""
	def __init__(self,api=None,group=None, target=None, name=None,
                 settings={}, kwargs=None, verbose=None):
		
		log.debug("Setup eventHandler")
		if api != None:
			log.warning("'api' parameter is depricated. Remove it.")
		self.api = api
		self.callbacks = {}
		self.states = []
		self._stopEvent = threading.Event()
		self.settings = settings
		self.sse = None
		if self.settings["ssl"]:
			self.url="https://{}:{}/api/stream?api_password={}&restrict=state_changed,HUD-SSECLIENT-CLOSE"
		else:
			self.url="http://{}:{}/api/stream?api_password={}&restrict=state_changed,HUD-SSECLIENT-CLOSE"
		self.url = self.url.format(self.settings["host"],self.settings["port"],self.settings["key"])
		threading.Thread.__init__(self,group=group, target=target, name=name)

	def add_listener(self,entity,callback):
		log.debug("Adding listener for {} to callback {}".format(str(entity),str(callback.__name__)))
		if entity in self.callbacks:
			log.debug("Found existsing listeners for {}. Adding this one to it.".format(str(entity)))
			self.callbacks[entity].append(callback)
		else:
			cbs = []
			cbs.append(callback)
			self.callbacks[entity] = cbs
			
	def _handleEvent(self,msg):
		if hasattr(msg,"data") and msg.data != "ping":
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
		This is bit of a hack. We can't immediatly close our SSEClient connection, until we got an event.
		We simply send a custom event to HA allowing us to close the connection.
		
		Source: http://somnambulistic-monkey.blogspot.be/2016/07/home-assistant-custom-events-and-amazon.html
		"""
		log.debug("Sending Event \"HUD-SSECLIENT-CLOSE\"")
		if self.settings["ssl"]:
			url="https://{}:{}/api/events/HUD-SSECLIENT-CLOSE?api_password={}"
		else:
			url="http://{}:{}/api/events/HUD-SSECLIENT-CLOSE?api_password={}"
		url = url.format(self.settings["host"],self.settings["port"],self.settings["key"])
		r = requests.post(url);
		
	def stop(self):
		
		log.info("Stopping SSEClient")
		log.debug("Stopping SSEClient->_stopEvent.set()")
		self._stopEvent.set()
		log.info("Waiting for an Event to close ...")
		self.sendClosingEvent()
	def isStopped(self):
		return self._stopEvent.isSet()
