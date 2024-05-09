"""
This module defines the TemperatureComponent class, part of a Home Assistant-based safety system designed to monitor and respond to temperature-related risks. TemperatureComponent is responsible for managing safety mechanisms that trigger based on direct temperature readings and forecasted temperature changes, providing a dynamic response to potential temperature hazards within a monitored environment.

The component utilizes Home Assistant's infrastructure to monitor temperature sensors and execute predefined safety mechanisms when certain temperature thresholds are reached or forecasted. This system is designed to be configurable, allowing users to define safety mechanisms through external configuration, making it adaptable to various scenarios and requirements.

Classes:
- DebounceState: A NamedTuple that represents the state of a debounce process.
- TemperatureComponent: Manages temperature-related safety mechanisms within Home Assistant.

Key Features:
- Direct temperature monitoring with immediate response mechanisms.
- Forecasted temperature monitoring for proactive safety measures.
- Configurable thresholds and response actions to accommodate different monitoring needs and scenarios.
- Integration with Home Assistant for accessing sensor data and executing actions.

Usage:
The TemperatureComponent class is intended to be used within a Home Assistant automation setup. Users can define safety mechanisms and their configurations in external YAML files, which the component will read and use to initialize the necessary monitoring and response logic.

Note:
This module is part of a larger system designed for enhancing safety through Home Assistant. It should be integrated with the appropriate Home Assistant setup and configured according to the specific needs and safety requirements of the environment being monitored.
"""

from typing import Dict, Any
from shared.safety_component import (
    SafetyComponent,
    safety_mechanism_decorator,
    DebounceState,
    SafetyMechanismResult,
)
from shared.safety_mechanism import SafetyMechanism
from shared.types_common import PreFault, RecoveryAction, SMState
from shared.common_entities import CommonEntities
import appdaemon.plugins.hass.hassapi as hass  # type: ignore

# CONFIG
DEBOUNCE_INIT = 1
SM_TC_2_DEBOUNCE_LIMIT = 3


class TemperatureComponent(SafetyComponent):
    """
    Manages and orchestrates temperature-related safety mechanisms within the Home Assistant framework.
    This component is responsible for initializing temperature monitoring mechanisms, processing
    temperature data, and executing appropriate actions based on configurable thresholds and forecasted conditions.

    It leverages Home Assistant's sensor data to proactively manage temperature risks, employing debouncing strategies
    to ensure reliable detection and response to temperature fluctuations. The component supports multiple safety mechanisms,
    each designed to monitor specific conditions and execute defined actions, such as sending alerts or triggering automations.
    """

    component_name = "TemperatureComponent"

    def __init__(self, hass_app: hass, common_entities: CommonEntities) -> None:  # type: ignore
        """
        Initializes the TemperatureComponent instance with the Home Assistant application context, setting up the foundation
        for temperature-related safety management within the smart home environment.

        Args:
            hass_app (hass.Hass): The Home Assistant application instance through which sensor data is accessed and actions are executed.
        """
        super().__init__(hass_app, common_entities)

    def get_prefaults_data(
        self, sm_modules: dict, component_cfg: list[dict[str, Any]]
    ) -> tuple[Dict[str, PreFault], Dict[str, RecoveryAction]]:
        """
        Retrieve pre-fault configurations from the component configuration and generate corresponding PreFault objects.

        Args:
            component_cfg (list[Dict[str, Dict[str, float]]]): A list of dictionaries where each dictionary
                contains a single location as the key and a dictionary of configuration data for that location.

        Returns:
            Dict[str, PreFault]: A dictionary where keys are the names of the pre-faults and values are
                the corresponding PreFault objects initialized with the provided configuration data.

        Processes each location's configuration to create two types of pre-faults:
        - One based on direct temperature thresholds.
        - Another based on forecasted temperature conditions.
        """
        ret_val_pr: dict[str, PreFault] = {}
        ret_val_ra: dict[str, RecoveryAction] = {}

        for location_dict in component_cfg:
            for location, data in location_dict.items():
                self.hass_app.log(
                    f"Processing prefaults for location: {location}, data: {data}"
                )

                # SM TC 1
                prefault_name: str = self._get_sm_tc_1_pr_name(location)
                recovery_action: RecoveryAction = self._get_sm_tc_1_recovery_action(
                    sm_modules, location, data, prefault_name
                )
                prefault: PreFault = self._get_sm_tc_1_prefault(
                    sm_modules, location, data, prefault_name
                )

                ret_val_pr[prefault_name] = prefault
                ret_val_ra[prefault_name] = recovery_action

                # SM TC 2
                prefault_name = self._get_sm_tc_2_pr_name(location)
                prefault = self._get_sm_tc_2_prefault(
                    sm_modules, location, data, prefault_name
                )
                recovery_action = self._get_sm_tc_2_recovery_action(
                    sm_modules, location, data, prefault_name
                )

                ret_val_pr[prefault_name] = prefault
                ret_val_ra[prefault_name] = recovery_action

        return (ret_val_pr, ret_val_ra)

    def _get_sm_tc_1_pr_name(self, location: str) -> str:
        return f"RiskyTemperature{location}"

    def _get_sm_tc_1_prefault(
        self, modules: dict, location: str, data: dict, prefault_name: str
    ) -> PreFault:
        """
        Generates a PreFault object for direct temperature monitoring based on the given location and data.

        Args:
            location (str): The location identifier used to create a unique pre-fault name.
            data (dict): Configuration data specific to this pre-fault, such as temperature thresholds.

        Returns:
            Tuple[str, PreFault]: A tuple containing the pre-fault's name and the PreFault object itself.
            The PreFault is configured to handle direct temperature conditions.
        """
        prefault_params = data
        sm_name = "sm_tc_1"

        # Add location to parametrs
        prefault_params["location"] = location

        # recovery_func = getattr(self.__class__, f"{prefault_name}_recovery", None)
        return PreFault(
            module=modules[self.__class__.__name__],
            name=prefault_name,
            parameters=prefault_params,
            sm_name=sm_name,
        )

    def _get_sm_tc_1_recovery_action(
        self, modules: dict, location: str, data: dict, prefault_name: str
    ) -> RecoveryAction:
        type = "ManipulateWindowInRoom"
        params = {"location": location, "actuator": None}
        recovery_func = self.RiskyTemperature_recovery
        return RecoveryAction(type, params, recovery_func)

    def _get_sm_tc_2_pr_name(self, location: str) -> str:
        return f"RiskyTemperature{location}ForeCast"

    def _get_sm_tc_2_prefault(
        self, modules: dict, location: str, data: dict, prefault_name: str
    ) -> PreFault:
        """
        Generates a PreFault object for forecast-based temperature monitoring based on the given location and data.

        Args:
            location (str): The location identifier used to create a unique pre-fault name.
            data (dict): Configuration data specific to this pre-fault, including forecast timespan and other parameters.

        Returns:
            Tuple[str, PreFault]: A tuple containing the pre-fault's name and the PreFault object itself.
            The PreFault is configured to handle forecasted temperature conditions.
        """
        prefault_params = data
        sm_name = "sm_tc_2"

        # Add location to parametrs
        prefault_params["location"] = location

        return PreFault(
            module=modules[self.__class__.__name__],
            name=prefault_name,
            parameters=prefault_params,
            sm_name=sm_name,
        )

    def _get_sm_tc_2_recovery_action(
        self, modules: dict, location: str, data: dict, prefault_name: str
    ) -> RecoveryAction:
        type = "ManipulateWindowInRoom"
        params = {"sensor": "sensor", "actuator": None}
        recovery_func = self.RiskyTemperature_recovery
        return RecoveryAction(type, params, recovery_func)

    def init_sm_tc_1(self, name: str, parameters: dict) -> bool:
        """
        Initializes a new temperature threshold-based safety mechanism. This process involves validating
        configuration parameters, setting up debounce states for reliable condition detection, and registering
        the mechanism within the system for ongoing temperature monitoring.

        This method dynamically configures a safety mechanism that triggers when temperature readings cross
        a specified threshold, facilitating immediate or preventative actions to mitigate potential risks.

        Args:
            name (str): A unique identifier for the safety mechanism.
            parameters (Dict[str, Any]): A dictionary containing the necessary configuration parameters
            such as 'temperature_sensor' and 'cold_thr' (cold threshold).

        Raises:
            KeyError: If essential parameters are missing, indicating incomplete configuration.
            ValueError: If parameter validations fail, such as incorrect types or unacceptable values.
        """
        is_param_ok = True

        if name in self.safety_mechanisms:
            self.hass_app.log("Doubled SM_TC_1 - Invalid Cfg", level="ERROR")
            return False

        try:
            temperature_sensor = parameters["temperature_sensor"]
            cold_thr = parameters["CAL_LOW_TEMP_THRESHOLD"]
            location = parameters["location"]
        except KeyError as e:
            self.hass_app.log(f"Key not found in sm_cfg: {e}", level="ERROR")
            is_param_ok = False
        else:
            is_param_ok = self.validate_entities(
                {
                    "temperature_sensor": temperature_sensor,
                    "cold_thr": cold_thr,
                    "location": location,
                },
                {"temperature_sensor": str, "cold_thr": float, "location": str},
            )

        if is_param_ok:
            # Store the SafetyMechanism instance in the dictionary
            # using the unique name as the key
            self.safety_mechanisms[name] = SafetyMechanism(
                self.hass_app,
                self.sm_tc_1,  # The method to call
                name,
                isEnabled=False,
                temperature_sensor=temperature_sensor,
                cold_thr=cold_thr,
                location=location,
            )
            # Initialize the debounce state for this mechanism
            self.debounce_states[name] = DebounceState(
                debounce=DEBOUNCE_INIT, force_sm=False
            )
            # Add recovery actions
            return True
        else:
            self.hass_app.log(f"SM {name} was not created due error", level="ERROR")
            return False

    def init_sm_tc_2(self, name: str, parameters: dict) -> bool:
        """
        Sets up a forecast-based temperature safety mechanism considering the rate of temperature change.
        This involves configuring the mechanism to predict future temperature conditions and trigger responses
        before hazardous thresholds are reached, based on trends and forecast spans.

        Args:
            name (str): The unique name identifying this safety mechanism, used for tracking and management.
            parameters (Dict[str, Any]): Configuration parameters including sensor IDs, rate of change thresholds,
            and forecast timespan for predictive monitoring.

        Raises:
            KeyError: Thrown when essential configuration parameters are absent, indicating a setup issue.
            ValueError: Thrown for invalid parameter values, ensuring configuration integrity.
        """
        is_param_ok = True  # Placeholder for actual parameter validation logic

        if name in self.safety_mechanisms:
            self.hass_app.log("Doubled SM_TC_2 - Invalid Cfg", level="ERROR")
            return False

        try:
            temperature_sensor = parameters["temperature_sensor"]
            cold_thr = parameters["CAL_LOW_TEMP_THRESHOLD"]
            forecast_timespan = parameters["CAL_FORECAST_TIMESPAN"]
            location = parameters["location"]
        except KeyError as e:
            self.hass_app.log(f"Key not found in sm_cfg: {e}", level="ERROR")
            is_param_ok = False
        else:
            is_param_ok = self.validate_entities(
                {
                    "temperature_sensor": temperature_sensor,
                    "cold_thr": cold_thr,
                    "forecast_timespan": forecast_timespan,
                    "location": location,
                },
                {
                    "temperature_sensor": str,
                    "cold_thr": float,
                    "forecast_timespan": float,
                    "location": str,
                },
            )
        if is_param_ok:
            # Store the SafetyMechanism instance in the dictionary
            # using the unique name as the key
            self.safety_mechanisms[name] = SafetyMechanism(
                self.hass_app,
                self.sm_tc_2,  # The method to call for sm_tc_2
                name,
                isEnabled=False,
                temperature_sensor=parameters["temperature_sensor"],
                cold_thr=parameters["CAL_LOW_TEMP_THRESHOLD"],
                forecast_timespan=parameters["CAL_FORECAST_TIMESPAN"],
                location=location,
                diverative=0.0,
                prev_val=0.0,
            )

            # Initialize the debounce state for this mechanism
            self.debounce_states[name] = DebounceState(
                debounce=DEBOUNCE_INIT, force_sm=False
            )

            # Initialize cyclic runnable to get diverative
            self.hass_app.run_every(self.calculate_diff, "now", 60)
            return True
        else:
            self.hass_app.log(f"SM {name} was not created due to error", level="ERROR")
            return False

    def enable_sm_tc_1(self, name: str, state: SMState) -> bool:
        if state == SMState.ENABLED:
            self.safety_mechanisms[name].isEnabled = True
            return True
        elif state == SMState.DISABLED:
            self.safety_mechanisms[name].isEnabled = False
            return True
        else:
            return False

    def enable_sm_tc_2(self, name: str, state: SMState) -> bool:
        if state == SMState.ENABLED:
            self.safety_mechanisms[name].isEnabled = True
            return True
        elif state == SMState.DISABLED:
            self.safety_mechanisms[name].isEnabled = False
            return True
        else:
            return False

    @safety_mechanism_decorator
    def sm_tc_1(
        self, sm: SafetyMechanism, entities_changes: dict[str, str] | None = None
    ) -> SafetyMechanismResult:
        """
        The core logic for a direct temperature threshold safety mechanism. It reads current temperature
        data, compares it against defined thresholds, and, if a risk condition is detected, executes configured
        actions to mitigate the risk.

        Args:
            sm (SafetyMechanism): The instance of the safety mechanism being processed.
            **kwargs: Additional keyword arguments, primarily for future extensions and compatibility.

        Operations:
            - Retrieves current temperature from the configured sensor.
            - Applies debouncing to stabilize detection over time.
            - Triggers configured actions if the temperature crosses the defined threshold.

        Note:
            This method is wrapped with a decorator to log its execution and handle any exceptions gracefully.
        """
        temperature_sensor: str = sm.sm_args["temperature_sensor"]
        cold_threshold: float = sm.sm_args["cold_thr"]
        location: str = sm.sm_args["location"]

        try:
            # Check if a stubbed value is provided in entities_changes
            if entities_changes and temperature_sensor in entities_changes:
                temperature = float(entities_changes[temperature_sensor])
                self.hass_app.log(
                    f"Using stubbed value for {temperature_sensor}: {temperature}",
                    level="DEBUG",
                )
            else:
                temperature = float(self.hass_app.get_state(temperature_sensor))

        except (ValueError, TypeError) as e:
            self.hass_app.log(f"Error handling temperature: {e}", level="ERROR")
            return SafetyMechanismResult(False, None)

        sm_result: bool = temperature < cold_threshold
        additional_info: dict[str, str] = {"location": location}

        return SafetyMechanismResult(result=sm_result, additional_info=additional_info)

    @safety_mechanism_decorator
    def sm_tc_2(
        self, sm: SafetyMechanism, entities_changes: dict[str, str] | None = None
    ) -> tuple[bool, dict[str, Any] | None]:
        """
        Implements logic for a forecast-based temperature change safety mechanism. This method analyzes
        temperature trends and forecasts future conditions to proactively address potential risks based
        on predicted temperature changes.

        Args:
            sm (SafetyMechanism): The safety mechanism instance being evaluated.
            **kwargs: Arbitrary keyword arguments, allowing for future flexibility in method signatures.

        Operations:
            - Calculates forecasted temperature using current data and rate of change.
            - Employs debouncing for reliable forecasting over specified intervals.
            - Executes preventive actions if forecasted conditions indicate a potential risk.

        Note:
            Enhanced with a decorator for execution logging and error management, ensuring robust operation.
        """
        temperature_sensor: str = sm.sm_args["temperature_sensor"]
        cold_threshold: float = sm.sm_args["cold_thr"]
        location: str = sm.sm_args["location"]
        forecast_timespan: float = sm.sm_args["forecast_timespan"]
        temperature_rate = sm.sm_args["diverative"]

        try:
            # Check if a stubbed value is provided in entities_changes
            if entities_changes and temperature_sensor in entities_changes:
                temperature = float(entities_changes[temperature_sensor])
                self.hass_app.log(
                    f"Using stubbed value for {temperature_sensor}: {temperature}",
                    level="DEBUG",
                )
            else:
                temperature = float(self.hass_app.get_state(temperature_sensor))

        except (ValueError, TypeError) as e:
            self.hass_app.log(f"Error handling temperature: {e}", level="ERROR")
            SafetyMechanismResult(False, None)

        # Ensure sm_args["forecast_timespan"] is in hours for this calculation
        forecast_timespan_in_minutes: float = (
            forecast_timespan * 60
        )  # Convert hours to minutes

        # Calculate forecasted temperature for the specified timespan
        # Since temperature_rate is per minute, multiply by forecast_timespan_in_minutes directly
        forecasted_temperature = (
            temperature + temperature_rate * forecast_timespan_in_minutes
        )

        sm_result: bool = forecasted_temperature < cold_threshold
        additional_info: dict[str, str] = {"location": location}

        return SafetyMechanismResult(result=sm_result, additional_info=additional_info)

    def calculate_diff(self, _: "Any") -> None:

        sm: SafetyMechanism = self.safety_mechanisms[
            "RiskyTemperatureOfficeForeCast"
        ]  # HARDCODED!
        # Get inputs
        try:
            temperature = float(
                self.hass_app.get_state(sm.sm_args["temperature_sensor"])
            )
        except ValueError as e:
            self.hass_app.log(f"Float conversion error: {e}", level="ERROR")
            return  # Exit if there's a conversion error

        sm.sm_args["diverative"] = temperature - sm.sm_args["prev_val"]
        sm.sm_args["prev_val"] = temperature
        self.hass_app.set_state(
            "sensor.office_temperature_rate", state=sm.sm_args["diverative"]
        )

    @staticmethod
    def RiskyTemperature_recovery(
        hass_app: hass,
        prefault: PreFault,
        common_entities: CommonEntities,
        **kwargs: dict[str, Any],
    ) -> dict | None:
        """Executes recovery actions for risky temperature conditions.
        params = {"location" : location, "actuator" : None}
        """

        changed_entities: dict = {}
        # Get inputs
        try:
            meas_room_temp = float(
                hass_app.get_state(prefault.parameters["temperature_sensor"])
            )
        except ValueError as e:
            hass_app.log(f"Float conversion error: {e}", level="ERROR")
            return None  # Exit if temperature conversion fails
        # First we shall close windows if outisde temperature is lower that in room
        outside_temp_raw: str | None = common_entities.get_outisde_temperature()
        if not outside_temp_raw:
            return None
        else:
            outside_temp = float(outside_temp_raw)
            if outside_temp < meas_room_temp:
                changed_entities[
                    TemperatureComponent.safety_mechanisms[prefault.name].sm_args[
                        "temperature_sensor"
                    ]
                ] = "off"
                # Check if we have actuator
                if kwargs["params"]["actuator"]:
                    changed_entities[kwargs["params"]["actuator"]] = (
                        "off"  # TODO Check it!
                    )
            else:
                changed_entities[
                    TemperatureComponent.safety_mechanisms[prefault.name].sm_args[
                        "temperature_sensor"
                    ]
                ] = "on"
                # Check if we have actuator
                if kwargs["params"]["actuator"]:
                    changed_entities[kwargs["params"]["actuator"]] = (
                        "on"  # TODO Check it!
                    )
            return changed_entities
