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
    
    # Static class variables to keep debounce
    sm_wmc1_debounce = 0
    sm_wmc1_inhibit = False
    sm_wmc2_debounce = 0
    sm_wmc2_inhibit = False
    
    def __init__(self, hass_app):
        """
        Initialize the window component.

        :param hass_app: The Home Assistant application instance.
        """
        super().__init__(hass_app)
        self.safety_mechanisms = []
        self.safety_mechanisms.extend(self.init_sm_wmc1())
        self.safety_mechanisms.extend(self.init_sm_wmc2())

    def init_sm_wmc1(self):
        """ Method to init safet mechanism 1 """
        safety_mechanisms = []
        is_param_ok = True
        # Iterate throught all safety mechanism instances
        for sm_cfg in self.hass_app.args['safety_mechanisms']['WindowComponent']['SM_WMC_1']:
            try:
                name = sm_cfg['name']
                temperature_sensor = sm_cfg['temperature_sensor']
                cold_thr = sm_cfg['CAL_LOW_TEMP_THRESHOLD']
            except KeyError as e:
                self.hass_app.log(f"Key not found in sm_cfg: {e}", level='ERROR')
                is_param_ok = False
            else:
                is_param_ok = self.validate_entities(   {'temperature_sensor': temperature_sensor,
                                                        'cold_thr':cold_thr},
                                                        {'temperature_sensor' : str,
                                                        'cold_thr':float})
            if is_param_ok:
                safety_mechanisms.append(
                                            SafetyMechanism(self.hass_app,
                                            self.sm_wmc_1,
                                            name,
                                            temperature_sensor=temperature_sensor,
                                            cold_thr = cold_thr)
                )
            else:
                self.hass_app.log(f'SM {name} was not created due error', level='ERROR')
        return safety_mechanisms

    def init_sm_wmc2(self):
        """ Method to init safet mechanism 2 """
        safety_mechanisms = []
        is_param_ok = True
        # Iterate throught all safety mechanism instances
        for sm_cfg in self.hass_app.args['safety_mechanisms']['WindowComponent']['SM_WMC_2']:
            try:
                name = sm_cfg['name']
                temperature_sensor = sm_cfg['temperature_sensor']
                cold_thr = sm_cfg['CAL_LOW_TEMP_THRESHOLD']
                forecast_timespan = sm_cfg['CAL_FORECAST_TIMESPAN']
                temperature_sensor_rate = sm_cfg['temperature_sensor_rate']
            except KeyError as e:
                self.hass_app.log(f"Key not found in sm_cfg: {e}", level='ERROR')
                is_param_ok = False
            else:
                is_param_ok = self.validate_entities(   {'temperature_sensor': temperature_sensor,
                                                        'cold_thr':cold_thr,
                                                        'forecast_timespan':forecast_timespan,
                                                        'temperature_sensor_rate':temperature_sensor_rate},
                                                        {'temperature_sensor' : str,
                                                        'cold_thr':float,
                                                        'forecast_timespan':float,
                                                        'temperature_sensor_rate': str})
            if is_param_ok:
                safety_mechanisms.append(
                                            SafetyMechanism(self.hass_app,
                                            self.sm_wmc_2,
                                            name,
                                            temperature_sensor=temperature_sensor,
                                            cold_thr = cold_thr,
                                            forecast_timespan = forecast_timespan,
                                            temperature_sensor_rate = temperature_sensor_rate)
                )
            else:
                self.hass_app.log(f'SM {name} was not created due error', level='ERROR')
        return safety_mechanisms


    @safety_mechanism_decorator
    def sm_wmc_1(self, sm : SafetyMechanism):
        """
        Safety mechanism specific for window monitoring.

        :param kwargs: Keyword arguments containing 'window_sensors' and 'temperature_sensor'.
        """
        is_active : bool = False
        temperature : float = 0.0
        # 10. Check if debouncing in process
        if WindowComponent.sm_wmc1_inhibit:
            # 20. Get inputs
            try:
                temperature = float(self.hass_app.get_state(sm.sm_args['temperature_sensor']))
                #temperature_rate = float(self.hass_app.get_state(sm.sm_args['temperature_sensor_rate']))
                #windows_state = any(self.hass_app.get_state(sensor) == "false" for sensor in sm.sm_args["window_sensors"])
            except ValueError as e:
                self.hass_app.log(f"Float conversion error: {e}", level='ERROR')
                
            # 30. Perform SM logic
            if(temperature < sm.sm_args['cold_thr']):
                if True: # Todo call FaultManger to check if prefualt is set active
                    WindowComponent.sm_wmc1_debounce-=1
                    if WindowComponent.sm_wmc1_debounce == -3:
                        is_active = True
                        WindowComponent.sm_wmc1_inhibit = False
                    else:
                        # Inhibit async triggers and scheduler next debounce in next CAL_FORECAST_TIMESPAN
                        WindowComponent.sm_wmc1_inhibit = True
                        self.hass_app.run_in(self.sm_wmc_1, 60,sm)
                else:
                    pass # Do nothing
            else:
                if True: # Todo call FaultManger to check if prefualt is set cleared
                    WindowComponent.sm_wmc1_debounce+=1
                    if WindowComponent.sm_wmc1_debounce == 3:
                        is_active = False
                        WindowComponent.sm_wmc1_inhibit = False
                    else:
                        # Inhibit async triggers and scheduler next debounce in next CAL_FORECAST_TIMESPAN
                        WindowComponent.sm_wmc1_inhibit = True
                        self.hass_app.run_in(self.sm_wmc_1, 60,sm)
                else:
                    pass # Do nothing
        if is_active:
            self.hass_app.log(f"{sm.name} is active")
            
            
    @safety_mechanism_decorator
    def sm_wmc_2(self, sm : SafetyMechanism):
        """
        Safety mechanism specific for window monitoring.

        :param kwargs: Keyword arguments containing 'window_sensors' and 'temperature_sensor'.
        """
        is_active : bool = False
        temperature : float = 0.0
        # 10. Check if debouncing in process
        if WindowComponent.sm_wmc2_inhibit:
            # 20. Get inputs
            try:
                temperature = float(self.hass_app.get_state(sm.sm_args['temperature_sensor']))
                temperature_rate = float(self.hass_app.get_state(sm.sm_args['temperature_sensor_rate']))
            except ValueError as e:
                self.hass_app.log(f"Float conversion error: {e}", level='ERROR')
                
            # 30. Perform SM logic 
            forecasted_temperature = temperature + temperature_rate*sm.sm_args['forecast_timespan']
            
            if(forecasted_temperature < sm.sm_args['cold_thr']):
                if True: # Todo call FaultManger to check if prefualt is set active
                    WindowComponent.sm_wmc2_debounce-=1
                    if WindowComponent.sm_wmc2_debounce == -3:
                        is_active = True
                        WindowComponent.sm_wmc2_inhibit = False
                    else:
                        # Inhibit async triggers and scheduler next debounce in next CAL_FORECAST_TIMESPAN
                        WindowComponent.sm_wmc2_inhibit = True
                        self.hass_app.run_in(self.sm_wmc_2, 60,sm)
                else:
                    pass # Do nothing
            else:
                if True: # Todo call FaultManger to check if prefualt is set cleared
                    WindowComponent.sm_wmc2_debounce+=1
                    if WindowComponent.sm_wmc2_debounce == 3:
                        is_active = False
                        WindowComponent.sm_wmc2_inhibit = False  
                    else:
                        # Inhibit async triggers and scheduler next debounce in next CAL_FORECAST_TIMESPAN
                        WindowComponent.sm_wmc2_inhibit = True
                        self.hass_app.run_in(self.sm_wmc_2, 60,sm)
                else:
                    pass # Do nothing
        if is_active:
            self.hass_app.log(f"{sm.name} is active")
        