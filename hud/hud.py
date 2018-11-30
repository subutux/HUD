#!/usr/bin/env python3
__version__ = "0.3b2"
import os
import sys
import argparse
import configparser
import logging
import signal

from .eventHandler import HAEventHandler
from . import elements
from . import remote
import pygame
from pygame.locals import *
from pgu import gui

# Quick-Fix (tm) for systemd


def _sighup(signal, frame):
    return true


signal.signal(signal.SIGHUP, _sighup)


def main():
    whereami = os.path.dirname(os.path.realpath(__file__))
    # Parse arguments
    p = argparse.ArgumentParser(description="A pygame GUI for Home Assistant.")
    p_config = p.add_argument_group('Configuration')
    p_config.add_argument('-c', '--config', help="config file to use",
                          required=True, type=argparse.FileType('r'))
    p_config.add_argument('-f', '--framebuffer',
                          help="Use this framebuffer as output for the UI\
    (defaults to window mode)",
                          default=None, type=str, metavar="/dev/fbX")
    p_config.add_argument('-t', '--touchscreen',
                          help="Enable touchscreen integration.\
     Use this as event input",
                          default=None, type=str, metavar="/dev/input/eventX")
    p_config.add_argument('-n', '--no-display',
                          help="We don't have a display. Sets the\
   SDL_VIDEODRIVER to \"dummy\". Usefull for testing",
                          dest="dummy", action="store_true",
                          default=False)
    p_config.add_argument('--width',
                          help="The width of the display or window",
                          dest="width", type=int,
                          default=False)
    p_config.add_argument('--heigth',
                          help="The height of the display or window",
                          dest="height", type=int,
                          default=False)
    p_homeassistant = p.add_argument_group(
        'HomeAssistant', " (optional) Parameters to override the config file")
    p_homeassistant.add_argument('-H', '--homeassistant', default=None,
                                 help="The location of home-assistant",
                                 metavar="host.name")
    p_homeassistant.add_argument('-p', '--port', default=None,
                                 help="the port to use for home-assistant\
     (default: 8123)",
                                 type=int)
    p_homeassistant.add_argument(
        '-k', '--key', default=None,
        help="The api password to use (default: None)", type=str)
    p_homeassistant.add_argument(
        '-s', '--ssl',
        help="Use ssl (default false)", default=False, action="store_true")
    p_logging = p.add_argument_group('Logging', " (optional) Logging settings")
    p_logging.add_argument(
        '-v', '--verbose',
        help="Log output", default=False, action="store_true")
    p_logging.add_argument(
        '-L', '--logLevel', dest="logLevel",
        help="Log level to use (default: ERROR)",
        choices=["INFO", "WARNING", "ERROR", "CRITICAL", "DEBUG"],
        default="ERROR", type=str)
    p_logging.add_argument(
        '-l', '--logfile',
        help="Instead of logging to stdout, log to this file", default=None)
    args = p.parse_args()

    # Setup logger
    logFormat = "%(asctime)s [%(threadName)s:%(name)s]\
 [%(levelname)-5.5s]  %(message)s"
    logFormatter = logging.Formatter(
        logFormat)
    log = logging.getLogger("HUD")
    log.setLevel(getattr(logging, args.logLevel.upper()))
    if args.verbose:
        if not args.logfile:
            consoleHandler = logging.StreamHandler(sys.stdout)
            consoleHandler.setFormatter(logFormatter)
            log.addHandler(consoleHandler)
        else:
            fileHandler = logging.FileHandler(str(args.logfile))
            fileHandler.setFormatter(logFormatter)
            log.addHandler(fileHandler)
    # Setup Home assistant config
    log.info("Startup: Load config")
    config = configparser.ConfigParser()
    config.read(args.config.name)
    print(config.sections())
    try:
        haconfig = {
            "host": (args.homeassistant if args.homeassistant else
                     config["HomeAssistant"]["Host"]),
            "port": (args.port if args.port else
                     config["HomeAssistant"]["Port"]),
            "ssl": (args.ssl if args.ssl else
                    config["HomeAssistant"]["SSL"]),
            "key": (args.key if args.key else
                    config["HomeAssistant"]["Password"])
        }
    except KeyError as e:
        log.error("Cannot find section [{}] in config file '{}'!".format(
            str(e), str(args.config.name)))
        exit(1)

    # Setup home assistant connection
    log.info("Startup: Create EventHandler")
    hass = remote.API(haconfig['host'], haconfig['key'],
                      haconfig['port'], haconfig['ssl'])
    HAE = HAEventHandler(hass, settings=haconfig)
    try:
        validation = remote.validate_api(hass)
        if str(validation) != "ok":
            log.info("Startup: Successfully connected to HomeAssistant!")
            raise Exception(validation)

    except Exception as e:
        log.error("hass connection verification failed: {}".format(
            str(validation)))
        exit(1)

    log.info("Startup: Setting screen")
    width = args.width
    height = args.height
    if args.framebuffer:
        log.info("Startup: Setting framebuffer")
        os.putenv('SDL_VIDEODRIVER', 'fbcon')
        os.putenv('SDL_FBDEV', args.framebuffer)
    if args.touchscreen:
        log.info("Startup: Setting up touchscreen support")
        os.putenv('SDL_MOUSEDRV', 'TSLIB')
        os.putenv('SDL_MOUSEDEV', args.touchscreen)
    if args.dummy:
        os.putenv('SDL_VIDEODRIVER', 'dummy')
    if args.framebuffer:
        pygame_opts = FULLSCREEN | HWSURFACE | DOUBLEBUF
        #                         ^UNTESTED!^
    else:
        pygame_opts = SWSURFACE
    screen = pygame.display.set_mode((width, height), pygame_opts)

    if args.touchscreen:
        # Hide the mouse cursor if we have a touchscreen
        pygame.mouse.set_visible(False)

    log.info("Startup: Load Theme")
    app = gui.Desktop(theme=gui.Theme(whereami + "/pgu.theme"))
    app.connect(gui.QUIT, app.quit, None)

    container = gui.Table(width=width, vpadding=0, hpadding=0, cls="desktop")
    _states = remote.get_states(hass)
    states = {}
    for st in _states:
        states[st.entity_id] = st
    for section in config.sections():
        if section != "HomeAssistant":
            log.info("Startup: Loading section {}".format(str(section)))
            c = container
            c.tr()
            try:
                state = states["group.{}"
                               .format(str(config[section]["group"]))]
            except KeyError:
                state = None
            header = elements.rowHeader(hass, state, table=c, width=width)
            HAE.add_listener(state.entity_id, header.set_hass_event)
            c.td(header.draw(), align=-1)
            c.tr()
            if state is None:
                log.warning("Startup: Unable to find group.{}".format(
                    str(config[section]["group"])))
                c.td(gui.Label("Startup: Unable to find group.{}".format(
                    str(config[section]["group"]))))
            else:
                log.info("Startup: Fetching entity statusses")
                # get all states from entities & add to the list
                # if entity is not None (eg. not found)
                entities = state.attributes['entity_id']
                for entity in entities:
                    log.info("Startup: Loading entity {}".format(
                        entity))
                    try:
                        state_entity = states[entity]
                    except KeyError:
                        log.info("Cannot find any state for {0}, skipping"
                                 .format(entity))
                        continue
                    # Changeable, lights are hmmMMmmm
                    if state_entity.domain == "light":
                        row = elements.rowLight(hass, state_entity, last=(
                            True if entity == entities[-1] else False),
                            width=width,
                            table=c)
                        log.info("Startup: Adding Event listener for {}"
                                 .format(entity))
                        HAE.add_listener(entity, row.set_hass_event)
                        # row.draw()
                        c.td(row.draw(), align=-1)
                    elif state_entity.domain in ('sensor', 'device_tracker'):
                        row = elements.rowSensor(hass, state_entity, last=(
                            True if entity == entities[-1] else False),
                            width=width)
                        log.info("Startup: Adding Event listener for {}"
                                 .format(entity))
                        HAE.add_listener(entity, row.set_hass_event)
                        c.td(row.draw(), align=-1)
                    else:
                        log.info("FIXME:entity {0} has an unknown domain {1}"
                                 .format(entity, state_entity.domain))
                    c.tr()

            container.td(gui.Spacer(height=4, width=width))
    log.info("Startup: Load elements onto surface")
    main = gui.Container(width=width, height=height)
    header = elements.Header("Home Assistant", width=width, height=40)
    slidebox = elements.Scrollable(container, width=width, height=height)
    main.add(header, 0, 0)
    main.add(container, 0, 60)

    # Start the EventDaemon
    log.info("Startup: start HAEventHandler")
    HAE.start()
    RunPlease = True
    while RunPlease:
        try:
            log.info("Start screen")
            app.run(main, screen=screen)
        except (KeyboardInterrupt, SystemExit):
            log.warning("Got Exit or Ctrl-C. Stopping.")
            RunPlease = False
            pass
        except AttributeError as e:
            log.error("AttributeError, restarting")
            pass

    HAE.stop()
    sys.exit(0)
