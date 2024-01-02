import appdaemon.plugins.hass.hassapi as hass
from typing import List, Type, Any, get_origin, get_args, Callable

class SafetyComponent:
    """ Base class for domain-specific safety components. """

    def __init__(self, hass_app: hass.Hass):
        """
        Initialize the safety component.

        :param hass_app: The Home Assistant application instance.
        """
        self.hass_app = hass_app

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

    
def safety_mechanism_decorator(func: Callable) -> Callable:
    """
    Decorator to wrap safety mechanism functions.

    This decorator can be used to add pre- and post-execution logic 
    around a safety mechanism function.

    :param func: The safety mechanism function to be decorated.
    :return: The wrapper function.
    """
    def wrapper(self, *args, **kwargs) -> Any:
        """
        Wrapper function for the safety mechanism.

        :param self: The instance of the class where the function is defined.
        :param args: Positional arguments for the safety mechanism function.
        :param kwargs: Keyword arguments for the safety mechanism function.
        :return: The result of the safety mechanism function.
        """
        self.hass_app.log(f'{func.__name__} was started!')

        result = func(self, *args, **kwargs) 

        self.hass_app.log(f'{func.__name__} was ended!')


        return result
    return wrapper    
