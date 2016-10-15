from pgu import gui
from pygame.locals import *
from pgu.gui.const import *
import homeassistant.remote as remote
import homeassistant.const  as hasconst
import icon_font_to_png
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

			status = remote.call_service(self.api,"homeassistant",'turn_on',{
				'entity_id': self.haevent.entity_id
				})
		else:
			status = remote.call_service(self.api,"homeassistant",'turn_off',{
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
		
class mdiIcons(object):
	def __init__(self,css_file,ttf_file):
		self.icons = icon_font_to_png.IconFont(css_file,ttf_file,True);
	def icon(self,iconName,size=32,color="black",scale="auto"):
		file = "{}-HUD.png".format(iconName)
		self.icons.export_icon(iconName,size,filename=file,export_dir="/tmp",color=color,scale=scale)
		return gui.Image("{}/{}".format("/tmp",file))
class rowLight(object):
	def __init__(self,api,entity,last=False,width=320):
		self.icons = mdiIcons("pgu.theme/mdi/materialdesignicons.css",
									   "pgu.theme/mdi/materialdesignicons-webfont.ttf")
		self.api = api
		self.width = width
		self.widget = gui.Table(width=width)
		self.entity = entity
		self.btn_cls = "button"
		self.sw_cls = "switch"
		self.ligth_width = (width-20)-36
		self.icon = 'mdi-lightbulb-outline'
		if last:
			self.btn_cls += "_last"
			self.sw_cls += "_last"
	def set_hass_event(self,event):
		self.light.set_hass_event(event)
		self.switch.set_hass_event(event)
	def draw(self):
		if self.icon:
			self.iconButton = gui.Button(self.icons.icon(self.icon,16),cls=self.btn_cls,height=20,width=20)
		else:
			self.ligth_width = self.width - 20
		self.light = Light(self.api,self.entity,cls=self.btn_cls,width=self.ligth_width,height=20)
		self.switch = LightSwitch(self.api,self.entity,cls=self.sw_cls)
		self.widget.tr()
		if self.icon:
			self.widget.td(self.iconButton)
		self.widget.td(self.light)
		self.widget.td(self.switch)
		return self.widget

class rowHeader(rowLight):
	def __init__(self,api,entity,width=320):
		self.width=width
		super().__init__(api,entity,last=False,width=width)
		self.icon = None
		self.btn_cls = "button_header"


		