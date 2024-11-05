# tests/test_temperature_component.py
# mypy: ignore-errors

from typing import Iterator, List
import pytest
from shared.types_common import FaultState, SMState
from unittest.mock import Mock
from .fixtures.hass_fixture import (
    mock_get_state,
    MockBehavior,
    update_mocked_get_state,
)  # Import utilities from conftest.py

@pytest.mark.parametrize(
    "test_size,temperature, expected_symptom_state, expected_fault_state, prefault_title, prefault_message",
    [
        (
            5,
            ["35", "36", "37", "8", "9"],
            FaultState.CLEARED,
            FaultState.CLEARED,
            None,
            None,
        ),
        (
            5,
            ["5", "6", "7", "8", "9"],
            FaultState.SET,
            FaultState.SET,
            "Hazard!",
            "RiskyTemperature\nlocation: Office\n",
        ),
        (
            10,
            ["5", "6", "7", "8", "9", "34", "34", "34", "34", "34"],
            FaultState.CLEARED,
            FaultState.CLEARED,
            "Hazard!",
            "RiskyTemperature\nlocation: Office\n\nStatus: Cleared",
        ),
    ],
)
def test_temp_comp_notification(
    mocked_hass_app_with_temp_component,
    test_size,
    temperature,
    expected_symptom_state,
    expected_fault_state,
    prefault_title,
    prefault_message,
):
    """
    Test Case: Verify symptom and fault states based on temperature input.

    Scenario:
        - Input: Temperature sequences with varying levels.
        - Expected Result: Symptom and fault states should match expected values based on temperature.
    """
    app_instance, _, __, ___, mock_behaviors_default = (
        mocked_hass_app_with_temp_component
    )

    test_mock_behaviours: List[MockBehavior[str, Iterator[str]]] = [
        MockBehavior("sensor.office_temperature", iter(temperature))
    ]
    mock_behaviors_default: List[MockBehavior] = update_mocked_get_state(
        mock_behaviors_default, test_mock_behaviours
    )

    app_instance.get_state.side_effect = lambda entity_id, **kwargs: mock_get_state(
        entity_id, mock_behaviors_default
    )
    app_instance.initialize()

    for _ in range(test_size):
        app_instance.sm_modules["TemperatureComponent"].sm_tc_1(
            app_instance.sm_modules["TemperatureComponent"].safety_mechanisms[
                "RiskyTemperatureOffice"
            ]
        )

    assert (
        app_instance.fm.check_symptom("RiskyTemperatureOffice")
        == expected_symptom_state
    )
    assert app_instance.fm.check_fault("RiskyTemperature") == expected_fault_state

    # Check notification
    if prefault_title:
        notify_call = [
            call
            for call in app_instance.call_service.call_args_list
            if "notify" in call.args[0]
        ]
        # Check last one
        assert notify_call[-1].kwargs["title"] == prefault_title
        assert notify_call[-1].kwargs["message"] == prefault_message