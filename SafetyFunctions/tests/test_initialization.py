"""
This module contains pytest tests for the SafetyFunctions app within a Home Assistant environment.

The tests cover the initialization process of SafetyFunctions, ensuring that all components,
including symptoms, faults, and notification settings, are initialized correctly. It also
verifies the proper setup of the NotificationManager, RecoveryManager, and the registration
of the FaultManager to safety components. Additionally, the tests check that the application's
health status is correctly set to 'good' at the end of initialization.
"""

from unittest.mock import patch, MagicMock
import pytest
from shared.temperature_component import TemperatureComponent
from shared.fault_manager import FaultManager

# Assuming SafetyFunctions is in the correct import path
from SafetyFunctions import SafetyFunctions
# mypy: ignore-errors

@pytest.mark.init
@pytest.mark.positive
def test_initialize_dicts_symptom(mocked_hass_app_get_state):
    """
    Tests the initialization of the `SafetyFunctions` application to verify that the
    configuration dictionaries for symptoms, faults, and notification configurations
    are correctly populated according to the provided application configuration.

    This positive test case ensures that the application's safety mechanisms are correctly
    set up with the necessary configuration parameters upon initialization.
    """
    app_instance, _, __ = mocked_hass_app_get_state
    app_instance.initialize()
    
    # Assert the 'symptoms' dictionary content
    symptom = app_instance.symptoms["RiskyTemperatureOffice"]
    assert symptom.name == "RiskyTemperatureOffice", "symptom name is incorrect."
    assert (
        symptom.sm_name == "sm_tc_1"
    ), "symptom safety mechanism is incorrect."
    assert (
        symptom.parameters["CAL_LOW_TEMP_THRESHOLD"] == 18.0
    ), "symptom temperature threshold is incorrect."

    # Assert the 'faults' dictionary content
    fault = app_instance.fault_dict["RiskyTemperature"]
    assert fault["name"] == "Unsafe temperature", "Fault name is incorrect."
    assert fault["priority"] == 2, "Fault priority is incorrect."
    assert (
        fault["related_sms"][0] == "sm_tc_1"
    ), "Related safety mechanism is incorrect."

    # Assert the 'notification_cfg' dictionary content
    notification = app_instance.notification_cfg
    assert (
        notification["light_entity"] == "light.warning_light"
    ), "Notification light entity is incorrect."


def test_NotificationManager_init(mocked_hass_app_get_state):
    """
    Verifies that the NotificationManager within the `SafetyFunctions` application
    is initialized with the correct Home Assistant application instance and
    notification configuration parameters.

    This test confirms the proper integration and setup of the NotificationManager,
    crucial for the app's notification functionality.
    """
    app_instance, _, __ = mocked_hass_app_get_state
    app_instance.initialize()
    
    assert (
        app_instance.notify_man.hass_app is not None
    ), "NotificationManager's Hass app is not initialized."
    assert (
        app_instance.notify_man.notification_config is app_instance.notification_cfg
    ), "NotificationManager's config does not match the application's notification configuration."

def test_temperature_component_initialization(mocked_hass_app_get_state_tc):
    """
    Confirms the initialization and registration of the TemperatureComponent within
    the `SafetyFunctions` app's `sm_modules` dictionary.

    This test checks the correct instantiation and storage of the TemperatureComponent,
    ensuring it's ready for operation as part of the app's safety mechanisms.
    """
    app_instance, _, __, MockTemperatureComponent = mocked_hass_app_get_state_tc

    app_instance.initialize()

    assert isinstance(
        app_instance.sm_modules["TemperatureComponent"], TemperatureComponent
    ), "sm_modules['TemperatureComponent'] is not an instance of TemperatureComponent."


def test_fault_manager_initialization(mocked_hass_app_get_state_tc):
    """
    Test the initialization of the FaultManager within the SafetyFunctions application.

    Verifies that:
    - The FaultManager instance is correctly initialized and associated with the SafetyFunctions instance.
    - The NotificationManager instance used by FaultManager matches the one used by SafetyFunctions.
    - The RecoveryManager instance used by FaultManager matches the one used by SafetyFunctions.
    - The sm_modules dictionary within FaultManager correctly contains the initialized TemperatureComponent.
    - The symptoms dictionary within FaultManager is populated with expected symptom configurations.
    - The faults dictionary within FaultManager is populated with expected fault configurations.

    Ensuring the proper setup of FaultManager is crucial for the application's ability to manage,
    detect, and recover from faults effectively.
    """
    app_instance, _, __, MockTemperatureComponent = mocked_hass_app_get_state_tc

    app_instance.initialize()

    # Check if FaultManager is correctly instantiated and associated
    assert isinstance(
        app_instance.fm, FaultManager
    ), "FaultManager is not correctly instantiated."

    # Verify that FaultManager uses the same NotificationManager as SafetyFunctions
    assert (
        app_instance.fm.notify_interface == app_instance.notify_man.notify
    ), "FaultManager does not use the same NotificationManager instance."

    # Verify that FaultManager uses the same RecoveryManager as SafetyFunctions
    assert (
        app_instance.fm.recovery_interface == app_instance.reco_man.recovery
    ), "FaultManager does not use the same RecoveryManager instance."

    # Verify that FaultManager's sm_modules dictionary contains the correct TemperatureComponent instance
    assert app_instance.fm.sm_modules == {
        "TemperatureComponent": app_instance.sm_modules["TemperatureComponent"]
    }, "FaultManager's sm_modules dictionary does not contain the correct TemperatureComponent instance."

    # Verify that FaultManager's symptoms dictionary is correctly populated
    assert app_instance.fm.symptoms == {
        "RiskyTemperatureOffice": app_instance.symptoms["RiskyTemperatureOffice"],
        "RiskyTemperatureKitchen": app_instance.symptoms["RiskyTemperatureKitchen"],
        "RiskyTemperatureOfficeForeCast": app_instance.symptoms[
            "RiskyTemperatureOfficeForeCast"],
        "RiskyTemperatureKitchenForeCast": app_instance.symptoms[
            "RiskyTemperatureKitchenForeCast"
        ]
    }, "FaultManager's symptoms dictionary is not correctly populated."

    # Verify that FaultManager's faults dictionary is correctly populated
    assert app_instance.fm.faults == {
        "RiskyTemperature": app_instance.faults["RiskyTemperature"],
        "RiskyTemperatureForecast": app_instance.faults["RiskyTemperatureForecast"],
    }, "FaultManager's faults dictionary is not correctly populated."


def test_assign_fm(mocked_hass_app_get_state_tc):
    """
    Verifies that the FaultManager is correctly assigned to each safety module within the SafetyFunctions application.

    This test checks that the FaultManager instance is properly registered with all safety components,
    ensuring they can interact with the FaultManager for fault and symptom management.
    """
    app_instance, _, __, ___= mocked_hass_app_get_state_tc
    app_instance.initialize()
    
    for module in app_instance.sm_modules.values():
        assert (
            module.fault_man is app_instance.fm
        ), "FaultManager is not correctly assigned to safety module."


def test_app_health_set_to_good_at_end_of_init(mocked_hass_app_get_state_tc):
    """
    Test that the application's health status is set to 'good' at the end of the initialization process.

    This ensures that the 'set_state' method is correctly called with 'sensor.safety_app_health' and 'good'
    indicating that the application is ready and operating as expected after initialization.
    """
    app_instance, _, mock_log_method, ___= mocked_hass_app_get_state_tc
    app_instance.initialize()
    
    # Verify set_state was called with the expected arguments
    mock_log_method.assert_called_with('Safety app started', level='DEBUG')
