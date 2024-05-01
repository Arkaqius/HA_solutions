"""
Module: types_enums.py

This module defines enumeration types used throughout the Safety Functions application, 
particularly within the Home Assistant-based safety management system. These enums 
provide a standardized set of possible states for faults (FaultState) and safety mechanisms (SMState),
ensuring consistency and clarity in state management and logic flow across the application.

Enums:
- FaultState: Enumerates the possible states of faults and pre-faults, aiding in the 
  identification and management of safety system conditions.
- SMState: Defines the operational states of Safety Mechanisms (SMs), offering insight
  into the activity and readiness of these mechanisms.

Usage:
Import the necessary enums into your module to leverage these predefined states for
fault management and safety mechanism state tracking. This centralizes state definitions,
facilitating easier maintenance and updates.
"""
from enum import Enum
from typing import Callable, Any

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
    Defines the operational states of Safety Mechanisms (SMs) within the safety management system.

    This enumeration helps to clearly define and track the current status of each safety mechanism,
    facilitating status checks and transitions in response to system events or conditions.

    Attributes:
        ERROR: Represents a state where the safety mechanism has encountered an error.
        NON_INITIALIZED: Indicates that the safety mechanism has not been initialized yet.
        DISABLED: The safety mechanism is initialized but currently disabled, not actively monitoring or acting on safety conditions.
        ENABLED: The safety mechanism is fully operational and actively engaged in monitoring or controlling its designated safety parameters.
    """
    ERROR = 0
    NON_INITIALIZED = 1
    DISABLED = 2
    ENABLED = 3
    
    
class PreFault:
    """
    Represents a pre-fault condition within the system, potentially leading to a fault.

    Pre-faults are conditions identified as precursors to faults, allowing preemptive actions
    to avoid faults altogether or mitigate their effects.

    Attributes:
        name (str): The name of the pre-fault.
        sm_name (str): The name of the safety mechanism associated with this pre-fault.
        module (SafetyComponent): The module where the safety mechanism is defined.
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
        module: "SafetyComponent",  # type: ignore
        parameters: dict,
        recover_actions: Callable | None = None,
    ) -> None:
        self.name: str = name
        self.sm_name: str = sm_name
        self.module = module
        self.state: FaultState = FaultState.NOT_TESTED
        self.recover_actions: Callable | Any = recover_actions
        self.parameters: dict = parameters
        self.sm_state = SMState.NON_INITIALIZED


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

    def __init__(self, name: str, related_prefaults: list, notification_level: int):
        self.name: str = name
        self.state: FaultState = FaultState.NOT_TESTED
        self.related_prefaults = related_prefaults
        self.notification_level: int = notification_level
        
        
class RecoveryAction:
    """
    Represents a specific recovery action within the safety management system.

    Each instance of this class represents a discrete recovery action that can be invoked in response to a fault condition.
    The class encapsulates the basic information necessary to identify and describe a recovery action, making it
    easier to manage and invoke these actions within the system.

    Attributes:
        name (str): The name of the recovery action, used to identify and reference the action within the system.
    """
    def  __init__(self, name: str) -> None:
        """
        Initializes a new instance of the RecoveryAction with a specific name.

        This constructor sets the name of the recovery action, which is used to identify and manage the action within
        the safety management system. The name should be unique and descriptive enough to clearly indicate the action's purpose.

        Args:
            name (str): The name of the recovery action, providing a unique identifier for the action within the system.
        """
        self.name: str = name