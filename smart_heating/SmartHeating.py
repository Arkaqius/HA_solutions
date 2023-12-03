'''
Smart heating AppDeamon application.
'''
import datetime
from math import nan
from enum import Enum
import appdaemon.plugins.hass.hassapi as hass

__author__ = 'Arkaqius'
'''
Offset smaller than 0 -> smaller flow
Offset bigger than 0 -> bigger flow
'''

#region Enumerations
class ROOM_INDEX_FH(Enum):
    '''
    Floor heating room index enumeration.
    '''
    LIVING_ROOM = 0
    CORRIDOR = 1
    BATHROOM = 2
    ENTRANCE = 3
    UPPER_CORRIDOR = 4
    WARDROBE = 5
    UPPER_BATHROOM = 6
    SIZE = 7

class ROOM_INDEX_RAD(Enum):
    '''
    Radaitor heating room index enumeration.
    '''
    OFFICE = 0
    KIDSROOM = 1
    BEDROOM = 2
    GARAGE = 3
    NUM_OF_RADIATORS = 4

class TRV_INDEX(Enum):
    '''
    TRV valves index enumeration.
    '''
    OFFICE = 0
    KIDSROOM = 1
    BEDROOM_LEFT = 2
    BEDROOM_RIGHT = 3
    GARAGE = 4
    NUM_OF_RADIATORS = 5
#endregion

class SmartHeating(hass.Hass):
    """
    SmartHeating - An AppDaemon app for intelligent heating control.

    The SmartHeating class is designed to optimize and control heating elements
    across various zones/rooms in a home automation setup using Home Assistant.
    This app utilizes the AppDaemon framework to interact with Home Assistant, 
    enabling the orchestration of various entities and automations for a 
    smart heating solution.

    Note: Ensure that the relevant Home Assistant entities (sensors, 
          climate entities, etc.) are configured and working properly for 
          effective use of this app.
    """
#region Cfg init functions
    def init_config(self) -> None:
        """
        Load and set up configuration from provided args.

        Extracts parameters and HALs from `args` for application use.

        Returns:
        None
        """
        # pylint: disable=W0201,C0103
        try:
            # Load config
            self.cycle_time = self.args['config']['cycle_time'] 
            self.warm_flag_offset = self.args['config']['warm_flag_offset']
            self.frezzying_flag_offset = self.args['config']['frezzing_flag_offset']
            self.logging_flag = self.args['config']['logging']
            self.error_offset_update_threshold = self.args['config']['error_offset_update_threshold']
            self.force_flow_offset = self.args['config']['force_flow_off']
            self.radiator_boost_threshold = self.args['config']['radiator_boost_threshold']
            self.rads_error_factor = self.args['config']['rads_error_factor']
            self.force_burn_thres = self.args['config']['force_burn_thres']
            # Load factor parameters
            self.wam_params = self.init_wam_params()
            self.rads_params = self.init_rads_params()
            self.log(f'{self.wam_params}',level='DEBUG')
            self.log(f'{self.rads_params}',level='DEBUG')
            # Load HAL for setpoint mapping In
            self.HAL_office_setpoint_in = self.args['HAL_setpoint_mapping_in']['office_setpoint']
            self.HAL_kidsroom_setpoint_in = self.args['HAL_setpoint_mapping_in']['kidsroom_setpoint']
            self.HAL_bedroom_setpoint_in = self.args['HAL_setpoint_mapping_in']['bedroom_setpoint']
            self.HAL_garage_setpoint_in = self.args['HAL_setpoint_mapping_in']['garage_setpoint']
            # Load HAL for setpoint mapping out
            self.HAL_office_setpoint_out = self.args['HAL_setpoint_mapping_out']['office_setpoint']
            self.HAL_kidsroom_setpoint_out = self.args['HAL_setpoint_mapping_out']['kidsroom_setpoint']
            self.HAL_bedroom_left_setpoint_out = self.args['HAL_setpoint_mapping_out']['bedroom_left_setpoint']
            self.HAL_bedroom_right_setpoint_out = self.args['HAL_setpoint_mapping_out']['bedroom_right_setpoint']
            self.HAL_garage_setpoint_out = self.args['HAL_setpoint_mapping_out']['garage_setpoint']
            # Load HAL for TRV pos
            self.HAL_TRV_garage_pos = self.args['HAL_TRV_pos']['garage_pos']
            self.HAL_TRV_bedroomLeft_pos = self.args['HAL_TRV_pos']['bedroomLeft_pos']
            self.HAL_TRV_bedroomRight_pos = self.args['HAL_TRV_pos']['bedroomRight_pos']
            self.HAL_TRV_office_pos = self.args['HAL_TRV_pos']['office_pos']
            self.HAL_TRV_kidsRoom_pos = self.args['HAL_TRV_pos']['kidsRoom_pos']
            #Load HAL for temperature errors
            self.HAL_livingRomm_tError = self.args['HAL_errors']['livingRoom_error']
            self.HAL_corridor_tError = self.args['HAL_errors']['corridor_error']
            self.HAL_bathroom_tError = self.args['HAL_errors']['bathroom_error']
            self.HAL_entrance_tError = self.args['HAL_errors']['entrance_error']
            self.HAL_upperCorridor_tError = self.args['HAL_errors']['uppercorridor_error']
            self.HAL_wardrobe_tError = self.args['HAL_errors']['wardrobe_error']
            self.HAL_upperBathroom_tError = self.args['HAL_errors']['upperbathroom_error']
            self.HAL_office_tError = self.args['HAL_errors']['office_error']
            self.HAL_kidsRoom_tError = self.args['HAL_errors']['kidsroom_error']
            self.HAL_garage_tError = self.args['HAL_errors']['garage_error']
            self.HAL_bedroom_tError = self.args['HAL_errors']['bedroom_error']
            # Load misc HALs
            self.HAL_makeWarm_flag = self.args['HAL_inputs']['makeWarm_flag']
            self.HAL_frezzing_flag = self.args['HAL_inputs']['frezzing_flag']
            self.HAL_forceFlow_flag = self.args['HAL_inputs']['forceFlow_flag']
            self.HAL_corridor_setpoint = self.args['HAL_inputs']['corridor_setpoint']
            self.HAL_wam_value = self.args['HAL_output']['wam_value']
            self.HAL_setpoint_offset = self.args['HAL_output']['setpoint_offset']
            self.HAL_thermostat_setpoint = self.args['HAL_output']['thermostat_setpoint']

        except KeyError as e:
            self.log(f"Configuration Error: Missing key {str(e)}", level="ERROR")
            self.stop_app("HeaterController")

        except TypeError as e:
            self.log(f"Type Error: {str(e)}", level="ERROR")
            self.stop_app("HeaterController")

    def log_config(self):
        config_items = [
            'cycle_time', 'warm_flag_offset', 'frezzying_flag_offset',
            'logging_flag', 'error_offset_update_threshold', 'force_flow_offset',
            'radiator_boost_threshold', 'rads_error_factor', 'force_burn_thres'
        ]

        for item in config_items:
            self.log(f"Config: {item}: {getattr(self, item)}", level="DEBUG")

    def init_wam_params(self) -> list[float]:
        """
        Initialize Weighted Average Method (WAM) parameters.

        Calculates and returns WAM factors based on input configurations.

        Returns:
        List[float]: Normalized WAM factors.
        """
        try:
            wam_factors_sum  = sum(self.args['wam_factors'].values())

            wam_params = [0]*ROOM_INDEX_FH.SIZE.value
            wam_params[ROOM_INDEX_FH.BATHROOM.value] = self.args['wam_factors']['bathroom']/wam_factors_sum
            wam_params[ROOM_INDEX_FH.CORRIDOR.value] = self.args['wam_factors']['corridor']/wam_factors_sum
            wam_params[ROOM_INDEX_FH.ENTRANCE.value] = self.args['wam_factors']['entrance']/wam_factors_sum
            wam_params[ROOM_INDEX_FH.LIVING_ROOM.value] = self.args['wam_factors']['living_room']/wam_factors_sum
            wam_params[ROOM_INDEX_FH.UPPER_BATHROOM.value] = self.args['wam_factors']['upperBathroom']/wam_factors_sum
            wam_params[ROOM_INDEX_FH.UPPER_CORRIDOR.value] = self.args['wam_factors']['upperCorridor']/wam_factors_sum
            wam_params[ROOM_INDEX_FH.WARDROBE.value] = self.args['wam_factors']['wardrobe']/wam_factors_sum

        except KeyError as e:
            self.log(f"Configuration Error: Missing key {str(e)}", level="ERROR")
            self.stop_app("HeaterController")

        except TypeError as e:
            self.log(f"Type Error: {str(e)}", level="ERROR")
            self.stop_app("HeaterController")
        return wam_params
    
    def init_rads_params(self) -> list[float]:
        """
        Initialize radiator factors.

        Returns:
        List[float]: Normalized radiator factors.
        """
        try:
            rads_factors = [0]*ROOM_INDEX_RAD.NUM_OF_RADIATORS.value
            rads_factors_sum  = sum(self.args['rads_factors'].values())
            rads_factors[ROOM_INDEX_RAD.OFFICE.value] = self.args['rads_factors']['office']/rads_factors_sum
            rads_factors[ROOM_INDEX_RAD.KIDSROOM.value] = self.args['rads_factors']['kidsroom']/rads_factors_sum
            rads_factors[ROOM_INDEX_RAD.BEDROOM.value] = self.args['rads_factors']['bedroom']/rads_factors_sum
            rads_factors[ROOM_INDEX_RAD.GARAGE.value] = self.args['rads_factors']['garage']/rads_factors_sum

        except KeyError as e:
            self.log(f"Configuration Error: Missing key {str(e)}", level="ERROR")
            self.stop_app("HeaterController")

        except TypeError as e:
            self.log(f"Type Error: {str(e)}", level="ERROR")
            self.stop_app("HeaterController")
        return rads_factors
#endregion

#region AppDeamon functions
    def initialize(self) -> None:
        """
        Initialize the app, set up the main loop, and define state callbacks.

        - Loads config.
        - Starts the main loop.
        - Initializes state listeners and internal fields.

        Returns:
        None
        """
        # pylint: disable=W0201,C0103
        # Load config
        self.init_config()
        # Initalize app main loop
        start_time = self.datetime() + datetime.timedelta(seconds=self.cycle_time)
        self.handle = self.run_every(self.sh_main_loop, start_time, self.cycle_time) # pylint: disable=W0201

        # Initalize callbacks
        self.listen_state(self.setpoint_update, self.HAL_garage_setpoint_in, devices=[self.HAL_garage_setpoint_out])
        self.listen_state(self.setpoint_update, self.HAL_bedroom_setpoint_in, devices=[self.HAL_bedroom_left_setpoint_out])
        self.listen_state(self.setpoint_update, self.HAL_bedroom_setpoint_in, devices=[self.HAL_bedroom_right_setpoint_out])
        self.listen_state(self.setpoint_update, self.HAL_kidsroom_setpoint_in, devices=[self.HAL_kidsroom_setpoint_out])
        self.listen_state(self.setpoint_update, self.HAL_office_setpoint_in, devices=[self.HAL_office_setpoint_out])

        # Initalize internal fields
        self.thermostat_error = None
        self.wam_errors = None
        self.rads_error = None
        self.warm_flag = None
        self.freezing_flag = None
        self.force_flow_flag = None
        self.radiator_positions = None
        self.previous_offset = 0
        self.log("Initalize finished", level="DEBUG")
        self.log_config()

    def setpoint_update(self, _, __, ___, new, kwargs):
        """
        Update setpoint values upon state change.

        Parameters:
        - new (str): The new state of the entity.
        - kwargs (dict): Additional arguments, expects 'devices'.

        Returns:
        None
        """
        self.log(f'Setpoint update new:{new} kvargs:{kwargs}',level='DEBUG')
        # Check if the device is a TRV and update the temperature
        for device in kwargs['devices']:
            self.call_service('climate/set_temperature',
                            entity_id=device,
                            temperature=new)

    def sh_main_loop(self, _) -> None:
        """
        Main smart heating event loop which orchestrates the logic for managing the heating system.

        This function acts as the core of the smart heating application, managing various system flags, 
        calculating offsets using different system parameters, and enforcing smart heating logic to ensure 
        optimal performance and safety of the heating system.

        Parameters:
            _ (Any): Unused parameter. Can be of any type. 

        Procedure:
            10. Initialize the final offset variable
            20. Gather all necessary current values of the system parameters
            30. Calculate offset using Weighted Arithmetic Mean (WAM) of errors
            40. Apply warm flag to the final offset if applicable
            50. Adjust offset considering the weather forecast (freezing flag)
            60. Check and apply forced burn to the final offset if needed
            70. Enforce safety priority flow and update the final offset
            80. Update the Thermostatic Radiator Valves (TRVs) states
            90. Update the thermostat offset with the finalized value

        Note: 
            - Every step from 30 to 70 adjusts `off_final` based on various parameters and checks.
            - The function interacts with several utility methods to get/set system parameters.
            - Logging and potential future actions (like alerts) may depend on the final offset and other parameters.
            - For a detailed understanding of each step and adjustment, refer to the respective utility method's docstring.

        Returns:
            None: The function does not return any value but updates system states and logs relevant information.
        """
        # pylint: disable=W0201,C0103
        # 10. Init internal variable
        off_final = 0

        # 20. Collect all neccessary current values
        self.thermostat_setpoint = self.sh_get_thermostat_setpoint()
        self.corridor_setpoint = self.sh_get_corridor_setpoint()
        self.wam_errors = self.sh_get_wam_errors()
        self.rads_error = self.sh_get_rad_errors()
        self.warm_flag = self.sh_get_warm_flag()
        self.freezing_flag = self.sh_get_freezing_flag()
        self.force_flow_flag = self.sh_get_force_flow_flag()
        self.radiator_positions = self.sh_get_radiator_postions()
        self.log_input_variables()

        # 30. Calculate offset based on WAM errors
        off_final = self.sh_apply_wam_voting(off_final)
        self.log(f'Offset after wam {off_final}',level = 'DEBUG')
        # 40. Apply warm flag
        off_final = self.sh_apply_warm_flag(off_final)
        self.log(f'Offset after warmflag {off_final}',level = 'DEBUG')
        # 50. Apply weather forecast
        off_final = self.sh_apply_weather_forecast(off_final)
        self.log(f'Offset after  weather forecast {off_final}',level = 'DEBUG')
        # 60. Check if boiler should be forced to burn 
            #(error on thermostat plus offset smaller than 0 and at least one rads error bigger than FORCE_BURN_THR)
        off_final = self.sh_check_forced_burn(off_final)
        self.log(f'Offset after force burn check  {off_final}',level = 'DEBUG')
        # 70. Check force flow flag, If in kids room or bedrrom is error > 0, then force flow
        off_final = self.sh_force_flow_for_safety_prio(off_final)
        self.log(f'Offset after force flow for safety prio {off_final}',level = 'DEBUG')
        # 80. Update TRVs
        self.sh_update_TRVs()
        # 90. Update thermostat offset
        self.sh_update_thermostat(round(off_final, 1))

    def log_input_variables(self):
        variables = [
            'thermostat_setpoint', 'corridor_setpoint',
            'wam_errors', 'rads_error', 'warm_flag',
            'freezing_flag', 'force_flow_flag', 'radiator_positions'
        ]

        for var in variables:
            try:
                self.log(f"Variable: {var}: {getattr(self, var)}", level="DEBUG")
            except AttributeError:
                self.log(f"Variable {var} not found!", level="ERROR")
            except Exception as e:
                self.log(f"An error occurred while logging {var}: {str(e)}", level="ERROR")

#endregion

#region SmartHeating logic functions
    def sh_force_flow_for_safety_prio(self, off_final) -> float:
        """
        Ensure safety priority by enforcing flow if necessary, based on radiator errors and flag state.

        Parameters:
            _ (Any): Unused parameter. Can be of any type.

        Returns:
            float: Returns the force_flow_offset if conditions are met, otherwise 0.
        """
        if (self.rads_error[ROOM_INDEX_RAD.BEDROOM.value] > 0):
            if self.force_flow_flag == 'on':
                return self.force_flow_offset
        return off_final
    
    def sh_check_forced_burn(self, off_final: float) -> float:
        """
        Check and apply forced burn based on corridor error, final offset and radiator errors.

        Parameters:
            off_final (float): Offset final value.

        Returns:
            float: Calculated forced burn value or 0 if conditions are not met.
        """
         # Check if any radiator error exceeds the threshold
        if (self.wam_errors[ROOM_INDEX_FH.CORRIDOR.value] + off_final) < 0 and any(a > self.force_burn_thres for a in self.rads_error):
            # Multiply each radiator error by its corresponding factor from self.rads_factors
            modified_rads_error = [r_error * self.rads_params[i] for i, r_error in enumerate(self.rads_error)]
            
            # Calculate the addition to the final offset based on the modified radiator errors
            forced_burn = sum(max(a, 0) for a in modified_rads_error) * self.rads_error_factor
            self.log(f'Forced_burn {forced_burn} ',level='DEBUG')
            return off_final + forced_burn  # Add the forced burn to the final offset
        else:
            return off_final  # Conditions not met, return the original offset
        
    def sh_apply_warm_flag(self, off_final: float) -> float:
        """
        Apply warm flag and retrieve updated offset.

        Parameters:
            off_final (float): Initial offset.

        Returns:
            float: Updated offset after applying warm flag.
        """
        # Check warm in flag and get offset
        ret_offset = off_final + self.sh_get_offset_warm_flag(self.warm_flag)
        return ret_offset

    def sh_apply_weather_forecast(self, off_final: float) -> float:
        """
        Apply weather forecast data (freezing flag) and get updated offset.

        Parameters:
            off_final (float): Initial offset.

        Returns:
            float: Updated offset after considering freezing flag.
        """
        # Check freezing forecast
        ret_offset = off_final + self.sh_get_offset_frezzing_flag(self.freezing_flag)    
        return ret_offset
   
    def sh_apply_wam_voting(self, off_final: float) -> float:
        """
        Apply Weighted Arithmetic Mean (WAM) voting and get updated offset.

        Parameters:
            off_final (float): Initial offset.

        Returns:
            float: Updated offset after applying WAM voting.
        """
        # Calculate WAM
        wam = round(self.sh_wam(self.wam_errors, self.wam_params), 2)
        self.sh_set_internal_wam_value(wam)
        return off_final + wam
        
    def sh_update_TRVs(self) -> None:
        """
        Update the thermostat radiator valves (TRVs) based on the error and radiator positions. 
        If the error is greater than 0.5 and the radiator position is below a threshold, 
        the preset mode of the radiator is set to 'boost'.

        Returns:
            None
        """
        # Radiator positions index: Office,KidsRoom,Bedroom1,Bedroom2,garage
        # Force open if TRV is closed and error is present
        if self.rads_error[ROOM_INDEX_RAD.OFFICE.value] > 0.5:
            if self.radiator_positions[TRV_INDEX.OFFICE.value] < self.radiator_boost_threshold:
                self.call_service('climate/set_preset_mode', entity_id='climate.office_TRV', preset_mode='boost')
                self.log('Forcing boost for office',level='DEBUG')
        if self.rads_error[ROOM_INDEX_RAD.KIDSROOM.value] > 0.5:
            if self.radiator_positions[TRV_INDEX.KIDSROOM.value] < self.radiator_boost_threshold:
                self.call_service('climate/set_preset_mode', entity_id='climate.kidsroom_TRV', preset_mode='boost')
                self.log('Forcing boost for kidsroom',level='DEBUG')
        if self.rads_error[ROOM_INDEX_RAD.BEDROOM.value] > 0.5:
            if self.radiator_positions[TRV_INDEX.BEDROOM_LEFT.value] < self.radiator_boost_threshold:
                self.call_service('climate/set_preset_mode', entity_id='climate.bedRoom_left_TRV', preset_mode='boost')
                self.log('Forcing boost for left bedrom',level='DEBUG')
            if self.radiator_positions[TRV_INDEX.BEDROOM_RIGHT.value] < self.radiator_boost_threshold:
                self.call_service('climate/set_preset_mode', entity_id='climate.bedRoom_right_TRV', preset_mode='boost')
                self.log('Forcing boost for right bedroom',level='DEBUG')
        if self.rads_error[ROOM_INDEX_RAD.GARAGE.value] > 0.5:
            if self.radiator_positions[TRV_INDEX.GARAGE.value] < self.radiator_boost_threshold:
                self.call_service('climate/set_preset_mode', entity_id='climate.garage_TRV', preset_mode='boost')
                self.log('Forcing boost for garage',level='DEBUG')

    def sh_update_thermostat(self, off_final: float) -> None:
        """
        Update the thermostat setpoint based on the corridor setpoint and a provided offset, 
        if the difference between the current thermostat setpoint and the new one is greater than 
        the predefined update threshold.

        Parameters:
            off_final (float): The offset to be added to the corridor setpoint to calculate the new thermostat setpoint.

        Returns:
            None
        """
        self.sh_set_internal_setpoint_offset(off_final)
        new_thermostat_setpoint : float = (self.corridor_setpoint - self.wam_errors[ROOM_INDEX_FH.CORRIDOR.value]) + off_final
        self.log(f'Updating thermostat,\n\tcorridor_t {(self.corridor_setpoint - self.wam_errors[ROOM_INDEX_FH.CORRIDOR.value])}\n\tcorridor_setpoint {self.corridor_setpoint}\n\toff_final: {off_final}\n\tthermostat_setpoint: {self.thermostat_setpoint}\n\tnew_thermostat_setpoint: {new_thermostat_setpoint}', level='DEBUG')
        #Check if error is higher that update threshold
        if (abs(self.thermostat_setpoint - new_thermostat_setpoint) >= self.error_offset_update_threshold):
            self.sh_set_thermostat_setpoint(new_thermostat_setpoint)

    def sh_get_radiator_postions(self) -> list[float]:
        """
        Retrieve the position values of different radiators from the HAL.

        Returns:
            List[float]: A list containing the position values of radiators in the order defined by the TRV_INDEX enum.
        """
        ret_array = [0]*TRV_INDEX.NUM_OF_RADIATORS.value
        ret_array[TRV_INDEX.OFFICE.value] = float(self.get_state(self.HAL_TRV_office_pos))
        ret_array[TRV_INDEX.KIDSROOM.value] = float(self.get_state(self.HAL_TRV_kidsRoom_pos))
        ret_array[TRV_INDEX.BEDROOM_LEFT.value] = float('100')
        ret_array[TRV_INDEX.BEDROOM_RIGHT.value] = float(self.get_state(self.HAL_TRV_bedroomRight_pos))
        ret_array[TRV_INDEX.GARAGE.value] = float(self.get_state(self.HAL_TRV_garage_pos))
        return ret_array
    
    def sh_wam(self, temperatures: list[float], weights: list[float]) -> float:
        """
        Calculate the weighted arithmetic mean of temperatures.

        Parameters:
            temperatures (List[float]): A list of temperature values.
            weights (List[float]): A list of weights corresponding to the temperature values.

        Returns:
            float: The calculated weighted arithmetic mean of temperatures. 
                    Returns NaN if the lengths of temperatures and weights do not match.
        """
        mean = nan
        if len(temperatures) == len(weights):
            mean = 0
            for idx, temp in enumerate(temperatures):
                mean = mean + temp * weights[idx]
            mean = mean/sum(weights)
        return mean
    
    def sh_get_wam_errors(self) -> list[float]:
        """
        Retrieve thermostat errors for different rooms from the HAL and return them as a list.

        Returns:
            List[float]: A list of thermostat errors corresponding to different rooms.
        """
        wam_errors = [0]*ROOM_INDEX_FH.SIZE.value
        wam_errors[ROOM_INDEX_FH.BATHROOM.value] = self.get_state(self.HAL_bathroom_tError)
        wam_errors[ROOM_INDEX_FH.CORRIDOR.value] = self.get_state(self.HAL_corridor_tError)
        wam_errors[ROOM_INDEX_FH.ENTRANCE.value] = self.get_state(self.HAL_entrance_tError)
        wam_errors[ROOM_INDEX_FH.LIVING_ROOM.value] = self.get_state(self.HAL_livingRomm_tError)
        wam_errors[ROOM_INDEX_FH.UPPER_BATHROOM.value] = self.get_state(self.HAL_upperBathroom_tError)
        wam_errors[ROOM_INDEX_FH.UPPER_CORRIDOR.value] = self.get_state(self.HAL_upperCorridor_tError)
        wam_errors[ROOM_INDEX_FH.WARDROBE.value] = self.get_state(self.HAL_wardrobe_tError)
        return [float(i) for i in wam_errors]

    def sh_get_rad_errors(self) -> list[float]:
        """
        Retrieve radiator errors for different rooms from the HAL and return them as a list.

        Returns:
            List[float]: A list of radiator errors corresponding to different rooms.
        """
        rads_errors = [0]*ROOM_INDEX_RAD.NUM_OF_RADIATORS.value
        rads_errors[ROOM_INDEX_RAD.BEDROOM.value] = self.get_state(self.HAL_bedroom_tError)
        rads_errors[ROOM_INDEX_RAD.GARAGE.value] = self.get_state(self.HAL_garage_tError)
        rads_errors[ROOM_INDEX_RAD.KIDSROOM.value] = self.get_state(self.HAL_kidsRoom_tError)
        rads_errors[ROOM_INDEX_RAD.OFFICE.value] = self.get_state(self.HAL_office_tError)
        return [float(i) for i in rads_errors]
#endregion

#region HAL opaque functions
    def sh_get_offset_frezzing_flag(self, freezing_flag: bool) -> int:
        """
        Get the offset for the freezing flag.

        Parameters:
            freezing_flag (bool): The freezing flag. True if freezing, False otherwise.

        Returns:
            int: The freezing flag offset if freezing_flag is True, otherwise 0.
        """
        if freezing_flag: 
            return self.frezzying_flag_offset
        return 0

    def sh_get_offset_warm_flag(self, warm_flag: str) -> int:
        """
        Get the offset for the warm flag.

        Parameters:
            warm_flag (str): The warm flag. 'on' if warm, 'off' otherwise.

        Returns:
            int: The warm flag offset if warm_flag is 'on', otherwise 0.
        """
        if warm_flag == 'on': 
            return self.warm_flag_offset
        return 0

    def sh_get_corridor_setpoint(self) -> float:
        """
        Retrieve the corridor setpoint from the HAL.

        Returns:
            float: The current corridor setpoint.
        """
        return float(self.get_state(self.HAL_corridor_setpoint))

    def sh_get_thermostat_setpoint(self) -> float:
        """
        Retrieve the thermostat setpoint from the HAL.

        Returns:
            float: The current thermostat setpoint.
        """
        return float(self.get_state(self.HAL_thermostat_setpoint))
    
    def sh_set_thermostat_setpoint(self, value: float) -> None:
        """
        Set a new thermostat setpoint in the HAL.

        Parameters:
            value (float): The new setpoint value to be set. The function enforces a minimum value of 15.0.

        Returns:
            None
        """
        self.call_service('number/set_value', entity_id=self.HAL_thermostat_setpoint, value=max(15.0,value))

    def sh_set_internal_wam_value(self, value):
        entity = self.get_entity(self.HAL_wam_value)
        entity.call_service('set_value', value=value)

    def sh_set_internal_setpoint_offset(self, value):
        entity = self.get_entity(self.HAL_setpoint_offset)
        entity.call_service('set_value', value=value)

    def sh_get_thermostat_error(self) -> float:
        """
        Retrieve the current thermostat error from the HAL.

        Returns:
            float: The current thermostat error.
        """
        return float(self.get_state(self.HAL_corridor_tError))
    
    def sh_get_freezing_flag(self) -> str:
        """
        Retrieve the current state of the freezing flag from the HAL.

        Returns:
            bool: The state of the freezing flag.
        """
        return self.get_state(self.HAL_frezzing_flag)

    def sh_get_warm_flag(self) -> str:
        """
        Retrieve the current state of the warm flag from the HAL.

        Returns:
            str: The state of the warm flag ('on' or 'off').
        """
        return self.get_state(self.HAL_makeWarm_flag)

    def sh_get_force_flow_flag(self) -> str:
        """
        Retrieve the current state of the force flow flag from the HAL.

        Returns:
            str: The state of the force flow flag ('on' or 'off').
        """
        return self.get_state(self.HAL_forceFlow_flag)
#endregion
    