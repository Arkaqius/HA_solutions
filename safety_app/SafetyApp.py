import appdaemon.plugins.hass.hassapi as hass

class SafetyApp(hass.Hass):

    def initialize(self):
        self.set_state("sensor.safety_app_health", state="good")