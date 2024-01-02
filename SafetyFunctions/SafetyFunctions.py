import appdaemon.plugins.hass.hassapi as hass
from shared.WindowComponent import WindowComponent


class SafetyFunctions(hass.Hass):
    """
    Main class for managing safety functions in the Home Assistant environment.
    """

    def initialize(self):
        """
        Initialize the SafetyFunctions app and its components.
        This method sets up the window sensor component and initializes the health status.
        """
        # Initialize domain-specific components
        self.window_sensor_component = WindowComponent(self)

        # Set the health status after initialization
        self.set_state("sensor.safety_app_health", state="good")
        self.log('Safety app started')

        # ... (rest of the SafetyFunctions class)
