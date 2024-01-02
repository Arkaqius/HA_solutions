from typing import Callable, List, Any

class SafetyMechanism:
    """
    Class to define and manage a safety mechanism in the Home Assistant environment.
    """

    def __init__(self, hass_app, callback: Callable[..., Any], name: str, **kwargs):
        """
        Initialize the SafetyMechanism.

        :param hass_app: The Home Assistant application instance.
        :param entities: List of entity IDs to monitor.
        :param callback: The callback function to execute when an entity state changes.
        :param name: The name of this safety mechanism.
        :param kwargs: Additional keyword arguments to pass to the callback function.
        """
        self.hass_app = hass_app
        self.entities = self.extract_entities(kwargs)
        self.callback = callback
        self.name = name
        self.setup_listeners()
        self.sm_args = kwargs

    def setup_listeners(self):
        """
        Set up listeners for each entity in the entities list.
        Listeners will trigger `entity_changed` method on state change of any monitored entity.
        """
        for entity in self.entities:
            self.hass_app.log(f"Setting up listener for entity: {entity}")
            self.hass_app.listen_state(self.entity_changed, entity)

    def entity_changed(self, entity: str, attribute: str, old: Any, new: Any, kwargs: dict):
        """
        Callback method called when a monitored entity changes state.

        :param entity: The entity ID of the state change.
        :param attribute: The attribute that changed.
        :param old: The old state value.
        :param new: The new state value.
        :param kwargs: Additional keyword arguments.
        """
        self.hass_app.log(f"Entity changed detected for {entity}, calling callback.")
        self.callback(**self.sm_args)
        
    def extract_entities(self, kwargs: dict) -> List[str]:
        """
        Extract entity IDs from the kwargs.

        :param kwargs: The specific arguments for the safety mechanism.
        :return: List of entity IDs to monitor.
        """
        entities = []
        for _, value in kwargs.items():
            if isinstance(value, list):
                entities.extend(value)
            elif isinstance(value, str):
                entities.append(value)
        return entities    