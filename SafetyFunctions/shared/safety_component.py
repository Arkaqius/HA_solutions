import appdaemon.plugins.hass.hassapi as hass
from typing import List, Type, Any, get_origin, get_args, Callable
import traceback
from collections import namedtuple
from shared.fault_manager import FaultManager


class SafetyComponent:
    """ Base class for domain-specific safety components. """

    # Define the named tuple with possible outcomes
    DebounceAction = namedtuple('DebounceAction', ['NO_ACTION', 'PREFAULT_SET', 'PREFAULT_HEALED'])
    DebounceResult = namedtuple('DebounceResult', ['action', 'counter'])

    # Set the possible outcomes
    DEBOUNCE_ACTION = DebounceAction(NO_ACTION=0, PREFAULT_SET=1, PREFAULT_HEALED=-1)
    
    def __init__(self, hass_app: hass.Hass, fault_man : FaultManager):
        """
        Initialize the safety component.

        :param hass_app: The Home Assistant application instance.
        """
        self.hass_app = hass_app
        self.fault_man = fault_man

    @staticmethod
    def is_valid_binary_sensor(entity_name: str) -> bool:
        """
        Check if a given entity name is a valid binary sensor.

        :param entity_name: The entity name to validate.
        :return: True if valid binary sensor, False otherwise.
        """
        return isinstance(entity_name, str) and entity_name.startswith("binary_sensor.")

    @staticmethod
    def is_valid_sensor(entity_name: str) -> bool:
        """
        Check if a given entity name is a valid sensor.

        :param entity_name: The entity name to validate.
        :return: True if valid sensor, False otherwise.
        """
        return isinstance(entity_name, str) and entity_name.startswith("sensor.")
    
    def validate_entity(self, entity_name : str, entity: Any, expected_type: Type) -> bool:
        """
        Validate a single entity against the expected type.

        :param entity: The entity to validate.
        :param expected_type: The expected type (e.g., type, List[type], etc.).
        :return: True if the entity is valid, False otherwise.
        """
        # Check for generic types like List[type]
        if get_origin(expected_type):
            if not isinstance(entity, get_origin(expected_type)):
                self.hass_app.log(f"Entity {entity_name} should be a {get_origin(expected_type).__name__}", level="ERROR")
                return False
            element_type = get_args(expected_type)[0]
            if not all(isinstance(item, element_type) for item in entity):
                self.hass_app.log(f"Elements of entity {entity_name} should be {element_type.__name__}", level="ERROR")
                return False
        # Non-generic types
        elif not isinstance(entity, expected_type):
            self.hass_app.log(f"Entity {entity_name} should be {expected_type.__name__}", level="ERROR")
            return False
        
        return True

    def validate_entities(self, sm_args: dict[str, Any], expected_types: dict[str, Type]) -> bool:
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
                self.hass_app.log(f"Missing required argument: {entity_name}", level="ERROR")
                return False
            if not self.validate_entity(entity_name,sm_args[entity_name], expected_type):
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

    def _debounce(self,current_counter, pr_test, debounce_limit=3):
        """
        Generic debouncing function that updates the counter based on the state
        and returns an action indicating whether a pre-fault should be set, cleared, or no action taken.
        
        :param current_counter: The current debounce counter for the sensor or mechanism.
        :param state: The current state to be debounced (True for active, False for inactive).
        :param debounce_limit: The limit at which the state is considered stable.
        :return: A tuple containing the debounce action and the updated counter.
        """
        if pr_test:
            new_counter = min(debounce_limit, current_counter + 1)
            action = self.DEBOUNCE_ACTION.PREFAULT_SET if new_counter >= debounce_limit else self.DEBOUNCE_ACTION.NO_ACTION
        else:
            new_counter = max(-debounce_limit, current_counter - 1)
            action = self.DEBOUNCE_ACTION.PREFAULT_HEALED if new_counter <= -debounce_limit else self.DEBOUNCE_ACTION.NO_ACTION

        return self.DebounceResult(action=action, counter=new_counter)
    
    def process_prefault(self,prefault_id,current_counter, pr_test, debounce_limit=3):
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
                - bool: A flag indicating whether to inhibit further triggers. 
                        True to inhibit, False to allow further triggers.

        Raises:
            None
        """
        
        is_inhib = False
        action = self.DEBOUNCE_ACTION.NO_ACTION
        prefault_cur_state = True # TODO get from FaultManager
        
        # Check if any actions is needed
        if (pr_test and not prefault_cur_state) or (not pr_test and prefault_cur_state):
            debounce_result  = self._debounce(current_counter,pr_test,debounce_limit)
            
            if debounce_result.action == self.DEBOUNCE_ACTION.PREFAULT_SET and not prefault_cur_state:
                # Call Fault Manager to set pre-fault
                self.fault_man.set_prefault(prefault_id)
                is_inhib = False
            elif action == self.DEBOUNCE_ACTION.PREFAULT_HEALED and prefault_cur_state:
                # Call Fault Manager to heal pre-fault
                self.fault_man.heal_prefault(prefault_id)
                is_inhib = False
            elif debounce_result.action == self.DEBOUNCE_ACTION.NO_ACTION:
                is_inhib = True
                           
        return debounce_result.counter, is_inhib

    
def safety_mechanism_decorator(func: Callable) -> Callable:
    """
    Decorator to wrap safety mechanism functions.

    This decorator can be used to add pre- and post-execution logic 
    around a safety mechanism function.

    :param func: The safety mechanism function to be decorated.
    :return: The wrapper function.
    """
    def wrapper(self, sm) -> Any:
        """
        Wrapper function for the safety mechanism.

        :param self: The instance of the class where the function is defined.
        :param args: Positional arguments for the safety mechanism function.
        :param kwargs: Keyword arguments for the safety mechanism function.
        :return: The result of the safety mechanism function.
        """
        self.hass_app.log(f'{func.__name__} was started!')

        result = func(self, sm) 

        self.hass_app.log(f'{func.__name__} was ended!')


        return result
    return wrapper    


