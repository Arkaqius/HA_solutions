"""
This module defines pytest fixtures for testing the SafetyFunctions app within a Home Assistant environment.

Fixtures include mocked instances of the Hass class from appdaemon, RecoveryManager, WindowComponent,
and service calls, allowing for isolated testing of app functionality without dependencies on the actual
Home Assistant environment.
"""

from unittest.mock import patch, MagicMock
import pytest
from SafetyFunctions import SafetyFunctions
from shared.window_component import WindowComponent


@pytest.fixture
def mocked_hass_app(app_config_valid):
    """
    Provides a mocked instance of the SafetyFunctions app with a mocked Hass class.

    This fixture is used for general testing of the app's initialization and functionality
    without requiring a live Home Assistant environment.
    """
    with patch("appdaemon.plugins.hass.hassapi.Hass") as MockHass:
        mock_logging = MagicMock()
        mock_logging.get_child.return_value = MagicMock()
        mock_hass = MockHass()
        mock_hass.logger = mock_logging

        app_instance = SafetyFunctions(
            mock_hass,
            "dummy_namespace",
            mock_logging,
            app_config_valid,
            "mock_config",
            "dummy_app_config",
            "dummy_global_vars",
        )
        app_instance.initialize()

        yield app_instance, mock_hass


@pytest.fixture
def mocked_hass_app_recovery_man(app_config_valid):
    """
    Provides a mocked instance of the SafetyFunctions app with a mocked Hass class
    and RecoveryManager, allowing for testing of recovery-related functionality.
    """
    with patch("appdaemon.plugins.hass.hassapi.Hass") as MockHass, patch(
        "SafetyFunctions.RecoveryManager"
    ) as MockRecoveryManager:
        mock_logging = MagicMock()
        mock_logging.get_child.return_value = MagicMock()
        mock_hass = MockHass()
        mock_hass.logger = mock_logging
        mock_hass.args = app_config_valid

        mock_hass.get_state = MagicMock(return_value="on")
        mock_hass.set_state = MagicMock()

        app_instance = SafetyFunctions(
            mock_hass,
            "dummy_namespace",
            mock_logging,
            mock_hass.args,
            "mock_config",
            "dummy_app_config",
            "dummy_global_vars",
        )
        app_instance.initialize()

        yield app_instance, mock_hass, MockRecoveryManager


@pytest.fixture
def mocked_hass_app_window_component(app_config_valid):
    """
    Provides a mocked instance of the SafetyFunctions app with a mocked Hass class
    and WindowComponent, facilitating testing of window-related functionality.
    """
    with patch("appdaemon.plugins.hass.hassapi.Hass") as MockHass, patch(
        "shared.window_component.WindowComponent"
    ) as MockWindowComponent:
        mock_logging = MagicMock()
        mock_logging.get_child.return_value = MagicMock()
        mock_hass = MockHass()
        mock_hass.logger = mock_logging
        mock_hass.args = app_config_valid

        MockWindowComponent.return_value = MagicMock(spec=WindowComponent)

        app_instance = SafetyFunctions(
            mock_hass,
            "dummy_namespace",
            mock_logging,
            mock_hass.args,
            "mock_config",
            "dummy_app_config",
            "dummy_global_vars",
        )
        yield app_instance, mock_hass, MockWindowComponent


@pytest.fixture
def mocked_call_service(mocked_hass_app):
    """
    Modifies the mocked Hass instance to include a side_effect for the call_service method,
    simulating different service call outcomes based on input arguments.
    """
    app_instance, mock_hass = mocked_hass_app

    def call_service_side_effect(service, *args, **kwargs):
        # Define outcomes based on the called service
        if service == "light/turn_on":
            return {"result": "light turned on"}
        elif service == "notify/notify":
            return {"result": "notification sent"}
        return None

    mock_hass.call_service.side_effect = call_service_side_effect

    yield mock_hass.call_service


@pytest.fixture
def mocked_hass_app_with_state_check(app_config_valid):
    """
    Provides a mocked instance of the SafetyFunctions app with a mocked Hass class,
    specifically for testing state changes, such as setting the app's health status.
    """
    with patch("appdaemon.plugins.hass.hassapi.Hass") as MockHass:
        mock_logging = MagicMock()
        mock_logging.get_child.return_value = MagicMock()
        mock_hass = MockHass()
        mock_hass.logger = mock_logging
        mock_hass.args = app_config_valid

        mock_hass.set_state = MagicMock()

        app_instance = SafetyFunctions(
            mock_hass,
            "dummy_namespace",
            mock_logging,
            mock_hass.args,
            "mock_config",
            "dummy_app_config",
            "dummy_global_vars",
        )
        yield app_instance, mock_hass

@pytest.fixture
def mocked_hass_app_fm_mocks(app_config_valid):
    """
    Provides a mocked instance of the SafetyFunctions app with a mocked Hass class.

    This fixture is used for general testing of the app's initialization and functionality
    without requiring a live Home Assistant environment.
    """
    with patch("appdaemon.plugins.hass.hassapi.Hass") as MockHass:
        mock_logging = MagicMock()
        mock_logging.get_child.return_value = MagicMock()
        mock_hass = MockHass()
        mock_hass.logger = mock_logging

        app_instance = SafetyFunctions(
            mock_hass,
            "dummy_namespace",
            mock_logging,
            app_config_valid,
            "mock_config",
            "dummy_app_config",
            "dummy_global_vars",
        )
        app_instance.initialize()

        yield app_instance, mock_hass