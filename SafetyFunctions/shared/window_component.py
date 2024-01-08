'''
TODO
'''
from typing import List
from shared.safety_component import SafetyComponent, safety_mechanism_decorator
from shared.safety_mechanism import SafetyMechanism
from shared.fault_manager import FaultManager
from shared.recovery_manager import RecoveryManager
from shared.safe_state_manager import SafeStateManager

class WindowComponent(SafetyComponent):
    """ Component handling safety mechanisms for windows. """

    def __init__(self, hass_app):
        """
        Initialize the window component.

        :param hass_app: The Home Assistant application instance.
        """
        super().__init__(hass_app)
        self.safety_mechanisms = []
        self.safety_mechanisms.extend(self.init_sm_wmc2())


    def init_sm_wmc2(self):
        """ Method to init safet mechanism 2 """
        safety_mechanisms = []
        is_param_ok = True
        # Iterate throught all safety mechanism instances
        for sm_cfg in self.hass_app.args['safety_mechanisms']['WindowComponent']['SM_WMC_2']:
            try:
                name = sm_cfg['name']
                window_sensors = sm_cfg['window_sensors']
                temperature_sensor = sm_cfg['temperature_sensor']
                cold_thr = sm_cfg['CAL_THR_Cold']
                cold_rate_thr = sm_cfg['CAL_THR_ColdRate']
                temperature_sensor_rate = sm_cfg['temperature_sensor_rate']
            except KeyError as e:
                self.hass_app.log(f"Key not found in sm_cfg: {e}", level='ERROR')
                is_param_ok = False
            else:
                is_param_ok = self.validate_entities(   {'window_sensors' : window_sensors, 
                                                        'temperature_sensor': temperature_sensor,
                                                        'cold_thr':cold_thr,
                                                        'cold_rate_thr':cold_rate_thr,
                                                        'temperature_sensor_rate':temperature_sensor_rate},
                                                        {'window_sensors': List[str],
                                                        'temperature_sensor' : str,
                                                        'cold_thr':float,
                                                        'cold_rate_thr':float,
                                                        'temperature_sensor_rate': str})
            if is_param_ok:
                safety_mechanisms.append(
                                            SafetyMechanism(self.hass_app,
                                            self.sm_wmc_2,
                                            name,
                                            window_sensors=window_sensors,
                                            temperature_sensor=temperature_sensor,
                                            cold_thr = cold_thr,
                                            cold_rate_thr = cold_rate_thr,
                                            temperature_sensor_rate = temperature_sensor_rate)
                )
            else:
                self.hass_app.log(f'SM {name} was not created due error', level='ERROR')
        return safety_mechanisms


    @safety_mechanism_decorator
    def sm_wmc_2(self, sm : SafetyMechanism):
        """
        Safety mechanism specific for window monitoring.

        :param kwargs: Keyword arguments containing 'window_sensors' and 'temperature_sensor'.
        """
        is_active : bool = False
        temperature : float = 0.0
        temperature_rate : float = 0.0
        windows_state : bool = False
        try:
            temperature = float(self.hass_app.get_state(sm.sm_args['temperature_sensor']))
            temperature_rate = float(self.hass_app.get_state(sm.sm_args['temperature_sensor_rate']))
            windows_state = any(self.hass_app.get_state(sensor) == "false" for sensor in sm.sm_args["window_sensors"])
        except ValueError as e:
            self.hass_app.log(f"Float conversion error: {e}", level='ERROR')
            
        # 20. Perform SM logic
        if(temperature < sm.sm_args['cold_thr'] and not windows_state):
            is_active = True
        elif(temperature_rate < sm.sm_args['cold_rate_thr'] and not windows_state):
            is_active = True
        else:
            is_active = False      

        if is_active:
            self.hass_app.log(f"{sm.name} is active")
            