"""
This module provides foundational structures and functionalities for implementing advanced safety mechanisms within Home Assistant applications. It introduces a systematic approach to handling, debouncing, and managing state changes of Home Assistant entities, enabling the creation of sophisticated safety and fault management strategies.

Components:
- `DebounceState`: A named tuple that stores the current state of a debouncing process, including the debounce counter and a flag indicating the necessity of action.
- `DebounceAction`: An enumeration that defines possible outcomes of the debouncing process, such as setting a pre-fault condition, clearing it, or taking no action.
- `DebounceResult`: A named tuple that encapsulates the result of a debouncing process, comprising the action to be taken and the updated counter value.
- `SafetyComponent`: A base class for creating domain-specific safety components. It provides methods for entity validation, debouncing logic, and interaction with a fault manager to set or clear pre-fault conditions based on dynamic sensor data.
- `safety_mechanism_decorator`: A decorator designed to wrap safety mechanism functions, adding pre- and post-execution logic around these functions for enhanced logging and execution control.

Features:
- Flexible monitoring and debouncing of entity states to prevent rapid toggling and ensure reliable fault detection.
- Integration with a fault management system, allowing for dynamic response to fault conditions and the ability to set or clear faults programmatically.
- Extensibility for developing custom safety mechanisms tailored to specific needs and scenarios within the smart home environment.

Usage:
The module's components are intended to be used as building blocks for developing custom safety mechanisms within Home Assistant. By subclassing `SafetyComponent` and utilizing `DebounceState`, `DebounceAction`, and `DebounceResult`, developers can create robust safety features that respond intelligently to changes in the Home Assistant environment.

Example:
A developer might create a `TemperatureSafetyComponent` subclass that monitors temperature sensors and uses the debouncing logic to manage heating elements within the home, ensuring a safe and comfortable environment.

This module streamlines the creation of safety mechanisms, emphasizing reliability, flexibility, and integration with Home Assistant's dynamic ecosystem.
"""

from typing import Type, Any, get_origin, get_args, Callable, Optional, NamedTuple
import traceback
from enum import Enum
from shared.fault_manager import FaultManager
from shared.types_common import FaultState
import appdaemon.plugins.hass.hassapi as hass  # type: ignore

NO_NEEDED = False


class DebounceState(NamedTuple):
    """
    Purpose: Acts as a memory for a particular safety mechanism. It stores the current state of the debouncing process for a specific mechanism,
    including the debounce counter and a flag indicating whether action should be forced for debouncing purposes.

    Usage: This state is maintained across calls to process_prefault to keep track of how many times a condition has been met or not met,
    helping to stabilize the detection over time by preventing rapid toggling due to transient states.

    Attributes:
        debounce (int): A counter used to stabilize the detection of a condition over time, preventing rapid toggling.
        force_sm (bool): A flag indicating whether sm shall be forced for debouncing purpose
    """

    debounce: int
    force_sm: bool


# Define the named tuple with possible outcomes
class DebounceAction(Enum):
    """
    Enumeration of debouncing actions that can be taken after evaluating a pre-fault condition.

    Attributes:
        NO_ACTION (int): Indicates that no action should be taken.
        PREFAULT_SET (int): Indicates a pre-fault condition should be set.
        PREFAULT_HEALED (int): Indicates a pre-fault condition has been cleared or healed.
    """

    NO_ACTION = 0
    PREFAULT_SET = 1
    PREFAULT_HEALED = -1


class DebounceResult(NamedTuple):
    """
    Represents the result of a debouncing process, encapsulating the action to be taken and the updated counter value.

    Attributes:
        action (DebounceAction): The action determined by the debouncing process.
        counter (int): The updated debounce counter after evaluating the pre-fault condition.
    """

    action: DebounceAction
    counter: int


class SafetyComponent:
    """
    A base class for creating and managing safety mechanisms within the Home Assistant environment.

    It provides the infrastructure for monitoring entity states, validating entities, debouncing state changes,
    and interacting with a fault management system. Subclasses can implement specific safety logic, such as
    monitoring for hazardous conditions and taking corrective actions.

    Attributes:
        hass_app: Reference to the Home Assistant application instance.
        fault_man: Optional instance of a fault manager for managing fault conditions.

    Methods:
        register_fm: Registers a fault manager instance with the safety component.
        validate_entity: Validates an entity against a specified type.
        validate_entities: Validates multiple entities against their expected types.
        safe_float_convert: Safely converts a string to a float.
        _debounce: Implements debouncing logic for state changes.
        process_prefault: Processes potential pre-fault conditions based on debouncing logic.
    """
    component_name = "UNKNOWN"  # Default value for the parent class
    
    def __init__(
        self,
        hass_app: hass.Hass,
    ):
        """
        Initialize the safety component.

        :param hass_app: The Home Assistant application instance.
        """
        self.hass_app = hass_app
        self.fault_man: Optional[FaultManager] = None

    def get_prefaults(self, modules : dict, component_cfg : str) -> dict:
        raise NotImplementedError
    
    def register_fm(self, fm: FaultManager) -> None:
        """
        Registers a FaultManager instance with this component, enabling interaction with the fault management system.

        This method associates a FaultManager object with the component, allowing it to set or clear fault conditions
        based on the outcomes of safety mechanism evaluations. The registered FaultManager is essential for the component
        to communicate fault states and recovery actions within the broader safety management system.

        Args:
            fm (FaultManager): An instance of FaultManager that will be used by this component to manage fault conditions.

        Note:
            It's important to register a FaultManager before invoking safety mechanisms that require fault state management
            to ensure the component can appropriately respond to and manage fault conditions.
        """
        self.fault_man = fm

    # @staticmethod
    # def is_valid_binary_sensor(entity_name: str) -> bool:
    #     """
    #     Check if a given entity name is a valid binary sensor.

    #     :param entity_name: The entity name to validate.
    #     :return: True if valid binary sensor, False otherwise.
    #     """
    #     return isinstance(entity_name, str) and entity_name.startswith("binary_sensor.")

    # @staticmethod
    # def is_valid_sensor(entity_name: str) -> bool:
    #     """
    #     Check if a given entity name is a valid sensor.

    #     :param entity_name: The entity name to validate.
    #     :return: True if valid sensor, False otherwise.
    #     """
    #     return isinstance(entity_name, str) and entity_name.startswith("sensor.")

    def validate_entity(
        self, entity_name: str, entity: Any, expected_type: Type
    ) -> bool:
        """
        Validate a single entity against the expected type.

        :param entity: The entity to validate.
        :param expected_type: The expected type (e.g., type, List[type], etc.).
        :return: True if the entity is valid, False otherwise.
        """
        # Check for generic types like List[type]
        if get_origin(expected_type):
            if not isinstance(entity, get_origin(expected_type)):
                self.hass_app.log(
                    f"Entity {entity_name} should be a {get_origin(expected_type).__name__}",
                    level="ERROR",
                )
                return False
            element_type = get_args(expected_type)[0]
            if not all(isinstance(item, element_type) for item in entity):
                self.hass_app.log(
                    f"Elements of entity {entity_name} should be {element_type.__name__}",
                    level="ERROR",
                )
                return False
        # Non-generic types
        elif not isinstance(entity, expected_type):
            self.hass_app.log(
                f"Entity {entity_name} should be {expected_type.__name__}",
                level="ERROR",
            )
            return False

        return True

    def validate_entities(
        self, sm_args: dict[str, Any], expected_types: dict[str, Type]
    ) -> bool:
        """
        Validate multiple entities against their expected types based on kwargs.

        This method checks whether each required entity (as specified in `expected_types`)
        is present in `sm_args` and whether each entity conforms to its expected type.

        Example usage:
            sm_args = {
                'window_sensors': ["binary_sensor.window1", "binary_sensor.window2"],
                'temperature_sensor': "sensor.room_temperature",
                'threshold': 25.0
            }

            expected_types = {
                'window_sensors': List[str],  # Expect a list of strings
                'temperature_sensor': str,    # Expect a string
                'threshold': float            # Expect a float
            }

            if not self.validate_entities(sm_args, expected_types):
                # Handle validation failure
                return False

        :param sm_args: The actual keyword arguments passed to the method.
                        It should contain all the entities required for the safety mechanism.
        :param expected_types: A dictionary mapping expected variable names to their expected types.
                               This dict defines what type each entity in `sm_args` should be.
        :return: True if all required entities are present in `sm_args` and valid, False otherwise.
        """
        for entity_name, expected_type in expected_types.items():
            if entity_name not in sm_args:
                self.hass_app.log(
                    f"Missing required argument: {entity_name}", level="ERROR"
                )
                return False
            if not self.validate_entity(
                entity_name, sm_args[entity_name], expected_type
            ):
                # The specific error message will be logged in validate_entity
                return False
        return True

    @staticmethod
    def safe_float_convert(value: str, default: float = 0.0) -> float:
        """
        Attempts to convert a string to a float. If the conversion fails,
        prints an error message and traceback to stdout, then returns a default value.

        Args:
        value (str): The string value to be converted to float.
        default (float, optional): The default value to return in case of conversion failure. Default is 0.0.

        Returns:
        float: The converted float value or the default value if conversion fails.
        """
        try:
            return float(value)
        except ValueError as e:
            print(f"An error occurred: {e}")
            traceback.print_exc()  # Prints the full traceback to stdout
            return default

    def _debounce(
        self, current_counter: int, pr_test: bool, debounce_limit: int = 3
    ) -> DebounceResult:
        """
        Generic debouncing function that updates the counter based on the state
        and returns an action indicating whether a pre-fault should be set, cleared, or no action taken.

        Args:
            current_counter (int): The current debounce counter for the mechanism.
            pr_test (bool): The result of the pre-fault test. True if the condition is detected, False otherwise.
            debounce_limit (int, optional): The limit at which the state is considered stable. Defaults to 3.

        Returns:
            DebounceResult: A named tuple containing the action to be taken (DebounceAction) and the updated counter (int).
        """
        if pr_test:
            new_counter = min(debounce_limit, current_counter + 1)
            action = (
                DebounceAction.PREFAULT_SET
                if new_counter >= debounce_limit
                else DebounceAction.NO_ACTION
            )
        else:
            new_counter = max(-debounce_limit, current_counter - 1)
            action = (
                DebounceAction.PREFAULT_HEALED
                if new_counter <= -debounce_limit
                else DebounceAction.NO_ACTION
            )

        return DebounceResult(action=action, counter=new_counter)

    def process_prefault(
        self,
        prefault_id: str,
        current_counter: int,
        pr_test: bool,
        additional_info: dict,
        debounce_limit: int = 2,
    ) -> tuple[int, bool]:
        """
        Handles the debouncing of a pre-fault condition based on a pre-fault test (pr_test).

        This method manages the pre-fault state by updating the debounce counter and
        interacting with the Fault Manager as needed. The pre-fault state is determined
        by the result of the pr_test and the current state of the debounce counter.
        This method is responsible for calling the necessary interfaces from the Fault
        Manager to set or clear pre-fault conditions.

        The method returns two values: the updated debounce counter and a boolean
        indicating whether to inhibit further triggers. If inhibition is true,
        further triggers are ignored except for time-based events used for debouncing purposes.

        Args:
            prefault_id (int): The identifier for the pre-fault condition.
            current_counter (int): The current value of the debounce counter.
            pr_test (bool): The result of the pre-fault test. True if the pre-fault
                            condition is detected, False otherwise.
            debounce_limit (int, optional): The threshold for the debounce counter
                                            to consider the state stable. Defaults to 3.

        Returns:
            tuple:
                - int: The updated debounce counter value.
                - bool: A flag indicating whether to safety mechanism shall be forced to trigger.
                        True to force, False to not.

        Raises:
            None
        """

        if not self.fault_man:
            self.hass_app.log("Fault manager not initialized!", level="ERROR")
            return current_counter, False

        # Prepare retVal
        force_sm: bool = False
        debounce_result: DebounceResult = DebounceResult(
            action=DebounceAction.NO_ACTION, counter=current_counter
        )

        # Get current prefault state
        prefault_cur_state: FaultState = self.fault_man.check_prefault(prefault_id)
        # Check if any actions is needed
        if (
            (pr_test and prefault_cur_state == FaultState.CLEARED)
            or (not pr_test and prefault_cur_state == FaultState.SET)
            or (prefault_cur_state == FaultState.NOT_TESTED)
        ):
            debounce_result = self._debounce(current_counter, pr_test, debounce_limit)

            if debounce_result.action == DebounceAction.PREFAULT_SET:
                # Call Fault Manager to set pre-fault
                self.fault_man.set_prefault(prefault_id, additional_info)
                self.hass_app.log(
                    f"PreFault {prefault_id} with {additional_info} was set",
                    level="DEBUG",
                )
                force_sm = False
            elif debounce_result.action == DebounceAction.PREFAULT_HEALED:
                # Call Fault Manager to heal pre-fault
                self.fault_man.clear_prefault(prefault_id, additional_info)
                self.hass_app.log(
                    f"PreFault {prefault_id} with {additional_info} was cleared",
                    level="DEBUG",
                )
                force_sm = False
            elif debounce_result.action == DebounceAction.NO_ACTION:
                force_sm = True
        else:
            # Debouncing not necessary at all (Test failed and prefault already raised or
            #  test passed and fault already cleared)
            pass
        
        self.hass_app.log(f"Leaving  process_prefault for {prefault_id} with counter:{debounce_result.counter} and force_sm {force_sm}",level="DEBUG")
        return debounce_result.counter, force_sm


def safety_mechanism_decorator(func: Callable) -> Callable:
    """
    A decorator to add additional logic before and after the execution of a safety mechanism function.

    This decorator is designed to wrap functions related to safety mechanisms, providing
    logging before and after the function's execution. It can be used to enhance visibility
    into the operation of safety mechanisms, such as logging the start and end of a function
    or handling exceptions.

    Args:
        func (Callable): The safety mechanism function to be decorated.

    Returns:
        Callable: A wrapped version of the input function with added pre- and post-execution logic.
    """

    def wrapper(self, sm: Any) -> Any:
        """
        Wrapper function for the safety mechanism.

        :param self: The instance of the class where the function is defined.
        :param args: Positional arguments for the safety mechanism function.
        :param kwargs: Keyword arguments for the safety mechanism function.
        :return: The result of the safety mechanism function.
        """
        self.hass_app.log(f"{func.__name__} was started!")

        result = func(self, sm)

        self.hass_app.log(f"{func.__name__} was ended!")

        return result

    return wrapper
