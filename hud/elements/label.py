from pgu import gui
import logging

log = logging.getLogger('HUD.element.eventLabel')
log.addHandler(logging.NullHandler())


class eventLabel(gui.Label):
    def __init__(self, entity, attr="state", **params):
        self.haevent = entity
        self.attr = attr
        super().__init__("", **params)
        self.width = params.get("width", None)
        self.set_hass_event(entity)

    def set_hass_event(self, haevent):
        self.haevent = haevent
        if self.attr in haevent.attributes:
            value = str(haevent.attributes[self.attr])
            self.value = value
        else:
            self.value = ""
        if self.width:
            self.style.width = self.width
        self.chsize()
        self.repaint()

    def resize(self, width=None, heigth=None):
        return (self.width, self.style.height)

