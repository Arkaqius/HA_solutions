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
        self.safety_mechanisms = []
        
        # Get config
        self.hass_app.log(self.hass_app.args)
        
        for sm_cfg in self.hass_app.args['safety_mechanisms']['WindowComponent']['SM_WMC_2']:
            name = sm_cfg['name']
            window_sensors = sm_cfg['window_sensors']
            temperature_sensor = sm_cfg['temperature_sensor']
            if(self.validate_entities(  {'window_sensors' : window_sensors, 'temperature_sensor': temperature_sensor},
                                        {'window_sensors': List[str], 'temperature_sensor' : str})):
                self.safety_mechanisms.append(
                                SafetyMechanism(self.hass_app,
                                self.sm_wmc_2,
                                name,
                                window_sensors=window_sensors,
                                temperature_sensor=temperature_sensor)
                )
            else:
                self.hass_app.log(f'SM {name} was not created due error', level='ERROR')
        
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
            