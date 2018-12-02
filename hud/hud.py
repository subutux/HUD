#!/usr/bin/env python3
__version__ = "0.4b1"
import os
import sys
import argparse
import configparser
import logging
import signal
import time

from .WebsocketHandler import HAWebsocketEventHandler
from . import eventWorker
from . import renderer
from . import remote
import pygame
from pygame.locals import *
from pgu import gui
# Quick-Fix (tm) for systemd


def _sighup(signal, frame):
    return true


def pygame_print(text, screen, x, y):
    screen.fill([200, 200, 200])
    whereami = os.path.dirname(os.path.realpath(__file__))
    font = pygame.font.Font(whereami + "/pgu.theme/Vera.ttf", 20)
    text = font.render(text, True, [255, 255, 255])
    screen.blit(text, (x, y))
    pygame.display.update()


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
    HAE = HAWebsocketEventHandler(settings=haconfig)
    try:
        validation = remote.validate_api(hass)
        if str(validation) != "ok":
            log.info("Startup: Successfully connected to HomeAssistant!")
            raise Exception(validation)

    except Exception as e:
        log.error("hass connection verification failed: {}".format(
            str(validation)))
        exit(1)
    # Start the EventDaemon
    log.info("Startup: start HAWebsocketEventHandler")
    HAE.start()
    log.info("Startup: start EventWorker")
    eventWorker.start(4, HAE)
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
    pygame.display.set_caption("HUD")
    screen.fill([200, 200, 200])
    pygame.display.update()
    log.info("Startup: Load Theme")
    app = gui.Desktop(theme=gui.Theme(whereami + "/pgu.theme"))
    app.connect(gui.QUIT, app.quit, None)
    timeout = 5
    while timeout != 0:
        if HAE.authenticated:
            pygame_print("Connected. Loading view...",
                         screen, 10, height / 2)
            break
        else:
            timeout -= 1
            log.info("Waiting for connection")
            pygame_print("Connecting to home assistant",
                         screen, 10, height / 2)
            time.sleep(1)
    if not HAE.authenticated:
        log.error("Connection failed")
        pygame_print("Connection failed",
                     screen, 10, height / 2)
        time.sleep(2)
        sys.exit(1)

    view = renderer.renderConfig(remote.get_states(hass),
                                 width, height, config, HAE)

    RunPlease = True
    while RunPlease:
        try:
            app.run(view, screen=screen)
        except (KeyboardInterrupt, SystemExit):
            log.warning("Got Exit or Ctrl-C. Stopping.")
            RunPlease = False
            pass
        except AttributeError as e:
            log.exception(e)
            log.error("AttributeError, restarting")
            sys.exit(1)

    HAE.stop()
    eventWorker.stop()
    sys.exit(0)
