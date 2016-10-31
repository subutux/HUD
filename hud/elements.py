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


icons = mdiIcons(whereami+"/pgu.theme/mdi/materialdesignicons.css",
									   whereami+"/pgu.theme/mdi/materialdesignicons-webfont.ttf")

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


class LightSwitch(gui.Switch):
	"""
	A switch representing the state of an event
	"""
	
	def __init__(self,api,haevent,**kwargs):
		self.api = api
		self.haevent = None
		
		super().__init__(value=False,**kwargs)
		
		self.connect(gui.CLICK,self.callback)
		self.set_hass_event(haevent)
	def callback(self):
		
		
		if self.event.state == hasconst.STATE_OFF:
			status = remote.call_service(self.api,self.event.domain,haconst.SERVICE_TURN_ON,{
				haconst.CONF_ENTITY_ID: self.haevent.entity_id
				})
		else:
			status = remote.call_service(self.api,self.event.domain,haconst.SERVICE_TURN_OFF,{
				haconst.CONF_ENTITY_ID: self.haevent.entity_id
				})

	def click(self):
		pass
	def set_hass_event(self,haevent):
		self.haevent = haevent;
		if self.haevent.state == hasconst.STATE_OFF:
			self._value = False
		elif self.haevent.state == hasconst.STATE_ON:
			self._value = True
		self.repaint()
	
class sensorValue(eventButton):
	"""
	A button containing the Sensor Value (state) of an event
	"""
	
	def __init__(self,api,haevent**kwargs):
		super().__init__(api,haevent,icon,**kwargs)
		self.cls = "sensor"
		
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
	def __init__(self,api,haevent,last=False,width=320,height=20):
		self.api = api
		self.width = width
		self.height = height
		self.icon = "mdi:eye"
		self._haevent = None
		self._btnicon = None
		self._name = None
		self._value = None
	  self.lastRow = False
		self.widget = gui.Container(height=self.height,width=self.width,align=-1,valign=-1,background=(220,220,220))
		self.haevent = haevent

		self.setup()
		
  def setup(self):
		"""
		Needs to be overridden
		
		with something like this:
		
		self.btnicon = iconButton(self.api,self.event,height=self.height)
		self.name = eventButton(self.api,self.event,height=self.height)
		self.value = eventButton(self.api,self.event,height=self.height)
	  """
	  pass
	 
  @property
	def haevent(self):
		return self._haevent

	@haevent.setter
	def haevent(self,haevent):
		## This needs to be SSEClient.Event
		## But don't know the inpact
		if isinstance(haevent,object):
			self._haevent = haevent
	
	@property
	def btnicon(self):
		return self._btnicon
	
	@btnicon.setter
	def btnicon(self,icon):
		if isinstance(icon,eventButton):
			self._btnicon = icon
			if self.lastRow:
				self._btnicon.cls += "_last"
	
  @property
	def name(self):
		return self._name

	@name.setter
	def name(self,name):
		if isinstance(name,eventButton):
			self._name = name	
			if self.lastRow:
				self._name.cls += "_last"

  @property
	def value(self):
		return self._value

	@value.setter
	def value(self,value):
		if isinstance(value,eventButton):
			self._value = value
			if self.lastRow:
				self._value.cls += "_last"
  
	def draw(self,update=False):
		#start with full width
		nameWidth = self.width
		btniconWidth = 0
		#check if we have an icon
		if self._btnicon:
		  btniconWidth = self._btn.style.width
			nameWidth -= self._btn.style.width
			self.widget.add(self._btnicon,0,0)
		self.widget.add(self._value,self.width-self._value.style.width,0)
	  nameWith -= self._value.style.width
	  self._name.style.width = nameWith
	  
		self.widget.add(self._name,btniconWidth,0)
		
		return self.widget
	
	def repaint(self):
		
		self.widget.remove(self._value)
		self.widget.add(self._value,self.width-self._value.style.width,0)
			self._name.style.width = self.width - self._value.style.width
		if self._btnicon:
		  self._name.style.width -= - self._btnicon.style.width
	
	def set_hass_event(self,event):
		"""
		This is the main callback or receiving new events
		
		Sets the haevents + toggle a repaint.
		"""
		self.haevent = event
		self._btnicon.set_hass_event(event)
		self._name.set_hass_event(event)
		self._value.set_hass_event(event)	
		self.repaint()
		


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

		
class rowLight(Row)
	def __init__(self,api,haevent,last=False,width=320,height=20):
		super().__init__(self,api,haevent,last=False,width=320,height=20)
	
	def setup(self):
		self.value = LightSwitch(self.api,self.haevent,height=20)
		self.name = eventButton(self.api,self.haevent,height=20)
		self.btnicon = IconButton(self.api,self.haevent,height=20)


class rowSensor(Row)
	def __init__(self,api,haevent,last=False,width=320,height=20):
		super().__init__(self,api,haevent,last=False,width=320,height=20)
	
	def setup(self):
		self.value = sensorValue(self.api,self.haevent,height=20)
		self.name = eventButton(self.api,self.haevent,height=20)
		self.btnicon = IconButton(self.api,self.haevent,height=20)




class rowHeader(rowLight):
	def __init__(self,api,entity,width=320,table=None):
		self.width=width
		super().__init__(api,entity,last=False,width=width,table=table)
		self.icon = None
		self.btn_cls = "button_header"


