"""
Smart heating AppDeamon application.
"""

import datetime
import traceback
from math import nan
from enum import Enum
import appdaemon.plugins.hass.hassapi as hass

__author__ = "Arkaqius"
"""
Offset smaller than 0 -> smaller flow
Offset bigger than 0 -> bigger flow
"""

# DEFAULT VALUES FOR FLOAT()
DEFAULT_COR_SETPOINT = 20.00
DEFAULT_COR_TERROR = 0.0
DEFAULT_RAD_POS = 50.0
DEFAULT_THERMOSTAT_SETPOINT = 20.00
DEFAULT_WAM_ERROR = 0.0
DEAFULT_RAD_ERR = 0.0


# region Enumerations
class ROOM_INDEX_FH(Enum):
    """
    Floor heating room index enumeration.
    """

    LIVING_ROOM = 0
    CORRIDOR = 1
    BATHROOM = 2
    ENTRANCE = 3
    UPPER_CORRIDOR = 4
    WARDROBE = 5
    UPPER_BATHROOM = 6
    SIZE = 7


class ROOM_INDEX_RAD(Enum):
    """
    Radaitor heating room index enumeration.
    """

    OFFICE = 0
    KIDSROOM = 1
    BEDROOM = 2
    GARAGE = 3
    NUM_OF_RADIATORS = 4


class TRV_INDEX(Enum):
    """
    TRV valves index enumeration.
    """

    OFFICE = 0
    KIDSROOM = 1
    BEDROOM_LEFT = 2
    BEDROOM_RIGHT = 3
    GARAGE = 4
    NUM_OF_TRV = 5


# endregion


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

    # region Cfg init functions
    def init_config(self) -> None:
        """
        Load and set up configuration from provided args.
        Extracts parameters and HALs from `args` for application use.
        """
        # Load config values using helper method
        self.cycle_time = self.get_config_value(
            "cycle_time", section="config", default=60
        )
        self.warm_flag_offset = self.get_config_value(
            "warm_flag_offset", section="config", default=0
        )
        self.frezzying_flag_offset = self.get_config_value(
            "frezzing_flag_offset", section="config", default=0
        )
        self.logging_flag = self.get_config_value(
            "logging", section="config", default=True
        )
        self.error_offset_update_threshold = self.get_config_value(
            "error_offset_update_threshold", section="config", default=0.5
        )
        self.force_flow_offset = self.get_config_value(
            "force_flow_off", section="config", default=0
        )
        self.radiator_boost_threshold = self.get_config_value(
            "radiator_boost_threshold", section="config", default=0
        )
        self.rads_error_factor = self.get_config_value(
            "rads_error_factor", section="config", default=1
        )
        self.force_burn_thres = self.get_config_value(
            "force_burn_thres", section="config", default=0
        )

        # Load factor parameters
        self.wam_params: list[float] = self.init_wam_params()
        self.rads_params: list[float] = self.init_rads_params()

        # Load HAL mappings using helper methods
        self.load_hal_mappings(
            "HAL_setpoint_mapping_in",
            [
                ("office_setpoint", "HAL_office_setpoint_in"),
                ("kidsroom_setpoint", "HAL_kidsroom_setpoint_in"),
                ("bedroom_setpoint", "HAL_bedroom_setpoint_in"),
                ("garage_setpoint", "HAL_garage_setpoint_in"),
            ],
        )

        self.load_hal_mappings(
            "HAL_setpoint_mapping_out",
            [
                ("office_setpoint", "HAL_office_setpoint_out"),
                ("kidsroom_setpoint", "HAL_kidsroom_setpoint_out"),
                ("bedroom_left_setpoint", "HAL_bedroom_left_setpoint_out"),
                ("bedroom_right_setpoint", "HAL_bedroom_right_setpoint_out"),
                ("garage_setpoint", "HAL_garage_setpoint_out"),
            ],
        )

        self.load_hal_mappings(
            "HAL_TRV_pos",
            [
                ("garage_pos", "HAL_TRV_garage_pos"),
                ("bedroomLeft_pos", "HAL_TRV_bedroomLeft_pos"),
                ("bedroomRight_pos", "HAL_TRV_bedroomRight_pos"),
                ("office_pos", "HAL_TRV_office_pos"),
                ("kidsRoom_pos", "HAL_TRV_kidsRoom_pos"),
            ],
        )

        self.load_hal_mappings(
            "HAL_errors",
            [
                ("livingRoom_error", "HAL_livingRomm_tError"),
                ("corridor_error", "HAL_corridor_tError"),
                ("bathroom_error", "HAL_bathroom_tError"),
                ("entrance_error", "HAL_entrance_tError"),
                ("uppercorridor_error", "HAL_upperCorridor_tError"),
                ("wardrobe_error", "HAL_wardrobe_tError"),
                ("upperbathroom_error", "HAL_upperBathroom_tError"),
                ("office_error", "HAL_office_tError"),
                ("kidsroom_error", "HAL_kidsRoom_tError"),
                ("garage_error", "HAL_garage_tError"),
                ("bedroom_error", "HAL_bedroom_tError"),
            ],
        )

        self.load_hal_mappings(
            "HAL_inputs",
            [
                ("makeWarm_flag", "HAL_makeWarm_flag"),
                ("frezzing_flag", "HAL_frezzing_flag"),
                ("forceFlow_flag", "HAL_forceFlow_flag"),
                ("corridor_setpoint", "HAL_corridor_setpoint"),
            ],
        )

        self.load_hal_mappings(
            "HAL_output",
            [
                ("wam_value", "HAL_wam_value"),
                ("setpoint_offset", "HAL_setpoint_offset"),
                ("thermostat_setpoint", "HAL_thermostat_setpoint"),
            ],
        )

    def get_config_value(self, key: str, section: str, default=None):
        """Helper to fetch config values with a default fallback."""
        return self.args.get(section, {}).get(key, default)

    def handle_config_error(self, error) -> None:
        """Handle configuration error by logging and stopping the app."""
        self.log(f"Configuration Error: Missing key {str(error)}", level="ERROR")
        self.stop_app("HeaterController")

    def load_hal_mappings(self, section: str, mappings: list) -> None:
        """Helper to load HAL mappings from args into class attributes."""
        for key, attribute in mappings:
            setattr(self, attribute, self.args.get(section, {}).get(key))

    def log_config(self) -> None:
        config_items: list[str] = [
            "cycle_time",
            "warm_flag_offset",
            "frezzying_flag_offset",
            "logging_flag",
            "error_offset_update_threshold",
            "force_flow_offset",
            "radiator_boost_threshold",
            "rads_error_factor",
            "force_burn_thres",
        ]

        for item in config_items:
            self.log(f"Config: {item}: {getattr(self, item)}", level="DEBUG")

    def init_wam_params(self) -> list[float]:
        """
        Initialize Weighted Average Method (WAM) parameters by normalizing the WAM factors.

        Returns:
        List[float]: Normalized WAM factors for the floor heating rooms.
        """
        wam_params: list[float] = self.init_params_from_args(
            "wam_factors", ROOM_INDEX_FH, ROOM_INDEX_FH.SIZE
        )
        return wam_params

    def init_rads_params(self) -> list[float]:
        """
        Initialize radiator factors by normalizing the radiator factors.

        Returns:
        List[float]: Normalized radiator factors.
        """
        rads_params: list[float] = self.init_params_from_args(
            "rads_factors", ROOM_INDEX_RAD, ROOM_INDEX_RAD.NUM_OF_RADIATORS
        )
        return rads_params

    def init_params_from_args(
        self, factor_key: str, room_index_enum: Enum, room_size_enum: Enum
    ) -> list[float]:
        """
        Generic method to initialize normalized factors from the args.

        Parameters:
        - factor_key (str): The key in the args dictionary to retrieve factors.
        - room_index_enum (Enum): Enum defining room indices.
        - room_size_enum (Enum): Enum representing the size/number of rooms.

        Returns:
        List[float]: A list of normalized factors.
        """
        factors_sum: int = sum(self.args[factor_key].values())  # Sum all factor values
        params = [0] * room_size_enum.value  # Initialize list with zeroes

        # Loop over the enum values to populate the params list with normalized values
        for room in room_index_enum:
            if room != room_size_enum:  # Avoid the SIZE or NUM_OF_RADIATORS enum
                params[room.value] = (
                    self.args[factor_key][room.name.lower()] / factors_sum
                )

        return params

    # endregion

    # region AppDeamon functions
    def initialize(self) -> None:
        """
        Initialize the app, set up the main loop, and define state callbacks.

        - Loads config.
        - Starts the main loop.
        - Initializes state listeners and internal fields.
        """
        try:
            # Load config
            self.init_config()

            # Initialize the app main loop
            self.start_main_loop()

            # Initialize state listeners
            self.setup_state_listeners()

            # Initialize internal fields
            self.initialize_internal_fields()

            # Log initialization completion
            self.log("Initialization finished", level="DEBUG")
            self.log_config()

        except Exception as e:
            self.handle_sw_error(
                "Error during initialization", e
            )  # SW error, stop the app

    def start_main_loop(self) -> None:
        """Starts the main loop for the app based on cycle time."""
        start_time = self.datetime() + datetime.timedelta(seconds=self.cycle_time)
        self.handle = self.run_every(self.sh_main_loop, start_time, self.cycle_time)

    def setup_state_listeners(self) -> None:
        """Set up state listeners for all setpoints."""
        setpoint_mappings = [
            (self.HAL_garage_setpoint_in, [self.HAL_garage_setpoint_out]),
            (
                self.HAL_bedroom_setpoint_in,
                [
                    self.HAL_bedroom_left_setpoint_out,
                    self.HAL_bedroom_right_setpoint_out,
                ],
            ),
            (self.HAL_kidsroom_setpoint_in, [self.HAL_kidsroom_setpoint_out]),
            (self.HAL_office_setpoint_in, [self.HAL_office_setpoint_out]),
        ]

        for input_setpoint, output_setpoints in setpoint_mappings:
            self.listen_state(
                self.setpoint_update, input_setpoint, devices=output_setpoints
            )

    def initialize_internal_fields(self) -> None:
        """Initialize the internal state variables for the app."""
        self.thermostat_error = None
        self.wam_errors = None
        self.rads_error = None
        self.warm_flag = None
        self.freezing_flag = None
        self.force_flow_flag = None
        self.radiator_positions = None
        self.previous_offset = 0

    def setpoint_update(self, _, __, ___, new, kwargs):
        """
        Update setpoint values upon state change.

        Parameters:
        - new (str): The new state of the entity.
        - kwargs (dict): Additional arguments, expects 'devices'.

        Returns:
        None
        """
        self.log(f"Setpoint update new:{new} kvargs:{kwargs}", level="DEBUG")
        # Check if the device is a TRV and update the temperature
        for device in kwargs["devices"]:
            self.call_service(
                "climate/set_temperature", entity_id=device, temperature=new
            )

    def sh_main_loop(self, _) -> None:
        """
        Main smart heating event loop which orchestrates the logic for managing the heating system.

        This function manages various system flags, calculates offsets using system parameters,
        and ensures optimal performance and safety of the heating system.

        Returns:
            None
        """
        try:
            off_final = 0

            # Collect current system values
            self.collect_system_values()
            self.log_input_variables()

            # Apply various adjustments to the offset
            off_final = self.calculate_final_offset(off_final)

            # Update TRVs and thermostat offset
            self.sh_update_TRVs()
            self.sh_update_thermostat(round(off_final, 1))
        except Exception as e:
            self.handle_hw_error(
                f"Error in main loop: {str(e)}"
            )  # HW error, safe state

    def collect_system_values(self) -> None:
        """Collect necessary current values of the system parameters."""
        self.thermostat_setpoint = self.sh_get_thermostat_setpoint()
        self.corridor_setpoint: float = self.sh_get_corridor_setpoint()
        self.wam_errors: list[float] = self.sh_get_wam_errors()
        self.rads_error: list[float] = self.sh_get_rad_errors()
        self.warm_flag: bool = self.sh_get_warm_flag()
        self.freezing_flag: bool = self.sh_get_freezing_flag()
        self.force_flow_flag: bool = self.sh_get_force_flow_flag()
        self.radiator_positions: list[float] = self.sh_get_radiator_postions()

    def calculate_final_offset(self, off_final: float) -> float:
        """
        Calculate the final offset using different system parameters. Handle HW errors.
        """
        # Apply WAM errors
        off_final = self.sh_apply_wam_voting(off_final)
        self.log(f"Offset after WAM: {off_final}", level="DEBUG")

        # Apply warm flag
        off_final = self.sh_apply_warm_flag(off_final)
        self.log(f"Offset after warm flag: {off_final}", level="DEBUG")

        # Apply weather forecast
        off_final = self.sh_apply_weather_forecast(off_final)
        self.log(f"Offset after weather forecast: {off_final}", level="DEBUG")

        # Check forced burn
        off_final = self.sh_check_forced_burn(off_final)
        self.log(f"Offset after forced burn check: {off_final}", level="DEBUG")

        # Check force flow for safety priority
        off_final = self.sh_force_flow_for_safety_prio(off_final)
        self.log(
            f"Offset after force flow for safety priority: {off_final}",
            level="DEBUG",
        )
        return off_final

    def log_input_variables(self) -> None:
        """
        Log important variables for debugging purposes. Handle errors in logging (HW Error).
        """
        variables = [
            "thermostat_setpoint",
            "corridor_setpoint",
            "wam_errors",
            "rads_error",
            "warm_flag",
            "freezing_flag",
            "force_flow_flag",
            "radiator_positions",
        ]

        for var in variables:
            try:
                self.log(f"Variable: {var}: {getattr(self, var)}", level="DEBUG")
            except AttributeError:
                self.log(f"Variable {var} not found!", level="ERROR")
            except Exception as e:
                self.log(
                    f"An error occurred while logging {var}: {str(e)}", level="ERROR"
                )

    # endregion

    # region SmartHeating logic functions
    def sh_force_flow_for_safety_prio(self, off_final) -> float:
        """
        Ensure safety priority by enforcing flow if necessary, based on radiator errors and flag state.

        Parameters:
            _ (Any): Unused parameter. Can be of any type.

        Returns:
            float: Returns the force_flow_offset if conditions are met, otherwise 0.
        """
        if self.rads_error[ROOM_INDEX_RAD.BEDROOM.value] > 0:
            if self.force_flow_flag == "on":
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
        if (self.wam_errors[ROOM_INDEX_FH.CORRIDOR.value] + off_final) < 0 and any(
            a > self.force_burn_thres for a in self.rads_error
        ):
            # Multiply each radiator error by its corresponding factor from self.rads_factors
            modified_rads_error = [
                r_error * self.rads_params[i]
                for i, r_error in enumerate(self.rads_error)
            ]

            # Calculate the addition to the final offset based on the modified radiator errors
            forced_burn = (
                sum(max(a, 0) for a in modified_rads_error) * self.rads_error_factor
            )
            self.log(f"Forced_burn {forced_burn} ", level="DEBUG")
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
        ret_offset: float = off_final + self.sh_get_offset_warm_flag(self.warm_flag)
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
        ret_offset: float = off_final + self.sh_get_offset_frezzing_flag(
            self.freezing_flag
        )
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
        """Update TRVs based on errors and radiator positions."""
        trv_mappings = {
            ROOM_INDEX_RAD.OFFICE: TRV_INDEX.OFFICE,
            ROOM_INDEX_RAD.KIDSROOM: TRV_INDEX.KIDSROOM,
            ROOM_INDEX_RAD.BEDROOM: (TRV_INDEX.BEDROOM_LEFT, TRV_INDEX.BEDROOM_RIGHT),
            ROOM_INDEX_RAD.GARAGE: TRV_INDEX.GARAGE,
        }

        for room, trv in trv_mappings.items():
            if isinstance(trv, tuple):  # For multiple TRVs like bedroom
                self.update_multiple_trvs(room, trv)
            else:
                self.update_trv(room, trv)

    def update_trv(self, room: ROOM_INDEX_RAD, trv: TRV_INDEX) -> None:
        """Update a single TRV based on room error and position."""
        if (
            self.rads_error[room.value] > 0.5
            and self.radiator_positions[trv.value] < self.radiator_boost_threshold
        ):
            self.call_service(
                "climate/set_preset_mode",
                entity_id=f"climate.{trv.name.lower()}_TRV",
                preset_mode="boost",
            )
            self.log(f"Forcing boost for {trv.name.lower()}", level="DEBUG")

    def update_multiple_trvs(
        self, room: ROOM_INDEX_RAD, trvs: tuple[TRV_INDEX, TRV_INDEX]
    ) -> None:
        """Update multiple TRVs (like bedroom with left and right TRVs)."""
        for trv in trvs:
            self.update_trv(room, trv)

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
        new_thermostat_setpoint: float = (
            self.corridor_setpoint - self.wam_errors[ROOM_INDEX_FH.CORRIDOR.value]
        ) + off_final
        self.log(
            f"Updating thermostat,\n\tcorridor_t {(self.corridor_setpoint - self.wam_errors[ROOM_INDEX_FH.CORRIDOR.value])}\n\tcorridor_setpoint {self.corridor_setpoint}\n\toff_final: {off_final}\n\tthermostat_setpoint: {self.thermostat_setpoint}\n\tnew_thermostat_setpoint: {new_thermostat_setpoint}",
            level="DEBUG",
        )
        # Check if error is higher that update threshold
        if (
            abs(self.thermostat_setpoint - new_thermostat_setpoint)
            >= self.error_offset_update_threshold
        ):
            self.sh_set_thermostat_setpoint(new_thermostat_setpoint)

    def sh_get_radiator_postions(self) -> list[float]:
        """Retrieve the position values of different radiators from the HAL."""
        ret_array = [
            self.get_state(getattr(self, f"HAL_TRV_{trv.name.lower()}_pos"))
            for trv in TRV_INDEX
        ]
        return [self.safe_float_convert(self, i, DEFAULT_RAD_POS) for i in ret_array]

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
        if len(temperatures) != len(weights):
            return nan

        total_weighted_temp: float = sum(
            temp * weight for temp, weight in zip(temperatures, weights)
        )
        return total_weighted_temp / sum(weights)

    def sh_get_wam_errors(self) -> list[float]:
        """
        Retrieve thermostat errors for different rooms from the HAL and return them as a list.

        Returns:
            List[float]: A list of thermostat errors corresponding to different rooms.
        """
        return [
            self.safe_float_convert(
                self,
                self.get_state(getattr(self, f"HAL_{room.name.lower()}_tError")),
                DEFAULT_WAM_ERROR,
            )
            for room in ROOM_INDEX_FH
        ]

    def sh_get_rad_errors(self) -> list[float]:
        """
        Retrieve radiator errors for different rooms from the HAL and return them as a list.

        Returns:
            List[float]: A list of radiator errors corresponding to different rooms.
        """
        return [
            self.safe_float_convert(
                self,
                self.get_state(getattr(self, f"HAL_{room.name.lower()}_tError")),
                DEAFULT_RAD_ERR,
            )
            for room in ROOM_INDEX_RAD
        ]

    # endregion

    # region HAL opaque functions

    def sh_get_value(self, hal_entity: str, default_value: float) -> float:
        """
        Generic method to retrieve a state value from the HAL and safely convert it to float.

        Parameters:
            hal_entity (str): The entity ID for the state in the HAL.
            default_value (float): The default value to return if the state is None or conversion fails.

        Returns:
            float: The state value as a float or the default value if conversion fails.
        """
        return self.safe_float_convert(self, self.get_state(hal_entity), default_value)

    def sh_get_flag_value(self, flag_entity: str) -> bool:
        """
        Retrieve a boolean flag from the HAL.

        Parameters:
            flag_entity (str): The entity ID for the flag in the HAL.

        Returns:
            bool: True if the flag is 'on', False otherwise.
        """
        return self.get_state(flag_entity) == "on"

    def sh_get_offset_flag(self, flag_entity: str, offset_value: int) -> int:
        """
        Retrieve the offset for a flag.

        Parameters:
            flag_entity (str): The entity ID for the flag in the HAL.
            offset_value (int): The offset value to return if the flag is 'on'.

        Returns:
            int: The offset if the flag is 'on', otherwise 0.
        """
        return offset_value if self.sh_get_flag_value(flag_entity) else 0

    def sh_set_value(self, entity: str, value: float, min_value: float = None) -> None:
        """
        Generic method to set a value in the HAL.

        Parameters:
            entity (str): The entity ID in the HAL.
            value (float): The value to set.
            min_value (float, optional): If provided, ensures the value is at least this value.
        """
        if min_value is not None:
            value = max(min_value, value)

        self.call_service("number/set_value", entity_id=entity, value=value)

    def sh_get_offset_frezzing_flag(self) -> int:
        """Get the offset for the freezing flag."""
        return self.sh_get_offset_flag(
            self.HAL_frezzing_flag, self.frezzying_flag_offset
        )

    def sh_get_offset_warm_flag(self) -> int:
        """Get the offset for the warm flag."""
        return self.sh_get_offset_flag(self.HAL_makeWarm_flag, self.warm_flag_offset)

    def sh_get_corridor_setpoint(self) -> float:
        """Retrieve the corridor setpoint from the HAL."""
        return self.sh_get_value(self.HAL_corridor_setpoint, DEFAULT_COR_SETPOINT)

    def sh_get_thermostat_setpoint(self) -> float:
        """Retrieve the corridor setpoint from the HAL."""
        return self.sh_get_value(self.HAL_thermostat_setpoint, DEFAULT_COR_SETPOINT)

    def sh_set_thermostat_setpoint(self, value: float) -> None:
        """Set a new thermostat setpoint in the HAL, ensuring it’s at least 15.0."""
        self.sh_set_value(self.HAL_thermostat_setpoint, value, min_value=15.0)

    def sh_set_internal_wam_value(self, value: float) -> None:
        """Set the internal WAM value in the HAL."""
        self.sh_set_value(self.HAL_wam_value, value)

    def sh_set_internal_setpoint_offset(self, value: float) -> None:
        """Set the internal setpoint offset in the HAL."""
        self.sh_set_value(self.HAL_setpoint_offset, value)

    def sh_get_freezing_flag(self) -> bool:
        """Retrieve the state of the freezing flag."""
        return self.sh_get_flag_value(self.HAL_frezzing_flag)

    def sh_get_warm_flag(self) -> bool:
        """Retrieve the state of the warm flag."""
        return self.sh_get_flag_value(self.HAL_makeWarm_flag)

    def sh_get_force_flow_flag(self) -> bool:
        """Retrieve the state of the force flow flag."""
        return self.sh_get_flag_value(self.HAL_forceFlow_flag)

    # endregion

    # region utilites
    def safe_float_convert(hass_app, value: str, default: float = 0.0) -> float:
        """
        Attempts to convert a string to a float. If the conversion fails,
        logs a warning and returns a default value, or raises a hardware error if no valid default is provided.

        Args:
            value (str): The string value to be converted to float.
            default (float, optional): The default value to return in case of conversion failure. Default is 0.0.

        Returns:
            float: The converted float value or the default value if conversion fails.
        """
        try:
            return float(value)
        except (TypeError, ValueError) as e:
            if default != 0.0:
                hass_app.log(
                    f"Conversion warning: Could not convert '{value}' to float. Returning default value {default}: {str(e)}",
                    level="WARNING",
                )
                return default
            else:
                hass_app.log(
                    f"Conversion error: Could not convert '{value}' to float: {str(e)}",
                    level="ERROR",
                )
                hass_app.handle_hw_error(
                    f"Failed to convert value '{value}' to float, no valid default provided. Raising hardware fault."
                )
                return default  # Default remains 0.0, but error is raised

    # endregion

    # region ErrorHandling
    def handle_sw_error(self, message: str, exception: Exception) -> None:
        """
        Handle software errors by logging the exception and stopping the app.

        Parameters:
            message (str): Custom error message to be logged.
            exception (Exception): The raised exception object.

        Raises:
            Exception: Re-raises the exception to fault hard.
        """
        self.log(
            f"SW ERROR: {message}: {str(exception)}\n{traceback.format_exc()}",
            level="ERROR",
        )
        raise exception

    def handle_hw_error(self, message: str) -> None:
        """
        Handle system/hardware errors by logging the error and entering a safe state.

        Parameters:
            message (str): Custom error message to be logged.
        """
        self.log(f"HW ERROR: {message}", level="ERROR")
        self.enter_safe_state()

    def enter_safe_state(self) -> None:
        """
        Placeholder method to enter a safe state.
        Add logic here to stop critical processes and prevent damage.
        """
        # Implementation to stop critical processes
        pass  # For now, this is a placeholder. In reality, you'd implement specific safe state actions.

    # endregion
