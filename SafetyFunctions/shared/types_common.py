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