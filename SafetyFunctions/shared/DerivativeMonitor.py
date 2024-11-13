"""
This module defines the DerivativeMonitor class, which is a singleton class designed to monitor entity changes
and calculate first and second derivatives. This is useful for tracking rate of change and acceleration of entity values,
such as temperature trends, in a Home Assistant-based safety system.

Classes:
- DerivativeMonitor: A singleton class to register entities, calculate derivatives, and provide access to derivative data.
"""

from typing import Optional, Dict, Any, Callable
from appdaemon.plugins.hass.hassapi import Hass  # type: ignore
from threading import Lock


class DerivativeMonitor:
    """
    Singleton class for monitoring entity state changes and calculating first and second derivatives.
    Allows entities to be registered with specific sampling times and saturation limits. Derivatives
    are calculated periodically based on the sampling time provided at registration.
    """

    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        """Ensures that only one instance of DerivativeMonitor is created."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DerivativeMonitor, cls).__new__(cls)
        return cls._instance

    def __init__(self, hass_app: Hass) -> None:
        """Initializes the singleton instance if not already initialized."""
        if not hasattr(self, "initialized"):
            self.hass_app = hass_app
            self.entities: Dict[str, Dict[str, Any]] = {}
            self.derivative_data: Dict[str, Dict[str, Optional[float]]] = {}
            self.initialized = True

    def register_entity(
        self,
        entity_id: str,
        sample_time: int,
        low_saturation: float,
        high_saturation: float,
    ) -> None:
        """
        Registers an entity to monitor with specified sampling time and saturation limits,
        and creates Home Assistant entities for the first and second derivatives.

        Args:
            entity_id (str): The ID of the entity to monitor.
            sample_time (int): Sampling time in seconds for fetching and calculating derivatives.
            low_saturation (float): Lower saturation limit for derivative values.
            high_saturation (float): Upper saturation limit for derivative values.
        """
        self.entities[entity_id] = {
            "sample_time": sample_time,
            "low_saturation": low_saturation,
            "high_saturation": high_saturation,
            "prev_value": None,
            "first_derivative": None,
            "second_derivative": None,
            "last_sample_time": None,
        }
        # Create derivative entities in Home Assistant with initial state as None
        self.hass_app.set_state(
            f"sensor.{entity_id}_rate",
            state=None,
            attributes={"friendly_name": f"{entity_id} Rate"},
        )
        self.hass_app.set_state(
            f"sensor.{entity_id}_rateOfRate",
            state=None,
            attributes={"friendly_name": f"{entity_id} Rate of Rate"},
        )

        self.schedule_sampling(entity_id, sample_time)

    def schedule_sampling(self, entity_id: str, sample_time: int) -> None:
        """
        Schedules periodic sampling for the specified entity based on its sampling time.

        Args:
            entity_id (str): The ID of the entity to sample.
            sample_time (int): Sampling time in seconds.
        """
        self.hass_app.run_every(
            self._calculate_diff, "now", sample_time, entity_id=entity_id
        )

    def _calculate_diff(self, kwargs: Dict[str, Any]) -> None:
        """
        Calculates the first and second derivatives for a registered entity's state
        and updates the corresponding Home Assistant entities.

        Args:
            kwargs (dict): Contains "entity_id" key identifying the entity to process.
        """
        entity_id = kwargs.get("entity_id")
        if entity_id not in self.entities:
            self.hass_app.log(f"Entity {entity_id} not registered.", level="ERROR")
            return

        entity_config = self.entities[entity_id]
        current_value = self._get_entity_value(entity_id)
        if current_value is None:
            return

        # Calculate first and second derivatives
        prev_value = entity_config["prev_value"]
        if prev_value is not None:
            first_derivative = current_value - prev_value
            first_derivative = max(
                entity_config["low_saturation"],
                min(first_derivative, entity_config["high_saturation"]),
            )

            prev_first_derivative = entity_config["first_derivative"]
            second_derivative: None | Any = (
                None
                if prev_first_derivative is None
                else first_derivative - prev_first_derivative
            )
            if second_derivative is not None:
                second_derivative = max(
                    entity_config["low_saturation"],
                    min(second_derivative, entity_config["high_saturation"]),
                )

            entity_config["first_derivative"] = first_derivative
            entity_config["second_derivative"] = second_derivative
        entity_config["prev_value"] = current_value

        # Store derivative data
        self.derivative_data[entity_id] = {
            "first_derivative": entity_config["first_derivative"],
            "second_derivative": entity_config["second_derivative"],
        }

        # Update derivative states in Home Assistant
        self.hass_app.set_state(
            f"sensor.{entity_id}_rate", state=entity_config["first_derivative"]
        )
        self.hass_app.set_state(
            f"sensor.{entity_id}_rateOfRate", state=entity_config["second_derivative"]
        )

    def _get_entity_value(self, entity_id: str) -> Optional[float]:
        """
        Retrieves the current value of the specified entity.

        Args:
            entity_id (str): The ID of the entity to retrieve.

        Returns:
            Optional[float]: The entity's current state as a float, or None if retrieval fails.
        """
        try:
            return float(self.hass_app.get_state(entity_id))
        except (TypeError, ValueError):
            self.hass_app.log(
                f"Unable to retrieve or convert state for {entity_id}.", level="ERROR"
            )
            return None

    def get_first_derivative(self, entity_id: str) -> Optional[float]:
        """
        Retrieves the first derivative for the specified entity.

        Args:
            entity_id (str): The ID of the entity.

        Returns:
            Optional[float]: The latest first derivative or None if unavailable.
        """
        return self.derivative_data.get(entity_id, {}).get("first_derivative")

    def get_second_derivative(self, entity_id: str) -> Optional[float]:
        """
        Retrieves the second derivative for the specified entity.

        Args:
            entity_id (str): The ID of the entity.

        Returns:
            Optional[float]: The latest second derivative or None if unavailable.
        """
        return self.derivative_data.get(entity_id, {}).get("second_derivative")
