import logging

from pgu import gui
from . import elements

log = logging.getLogger('HUD.renderer')
log.addHandler(logging.NullHandler())


def render(_states, width, height, config, EventHandler):
    container = gui.Table(width=width, vpadding=0, hpadding=0, cls="desktop")
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
            header = elements.rowHeader(state, table=c, width=width)
            EventHandler.add_listener(state.entity_id, header.set_hass_event)
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
                        row = elements.rowLight(state_entity, last=(
                            True if entity == entities[-1] else False),
                            width=width,
                            table=c)
                        log.info("Startup: Adding Event listener for {}"
                                 .format(entity))
                        EventHandler.add_listener(entity, row.set_hass_event)
                        # row.draw()
                        c.td(row.draw(), align=-1)
                    elif state_entity.domain in ('sensor', 'device_tracker'):
                        row = elements.rowSensor(state_entity, last=(
                            True if entity == entities[-1] else False),
                            width=width)
                        log.info("Startup: Adding Event listener for {}"
                                 .format(entity))
                        EventHandler.add_listener(entity, row.set_hass_event)
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
    main.add(slidebox, 0, 60)
    return main
