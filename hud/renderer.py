import logging

from pgu import gui
from . import elements

log = logging.getLogger('HUD.renderer')
log.addHandler(logging.NullHandler())


def renderConfig(hastates, width, height, config, EventHandler):
    states = {}
    for state in hastates:
        states[state.entity_id] = state
    views = {view: content for view, content in states.items()
             if content.domain == "group" and
             "view" in content.attributes and
             content.attributes["view"]}

    log.debug(views)
    # For now, render the default_view
    default_view = views["group.beneden"]
    container = renderView(default_view, states, width, height, EventHandler)
    log.info("Startup: Load elements onto surface")
    main = gui.Container(width=width, height=height)
    header = elements.Header("Home Assistant", width=width, height=40)
    slidebox = elements.Scrollable(container, width=width, height=height)
    main.add(header, 0, 0)
    main.add(slidebox, 0, 60)
    return main


def renderView(view, states, width, height, EventHandler):
    container = gui.Table(width=width, vpadding=0, hpadding=0, cls="desktop")
    for entity in view.attributes["entity_id"]:
        if entity in states:
            state = states[entity]
            if state.domain == "group":
                row = renderGroup(state, states, width, height, EventHandler)
                container.td(row)
                container.tr()
                container.td(gui.Spacer(cls="desktop", width=width, height=5))
                container.tr()
            else:
                row = renderEntity(state, states, width, height, EventHandler)
                if row:
                    container.td(row)
                    container.td(gui.Spacer(cls="desktop",
                                            width=width, height=20))
                    container.tr()
                    container.tr()
        else:
            log.info("Cannot find any state for {}. Skipping".format(entity))
    return container


def renderEntity(entity, states, width, height, EventHandler, last=False):
    row = None
    if entity.domain == "light":
        row = elements.rowLight(entity, last=last, width=width)
        log.info("Startup: Adding Event listener for {}"
                 .format(entity))
    elif entity.domain in ('sensor', 'device_tracker'):
        row = elements.rowSensor(entity, last=last, width=width)
        log.info("Startup: Adding Event listener for {}"
                 .format(entity))
    elif entity.domain == "media_player":
        row = elements.media_player.MediaPlayer(
            entity, width=width)
    else:
        log.info("FIXME:entity {0} has an unknown domain {1}"
                 .format(entity.name, entity.domain))
    if row:
        EventHandler.add_listener(entity.entity_id, row.set_hass_event)
    return row


def renderGroup(group, states, width, height, EventHandler):
    c = gui.Table(width=width, vpadding=0, hpadding=0, cls="desktop")
    header = elements.rowHeader(group, table=c, width=width)
    EventHandler.add_listener(group.entity_id, header.set_hass_event)
    c.td(header.draw(), align=-1)
    c.tr()
    log.info("Startup: Building group %s", group.name)
    entities = group.attributes['entity_id']
    for entity in entities:
        log.info("Startup: Loading entity {}".format(
            entity))
        try:
            state_entity = states[entity]
        except KeyError:
            log.info("Cannot find any state for {0}, skipping"
                     .format(entity))
            continue
        row = renderEntity(
            state_entity,
            states,
            width, height,
            EventHandler,
            last=(True if entity == entities[-1] else False))
        if row:
            c.td(row.draw(), align=-1)
            c.tr()
    return c
