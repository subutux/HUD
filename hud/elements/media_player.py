from pgu import gui
import imagesize
from .icons import icons
from .label import eventLabel
import homeassistant.const as hasconst
from .. import eventWorker


class PlayButton(gui.Button):
    def __init__(self, haevent, **kwargs):
        self.haevent = None
        super().__init__(haevent.name, **kwargs)

        self.set_hass_event(haevent)
        self.connect(gui.CLICK, self.callback)
        self.icon = icons.icon("mdi-play", 20,
                               color="rgb(200,200,200)")
        super().__init__(self.icon, **kwargs)

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


class PrevButton(gui.Button):
    def __init__(self, haevent, **kwargs):
        self.haevent = None
        super().__init__(haevent.name, **kwargs)

        self.set_hass_event(haevent)
        self.connect(gui.CLICK, self.callback)
        self.icon = icons.icon("mdi-skip-backward", 20,
                               color="rgb(200,200,200)")
        super().__init__(self.icon, **kwargs)

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


class NextButton(gui.Button):
    def __init__(self, haevent, **kwargs):
        self.haevent = None
        super().__init__(haevent.name, **kwargs)

        self.set_hass_event(haevent)
        self.connect(gui.CLICK, self.callback)
        self.icon = icons.icon("mdi-skip-forward", 20,
                               color="rgb(200,200,200)")
        super().__init__(self.icon, **kwargs)

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


class rowMediaInfo(object):
    def __init__(self, entity, width=320):
        self.widget = gui.Container(width=width,
                                    align=-1, valign=-1,
                                    background=(255, 255, 255))
        self.title = eventLabel(entity, "media_title",
                                width=width - 10, background=(255, 255, 255))
        self.artist = eventLabel(entity, "media_artist",
                                 width=width - 10, background=(255, 255, 255))
        self.name = eventLabel(entity, "friendly_name",
                               width=width - 10, background=(255, 255, 255))
        self.width = width
        self.widget.add(self.name, 10, 0)
        self.widget.add(self.title, 10, 20)
        self.widget.add(self.artist, 10, 42)
        self.pictureUrl = None
        self.set_hass_event(entity)

    def BackgroundFromFile(self, tmpfile):
        size = imagesize.get(tmpfile)
        if size[0] > (self.width - 100):
            wpercent = ((self.width - 100) / float(size[0]))
            hsize = int(float(size[1]) * wpercent)
        else:
            hsize = size[1]
        Image = gui.Image(tmpfile, style={
            "width": int(self.width - 100),
            "height": hsize
        })
        # os.remove(tmpfile)
        self.widget.add(Image, 50, 0)
        self.widget.add(self.name, 10, hsize - (19 * 3))
        self.widget.add(self.title, 10, hsize - (19 * 2))
        self.widget.add(self.artist, 10, hsize - 19)
        self.widget.repaint()

    def draw(self):
        self.widget.resize(width=self.width)
        self.widget.repaint()
        return self.widget

    def set_hass_event(self, event):
        self.entity = event
        if "entity_picture" in self.entity.attributes:
            if self.pictureUrl != self.entity.attributes["entity_picture"]:
                self.pictureUrl = self.entity.attributes["entity_picture"]
                eventWorker.do("download",
                               (self.BackgroundFromFile, self.pictureUrl))
        self.name.set_hass_event(event)
        self.artist.set_hass_event(event)
        self.title.set_hass_event(event)


class rowMediaControls(object):
    def __init__(self, entity, width=320):
        self.widget = gui.Container(height=20, width=width,
                                    align=-1, valign=-1,
                                    background=(255, 255, 255))
        self.entity = entity
        self.width = width
        self.prev = PrevButton(self.entity, height=20, width=36)
        self.play = PlayButton(self.entity, height=20, width=40)
        self.next = NextButton(self.entity, height=20, width=36)

    def draw(self):
        total_width = (36 + 16) * 2 + (40 + 16)
        offset = (self.width - total_width) / 2
        self.widget.add(self.prev, offset, 0)
        self.widget.add(self.play, offset + 36 + 16, 0)
        self.widget.add(self.next, offset + (36 + 16) + (40 + 16), 0)
        return self.widget

    def set_hass_event(self, event):
        self.entity = event
        self.prev.set_hass_event(event)
        self.play.set_hass_event(event)
        self.next.set_hass_event(event)


class MediaPlayer(object):
    def __init__(self, entity, width=320):
        self.widget = gui.Table(height=80, width=width,
                                align=-1, valign=-1,
                                background=(255, 255, 255))
        self.info = rowMediaInfo(entity, width=width)
        self.controls = rowMediaControls(entity, width=width)
        self.info.set_hass_event(entity)
        self.controls.set_hass_event(entity)
        self.widget.tr()
        self.widget.td(self.info.draw())
        self.widget.tr()
        self.widget.td(self.controls.draw())

    def draw(self):
        self.widget.repaint()
        return self.widget

    def set_hass_event(self, event):
        self.entity = event
        self.info.set_hass_event(event)
        self.controls.set_hass_event(event)

