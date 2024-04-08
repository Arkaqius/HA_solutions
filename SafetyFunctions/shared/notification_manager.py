"""
Notification Manager Module for Home Assistant Safety System

This module contains the NotificationManager class, designed to handle various types of notifications within a Home Assistant-based safety system. 
It facilitates the delivery of notifications through Home Assistant's notification services, dashboard updates, and other notification mechanisms 
such as lights and alarms. The NotificationManager is configurable, allowing for dynamic notification behaviors based on the severity of detected faults and system states.

The NotificationManager class provides a structured way to manage and execute notifications based on predefined levels of urgency. It maps different 
notification levels to specific methods that handle the logic for each notification type, ensuring that users are informed of system states and faults in a timely and appropriate manner.

Features include:
- Configurable notification levels, allowing for tailored responses to different fault conditions.
- Integration with Home Assistant services for sending notifications to devices, updating dashboard states, and controlling home automation entities like lights and alarms.
- Support for additional information in notifications, enabling detailed fault descriptions to be communicated to the user.

This module plays a crucial role in the safety system's ability to notify users of faults and system states, contributing to the overall responsiveness and reliability of the system.

Classes:
    NotificationManager: Manages the configuration and execution of notifications within the safety system.
"""

from typing import Optional, Callable
import appdaemon.plugins.hass.hassapi as hass  # type: ignore


class NotificationManager:
    """
    A manager for sending notifications within a Home Assistant-based safety system, using various
    methods like alerts to mobile devices, dashboard updates, and control of home automation entities
    (e.g., lights, alarms) based on event severity.

    Attributes:
        hass_app (hass.Hass): An instance of the Home Assistant application for service calls.
        notification_config (dict): Configuration for notification preferences, including entity IDs.

    Args:
        hass_app (hass.Hass): The Home Assistant application instance.
        notification_config (dict): Configuration for different notification levels and entities.
    """

    def __init__(self, hass_app: hass.Hass, notification_config: dict):
        """
        Initializes the NotificationManager with Home Assistant and notification configurations.

        Parameters:
            hass_app: Home Assistant application instance for making service calls.
            notification_config: Configurations for notification levels and corresponding entities.
        """
        self.hass_app = hass_app
        self.notification_config = notification_config

        # Map notification levels to their respective methods
        self.level_methods : dict[int, Callable[[str], None] | None] = {
            1: self._notify_level_1_additional,
            2: self._notify_level_2_additional,
            3: None,
            4: None,
        }

    def notify(self, fault: str, level: int, additional_info: Optional[dict]) -> None:
        """
        Sends notifications based on fault severity, employing various methods like alerts,
        dashboard updates, and automation controls.

        Parameters:
            fault: The fault's name.
            level: Notification level, dictating the notification type.
            additional_info: Additional fault details (optional) for the notification message.
        """

        # Construct the message to be sent
        message = f"{fault}\n"
        if additional_info:
            for key, value in additional_info.items():
                message += f"{key}: {value}\n"

        # Send notification to company apps
        self._notify_company_app(level, message)
        # Set dashboard notification
        self._set_dashboard_notification(message, level)
        # Call the corresponding method for the notification level
        notify_method = self.level_methods.get(level)
        if notify_method:
            notify_method(message)
        else:
            self.hass_app.log(
                f"Notification level {level} has not additional actions", level="DEBUG"
            )

    def _set_dashboard_notification(self, message: str, level: int) -> None:
        """
        Displays a notification message on the Home Assistant dashboard based on severity level.

        Parameters:
            message: The message to be displayed.
            level: The message's severity level, influencing its presentation.
        """
        # This function assumes that you have an entity in Home Assistant that represents
        # a text field on a dashboard. You would need to create this entity and configure it
        # to display messages.
        dashboard_entity = self.notification_config.get(f"dashboard_{level}_entity")
        if dashboard_entity:
            self.hass_app.set_state(dashboard_entity, state=message)
        else:
            self.hass_app.log(
                f"No dashboard entity configured for level '{level}'", level="WARNING"
            )

    def _notify_level_1_additional(self, message: str) -> None:
        """
        Triggers an immediate response for level 1 notifications by sounding an alarm and turning lights red.
        This method represents the highest priority action, indicating an immediate emergency.

        Args:
            message (str): The detailed message for the notification, not directly used in this method but
                           required for consistency with the interface.
        """
        self.hass_app.call_service(
            "alarm_control_panel/alarm_trigger",
            entity_id=self.notification_config["alarm_entity"],
        )
        self.hass_app.call_service(
            "light/turn_on",
            entity_id=self.notification_config["light_entity"],
            color_name="red",
        )

    def _notify_level_2_additional(self, message: str) -> None:
        """
        Handles level 2 notifications by turning lights yellow, symbolizing a hazard that may not require
        immediate evacuation but still demands attention.

        Args:
            message (str): The detailed message for the notification, not directly used in this method but
                           required for consistency with the interface.
        """
        self.hass_app.call_service(
            "light/turn_on",
            entity_id=self.notification_config["light_entity"],
            color_name="yellow",
        )

    def _prepare_notification_data(self, level: int, message: str) -> dict:
        """
        Prepares the notification data based on the level and fault details.

        Args:
            level (int): The urgency level of the notification.
            fault (str): The fault identifier.
            message (str): The message to be sent.

        Returns:
            dict: The notification data ready to be sent.
        """
        base_url = "/lovelace/home-safety"
        common_data = {
            "persistent": True,
            "url": base_url,
        }

        notification_configs = {
            1: {
                "title": "Immediate Emergency!",
                "message": message,
                "data": {
                    **common_data,
                    "color": "#FF0000",  # Red for immediate emergencies.
                    "vibrationPattern": "100, 1000, 100, 1000, 100",
                    "sticky": True,
                    "tag": "Emergency_Fault",
                    "notification_icon": "mdi:exit-run",
                    "importance": "high",  # Setting high importance for level 1 notifications
                },
            },
            2: {
                "title": "Hazard!",
                "message": message,
                "data": {
                    **common_data,
                    "color": "#FFA500",  # Orange, a mix of yellow and red.
                    "sticky": True,
                    "tag": "Hazard_Fault",
                    "notification_icon": "mdi:hazard-lights",
                },
            },
            3: {
                "title": "Warning!",
                "message": message,
                "data": {
                    **common_data,
                    "color": "#FFFF00",  # Hex code for yellow.
                    "sticky": False,
                    "tag": "Warning_Fault",
                    "notification_icon": "mdi:home-alert",
                },
            },
            # Level 4 is intentionally left out as per previous instructions
        }

        return notification_configs.get(level, {})

    def _notify_company_app(self, level: int, message: str) -> None:
        """
        Sends a company app notification based on the specified level and fault details.

        Args:
            level (int): The notification level.
            fault (str): The fault identifier.
            message (str): The detailed message for the notification.
        """
        if level == 4:
            # No notification is sent for level 4.
            return

        notification_data = self._prepare_notification_data(level, message)
        if notification_data:
            # Convert dict to JSON string if necessary or use as is for service call.
            # json_data = json.dumps(notification_data['data'])
            self.hass_app.call_service(
                "notify/notify",
                title=notification_data["title"],
                message=notification_data["message"],
                data=notification_data["data"],
            )
        else:
            self.hass_app.log(
                f"No notification configuration for level {level}", level="WARNING"
            )
