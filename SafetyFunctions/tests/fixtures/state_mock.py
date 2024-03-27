from typing import Iterator, List, Optional

class MockBehavior:
    """
    Represents the behavior of a mocked function for a specific entity and its responses.

    Attributes:
        entity_id (str): The ID of the entity this behavior is associated with.
        generator (Iterator): An iterator that yields values to return for the associated entity ID.

    Methods:
        get_value(called_entity_id): Retrieves the next value from the generator if the entity IDs match.
    """
    def __init__(self, entity_id: str, generator: Iterator):
        """
        Initializes the MockBehavior with an entity ID and a generator for its values.

        Args:
            entity_id (str): The ID of the entity to mock.
            generator (Iterator): An iterator that provides the sequence of values to return.
        """
        self.entity_id = entity_id
        self.generator = generator

    def get_value(self, called_entity_id: str) -> Optional[str]:
        """
        Gets the next value from the generator if the called entity ID matches this behavior's entity ID.

        Args:
            called_entity_id (str): The entity ID for which the value is being requested.

        Returns:
            Optional[str]: The next value from the generator if the entity IDs match; otherwise, None.
        """
        if called_entity_id == self.entity_id:
            return next(self.generator, None)
        return None
    
def mock_get_state(entity_id: str, mock_behaviors: List[MockBehavior]) -> str:
    """
    Simulates the behavior of the `get_state` function based on predefined behaviors.

    Iterates over a list of MockBehavior objects to find a match for the called entity ID and
    returns the next value from the matched behavior's generator.

    Args:
        entity_id (str): The ID of the entity for which the state is being requested.
        mock_behaviors (List[MockBehavior]): A list of MockBehavior objects representing different entities' behaviors.

    Returns:
        str: The next value from the matched behavior's generator, or "default_value" if no match is found.
    """
    for behavior in mock_behaviors:
        value = behavior.get_value(entity_id)
        if value is not None:
            return value
    return "default_value"

