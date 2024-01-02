'''
TODO
'''
from typing import List
from shared.SafetyComponent import SafetyComponent, safety_mechanism_decorator
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
                            self.sm_wmc_2,
                            'SM_WMC_2 - office',
                            window_sensors=["binary_sensor.office_window_contact_contact"],
                            temperature_sensor="sensor.office_temperature")
        ]

    @safety_mechanism_decorator
    def sm_wmc_2(self, **kwargs):
        """
        Safety mechanism specific for window monitoring.

        :param kwargs: Keyword arguments containing 'window_sensors' and 'temperature_sensor'.
        """
        # 10. Check for required arguments
        if(self.validate_entities(kwargs,
            {'window_sensors': List[str],
            'temperature_sensor' : str})):
            pass
          
            # 20. Perform SM logic
        
            # 30. Perform results actions
        
            # 40. Set/Heal faults
    
            # 50. Perform SafeState
            