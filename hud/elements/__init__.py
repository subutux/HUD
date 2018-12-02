from pgu import gui
from pygame.locals import *
import pygame.event
from pgu.gui.const import *
from .. import eventWorker
from . import media_player
from .label import eventLabel
from .icons import icons
import homeassistant.const as hasconst
import moosegesture
import logging
log = logging.getLogger('HUD.Elements')
log.addHandler(logging.NullHandler())


class Scrollable(gui.SlideBox):
    def __init__(self, widget, width, height,
                 scroll_horizontal=False, **params):
        super().__init__(widget, width, height)
        self.connect(gui.MOUSEMOTION, self.motion)
        self.connect(gui.MOUSEBUTTONUP, self.setMotion, False)
        self.connect(gui.MOUSEBUTTONDOWN, self.setMotion, True)
        self.inMotion = False
        self.prevLocs = []
        self.hscroll = 0
        self.vscroll = 0
        self.scroll_horizontal = scroll_horizontal

    def setMotion(self, motion):
        self.inMotion = motion
        if not motion:
            self.prevLocs = []
            if self.hscroll < 0:
                self.hscroll = 0
                self.offset = (self.hscroll, self.vscroll)
                self.repaint()
            if self.vscroll < 0:
                self.vscroll = 0
                self.offset = (self.hscroll, self.vscroll)
                self.repaint()

    def addPrevLoc(self, loc):
        self.prevLocs.append(loc)

    def motion(self, _event):
        if self.inMotion:
            self.addPrevLoc(_event.pos)
            direction = moosegesture.getGesture(self.prevLocs)
            if len(direction) == 0:
                return
            if direction[-1].startswith("D"):
                self.vscroll = self.vscroll - 5
            elif direction[-1].startswith("U"):
                self.vscroll = self.vscroll + 5
            elif direction[-1] == "L" and self.scroll_horizontal:
                self.hscroll = self.hscroll + 5
            elif direction[-1] == "R" and self.scroll_horizontal:
                self.hscroll = self.hscroll - 5
            self.offset = (self.hscroll, self.vscroll)
            self.repaint()


class Light(gui.Button):
    def __init__(self, haevent, **kwargs):
        self.haevent = None
        super().__init__(haevent.name, **kwargs)

        self.set_hass_event(haevent)
        self.connect(gui.CLICK, self.callback)

    def callback(self):
        eventWorker.do("toggle_event", self.haevent)

    def set_hass_event(self, haevent):
        self.haevent = haevent

        if self.haevent.state == hasconst.STATE_OFF:

            self.state = 0
            self.pcls = ""
        elif self.haevent.state == hasconst.STATE_ON:

            self.state = 1
            self.pcls = "down"
        self.repaint()

    def event(self, e):

        if e.type == ENTER:
            self.repaint()
        elif e.type == EXIT:
            self.repaint()
        elif e.type == FOCUS:
            self.repaint()
        elif e.type == BLUR:
            self.repaint()
        elif e.type == KEYDOWN:
            if e.key == K_SPACE or e.key == K_RETURN:
                self.state = 1
                self.repaint()
        elif e.type == MOUSEBUTTONDOWN:
            self.state = 1
            self.repaint()
        elif e.type == KEYUP:
            if self.state == 1:
                sub = pygame.event.Event(CLICK, {'pos': (0, 0), 'button': 1})
                # self.send(sub.type,sub)
                self._event(sub)
                # self.event(sub)
                # self.click()

            # self.state = 0
            self.repaint()
        elif e.type == MOUSEBUTTONUP:
            # self.state = 0
            self.repaint()
        elif e.type == CLICK:
            self.click()

#       if self.haevent.state == hasconst.STATE_ON: img = self.style.down
#       s.blit(img,(0,0))


class Sensor(gui.Button):
    def __init__(self, haevent, **kwargs):
        self.haevent = None
        super().__init__(haevent.name, **kwargs)

        self.set_hass_event(haevent)

    def set_hass_event(self, haevent):
        self.haevent = haevent

        if self.haevent.state == hasconst.STATE_OFF:

            self.state = 0
            self.pcls = ""
        elif self.haevent.state == hasconst.STATE_ON:

            self.state = 1
            self.pcls = "down"
        self.repaint()

    def event(self, e):
        pass


class LightSwitch(gui.Switch):
    def __init__(self, haevent, **kwargs):
        self.haevent = None

        super().__init__(value=False, **kwargs)

        self.connect(gui.CLICK, self.callback)
        self.set_hass_event(haevent)

    def callback(self):
        eventWorker.do("toggle_event", self.haevent)

    def click(self):
        pass

    def set_hass_event(self, haevent):
        self.haevent = haevent
        if self.haevent.state == hasconst.STATE_OFF:
            self._value = False
        elif self.haevent.state == hasconst.STATE_ON:
            self._value = True
        self.repaint()


class Header(gui.Button):
    def __init__(self, name, **kwargs):
        kwargs.setdefault("cls", "header")
        self.pcls = "down"
        self.state = 1
        super().__init__(name, **kwargs)

    def event(self, e):

        if e.type == ENTER:
            self.repaint()
        elif e.type == EXIT:
            self.repaint()
        elif e.type == FOCUS:
            self.repaint()
        elif e.type == BLUR:
            self.repaint()
        elif e.type == KEYDOWN:
            if e.key == K_SPACE or e.key == K_RETURN:
                self.state = 1
                self.repaint()
        elif e.type == MOUSEBUTTONDOWN:
            self.state = 1
            self.repaint()
        elif e.type == KEYUP:
            if self.state == 1:
                sub = pygame.event.Event(CLICK, {'pos': (0, 0), 'button': 1})
                # self.send(sub.type,sub)
                self._event(sub)
                # self.event(sub)
                # self.click()

            # self.state = 0
            self.repaint()
        elif e.type == MOUSEBUTTONUP:
            # self.state = 0
            self.repaint()
        elif e.type == CLICK:
            self.click()


class sensorValue(gui.Button):
    def __init__(self, haevent, **kwargs):
        self.haevent = None
        super().__init__("", **kwargs)
        self.set_hass_event(haevent)

    def set_hass_event(self, haevent):

        self.haevent = haevent
        self.sValue = haevent.state
        if "unit_of_measurement" in haevent.attributes:
            self.sValue += " {}".format(
                haevent.attributes["unit_of_measurement"])
        self.value = self.sValue
        self.repaint()

    def event(self, e):
        pass


class rowLight(object):
    def __init__(self, entity, last=False, width=320, table=None):
        self.width = width
        # self.widget = gui.Table(width=width) if table == None else table
        self.widget = gui.Container(
            height=20, width=width,
            align=-1, valign=-1,
            background=(220, 220, 220))
        self.entity = entity
        self.btn_cls = "button"
        self.sw_cls = "switch"
        self.ligth_width = (width - 36) - 36
        self.icon = 'mdi-lightbulb'

        if last:
            self.btn_cls += "_last"
            self.sw_cls += "_last"

    def set_hass_event(self, event):
        self.light.set_hass_event(event)
        if self.entity.state != "unknown":
            self.switch.set_hass_event(event)

    def draw(self):
        if self.icon:
            self.iconButton = gui.Button(icons.icon(
                self.icon, 20, color="rgb(68, 115, 158)"),
                cls=self.btn_cls, height=20, width=36)
        else:
            self.iconButton = gui.Button(
                " ", cls=self.btn_cls, height=20, width=36)
        self.light = Light(self.entity,
                           cls=self.btn_cls, width=self.width - 84, height=20)
        if self.entity.state != "unknown":
            self.switch = LightSwitch(self.entity, cls=self.sw_cls)
        else:
            self.switch = gui.Button("", cls=self.btn_cls, width=20, height=20)

        self.widget.add(self.iconButton, 0, 0)
        self.widget.add(self.light, 36, 0)
        self.widget.add(self.switch, self.width - 36, 0)
        return self.widget


class rowSensor(object):
    def __init__(self, entity, last=False, width=320):
        self.width = width
        # self.widget = gui.Table(width=width)
        self.widget = gui.Container(
            height=20, width=self.width,
            align=-1, valign=-1, background=(220, 220, 220))
        self.entity = entity
        self.btn_cls = "button"
        self.sw_cls = "sensor"

        self.sensorName_width = (width - 36)
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

    def set_hass_event(self, event):
        """
        Update the hass event on our widgets

        We need to re-calculate the width of self.sensorName
        because the sensor value could be larger/smaller then
        its previous state.

        We then remove the self.state from the widget & re-add it
        """
        self.state.set_hass_event(event)
        stateWidth = self.state._value.style.width + \
            self.state.style.padding_left + self.state.style.padding_right
        self.sensorName.style.width = self.sensorName_width - stateWidth
        self.sensorName.set_hass_event(event)
        self.widget.remove(self.state)
        self.widget.add(self.state, self.width - stateWidth, 0)

    def draw(self):
        if self.icon:
            self.iconButton = gui.Button(icons.icon(
                self.icon, 20, color="rgb(68, 115, 158)"),
                cls=self.btn_cls, height=20, width=36)
        else:
            self.iconButton = gui.Button(
                " ", cls=self.btn_cls, height=20, width=36)
        self.state = sensorValue(
            self.entity, cls=self.sw_cls, height=20)
        stateWidth = self.state._value.style.width + \
            self.state.style.padding_left + self.state.style.padding_right
        self.sensorName = Sensor(
            self.entity, cls=self.btn_cls, width=(
                self.sensorName_width - stateWidth), height=20)
        self.widget.add(self.iconButton, 0, 0)
        self.widget.add(self.sensorName, 36, 0)
        self.widget.add(self.state, self.width - stateWidth, 0)
        return self.widget


class rowHeader(rowLight):
    def __init__(self, entity, width=320, table=None):
        self.width = width
        super().__init__(entity, last=False, width=width, table=table)
        self.icon = None
        self.btn_cls = "button_header"
