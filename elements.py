from pgu import gui
import homeassistant.remote as remote
import homeassistant.const  as hasconst
import time
class Light(gui.Button):
	def __init__(self,api,haevent,**kwargs):
		self.api = api
		self.haevent = haevent
		super().__init__(haevent.name,**kwargs)

		self.connect(gui.CLICK,self.callback)

	def callback(self):
		print('callback')
		if self.haevent.state == hasconst.STATE_OFF:
			status = remote.call_service(self.api,self.haevent.domain,'turn_on',{
				'entity_id': self.haevent.entity_id
				})
		else:
			status = remote.call_service(self.api,self.haevent.domain,'turn_off',{
				'entity_id': self.haevent.entity_id
				})
		print (status);
		# TODO: Fix time
		time.sleep(2)
		self.set_hass_event(remote.get_state(self.api,self.haevent.entity_id))

	def set_hass_event(self,haevent):
		self.haevent = haevent;
		if self.haevent.state == hasconst.STATE_OFF:
			self.state = 0
		elif self.haevent.state == hasconst.STATE_ON:
			self.state = 1

