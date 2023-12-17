from shared.SafetyComponent import SafetyComponent
from shared.SafetyMechanism import SafetyMechanism

class WindowComponent(SafetyComponent):
    """ Component handling safety mechanisms for windows. """

    def __init__(self, hass_app):
        """
        Initialize the window component.

        :param hass_app: The Home Assistant application instance.
        """
        super().__init__(hass_app)
        self.safety_mechanisms = [
            SafetyMechanism(self.hass_app,
                            ["binary_sensor.office_window_contact_contact", "sensor.office_temperature"],
                            self.SM_WMC_2,
                            'SM_WMC_2 - office',
                            window_sensors=["binary_sensor.office_window_contact_contact"],
                            temperature_sensor="sensor.office_temperature")
        ]

    def SM_WMC_2(self, **kwargs):
        """
        Safety mechanism specific for window monitoring.

        :param kwargs: Keyword arguments containing 'window_sensors' and 'temperature_sensor'.
        """
        # Check for required arguments
        required_args = ['window_sensors', 'temperature_sensor']
        for arg in required_args:
            if arg not in kwargs:
                self.hass_app.log(f"Missing required argument: {arg}", level="ERROR")
                return

        # Validate window_sensors
        if not isinstance(kwargs['window_sensors'], list) or not all(SafetyComponent.is_valid_binary_sensor(sensor) for sensor in kwargs['window_sensors']):
            self.hass_app.log("window_sensors must be a list of valid binary sensor entity names", level="ERROR")
            return

        # Validate temperature_sensor
        if not SafetyComponent.is_valid_sensor(kwargs['temperature_sensor']):
            self.hass_app.log("temperature_sensor must be a valid sensor entity name", level="ERROR")
            return

        self.hass_app.log('SM_WMC_2 start')
        self.hass_app.log(f"Mine kwargs {kwargs}")
        self.hass_app.log('SM_WMC_2 stop')