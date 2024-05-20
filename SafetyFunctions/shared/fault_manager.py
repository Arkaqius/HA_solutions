"""
Fault Management Module for Home Assistant Safety System

This module defines the core components and logic necessary for managing faults and pre-faults within a Home Assistant-based safety system.
It facilitates the detection, tracking, and resolution of fault conditions, integrating closely with safety mechanisms to proactively address potential issues before they escalate into faults.

Classes:
    PreFault: Represents pre-fault conditions that are potential precursors to faults.
    Fault: Represents faults within the system, which are conditions requiring attention.
    FaultManager: Manages faults and pre-faults, orchestrating detection and response.

The module supports a many-to-one mapping of pre-faults to faults, allowing multiple pre-fault conditions to contribute to or influence the state of a single fault.
This design enables a nuanced and responsive fault management system capable of handling complex scenarios and dependencies within the safety system architecture.

Primary functionalities include:
- Initializing and tracking the states of faults and pre-faults based on system configuration and runtime observations.
- Dynamically updating fault states in response to changes in associated pre-fault conditions.
- Executing defined recovery actions and notifications as part of the fault resolution process.

This module is integral to the safety system's ability to maintain operational integrity and respond effectively to detected issues,
ensuring a high level of safety and reliability.

Note:
    This module is designed for internal use within the Home Assistant safety system
    and relies on configurations and interactions with other system components, including safety mechanisms and recovery action definitions.
"""

from typing import Optional, Callable
from shared.types_common import FaultState, SMState, PreFault, Fault
import appdaemon.plugins.hass.hassapi as hass


class FaultManager:
    """
    Manages the fault and pre-fault conditions within the safety management system.

    This includes initializing fault and pre-fault objects, enabling pre-faults, setting and
    clearing fault states, and managing notifications and recovery actions associated with faults.

    Attributes:
        notify_man (NotificationManager): The manager responsible for handling notifications.
        recovery_man (RecoveryManager): The manager responsible for executing recovery actions.
        faults (dict[str, Fault]): A dictionary of fault objects managed by this manager.
        prefaults (dict[str, PreFault]): A dictionary of pre-fault objects managed by this manager.
        sm_modules (dict): A dictionary mapping module names to module objects containing safety mechanisms.

    Args:
        notify_man (NotificationManager): An instance of the NotificationManager.
        recovery_man (RecoveryManager): An instance of the RecoveryManager.
        sm_modules (dict): A dictionary mapping module names to loaded module objects.
        prefault_dict (dict): A dictionary with pre-fault configurations.
        fault_dict (dict): A dictionary with fault configurations.
    """

    def __init__(
        self,
        hass: hass,
        sm_modules: dict,
        prefault_dict: dict,
        fault_dict: dict,
    ) -> None:
        """
        Initialize the Fault Manager.

        :param config_path: Path to the YAML configuration file.
        """
        self.notify_interface: (
            Callable[[str, int, FaultState, dict | None], None] | None
        ) = None
        self.recovery_interface: Callable[[PreFault], None] | None = None
        self.faults: dict[str, Fault] = fault_dict
        self.prefaults: dict[str, PreFault] = prefault_dict
        self.sm_modules: dict = sm_modules
        self.hass: hass.Hass = hass

    def register_callbacks(
        self,
        recovery_interface: Callable[[PreFault], None],
        notify_interface: Callable[[str, int, FaultState, dict | None], None],
    ) -> None:
        self.recovery_interface = recovery_interface
        self.notify_interface = notify_interface

    def init_safety_mechanisms(self) -> None:
        """
        Initializes safety mechanisms for each pre-fault condition.

        This function iterates over all pre-faults defined in the system, initializing their respective
        safety mechanisms as specified by the safety mechanism's name (`sm_name`). It also sets the initial state
        of the pre-faults to DISABLED if initialization is successful, or to ERROR otherwise.
        """
        for prefault_name, prefault_data in self.prefaults.items():
            result: bool = prefault_data.module.init_safety_mechanism(
                prefault_data.sm_name, prefault_name, prefault_data.parameters
            )
            if result:
                prefault_data.sm_state = SMState.DISABLED
            else:
                prefault_data.sm_state = SMState.ERROR

    def get_all_prefault(self) -> dict[str, PreFault]:
        """
        TODO
        """
        return self.prefaults

    def enable_all_prefaults(self) -> None:
        """
        Enables all pre-fault safety mechanisms that are currently disabled.

        This method iterates through all pre-faults stored in the system, and for each one that is in a DISABLED
        state, it attempts to enable the safety mechanism associated with it. The enabling function is dynamically
        invoked based on the `sm_name`. If the enabling operation is successful, the pre-fault state is updated
        to ENABLED, otherwise, it remains in ERROR.

        During the enabling process, the system also attempts to fetch and update the state of the safety mechanisms
        directly through the associated safety mechanism's function, updating the system's understanding of each
        pre-fault's current status.
        """
        for prefault_name, prefault_data in self.prefaults.items():
            if prefault_data.sm_state == SMState.DISABLED:
                result: bool = prefault_data.module.enable_safety_mechanism(
                    prefault_name, SMState.ENABLED
                )
                if result:
                    prefault_data.sm_state = SMState.ENABLED
                    # Force each sm to get state if possible
                    sm_fcn = getattr(prefault_data.module, prefault_data.sm_name)
                    sm_fcn(prefault_data.module.safety_mechanisms[prefault_data.name])
                else:
                    prefault_data.sm_state = SMState.ERROR

    def set_prefault(
        self, prefault_id: str, additional_info: Optional[dict] = None
    ) -> None:
        """
        Sets a pre-fault to its active state, indicating a potential fault condition.

        This method updates the pre-fault's state to SET, triggers any associated faults.

        Args:
            prefault_id (str): The identifier of the pre-fault to set.
            additional_info (dict | None, optional): Additional information or context for the pre-fault. Defaults to None.

        Raises:
            KeyError: If the specified prefault_id does not exist in the prefaults dictionary.
        """
        # Update prefault registry
        self.prefaults[prefault_id].state = FaultState.SET

        # Call Related Fault
        self._set_fault(prefault_id, additional_info)

    def clear_prefault(self, prefault_id: str, additional_info: dict) -> None:
        """
        Clears a pre-fault state, indicating that the condition leading to a potential fault has been resolved.

        This method updates the specified pre-fault's state to CLEARED. It then attempts to clear any
        associated fault states if applicable. This is an important part of the fault management process,
        allowing the system to recover from potential issues and restore normal operation.

        The method also triggers notifications and recovery actions if specified for the cleared pre-fault,
        based on the provided additional information. This ensures that any necessary follow-up actions
        are taken to fully address and resolve the condition.

        Args:
            prefault_id (str): The identifier of the pre-fault to be cleared.
            additional_info (dict | None, optional): Additional information or context relevant to the pre-fault being cleared. Defaults to None.

        Raises:
            KeyError: If the specified prefault_id does not exist in the prefaults dictionary, indicating an attempt to clear an undefined pre-fault.
        """
        # Update prefault registry
        self.prefaults[prefault_id].state = FaultState.CLEARED

        # Call Related Fault
        self._clear_fault(prefault_id, additional_info)

    def check_prefault(self, prefault_id: str) -> FaultState:
        """
        Checks the current state of a specified pre-fault.

        This method returns the current state of the pre-fault identified by the given `prefault_id`.
        The state indicates whether the pre-fault is active (SET), has been cleared (CLEARED), or
        has not been tested (NOT_TESTED). This allows other parts of the system to query the status
        of pre-faults and make decisions based on their current states.

        Args:
            prefault_id (str): The identifier of the pre-fault whose state is to be checked.

        Returns:
            FaultState: The current state of the specified pre-fault. Possible states are defined
                        in the FaultState Enum (NOT_TESTED, SET, CLEARED).

        Raises:
            KeyError: If the specified prefault_id does not exist in the prefaults dictionary, indicating
                    an attempt to check an undefined pre-fault.
        """
        return self.prefaults[prefault_id].state

    def _set_fault(self, prefault_id: str, additional_info: Optional[dict]) -> None:
        """
        Sets the state of a fault based on a triggered pre-fault condition.

        This private method is called when a pre-fault condition is detected (set) and aims to aggregate
        such pre-fault conditions to determine if a corresponding fault state should also be set. It involves
        updating the fault's state to SET, triggering notifications, and executing any defined recovery actions
        specific to the pre-fault. The method aggregates several pre-faults to evaluate the overall state of
        a related fault, ensuring comprehensive fault management.

        This process is central to the fault management system's ability to respond to potential issues
        proactively, allowing for the mitigation of faults through early detection and response.

        Args:
            prefault_id (str): The identifier of the pre-fault that triggered this fault setting process.
            additional_info (dict | None, optional): Additional information or context relevant to the fault being set. This information may be used in notifications and recovery actions. Defaults to None.

        Note:
            This method should only be called internally within the fault management system, as part of handling
            pre-fault conditions. It assumes that a mapping exists between pre-faults and faults, allowing for
            appropriate fault state updates based on pre-fault triggers.
        """
        # Get sm name based on prefault_id
        sm_name: str = self.prefaults[prefault_id].sm_name

        # Collect all faults mapped from that prefault
        fault: Fault | None = self.found_mapped_fault(prefault_id, sm_name)
        if fault:
            # Set Fault
            fault.state = FaultState.SET
            self.hass.log(f"Fault {fault.name} was set", level="DEBUG")

            # Determinate additional info
            info_to_send: dict | None = self._determinate_info(
                "sensor.fault_" + fault.name, additional_info, FaultState.SET
            )

            # Prepare the attributes for the state update
            attributes: dict = info_to_send if info_to_send else {}

            # Clear HA entity
            self.hass.set_state(
                "sensor.fault_" + fault.name, state="Set", attributes=attributes
            )

            # Call notifications
            if self.notify_interface:
                self.notify_interface(
                    fault.name,
                    fault.notification_level,
                    FaultState.SET,
                    additional_info,
                )
            else:
                self.hass.log("No notification interface", level="WARNING")

            # Call recovery actions (specific for prefault)
            if self.recovery_interface:
                self.recovery_interface(self.prefaults[prefault_id])
            else:
                self.hass.log("No recovery interface", level="WARNING")

        else:
            pass  # Error logged in previous call

    def _determinate_info(
        self, entity_id: str, additional_info: Optional[dict], fault_state: FaultState
    ) -> Optional[dict]:
        """
        Determine the information to send based on the current state and attributes of the entity,
        merging or clearing it with additional information provided based on the fault state.

        Args:
            entity_id (str): The Home Assistant entity ID to check.
            additional_info (Optional[dict]): Additional details to merge with or clear from the entity's current attributes.
            fault_state (FaultState): The state of the fault, either Set or Cleared.

        Returns:
            Optional[dict]: The updated information as a dictionary, or None if there is no additional info.
        """
        # If no additional info is provided, return None
        if not additional_info:
            return None

        # Retrieve the current state object for the entity
        state = self.hass.get_state(entity_id, attribute="all")
        # If the entity does not exist, simply return the additional info if the fault is being set
        if not state:
            return additional_info if fault_state == FaultState.SET else {}

        # Get the current attributes of the entity; if none exist, initialize to an empty dict
        current_attributes = state.get("attributes", {})
        if fault_state == FaultState.SET:
            # Prepare the information to send by merging or updating current attributes with additional info
            info_to_send = current_attributes.copy()
            for key, value in additional_info.items():
                if key in current_attributes and current_attributes[key] not in [
                    None,
                    "None",
                    "",
                ]:
                    # If the current attribute exists and is not None, check if the value needs updating
                    current_value = current_attributes[key]
                    # If the current attribute is a comma-separated string, append new value if it's not already included
                    if isinstance(
                        current_value, str
                    ) and value not in current_value.split(", "):
                        current_value += ", " + value
                    info_to_send[key] = current_value
                else:
                    # If the current attribute is None or does not exist, set it to the new value
                    info_to_send[key] = value
            return info_to_send
        elif fault_state == FaultState.CLEARED:
            # Clear specified keys from the current attributes if they exist
            info_to_send = current_attributes.copy()
            for key in additional_info.keys():
                if key in info_to_send:
                    # Check if other values need to remain (if it was a list converted to string)
                    if ", " in info_to_send[key]:
                        # Remove only the specified value and leave others if any
                        new_values = [
                            val
                            for val in info_to_send[key].split(", ")
                            if val != additional_info[key]
                        ]
                        info_to_send[key] = ", ".join(new_values)
                    else:
                        # Completely remove the key if only one value was stored
                        del info_to_send[key]
            return info_to_send

        return additional_info

    def _clear_fault(self, prefault_id: str, additional_info: dict) -> None:
        """
        Clears the state of a fault based on the resolution of a triggering pre-fault condition.

        This private method is invoked when a pre-fault condition that previously contributed to setting a fault
        is resolved (cleared). It assesses the current state of related pre-faults to determine whether the associated
        fault's state can also be cleared. This involves updating the fault's state to CLEARED and triggering appropriate
        notifications. The method ensures that faults are accurately reflected and managed based on the current status
        of their contributing pre-fault conditions.

        Clearing a fault involves potentially complex logic to ensure that all contributing factors are considered,
        making this method a critical component of the system's ability to recover and return to normal operation after
        a fault condition has been addressed.

        Args:
            prefault_id (str): The identifier of the pre-fault whose resolution triggers the clearing of the fault.
            additional_info (dict | None, optional): Additional information or context relevant to the fault being cleared. This information may be used to inform notifications. Defaults to None.

        Note:
            As with `_set_fault`, this method is designed for internal use within the fault management system. It assumes
            the existence of a logical mapping between pre-faults and their corresponding faults, which allows the system
            to manage fault states dynamically based on the resolution of pre-fault conditions.
        """

        # Get sm name based on prefault_id
        sm_name: str = self.prefaults[prefault_id].sm_name

        # Collect all faults mapped from that prefault
        fault: Fault | None = self.found_mapped_fault(prefault_id, sm_name)

        if fault and not any(
            prefault.state == FaultState.SET
            for prefault in self.prefaults.values()
            if prefault.sm_name == sm_name
        ):  # If Fault was found and if other fault related prefaults are not raised
            # Clear Fault
            fault.state = FaultState.CLEARED
            self.hass.log(f"Fault {fault.name} was cleared", level="DEBUG")

            # Determinate additional info
            info_to_send = self._determinate_info(
                "sensor.fault_" + fault.name, additional_info, FaultState.SET
            )

            # Prepare the attributes for the state update
            attributes = info_to_send if info_to_send else {}

            # Clear HA entity
            self.hass.set_state(
                "sensor.fault_" + fault.name, state="Cleared", attributes=attributes
            )

            # Call notifications
            if self.notify_interface:
                self.notify_interface(
                    fault.name,
                    fault.notification_level,
                    FaultState.CLEARED,
                    additional_info,
                )
            else:
                self.hass.log("No notification interface", level="WARNING")
                
            # Call recovery actions (specific for prefault)
            if self.recovery_interface:
                self.recovery_interface(self.prefaults[prefault_id])
            else:
                self.hass.log("No recovery interface", level="WARNING")

    def check_fault(self, fault_id: str) -> FaultState:
        """
        Checks the current state of a specified fault.

        This method returns the current state of the fault identified by the given `fault_id`.
        The state indicates whether the fault is active (SET), has been resolved (CLEARED),
        or has not yet been tested (NOT_TESTED). This functionality allows other components
        of the system to query the status of faults and adjust their behavior accordingly.

        Args:
            fault_id (str): The identifier of the fault whose state is to be checked.

        Returns:
            FaultState: The current state of the specified fault, indicating whether it is
                        NOT_TESTED, SET, or CLEARED.

        Raises:
            KeyError: If the specified fault_id does not exist in the faults dictionary,
                    indicating an attempt to check an undefined fault.
        """
        return self.faults[fault_id].state

    def found_mapped_fault(self, prefault_id: str, sm_id: str) -> Optional[Fault]:
        """
        Finds the fault associated with a given pre-fault identifier.

        This private method searches through the registered faults to find the one that is
        mapped from the specified pre-fault. This mapping is crucial for the fault management
        system to correctly associate pre-fault conditions with their corresponding fault states.
        It ensures that faults are accurately updated based on the status of triggering pre-faults.

        Note that this method assumes a many-to-one mapping between pre-faults and faults. If multiple
        faults are found to be associated with a single pre-fault, this indicates a configuration or
        logical error within the fault management setup.

        Args:
            prefault_id (str): The identifier of the pre-fault for which the associated fault is sought.
            sm_id (str) : The identifier of the sm

        Returns:
            Optional[Fault]: The fault object associated with the specified pre-fault, if found. Returns
                            None if no associated fault is found or if multiple associated faults are detected,
                            indicating a configuration error.

        Note:
            This method is intended for internal use within the fault management system. It plays a critical
            role in linking pre-fault conditions to their corresponding faults, facilitating the automated
            management of fault states based on system observations and pre-fault activations.
        """

        # Collect all faults mapped from that prefault
        matching_objects: list[Fault] = [
            fault for fault in self.faults.values() if sm_id in fault.related_prefaults
        ]

        # Validate there's exactly one occurrence
        if len(matching_objects) == 1:
            return matching_objects[0]

        elif len(matching_objects) > 1:
            self.hass.log(
                f"Error: Multiple faults found associated with prefault_id '{prefault_id}', indicating a configuration error.",
                level="ERROR",
            )
        else:
            self.hass.log(
                f"Error: No faults associated with prefault_id '{prefault_id}'. This may indicate a configuration error.",
                level="ERROR",
            )

        return None
