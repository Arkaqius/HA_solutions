import appdaemon.plugins.hass.hassapi as hass

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
