from pgu import gui
from pygame.locals import *
from pgu.gui.const import *
import homeassistant.remote as remote
import homeassistant.const  as hasconst
import time
class Light(gui.Button):
	def __init__(self,api,haevent,**kwargs):
		self.api = api
		self.haevent = None
		super().__init__(haevent.name,**kwargs)

		self.set_hass_event(haevent)
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
		self.set_hass_event(remote.get_state(self.api,self.haevent.entity_id))

	def set_hass_event(self,haevent):
		self.haevent = haevent;
		print(haevent)
		if self.haevent.state == hasconst.STATE_OFF:
			print("off")
			self.state = 0
			self.pcls = ""
		elif self.haevent.state == hasconst.STATE_ON:
			print("on")
			self.state = 1
			self.pcls = "down"
		self.repaint()
	def update_hass_event():
		self.set_hass_event(remote.get_state(self.api,self.haevent.entity_id))		
	def event(self,e):

		if e.type == ENTER: self.repaint()
		elif e.type == EXIT: self.repaint()
		elif e.type == FOCUS: self.repaint()
		elif e.type == BLUR: self.repaint()
		elif e.type == KEYDOWN:
		    if e.key == K_SPACE or e.key == K_RETURN:
		        self.state = 1
		        self.repaint()
		elif e.type == MOUSEBUTTONDOWN:
		    self.state = 1
		    self.repaint()
		elif e.type == KEYUP:
		    if self.state == 1:
		        sub = pygame.event.Event(CLICK,{'pos':(0,0),'button':1})
		        #self.send(sub.type,sub)
		        self._event(sub)
		        #self.event(sub)
		        #self.click()

		    #self.state = 0
		    self.repaint()
		elif e.type == MOUSEBUTTONUP:
		    #self.state = 0
		    self.repaint()
		elif e.type == CLICK:
		    self.click()
		
#		if self.haevent.state == hasconst.STATE_ON: img = self.style.down
#		s.blit(img,(0,0))		

class LightSwitch(gui.Switch):
	def __init__(self,api,haevent,**kwargs):
		self.api = api
		self.haevent = None
		print(kwargs["cls"])
		super().__init__(value=False,**kwargs)
		print(self.style.height)
		self.connect(gui.CLICK,self.callback)
		self.set_hass_event(haevent)
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
		self.update_hass_event()
	def click(self):
		pass
	def set_hass_event(self,haevent):
		self.haevent = haevent;
		if self.haevent.state == hasconst.STATE_OFF:
			self._value = False
		elif self.haevent.state == hasconst.STATE_ON:
			self._value = True
		self.repaint()
	def update_hass_event(self):
		self.set_hass_event(remote.get_state(self.api,self.haevent.entity_id))		
		
#		if self.haevent.state == hasconst.STATE_ON: img = self.style.down
#		s.blit(img,(0,0))		

class Header(gui.Button):
	def __init__(self,name,**kwargs):
		kwargs.setdefault("cls","header")
		self.pcls = "down"
		self.state = 1
		super().__init__(name,**kwargs)

	def event(self,e):

		if e.type == ENTER: self.repaint()
		elif e.type == EXIT: self.repaint()
		elif e.type == FOCUS: self.repaint()
		elif e.type == BLUR: self.repaint()
		elif e.type == KEYDOWN:
		    if e.key == K_SPACE or e.key == K_RETURN:
		        self.state = 1
		        self.repaint()
		elif e.type == MOUSEBUTTONDOWN:
		    self.state = 1
		    self.repaint()
		elif e.type == KEYUP:
		    if self.state == 1:
		        sub = pygame.event.Event(CLICK,{'pos':(0,0),'button':1})
		        #self.send(sub.type,sub)
		        self._event(sub)
		        #self.event(sub)
		        #self.click()

		    #self.state = 0
		    self.repaint()
		elif e.type == MOUSEBUTTONUP:
		    #self.state = 0
		    self.repaint()
		elif e.type == CLICK:
		    self.click()
		
#		if self.haevent.state == hasconst.STATE_ON: img = self.style.down
#		s.blit(img,(0,0))		
