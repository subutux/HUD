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


screen = pygame.display.set_mode((350,600),SWSURFACE)

# For now, only use our "Light" section

# try to get the state of the entity

app = gui.Desktop(theme=gui.Theme("./pgu.theme"))
app.connect(gui.QUIT,app.quit,None)

container=gui.Table(width=230)

for section in config.sections():
	if section != "HomeAssistant":
		c = gui.Table(width=320)
		c.tr()
		c.td(gui.Label(section),cls="sectionlabel",align=-1)
		
		state = remote.get_state(hass,"group.{}".format(str(config[section]["group"])))
		if state == None:
			c.tr()
			c.td(gui.Label("Unable to find group.{}".format(str(config[section]["group"]))))
		else:
			entity_ids = state.attributes['entity_id']
			for entity_id in entity_ids:
				c.tr()
				entity = remote.get_state(hass,entity_id)
				# Changeable, lights are hmmMMmmm
				if (entity.domain == "light"):
					widget = gui.Table(width=320)
					widget.tr()
					btn_cls = "button"
					sw_heigth = 400
					sw_cls = "switch"
					if entity_id == entity_ids[-1]:
						btn_cls += "_last"
						sw_cls += "_last"
						sw_heigth += 8
					i = gui.Button(gui.Image("pgu.theme/icons/ic_lightbulb_outline_black_18dp.png"),cls=btn_cls,height=20,width=20)
					widget.td(i)
					l = elements.Light(hass,entity,cls=btn_cls,width=264,height=20)
					HAE.add_listener(entity.entity_id,l.set_hass_event)
					widget.td(l,align=1)
					s = elements.LightSwitch(hass,entity,cls=sw_cls)
					widget.td(s,align=1)
					HAE.add_listener(entity.entity_id,s.set_hass_event)
					
					c.td(widget)
				elif (entity.domain == "sensor"):
					widget = gui.Label("{} : {}".format(str(entity.name),str(entity.state)))
					c.td(widget)
		container.tr()
		container.td(c)

main = gui.Container(width=320,height=600)
header = elements.Header("Home Assistant",width=360,height=40)


main.add(header,0,0)
main.add(container,0,70)
app.init(main)
# Start the EventDaemon
HAE.start()
clock = pygame.time.Clock()
wait = 5000 # 5s
last_tick = 0
done = False
while not done:
	for e in pygame.event.get():
		if e.type is QUIT:
			done = True
			HAE.stop()
		elif e.type is KEYDOWN and e.key == K_ESCAPE:
			done = True
			HAE.stop()
		else:
			app.event(e)
	dt = clock.tick(30)/1000.0
	app.paint()

	# hass events grabber
	# now_tick = pygame.time.get_ticks();
	# if (now_tick - last_tick) >= wait:
	# 	HAE.update()
	# 	last_tick=now_tick


	pygame.display.flip()
