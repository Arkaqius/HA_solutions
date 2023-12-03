import appdaemon.plugins.hass.hassapi as hass

class SafetyFunctions(hass.Hass):

    def initialize(self):
        self.set_state("sensor.SafetyFunctions_health", state="good")
    