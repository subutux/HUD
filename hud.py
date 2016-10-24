#!/usr/bin/env python3
try:
	import homeassistant.remote as remote
except:
	print("Unable to import HomeAssistant! (try pip3 install homeassistant maybe?)")
	exit(1)
try:
	import pygame
	from pygame.locals import *
except:
	print("Unable to import pygame! (See the readme for installing pygame for python3)")
	exit(1)
try:
	from pgu import gui
except:
	print("Unable to import pgu.gui! (See the readme for installing pgu)")

import elements
from eventHandler import HAEventHandler
import sys
import argparse
import configparser
import logging
p = argparse.ArgumentParser()

p.add_argument('-c','--config',help="config file to use",required=True,type=argparse.FileType('r'))
p.add_argument('-H','--homeassistant',default=None,help="The location of home-assistant")
p.add_argument('-p','--port',default=None,help="the port to use for home-assistant (default: 8123)",type=int)
p.add_argument('-k','--key',default=None,help="The api password to use (default: None)",type=str)
p.add_argument('-s','--ssl',help="Use ssl (default false)",default=False,action="store_true")
p.add_argument('-v','--verbose',help="Log output",default=False,action="store_true")
p.add_argument('-l','--logfile',help="Instead of logging to stdout, log to this file",default=None)
args = p.parse_args();

# Setup logger
logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
rootLogger = logging.getLogger()

if args.verbose:
	if not args.logfile:
		consoleHandler = logging.streamHander(sys.stdout)
		consoleHandler.setFormatter(logFormatter)
		rootLogger.addHandler(consoleHandler)
	else:
		fileHandler = logging.FileHandler(str(args.logfile))
		fileHandler.setFormatter(logFormatter)
		rootLogger.addHandler(fileHandler)

# Setup Home assistant config

config = configparser.ConfigParser()
config.read(args.config.name)
print(config.sections())
try:
	haconfig = {
		"host" : (args.homeassistant if args.homeassistant else config["HomeAssistant"]["Host"]),
		"port" : (args.port if args.port else config["HomeAssistant"]["Port"]),
		"ssl" : (args.ssl if args.ssl else config["HomeAssistant"]["SSL"]),
		"key": (args.key if args.key else config["HomeAssistant"]["Password"])
	}
except KeyError as e:
	print ("Cannot find section [{}] in config file '{}'!".format(str(e),str(args.config.name)))
	exit(1)

# Setup home assistant connection

hass = remote.API(haconfig['host'],haconfig['key'],haconfig['port'],haconfig['ssl'])
HAE = HAEventHandler(hass,settings=haconfig)
try:
	validation = remote.validate_api(hass)
	if str(validation) != "ok":
		raise Exception(validation)

except Exception as e:
	print ("hass connection verification failed: {}".format(str(validation)))
	exit(1)


screen = pygame.display.set_mode((320,480),SWSURFACE)

# For now, only use our "Light" section

# try to get the state of the entity

app = gui.Desktop(theme=gui.Theme("./pgu.theme"))
app.connect(gui.QUIT,app.quit,None)

container=gui.Table(width=230,vpadding=0, hpadding=0)

for section in config.sections():
	if section != "HomeAssistant":
		c = container
		c.tr()
		state = remote.get_state(hass,"group.{}".format(str(config[section]["group"])))
		header = elements.rowHeader(hass,state,table=c)
		HAE.add_listener(state.entity_id,header.set_hass_event)
		c.td(header.draw())
		if state == None:
			c.tr()
			c.td(gui.Label("Unable to find group.{}".format(str(config[section]["group"]))))
		else:
			# get all states from entities & add to the list if entity is not None (eg. not found)
			entities =  [e for e in [remote.get_state(hass,eid) for eid in state.attributes['entity_id']] if e != None]
			for entity in entities:
				c.tr()
				# Changeable, lights are hmmMMmmm
				if (entity.domain == "light"):
					row = elements.rowLight(hass,entity,last=(True if entity == entities[-1] else False),table=c)
					
					HAE.add_listener(entity.entity_id,row.set_hass_event)
					 #row.draw()
					c.td(row.draw(),align=-1)
				elif (entity.domain == "sensor"):
					# widget = gui.Label("{} : {}".format(str(entity.name),str(entity.state)))
					# c.td(widget)
					row = elements.rowSensor(hass,entity,last=(True if entity == entities[-1] else False))
					HAE.add_listener(entity.entity_id,row.set_hass_event)
					c.td(row.draw())
		#container.tr()
		#container.td(c)
		#container.tr()
		container.td(gui.Spacer(height=4,width=320))

main = gui.Container(width=320,height=480)
header = elements.Header("Home Assistant",width=320,height=40)


main.add(header,0,0)
main.add(container,0,70)

# Start the EventDaemon
HAE.start()
while True:
	try:
		app.run(main,screen=screen )
	except AttributeError as e:
		print ("AttributeError, restarting")
		pass

HAE.stop()
