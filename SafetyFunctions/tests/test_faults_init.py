from unittest.mock import patch, MagicMock
import pytest
from shared.window_component import WindowComponent
from shared.fault_manager import FaultState

# Assuming SafetyFunctions is in the correct import path
from SafetyFunctions import SafetyFunctions

def test_faults_init_RiskyTemperature(mocked_hass_app):
    """
    Test the initialization of the 'RiskyTemperature' fault in the SafetyFunctions application.

    Verifies that the 'RiskyTemperature' fault:
    - Is correctly named 'RiskyTemperature'.
    - Is initialized with a state of 'NOT_TESTED', indicating it hasn't been triggered yet.
    - Is related to the correct prefault 'sm_wmc_1', which it depends on for activation.
    - Has a notification level set to '2', denoting its priority or severity.

    This test ensures that fault configurations are correctly set up during the application's
    initialization process, which is crucial for the fault management system to operate as intended.
    """
    app_instance, _, __= mocked_hass_app

    # Verify the fault's name is as expected
    assert app_instance.faults["RiskyTemperature"].name == "RiskyTemperature", \
        "'RiskyTemperature' fault does not have the correct name."

    # Verify the fault's initial state is NOT_TESTED
    assert app_instance.faults["RiskyTemperature"].state == FaultState.NOT_TESTED, \
        "'RiskyTemperature' fault should initially be in the 'NOT_TESTED' state."

    # Verify the fault is related to the correct prefault
    assert app_instance.faults["RiskyTemperature"].related_prefaults == ['sm_wmc_1'], \
        "'RiskyTemperature' fault is not correctly related to 'sm_wmc_1' prefault."

    # Verify the fault's notification level is set to 2
    assert app_instance.faults["RiskyTemperature"].notification_level == 2, \
        "'RiskyTemperature' fault does not have the correct notification level."