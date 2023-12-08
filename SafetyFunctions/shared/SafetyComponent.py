import appdaemon.plugins.hass.hassapi as hass

# Base class for domain-specific components
class SafetyComponent():
    def __init__(self,hass_app):
        self.hass_app = hass_app
        # Common initialization for all safety components

    def handle_sensor_change(self, entity, attribute, old, new, kwargs):
        pass