from shared.SafetyComponent import SafetyComponent
from shared.SafetyMechanism import SafetyMechanism

class WindowComponent(SafetyComponent):
    def __init__(self, hass_app):
        super().__init__(hass_app)  # Call the base class __init__
        # Initialization specific to WindowComponent
        # Example: Initializing a safety mechanism for window sensors
        self.safety_mechanisms = [
            SafetyMechanism(self.hass_app, ["binary_sensor.office_window_contact_contact, sensor.office_temperature"], self.SM_WMC_2, 'SM_WMC_2 - office')
        ]

    def SM_WMC_2(self,window_sensors : list, temperature_sensor : str):
        self.hass_app.log('SM_WMC_2 start')
        
        self.hass_app.log('SM_WMC_2 stop')
        