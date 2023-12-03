"""
DailyRoutines AppDaemon Application

This application automates a goodnight routine for a smart home, triggering
various Home Assistant services and checking their statuses.
"""

import appdaemon.plugins.hass.hassapi as hass
from datetime import datetime, timezone, timedelta

MINUTES_5 = 60*5

class DailyRoutines(hass.Hass):
    """
    Class representing the DailyRoutines automation for AppDaemon.
    """

    def initialize(self) -> None:
        """
        Initialize the goodnight routine listener.
        """
        self.turn_off_ligts_scene = self.args['turn_off_ligts_scene']
        self.ww_activate = self.args['ww_activate']
        self.awake_state = self.args['awake_state']
        self.next_awake = self.args['next_awake_time']

        self.listen_state(self.goodnight_triggered, self.awake_state, new="sleep")
        self.listen_state(self.awake_triggered, self.awake_state, new="awake")
        self.listen_state(self.next_awake_set, self.next_awake)

    def next_awake_set(self, entity: str, attribute: str, old: str, new: str, kwargs: dict) -> None:
        """
        Handle the event when the next awake time is set.
        Schedule preparations 30 minutes before the actual wake-up time.
        """
        try:
            # Parse the next wake-up time
            next_awake_time = datetime.strptime(new, "%Y-%m-%dT%H:%M:%S%z")
            # Calculate 30 minutes before the wake-up time
            prep_time = next_awake_time - timedelta(minutes=30)

            # Ensure the current time is timezone-aware using the same timezone
            current_time = datetime.now(timezone.utc).astimezone(next_awake_time.tzinfo)

            if current_time < prep_time:
                # Calculate seconds until the preparation time
                seconds_until_prep = int((prep_time - current_time).total_seconds())
                # Schedule the preparation function
                self.run_in(self.preparation_tasks, seconds_until_prep)
                self.log(f"Scheduled preparation tasks in {seconds_until_prep} seconds.")
        except ValueError:
            self.log(f"Invalid datetime format for next awake time [{new}].")

    def preparation_tasks(self, kwargs) -> None:
        """
        Perform preparation tasks.
        """
        self.log("Performing wake-up preparation tasks.")
        # Add logic for the preparation tasks here, such as heating water
        self.turn_warm_water(True)
        self.run_in(self.preparation_tasks_end, MINUTES_5)

    def preparation_tasks_end(self,_) -> None:
        """
        Perform preparation tasks finish actions
        """
        self.log("Performing wake-up preparation tasks finishing")
        # Add logic for the preparation tasks here, such as heating water
        self.turn_warm_water(False)       

    def goodnight_triggered(self, entity: str, attribute: str, old: str, new: str, kwargs: dict) -> None:
        """
        Handle the event when the goodnight status is triggered.

        Args:
        - entity: Entity being monitored
        - attribute: Attribute being monitored
        - old: Previous state
        - new: New state
        - kwargs: Additional arguments
        """

        self.activate_turn_off_lights_scene()
        # self.close_blinds_and_curtains()
        self.turn_warm_water(False)
        # self.turn_off_fans()
        # self.turn_off_multimedia_devices()

        self.log("Goodnight routine executed successfully.")

    def awake_triggered(self, entity: str, attribute: str, old: str, new: str, kwargs: dict) -> None:
        """
        Handle the event when the goodnight status is triggered.

        Args:
        - entity: Entity being monitored
        - attribute: Attribute being monitored
        - old: Previous state
        - new: New state
        - kwargs: Additional arguments
        """

        self.activate_goodmorning_lights_scene()
        # self.open_blinds_and_curtains()
        self.log("Awake routine executed successfully.")    
     
    def activate_turn_off_lights_scene(self) -> None:
        """
        Activate the 'TurnOffLights' scene in Home Assistant.
        """
        self.turn_on(self.turn_off_ligts_scene)

    def activate_goodmorning_lights_scene(self) -> None:
        """
        Activate the 'TurnOffLights' scene in Home Assistant.
        """
        self.turn_on(self.goodmorning_scene)

    def close_blinds_and_curtains(self) -> None:
        """
        Close all automated blinds and curtains.
        """
        raise NotImplementedError

    def turn_warm_water(self,state) -> None:
        """
        Turn off/on the warm water.
        """
        if state:
            self.turn_on(self.ww_activate)
        else:
            self.turn_off(self.ww_activate)            

    def turn_off_fans(self) -> None:
        """
        Turn off all fans.
        """
        raise NotImplementedError

    def turn_off_multimedia_devices(self) -> None:
        """
        Turn off all multimedia devices.
        """
        raise NotImplementedError

    def await_ha_confirmation(self) -> bool:
        """
        Await a confirmation from Home Assistant.

        Returns:
        - bool: True if confirmation received, False otherwise.
        """
        raise NotImplementedError

    def check_lights_and_ww_status(self) -> bool:
        """
        Check the status of lights and warm water.

        Returns:
        - bool: True if statuses are correct, False otherwise.
        """
        raise NotImplementedError
