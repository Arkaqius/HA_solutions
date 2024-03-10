from enum import Enum
from typing import Callable, Optional
from shared.recovery_manager import RecoveryManager
from shared.notification_manager import NotificationManager


class FaultState(Enum):
    NOT_TESTED = 0
    SET = 1
    CLEARED = 2


class SMState(Enum):
    DISABLED = 0
    ENABLED = 1


class PreFault:
    def __init__(
        self,
        name: str,
        sm_name: str,
        module,
        parameters: dict,
        recover_actions: Callable | None = None,
    ):
        self.name: str = name
        self.sm_name: str = sm_name
        self.module = module
        self.state: FaultState = FaultState.NOT_TESTED
        self.recover_actions: Callable | None = recover_actions
        self.parameters: dict = parameters
        self.sm_state = SMState.DISABLED


class Fault:
    def __init__(self, name, related_prefaults: list, notification_level: int):
        self.name: str = name
        self.state: FaultState = FaultState.NOT_TESTED
        self.related_prefaults = related_prefaults
        self.notification_level: int = notification_level


class FaultManager:
    def __init__(
        self,
        notify_man,
        recovery_man: RecoveryManager,
        sm_modules: list,
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

    def enable_prefaults(self):
        for prefault_name, prefault_data in self.prefaults.items():
            init_fcn = getattr(prefault_data.module, "init_" + prefault_data.sm_name)
            init_fcn(prefault_name, prefault_data.parameters)

    def set_prefault(self, prefault_id, additional_info=None):
        """
        Set a pre-fault state.

        :param prefault_id: The identifier of the pre-fault.
        :param name: Name of the pre-fault.
        :param state: State of the pre-fault (True/False).
        :param additional_info: Additional information about the pre-fault.
        """
        # Update prefault registry
        self.prefaults[prefault_id].sm_state = FaultState.SET

        # Call Related Fault
        self._set_fault(prefault_id, additional_info)

    def clear_prefault(self, prefault_id, additional_info):
        """
        Clear a pre-fault state.

        :param prefault_id: The identifier of the pre-fault.
        """
        # Update prefault registry
        self.prefaults[prefault_id].sm_state = FaultState.CLEARED

        # Call Related Fault
        self._clear_fault(prefault_id, additional_info)

    def check_prefault(self, prefault_id):
        """
        Check the state of a pre-fault.

        :param prefault_id: The identifier of the pre-fault.
        :return: The state of the pre-fault (True/False).
        """
        return self.prefaults[prefault_id].state

    def _set_fault(self, prefault_id, additional_info):
        """
        Set a fault state. This typically involves aggregating several pre-faults.

        :param fault_id: The identifier of the fault.
        :param name: Name of the fault.
        :param state: State of the fault (True/False).
        :param related_prefaults: List of related pre-faults.
        :param additional_info: Additional information about the fault.
        """

        # Collect all faults mapped from that prefault
        fault = self._found_mapped_fault(prefault_id)
        # Set Fault
        fault.state = FaultState.SET

        # Call notifications
        self.notify_man.notify(fault.name, fault.notification_level, additional_info)

        # Call recovery actions (specific for prefault)
        self.recovery_man.recovery(
            self.prefaults[prefault_id].recover_actions, additional_info
        )

    def _clear_fault(self, prefault_id: str, additional_info):
        """
        Clear a fault state.

        :param fault_id: The identifier of the fault.
        """

        # Collect all faults mapped from that prefault
        fault = self._found_mapped_fault(prefault_id)

        if fault:  # If Fault was found
            # Set Fault
            fault.state = FaultState.CLEARED

            # Call notifications
            self.notify_man.notify(
                fault.name, fault.notification_level, additional_info
            )

    def check_fault(self, fault_id):
        """
        Check the state of a fault.

        :param fault_id: The identifier of the fault.
        :return: The state of the fault (True/False).
        """
        return self.faults[fault_id].state

    def _found_mapped_fault(self, prefault_id: str) -> Optional[Fault]:

        # Collect all faults mapped from that prefault
        matching_objects = [
            fault
            for fault in self.faults.values()
            if prefault_id in fault.related_prefaults
        ]

        # Validate there's exactly one occurrence
        if len(matching_objects) == 1:
            print("Found exactly one matching fault:", matching_objects[0])
            return matching_objects[0]

        print("Error: Found multiple objects with prefault_id =", prefault_id)
        return None
