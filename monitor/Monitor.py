import appdaemon.plugins.hass.hassapi as hass
from datetime import datetime, timezone, time

RESET_TIME  = "9:00:00"

class Monitor(hass.Hass):
    """
    Class representing the monitoring functionalities for AppDaemon.
    """

    def initialize(self) -> None:
        """
        Initialize the awake and sleep state listeners.
        """
        self.ux_awake_state = self.args['ux_awake_state']
        self.next_alarm_sensor = self.args['next_alarm_sensor']

        # Listen for changes to the input_boolean.ux_awake_state entity
        self.listen_state(self.ux_awake_state_changed, self.ux_awake_state)
        # Listen for changes to the next_alarm sensor
        self.listen_state(self.alarm_time_set, self.next_alarm_sensor)
        # Immediately check the current state of the alarm sensor
        current_alarm_value = self.get_state(self.next_alarm_sensor)
        if current_alarm_value or current_alarm_value != 'Unavailable':
            # Fake a state change to handle the current value of the sensor
            self.alarm_time_set(self.next_alarm_sensor, "state", None, current_alarm_value, {})
        # Reset awake state every fixed time
        self.run_daily(self.reset_awake,RESET_TIME)

    def ux_awake_state_changed(self, entity: str, attribute: str, old: str, new: str, kwargs: dict) -> None:
        """
        Handle the event when the ux_awake_state changes.
        """
        if new == "on":
            self.log("User is awake.")
            self.set_state("binary_sensor.monitor_awake_state", state="awake")
        elif new == "off":
            self.log("User is asleep.")
            self.set_state("binary_sensor.monitor_awake_state", state="sleep")

    def alarm_time_set(self, entity: str, attribute: str, old: str, new: str, kwargs: dict) -> None:
        """
        Handle the event when the next_alarm sensor changes.
        Schedule a check when the alarm time is within the waking hours (4 AM to 9 AM).
        """
        try:
            # Adjusted format to match ISO 8601
            next_alarm_time = datetime.strptime(new, "%Y-%m-%dT%H:%M:%S%z")

            # Ensure the current time is also timezone-aware using the same timezone as the alarm
            current_time = datetime.now(timezone.utc).astimezone(next_alarm_time.tzinfo)

            # Define the waking hours range
            waking_hours_start = time(4, 0)  # 4 AM TODO, hardcoded!
            waking_hours_end = time(9, 0)  # 9 AM TODO, hardcoded!

            # Check if the alarm is within the waking hours
            if waking_hours_start <= next_alarm_time.time() <= waking_hours_end:
                # Calculate how many seconds from now until the alarm time
                time_difference = next_alarm_time - current_time
                seconds_to_alarm = int(time_difference.total_seconds())
                # Schedule the alarm_triggered function to run at the alarm time
                self.run_in(self.alarm_triggered, seconds_to_alarm)
                self.set_state("sensor.next_awake_time", state=next_alarm_time)
                self.log(f"Setting runable in next {seconds_to_alarm} seconds")
            else:
                self.log("Alarm is outside of waking hours, ignoring.")
        except ValueError:
            self.log(f"Invalid datetime format in next_alarm_sensor [{new}]. Please ensure it's in '%Y-%m-%d %H:%M:%S' format.")

    def alarm_triggered(self, _) -> None:
        """
        Callback for when the alarm time is hit.
        """
        self.log("Alarm was hit. Setting user state to asleep.")
        self.turn_on(self.ux_awake_state)
        self.set_state("binary_sensor.monitor_awake_state", state="awake")

    def reset_awake(self,_) -> None:
        """
        Callback for reset awake state
        """
        self.set_state("binary_sensor.monitor_awake_state", state="awake")
        