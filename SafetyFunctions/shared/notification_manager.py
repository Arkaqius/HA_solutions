import appdaemon.plugins.hass.hassapi as hass


class NotificationManager:
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

    def notify(self, fault: str, level: int, additional_info: dict):
        """
        Send a notification based on the fault level.

        :param fault: The name or description of the fault.
        :param level: The notification level (1-4).
        :param additional_info: A dictionary with additional details about the fault.
        """
        # Construct the message to be sent
        message = f"Fault Detected: {fault}\n"
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
        Display a message on the Home Assistant dashboard.

        :param message: The message to display.
        :param level: The level of the message ('info', 'warning', or 'hazard').
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
