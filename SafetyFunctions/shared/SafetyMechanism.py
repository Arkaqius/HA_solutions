import appdaemon.plugins.hass.hassapi as hass

class SafetyMechanism:
    def __init__(self, hass_app, entities, callback, name : str):
        self.hass_app = hass_app
        self.entities = entities
        self.callback = callback
        self.name = name
        self.setup_listeners()

    def setup_listeners(self):
        """
        Set up listeners for each entity in the list.
        """
        for entity in self.entities:
            self.hass_app.listen_state(self.entity_changed, entity)

    def entity_changed(self, entity, attribute, old, new, kwargs):
        """
        Called when a monitored entity changes state.
        """
        self.callback(entity, attribute, old, new, kwargs)