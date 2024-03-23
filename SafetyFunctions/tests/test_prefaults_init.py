from shared.fault_manager import SMState


def test_prefaults_init_RiskyTemperatureOffice(mocked_hass_app):
    """
    Test the initialization of the 'RiskyTemperatureOffice' prefault in the SafetyFunctions app.

    Ensures that the prefault:
    - Is named 'RiskyTemperatureOffice'.
    - Uses 'sm_wmc_1' as its safety mechanism.
    - Is associated with the 'WindowComponent' module.
    - Has correct parameters for the low temperature threshold and temperature sensor.
    - Uses the 'RiskyTemperatureRecovery' recovery action from the 'WindowComponent'.
    """
    app_instance, _, __ = mocked_hass_app

    assert (
        app_instance.prefaults["RiskyTemperatureOffice"].name
        == "RiskyTemperatureOffice"
    ), "Prefault 'RiskyTemperatureOffice' does not have the correct name."
    assert (
        app_instance.prefaults["RiskyTemperatureOffice"].sm_name == "sm_wmc_1"
    ), "'RiskyTemperatureOffice' does not use 'sm_wmc_1' as its safety mechanism."
    assert (
        app_instance.prefaults["RiskyTemperatureOffice"].module
        == app_instance.sm_modules["WindowComponent"]
    ), "'RiskyTemperatureOffice' is not correctly associated with the 'WindowComponent' module."
    assert app_instance.prefaults["RiskyTemperatureOffice"].parameters == {
        "CAL_LOW_TEMP_THRESHOLD": 28,
        "temperature_sensor": "sensor.office_temperature",
    }, "'RiskyTemperatureOffice' does not have the correct parameters."
    assert (
        app_instance.prefaults["RiskyTemperatureOffice"].recover_actions
        == app_instance.sm_modules["WindowComponent"].RiskyTemperatureRecovery
    ), "'RiskyTemperatureOffice' does not use the correct recovery action."

    assert app_instance.prefaults["RiskyTemperatureOffice"].sm_state == SMState.ENABLED


def test_prefaults_init_RiskyTemperatureOfficeForecast(mocked_hass_app):
    """
    Test the initialization of the 'RiskyTemperatureOfficeForeCast' prefault in the SafetyFunctions app.

    Ensures that the prefault:
    - Is named 'RiskyTemperatureOfficeForeCast'.
    - Uses 'sm_wmc_2' as its safety mechanism.
    - Is associated with the 'WindowComponent' module.
    - Has correct parameters for the low temperature threshold, forecast timespan, temperature sensor, and temperature sensor rate.
    - Uses the 'RiskyTemperatureRecovery' recovery action from the 'WindowComponent'.
    """
    app_instance, _, __ = mocked_hass_app

    # Call init explicit as it anusual here
    app_instance.initialize()

    assert (
        app_instance.prefaults["RiskyTemperatureOfficeForeCast"].name
        == "RiskyTemperatureOfficeForeCast"
    ), "Prefault 'RiskyTemperatureOfficeForeCast' does not have the correct name."
    assert (
        app_instance.prefaults["RiskyTemperatureOfficeForeCast"].sm_name == "sm_wmc_2"
    ), "'RiskyTemperatureOfficeForeCast' does not use 'sm_wmc_2' as its safety mechanism."
    assert (
        app_instance.prefaults["RiskyTemperatureOfficeForeCast"].module
        == app_instance.sm_modules["WindowComponent"]
    ), "'RiskyTemperatureOfficeForeCast' is not correctly associated with the 'WindowComponent' module."
    assert app_instance.prefaults["RiskyTemperatureOfficeForeCast"].parameters == {
        "CAL_LOW_TEMP_THRESHOLD": 28,
        "CAL_FORECAST_TIMESPAN": 60,
        "temperature_sensor": "sensor.office_temperature",
        "temperature_sensor_rate": "sensor.office_temperature_rate",
    }, "'RiskyTemperatureOfficeForeCast' does not have the correct parameters."
    assert (
        app_instance.prefaults["RiskyTemperatureOfficeForeCast"].recover_actions
        == app_instance.sm_modules["WindowComponent"].RiskyTemperatureRecovery
    ), "'RiskyTemperatureOfficeForeCast' does not use the correct recovery action."

    assert (
        app_instance.prefaults["RiskyTemperatureOfficeForeCast"].sm_state
        == SMState.ENABLED
    )


def test_enablePrefaults_during_init(mocked_hass_app):
    """
    Test that prefaults are enabled during the initialization of the SafetyFunctions app.

    This test verifies that:
    - The 'RiskyTemperatureOffice' prefault is transitioned to the ENABLED state as part of the initialization process.
    - The 'RiskyTemperatureOfficeForeCast' prefault is also transitioned to the ENABLED state during initialization.

    Ensuring prefaults are enabled during initialization is crucial for the application to start monitoring
    conditions that could lead to faults right away, aligning with the app's proactive safety management strategy.
    """
    app_instance, _, __ = mocked_hass_app

    # Verify 'RiskyTemperatureOffice' prefault is ENABLED after initialization
    assert (
        app_instance.fm.prefaults["RiskyTemperatureOffice"].sm_state == SMState.ENABLED
    ), "'RiskyTemperatureOffice' prefault should be in the ENABLED state after initialization."

    # Verify 'RiskyTemperatureOfficeForeCast' prefault is ENABLED after initialization
    assert (
        app_instance.fm.prefaults["RiskyTemperatureOfficeForeCast"].sm_state
        == SMState.ENABLED
    ), "'RiskyTemperatureOfficeForeCast' prefault should be in the ENABLED state after initialization."
