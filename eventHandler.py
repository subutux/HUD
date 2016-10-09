import homeassistant.remote as remote
import threading
import time
class HAEventHandler(threading.Thread):
	"""
	Quick and dirty eventHandler
	"""
	def __init__(self,api,group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None):
		self.api = api
		self.callbacks = {}
		self.states = []
		self._stopEvent = threading.Event()
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
	def run(self,every=5):
		while not self._stopEvent.isSet():
			self.update()
			time.sleep(every)


	def stop(self):
		self._stopEvent.set()
	def isStopped(self):
		return self._stopEvent.isSet()
