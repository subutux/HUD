from pgu import gui
from pygame.locals import *
from pgu.gui.const import *
from PIL import Image, ImageOps, ImageDraw
import homeassistant.remote as remote
import homeassistant.const  as hasconst
import icon_font_to_png
import time
import os.path
whereami = os.path.dirname(os.path.realpath(__file__))

####
def maskImage(image,mask,size=(20,20),outputRoot="/tmp")

	mask = Image.new('L', size, 0)
	draw = ImageDraw.Draw(mask) 
	draw.ellipse((0, 0) + size, fill=255)
	im = Image.open(image)
	output = ImageOps.fit(im, mask.size, centering=(0.5, 0.5))
	output.putalpha(mask)
	outputFile = '{}/{}_masked_with_{}.png'.format(outputRoot,
																								os.path.splittext(os.path.basename(image))[0]),
																								os.path.splittext(os.path.basename(mask))[0])
	output.save(outputFile)
	return outputFile
###
class mdiIcons(object):
	"""
	Class for easy converting font icon to a gui.Image
	"""
	def __init__(self,css_file,ttf_file):
		"""
		
		@css_file the css file of the webfont

		@ttf_file the font file of the webfont
		"""
		self.icons = icon_font_to_png.IconFont(css_file,ttf_file,True);
	def icon(self,iconName,size=16,color="black",scale="auto"):
		"""
		get a gui.Image from the icon font

		@iconName the css name of the icon
				  Note: homeAssistant uses a mdi: prefix & is converted
				  		to our prefix
		@size the icon size in px (w=h), default 16
		@color the color of the icon you want, default black
		@scale the scaling to use, default auto
		"""
		if iconName.startswith("mdi:"):
			iconName = iconName.replace('mdi:','mdi-',1)
		file = "{}-x{}-c{}-s{}-HUD.png".format(iconName,str(size),color,str(scale))
		# if we find a file in the tmp folder, use that
		if os.path.isfile("{}/{}".format("/tmp",iconName)):
			return gui.Image("{}/{}".format("/tmp",iconName))
		self.icons.export_icon(iconName,size,filename=file,export_dir="/tmp",color=color,scale=scale)
		return gui.Image("{}/{}".format("/tmp",file))


icons = mdiIcons(whereami+"/pgu.theme/mdi/materialdesignicons.css",
									   whereami+"/pgu.theme/mdi/materialdesignicons-webfont.ttf")

class eventButton(gui.Button):
	"""
	A class to set the state of a button depending on an event
	"""
	def __init__(self,api,haevent,value,**kwargs):
		self.api = api
		self.haevent = None
		self.button_name = None
		super().__init__(value,**kwargs)

		self.set_hass_event(haevent)
		self.connect(gui.CLICK,self.callback)
		
  	
	def callback(self):
		
		if self.event.state == hasconst.STATE_OFF:
			status = remote.call_service(self.api,self.event.domain,haconst.SERVICE_TURN_ON,{
				haconst.CONF_ENTITY_ID: self.haevent.entity_id
				})
		else:
			status = remote.call_service(self.api,self.event.domain,haconst.SERVICE_TURN_OFF,{
				haconst.CONF_ENTITY_ID: self.haevent.entity_id
				})

	def set_hass_event(self,event):
		self.event = event;
		
		if self.event.state == hasconst.STATE_OFF:
			
			self.state = 0
			self.pcls = ""
		elif self.event.state == hasconst.STATE_ON:
			
			self.state = 1
			self.pcls = "down"
		self.repaint()
	def event(self,e):

		if e.type == ENTER: self.repaint()
		elif e.type == EXIT: self.repaint()
		elif e.type == FOCUS: self.repaint()
		elif e.type == BLUR: self.repaint()
		elif e.type == MOUSEBUTTONDOWN:
		    self.state = 1
		    self.repaint()
		elif e.type == MOUSEBUTTONUP:
		    self.repaint()
		elif e.type == CLICK:
		    self.click()


class IconButton(eventButton):
	"""
	A button containing the icon of the event.
	"""
	def __init__(self,api,haevent**kwargs):
		if "icon" in haevent.attributes:
			self.icon = haevent.attributes["icon"]
		else:
			self.icon = 'mdi-eye'
		value = icons.icon(self.icon,20,color="rgb(68, 115, 158)")
		super().__init__(api,haevent,icon,**kwargs)


class sensorValue(eventButton):
	"""
	A button containing the Sensor Value (state) of an event
	"""
	
	def __init__(self,api,haevent**kwargs):
		super().__init__(api,haevent,icon,**kwargs)
		
  def create_value(self,haevent):
		sValue = self.haevent.state
		if "unit_of_measurement" in self.haevent.attributes:
			sValue += " {}".format(self.haevent.attributes["unit_of_measurement"])
		return sValue
		
	def set_hass_event(self,haevent):
		self.haevent = haevent
		self.value = self.create_value()
		self.repaint()
		
  def event(self,e):
  	return True



class Row(object):
	"""
	The main class for all rows. To create a new row, inherit from this one
	"""
	def __init__(self,api,event,last=False,width=320,height=20):
		self.api = api
		self.width = width
		self.height = height
		self.icon = "mdi:eye"
		self.widget = gui.Container(height=self.height,width=self.width,align=-1,valign=-1,background=(220,220,220))
		self.setup()
  
  def setup(self):
		"""
		Needs to be overridden
		"""
  	self.btnicon = gui.Button(icons.icon(self.icon,20,color="rgb(68, 115, 158)"),cls=self.btn_cls,height=self.height,width=36)
		self.name = eventButton(self.api,self.event,height=self.height)
		self.value = eventButton(self.api,self.event,height=self.height)
	
  	self.set_hass_event(haevent)
		self.connect(gui.CLICK,self.callback)


		
#		if self.haevent.state == hasconst.STATE_ON: img = self.style.down
#		s.blit(img,(0,0))		

class LightSwitch(gui.Switch):
	def __init__(self,api,haevent,**kwargs):
		self.api = api
		self.haevent = None
		
		super().__init__(value=False,**kwargs)
		
		self.connect(gui.CLICK,self.callback)
		self.set_hass_event(haevent)
	def callback(self):
		
		if self.haevent.state == hasconst.STATE_OFF:

			status = remote.call_service(self.api,"homeassistant",'turn_on',{
				'entity_id': self.haevent.entity_id
				})
		else:
			status = remote.call_service(self.api,"homeassistant",'turn_off',{
				'entity_id': self.haevent.entity_id
				})
		
		# TODO: Fix time
		#self.update_hass_event()
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
		"""
		Currently, we don't care for events on the header
		"""
		
		return True



class eventLabel(gui.Label):
	def __init__(self,entity):
		self.haevent = entity
		super().__init__("")
		self.set_hass_event(entity)
	def set_hass_event(self,haevent):
		self.haevent = haevent
		self.value = haevent.state
		self.repaint()
	
class rowLight(object):
	def __init__(self,api,entity,last=False,width=320,table=None):
		self.api = api
		self.width = width
		#self.widget = gui.Table(width=width) if table == None else table
		self.widget = gui.Container(height=20,width=320,align=-1,valign=-1,background=(220, 220, 220))
		self.entity = entity
		self.btn_cls = "button"
		self.sw_cls = "switch"
		self.ligth_width = (width-36)-36
		self.icon = 'mdi-lightbulb'
		
		if last:
			self.btn_cls += "_last"
			self.sw_cls += "_last"
	def set_hass_event(self,event):
		self.light.set_hass_event(event)
		if self.entity.state != "unknown":
			self.switch.set_hass_event(event)

	def draw(self):
		if self.icon:
			self.iconButton = gui.Button(icons.icon(self.icon,20,color="rgb(68, 115, 158)"),cls=self.btn_cls,height=20,width=36)
		else:
			self.iconButton = gui.Button(" ",cls=self.btn_cls,height=20,width=36)
		self.light = Light(self.api,self.entity,cls=self.btn_cls,width=238,height=20)
		if self.entity.state != "unknown":
			self.switch = LightSwitch(self.api,self.entity,cls=self.sw_cls)
		else:
			self.switch= gui.Button("",cls=self.btn_cls,width=20,height=20)

		self.widget.add(self.iconButton,0,0)
		self.widget.add(self.light,36,0)
		self.widget.add(self.switch,self.width-36,0)
		return self.widget

class rowSensor(object):
	def __init__(self,api,entity,last=False,width=320):
		self.api = api
		self.width = width
		#self.widget = gui.Table(width=width)
		self.widget = gui.Container(height=20,width=self.width,align=-1,valign=-1,background=(220,220,220))
		self.entity = entity
		self.btn_cls = "button"
		self.sw_cls = "sensor"
		
		self.light_width = (width-36)
		#                          |   
		#                          |   
		#                          +----> Switch size
		if "icon" in entity.attributes:
			self.icon = entity.attributes["icon"]
		else:
			self.icon = 'mdi-eye'
		if last:
			self.btn_cls += "_last"
			self.sw_cls += "_last"
	def set_hass_event(self,event):
		self.light.set_hass_event(event)
		self.state.set_hass_event(event)

	def draw(self):
		if self.icon:
			self.iconButton = gui.Button(icons.icon(self.icon,20,color="rgb(68, 115, 158)"),cls=self.btn_cls,height=20,width=36)
		else:
			self.iconButton = gui.Button(" ",cls=self.btn_cls,height=20,width=36)
		self.state = sensorValue(self.api,self.entity,cls=self.sw_cls,height=20)
		stateWidth = self.state._value.style.width + self.state.style.padding_left + self.state.style.padding_right
		self.light = Light(self.api,self.entity,cls=self.btn_cls,width=(self.light_width-stateWidth),height=20)
		self.widget.add(self.iconButton,0,0)
		self.widget.add(self.light,36,0)
		print("Width state = {}".format(str(self.state._value.style.width)))
		self.widget.add(self.state,self.width-stateWidth,0)
		return self.widget

class rowHeader(rowLight):
	def __init__(self,api,entity,width=320,table=None):
		self.width=width
		super().__init__(api,entity,last=False,width=width,table=table)
		self.icon = None
		self.btn_cls = "button_header"


