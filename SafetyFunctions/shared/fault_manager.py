"""
Fault Management Module for Home Assistant Safety System

This module defines the core components and logic necessary for managing faults and pre-faults within a Home Assistant-based safety system. 
It facilitates the detection, tracking, and resolution of fault conditions, integrating closely with safety mechanisms to proactively address potential issues before they escalate into faults.

Classes:
    FaultState (Enum): Enumerates the possible states of faults within the system.
    SMState (Enum): Enumerates the operational states of Safety Mechanisms (SMs).
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

from enum import Enum
from typing import Callable, Optional
from shared.recovery_manager import RecoveryManager
from shared.notification_manager import NotificationManager


class FaultState(Enum):
    """
    Represents the possible states of a fault and prefaults within the safety management system.

    Attributes:
        NOT_TESTED: Initial state, indicating the fault has not yet been tested.
        SET: Indicates that the fault condition has been detected.
        CLEARED: Indicates that the fault condition has been resolved.
    """

    NOT_TESTED = 0
    SET = 1
    CLEARED = 2


class SMState(Enum):
    """
    Represents the operational states of a Safety Mechanism (SM).

    Attributes:
        DISABLED: Indicates the SM is currently inactive or turned off.
        ENABLED: Indicates the SM is active and monitoring for conditions.
    """

    DISABLED = 0
    ENABLED = 1


class PreFault:
    """
    Represents a pre-fault condition within the system, potentially leading to a fault.

    Pre-faults are conditions identified as precursors to faults, allowing preemptive actions
    to avoid faults altogether or mitigate their effects.

    Attributes:
        name (str): The name of the pre-fault.
        sm_name (str): The name of the safety mechanism associated with this pre-fault.
        module: The module where the safety mechanism is defined.
        parameters (dict): Configuration parameters for the pre-fault.
        recover_actions (Callable | None): The recovery action to execute if this pre-fault is triggered.
        state (FaultState): The current state of the pre-fault.
        sm_state (SMState): The operational state of the associated safety mechanism.

    Args:
        name (str): The name identifier of the pre-fault.
        sm_name (str): The safety mechanism's name associated with this pre-fault.
        module: The module object where the safety mechanism's logic is implemented.
        parameters (dict): A dictionary of parameters relevant to the pre-fault condition.
        recover_actions (Callable | None, optional): A callable that executes recovery actions for this pre-fault. Defaults to None.
    """

    def __init__(
        self,
        name: str,
        sm_name: str,
        module,
        parameters: dict,
        recover_actions: Callable | None = None,
    ) -> None:
        self.name: str = name
        self.sm_name: str = sm_name
        self.module = module
        self.state: FaultState = FaultState.NOT_TESTED
        self.recover_actions: Callable | None = recover_actions
        self.parameters: dict = parameters
        self.sm_state = SMState.DISABLED


class Fault:
    """
    Represents a fault within the safety management system.

    A fault is a condition that has been identified as an error or failure state within
    the system, requiring notification and possibly recovery actions.

    Attributes:
        name (str): The name of the fault.
        state (FaultState): The current state of the fault.
        related_prefaults (list): A list of pre-faults related to this fault.
        notification_level (int): The severity level of the fault for notification purposes.

    Args:
        name (str): The name identifier of the fault.
        related_prefaults (list): List of names of safety mechanism that can trigger this fault.
        notification_level (int): The severity level assigned to this fault for notification purposes.
    """

    def __init__(self, name, related_prefaults: list, notification_level: int):
        self.name: str = name
        self.state: FaultState = FaultState.NOT_TESTED
        self.related_prefaults = related_prefaults
        self.notification_level: int = notification_level


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
        hass,
        notify_man,
        recovery_man: RecoveryManager,
        sm_modules: dict,
        prefault_dict: dict,
        fault_dict: dict,
    ):
        """
        Initialize the Fault Manager.

        :param config_path: Path to the YAML configuration file.
        """
        self.notify_man: NotificationManager = notify_man
        self.recovery_man: RecoveryManager = recovery_man
        self.faults: dict[str, Fault] = fault_dict
        self.prefaults: dict[str, PreFault] = prefault_dict
        self.sm_modules = sm_modules
        self.hass = hass

    def enable_prefaults(self):
        """
        Enables all pre-faults by initializing them with their respective safety mechanisms.

        This method iterates through all registered pre-faults, retrieves the initialization function
        for each pre-fault's associated safety mechanism, and calls this function with the pre-fault's
        name and parameters. This is typically used to set up and activate monitoring for conditions
        that could lead to faults, ensuring that the safety mechanisms are ready to detect and
        respond to potential issues.

        Each pre-fault's associated module must contain an initialization function named after
        the pattern 'init_{sm_name}', where {sm_name} is the safety mechanism's name associated
        with the pre-fault. This function is expected to configure or activate the safety mechanism
        as necessary.

        Raises:
            AttributeError: If the initialization function for a pre-fault's safety mechanism is not found.
        """
        for prefault_name, prefault_data in self.prefaults.items():
            init_fcn = getattr(prefault_data.module, "init_" + prefault_data.sm_name)
            result: bool = init_fcn(prefault_name, prefault_data.parameters)
            if result:
                prefault_data.sm_state = SMState.ENABLED

    def set_prefault(self, prefault_id, additional_info=None):
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

    def clear_prefault(self, prefault_id, additional_info):
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

    def check_prefault(self, prefault_id) -> FaultState:
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

    def _set_fault(self, prefault_id: str, additional_info: Optional[dict]):
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
        sm_name = self.prefaults[prefault_id].sm_name

        # Collect all faults mapped from that prefault
        fault = self._found_mapped_fault(prefault_id, sm_name)
        if fault:
            # Set Fault
            fault.state = FaultState.SET
            
            # Set HA entity
            self.hass.set_state('sensor.fault_'+ fault.name, state="Set")

            # Call notifications
            self.notify_man.notify(
                fault.name, fault.notification_level, additional_info
            )

            # Call recovery actions (specific for prefault)
            if self.prefaults[prefault_id].recover_actions:
                self.recovery_man.recovery(
                    self.prefaults[prefault_id].recover_actions, additional_info
                )
        else:
            pass  # Error logged in previous call

    def _clear_fault(self, prefault_id: str, additional_info):
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
        sm_name = self.prefaults[prefault_id].sm_name

        # Collect all faults mapped from that prefault
        fault = self._found_mapped_fault(prefault_id, sm_name)

        if fault and not any(
            prefault.state == FaultState.SET
            for prefault in self.prefaults.values()
            if prefault.sm_name == sm_name
        ):  # If Fault was found and if other fault related prefaults are not raised
            # Clear Fault
            fault.state = FaultState.CLEARED
            
            # Clear HA entity
            self.hass.set_state('sensor.fault_'+ fault.name, state="Cleared")

            # Call notifications
            self.notify_man.notify(
                fault.name, fault.notification_level, additional_info
            )

    def check_fault(self, fault_id):
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

    def _found_mapped_fault(self, prefault_id: str, sm_id: str) -> Optional[Fault]:
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
        matching_objects = [
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
