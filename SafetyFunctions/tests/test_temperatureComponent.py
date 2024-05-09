from shared.types_common import FaultState
from .fixtures.hass_fixture import MockBehavior, mock_get_state
# mypy: ignore-errors

def test_temp_comp_smtc1_1(mocked_hass_app_get_state):
    app_instance, mock_hass, _ = mocked_hass_app_get_state

    # Preparations
    temperature_behavior = MockBehavior(
        "sensor.office_temperature", iter(["5", "6", "7", "8", "9","5", "6", "7", "8", "9","5", "6", "7", "8", "9","5", "6", "7", "8", "9"])
    )
    
    fault_behavior = MockBehavior(
        "sensor.fault_RiskyTemperature", iter([None, None, None, None, None])
    )
    humidity_behavior = MockBehavior("sensor.office_humidity", iter(["45", "50"]))
    mock_behaviors = [temperature_behavior, humidity_behavior, fault_behavior]

    # Manually set the side_effect of the mocked `get_state` to use our custom mock_get_state function
    app_instance.get_state.side_effect = lambda entity_id, **kwargs: mock_get_state(entity_id, mock_behaviors)

    app_instance.initialize()

    app_instance.sm_modules["TemperatureComponent"].sm_tc_1(
        app_instance.sm_modules["TemperatureComponent"].safety_mechanisms[
            "RiskyTemperatureOffice"
        ]
    )

    assert (
        app_instance.fm.check_prefault("RiskyTemperatureOffice")
        == FaultState.SET
    )


def test_temp_comp_smtc1_2(mocked_hass_app_get_state):
    app_instance, mock_hass, _ = mocked_hass_app_get_state

    app_instance.initialize()
    # Preparations
    temperature_behavior = MockBehavior(
        "sensor.office_temperature", iter(["35", "36", "37", "37","8", "9", "10", "10", "8", "9", "10", "10", "8", "9", "10", "10", "8", "9", "10", "10"])
    )
    humidity_behavior = MockBehavior("sensor.office_humidity", iter(["45", "50"]))
    mock_behaviors = [temperature_behavior, humidity_behavior]

    # Manually set the side_effect of the mocked `get_state` to use our custom mock_get_state function
    app_instance.get_state.side_effect = lambda entity_id, **kwargs: mock_get_state(entity_id, mock_behaviors)

    app_instance.sm_modules["TemperatureComponent"].sm_tc_1(
        app_instance.sm_modules["TemperatureComponent"].safety_mechanisms[
            "RiskyTemperatureOffice"
        ]
    )
    app_instance.sm_modules["TemperatureComponent"].sm_tc_1(
        app_instance.sm_modules["TemperatureComponent"].safety_mechanisms[
            "RiskyTemperatureOffice"
        ]
    )
    app_instance.sm_modules["TemperatureComponent"].sm_tc_1(
        app_instance.sm_modules["TemperatureComponent"].safety_mechanisms[
            "RiskyTemperatureOffice"
        ]
    )
    
    app_instance.sm_modules["TemperatureComponent"].sm_tc_1(
        app_instance.sm_modules["TemperatureComponent"].safety_mechanisms[
            "RiskyTemperatureOffice"
        ]
    )
    
    # Smc called 5 times with good temperature - CLEARED
    assert (
        app_instance.fm.check_prefault("RiskyTemperatureOffice") == FaultState.CLEARED
    )
    assert app_instance.fm.check_fault("RiskyTemperature") == FaultState.SET # Kitchen is still set

    app_instance.sm_modules["TemperatureComponent"].sm_tc_1(
        app_instance.sm_modules["TemperatureComponent"].safety_mechanisms[
            "RiskyTemperatureOffice"
        ]
    )
    app_instance.sm_modules["TemperatureComponent"].sm_tc_1(
        app_instance.sm_modules["TemperatureComponent"].safety_mechanisms[
            "RiskyTemperatureOffice"
        ]
    )

    app_instance.sm_modules["TemperatureComponent"].sm_tc_1(
        app_instance.sm_modules["TemperatureComponent"].safety_mechanisms[
            "RiskyTemperatureOffice"
        ]
    )

    # Smc called 2 times with bad temperature - still CLEARED
    assert (
        app_instance.fm.check_prefault("RiskyTemperatureOffice") == FaultState.CLEARED
    )
    assert app_instance.fm.check_fault("RiskyTemperature") == FaultState.SET

    app_instance.sm_modules["TemperatureComponent"].sm_tc_1(
        app_instance.sm_modules["TemperatureComponent"].safety_mechanisms[
            "RiskyTemperatureOffice"
        ]
    )

    # Smc called 4 times with bad temperature - SET
    assert app_instance.fm.check_prefault("RiskyTemperatureOffice") == FaultState.SET
    assert app_instance.fm.check_fault("RiskyTemperature") == FaultState.SET


def test_temp_comp_smtc2_1(mocked_hass_app_get_state):
    """
    Let's calculate a suitable temperature rate. Assume the current temperature is 27.0°C, and we want it to cross 28.0°C in 2 hours:
    Temperature Threshold: 18.0°C
    Current Temperature: 19.0°C
    Desired Increase in 2 Hours: 1.0°C (to reach just over the threshold) -> -1.5/120 = -0.0125 C/min
    Forecast Timespan: 2 hours (120 minutes)
    """

    app_instance, mock_hass, _ = mocked_hass_app_get_state

    app_instance.initialize()
    
    # Preparations
    temperature_behavior = MockBehavior(
        "sensor.office_temperature",
        iter(
            [
                "19",
                "19",
                "19",
                "18.9",
                "18.9",
                "19",
                "19",
                "19",
                "18.9",
                "18.9",
                "19",
                "19",
                "19",
                "18.9",
                "18.9",
            ]
        ),
    )
    temp_rate_behavior = MockBehavior(
        "sensor.office_temperature_rate",
        iter(
            [
                "-0.0125",
                "-0.0125",
                "-0.0125",
                "-0.0125",
                "-0.0125",
                "-0.0125",
                "-0.0125",
                "-0.0125",
                "-0.0125",
                "-0.0125",
                "-0.0125",
                "-0.0125",
                "-0.0125",
                "-0.0125",
                "-0.0125",
            ]
        ),
    )
    mock_behaviors = [temperature_behavior, temp_rate_behavior]

    # Manually set the side_effect of the mocked `get_state` to use our custom mock_get_state function
    app_instance.get_state.side_effect = lambda entity_id, **kwargs: mock_get_state(entity_id, mock_behaviors)

    app_instance.sm_modules["TemperatureComponent"].safety_mechanisms["RiskyTemperatureOfficeForeCast"].sm_args["diverative"] = -0.0125
    assert (
        app_instance.fm.check_prefault("RiskyTemperatureOfficeForeCast")
        == FaultState.SET
    )

    app_instance.sm_modules["TemperatureComponent"].sm_tc_2(
        app_instance.sm_modules["TemperatureComponent"].safety_mechanisms[
            "RiskyTemperatureOfficeForeCast"
        ]
    )

    app_instance.sm_modules["TemperatureComponent"].sm_tc_2(
        app_instance.sm_modules["TemperatureComponent"].safety_mechanisms[
            "RiskyTemperatureOfficeForeCast"
        ]
    )

    app_instance.sm_modules["TemperatureComponent"].sm_tc_2(
        app_instance.sm_modules["TemperatureComponent"].safety_mechanisms[
            "RiskyTemperatureOfficeForeCast"
        ]
    )

    app_instance.sm_modules["TemperatureComponent"].sm_tc_2(
        app_instance.sm_modules["TemperatureComponent"].safety_mechanisms[
            "RiskyTemperatureOfficeForeCast"
        ]
    )

    app_instance.sm_modules["TemperatureComponent"].sm_tc_2(
        app_instance.sm_modules["TemperatureComponent"].safety_mechanisms[
            "RiskyTemperatureOfficeForeCast"
        ]
    )

    app_instance.sm_modules["TemperatureComponent"].sm_tc_2(
        app_instance.sm_modules["TemperatureComponent"].safety_mechanisms[
            "RiskyTemperatureOfficeForeCast"
        ]
    )

    app_instance.sm_modules["TemperatureComponent"].sm_tc_2(
        app_instance.sm_modules["TemperatureComponent"].safety_mechanisms[
            "RiskyTemperatureOfficeForeCast"
        ]
    )

    app_instance.sm_modules["TemperatureComponent"].sm_tc_2(
        app_instance.sm_modules["TemperatureComponent"].safety_mechanisms[
            "RiskyTemperatureOfficeForeCast"
        ]
    )

    app_instance.sm_modules["TemperatureComponent"].sm_tc_2(
        app_instance.sm_modules["TemperatureComponent"].safety_mechanisms[
            "RiskyTemperatureOfficeForeCast"
        ]
    )

    app_instance.sm_modules["TemperatureComponent"].sm_tc_2(
        app_instance.sm_modules["TemperatureComponent"].safety_mechanisms[
            "RiskyTemperatureOfficeForeCast"
        ]
    )

    assert (
        app_instance.fm.check_prefault("RiskyTemperatureOfficeForeCast")
        == FaultState.SET
    )
