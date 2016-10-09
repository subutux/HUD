import homeassistant.remote as remote
import homeassistant.core as ha
import threading
import time
import json
from sseclient import SSEClient
class HAEventHandler(threading.Thread):
	"""
	Quick and dirty eventHandler
	"""
	def __init__(self,api,group=None, target=None, name=None,
                 settings={}, kwargs=None, verbose=None):
		self.api = api
		self.callbacks = {}
		self.states = []
		self._stopEvent = threading.Event()
		self.settings = settings
		if self.settings["ssl"]:
			self.url="https://{}:{}/api/stream?api_password={}"
		else:
			self.url="https://{}:{}/api/stream?api_password={}"
		self.url = self.url.format(self.settings["host"],self.settings["port"],self.settings["key"])
		threading.Thread.__init__(self,group=group, target=target, name=name)

	def add_listener(self,entity,callback):
		if entity in self.callbacks:
			self.callbacks[entity].append(callback)
		else:
			cbs = []
			cbs.append(callback)
			self.callbacks[entity] = cbs
	def update(self):
		self.states = remote.get_states(self.api)
		for state in self.states:
			if state.entity_id in self.callbacks:
				for cb in self.callbacks[state.entity_id]:
					cb(state)
	def run(self):
		messages = SSEClient(self.url)
		#TODO Fix this to determine what class to use
		for msg in messages:
			print(msg.data)
			if hasattr(msg,"data") and msg.data != "ping" and msg.event_type == "state_chanted":
				print (json.loads(msg.data))
				state = ha.State.from_dict(json.loads(msg.data))
				if state.entity_id in self.callbacks:
					for cb in self.callbacks[state.entity_id]:
						cb(state)


	def stop(self):
		self._stopEvent.set()
	def isStopped(self):
		return self._stopEvent.isSet()
