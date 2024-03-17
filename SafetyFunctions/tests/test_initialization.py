from unittest.mock import patch, MagicMock
import pytest
from shared.window_component import WindowComponent
# Assuming SafetyFunctions is in the correct import path
from SafetyFunctions import SafetyFunctions

@pytest.mark.init
@pytest.mark.positive
def test_initialize_dicts_prefault(mocked_hass_app):
    """
    Tests the initialization of the `SafetyFunctions` application to verify that the 
    configuration dictionaries for prefaults, faults, and notification configurations
    are correctly populated according to the provided application configuration.

    This positive test case ensures that the application's safety mechanisms are correctly
    set up with the necessary configuration parameters upon initialization.
    """
    app_instance, _ = mocked_hass_app
   
    # Assert the 'prefaults' dictionary content
    prefault = app_instance.prefault_dict['RiskyTemperatureOffice']
    assert prefault['name'] == 'RiskyTemperatureOffice', "Prefault name is incorrect."
    assert prefault['safety_mechanism'] == 'sm_wmc_1', "Prefault safety mechanism is incorrect."
    assert prefault['parameters']['CAL_LOW_TEMP_THRESHOLD'] == 28.0, "Prefault temperature threshold is incorrect."
    
    # Assert the 'faults' dictionary content
    fault = app_instance.fault_dict['RiskyTemperature']
    assert fault['name'] == 'Unsafe temperature', "Fault name is incorrect."
    assert fault['priority'] == 2, "Fault priority is incorrect."
    assert fault['related_sms'][0] == 'sm_wmc_1', "Related safety mechanism is incorrect."
    
    # Assert the 'notification_cfg' dictionary content
    notification = app_instance.notification_cfg
    assert notification['light_entity'] == 'light.warning_light', "Notification light entity is incorrect."

def test_NotificationManager_init(mocked_hass_app):
    """
    Verifies that the NotificationManager within the `SafetyFunctions` application
    is initialized with the correct Home Assistant application instance and 
    notification configuration parameters.

    This test confirms the proper integration and setup of the NotificationManager,
    crucial for the app's notification functionality.
    """
    app_instance, _ = mocked_hass_app
      
    assert app_instance.notify_man.hass_app is not None, "NotificationManager's Hass app is not initialized."
    assert app_instance.notify_man.notification_config is app_instance.notification_cfg, "NotificationManager's config does not match the application's notification configuration."
    
def test_RecoveryManager_init(mocked_hass_app_recovery_man):
    """
    Ensures that the RecoveryManager is correctly instantiated during the
    initialization of the `SafetyFunctions` application.

    The RecoveryManager plays a vital role in managing the recovery processes
    for faults, and this test confirms its activation.
    """
    _, __, MockRecoveryManager = mocked_hass_app_recovery_man

    MockRecoveryManager.assert_called_once()

def test_window_component_initialization(mocked_hass_app_window_component):
    """
    Confirms the initialization and registration of the WindowComponent within
    the `SafetyFunctions` app's `sm_modules` dictionary.

    This test checks the correct instantiation and storage of the WindowComponent,
    ensuring it's ready for operation as part of the app's safety mechanisms.
    """
    app_instance, _, MockWindowComponent = mocked_hass_app_window_component

    app_instance.initialize()

    assert isinstance(app_instance.sm_modules["WindowComponent"], WindowComponent), \
        "sm_modules['WindowComponent'] is not an instance of WindowComponent."
       
def test_prefaults_init(mocked_hass_app):
    pass
