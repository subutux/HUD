import homeassistant.remote as remote
class HAEventHandler(object):
	"""
	Quick and dirty eventHandler
	"""
	def __init__(self,api):
		self.api = api
		self.callbacks = {}
		self.states = []
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
