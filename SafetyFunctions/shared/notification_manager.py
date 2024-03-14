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
from typing import Optional
import appdaemon.plugins.hass.hassapi as hass

class NotificationManager:
    """
    Manages notifications within a Home Assistant-based safety system.

    This class interfaces with Home Assistant to send notifications through various channels
    based on the severity of events or faults detected within the system. It supports multiple
    levels of notifications, from high-priority alerts that trigger immediate actions (such as
    sending alerts to mobile devices and activating alarms) to informational updates displayed
    on the Home Assistant dashboard.

    Attributes:
        hass_app (hass.Hass): Instance of the Home Assistant application for service calls.
        notification_config (dict): Configuration dict specifying notification preferences and
            entity IDs for various notification methods and levels.

    Args:
        hass_app (hass.Hass): The Home Assistant application instance, used for making service calls.
        notification_config (dict): A dictionary containing configurations for notification levels,
            including entity IDs for alarms, lights, and dashboard notification entities.
    """
    def __init__(self, hass_app: hass.Hass, notification_config: dict):
        """
        Initialize the Notification Manager with specific configurations.

        :param hass_app: The Home Assistant application instance.
        :param notification_config: A dictionary containing the notification configuration.
        """
        self.hass_app = hass_app
        self.notification_config = notification_config

        # Map notification levels to their respective methods
        self.level_methods = {
            1: self.notify_level_1,
            2: self.notify_level_2,
            3: self.notify_level_3,
            4: self.notify_level_4,
        }

    def notify(self, fault: str, level: int, additional_info: Optional[dict]):
        """
        Sends a notification based on the specified fault level and additional fault details.

        Depending on the notification level, this method triggers different actions, such as
        sending alerts to mobile devices, updating the Home Assistant dashboard, or controlling
        home automation entities like lights and alarms to indicate the severity of the fault.

        Args:
            fault (str): Name of the fault.
            level (int): The notification level, determining the type of notification to send.
            additional_info (Optional[dict]): Additional details about the fault, which can be included
                in the notification message. Defaults to None.
        """
        
        # Construct the message to be sent
        message = f"Fault Detected: {fault}\n"
        if additional_info:
            for key, value in additional_info.items():
                message += f"{key}: {value}\n"

        # Call the corresponding method for the notification level
        notify_method = self.level_methods.get(level)
        if notify_method:
            notify_method(message)
        else:
            self.hass_app.log(
                f"Notification level {level} is not supported.", level="WARNING"
            )

    def set_dashboard_notification(self, message: str, level: str):
        """
        Displays a message on the Home Assistant dashboard corresponding to the specified level.

        This method is used for informational purposes, providing updates or alerts on the Home Assistant
        dashboard based on the severity level of the message.

        Args:
            message (str): The message to display on the dashboard.
            level (str): The severity level ('info', 'warning', or 'hazard') of the message, which may
                determine the style or placement of the notification on the dashboard.
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

    def notify_level_1(self, message):
        # Send a high-priority notification to the phone, sound alarm, and turn light red
        self.hass_app.call_service(
            "notify/notify",
            message=message,
            title="High Priority Alert",
            data={"priority": "high"},
        )
        self.hass_app.call_service(
            "alarm_control_panel/alarm_trigger",
            entity_id=self.notification_config["alarm_entity"],
        )
        self.hass_app.call_service(
            "light/turn_on",
            entity_id=self.notification_config["light_entity"],
            color_name="red",
        )

    def notify_level_2(self, message):
        # Send a high-priority notification to the phone and dashboard, turn light yellow
        self.hass_app.call_service(
            "notify/notify", message=message, title="Alert", data={"priority": "high"}
        )
        self.set_dashboard_notification(message, "hazard")
        self.hass_app.call_service(
            "light/turn_on",
            entity_id=self.notification_config["light_entity"],
            color_name="yellow",
        )

    def notify_level_3(self, message):
        # Send a normal notification to the phone and as a warning to the dashboard
        self.hass_app.call_service("notify/notify", message=message, title="Warning")
        self.set_dashboard_notification(message, "warning")

    def notify_level_4(self, message):
        # Only display the information on the dashboard
        self.set_dashboard_notification(message, "info")
