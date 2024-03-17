from unittest.mock import patch, MagicMock
import pytest
from SafetyFunctions import SafetyFunctions
from shared.window_component import WindowComponent


@pytest.fixture
def mocked_hass_app(app_config_valid):
    with patch("appdaemon.plugins.hass.hassapi.Hass") as MockHass:
        # Create a mock logger with a `get_child` method
        mock_logging = MagicMock()
        mock_logging.get_child = MagicMock(return_value=MagicMock())

        # Pass the mock logger to the constructor
        mock_hass = MockHass()
        mock_hass.logger = mock_logging

        # Now create an instance of your app, passing the mocked Hass as the hass argument
        # Make sure to provide the appropriate mocked or dummy arguments
        app_instance = SafetyFunctions(
            mock_hass,
            "dummy_namespace",
            mock_logging,
            app_config_valid,
            "mock_config",
            "dummy_app_config",
            "dummy_global_vars",
        )

        # Initialize the SafetyFunctions instance
        app_instance.initialize()

        yield app_instance, mock_hass


@pytest.fixture
def mocked_hass_app_recovery_man(app_config_valid):
    with patch("appdaemon.plugins.hass.hassapi.Hass") as MockHass, patch(
        "SafetyFunctions.RecoveryManager"
    ) as MockRecoveryManager:  # Mock RecoveryManager
        # Create a mock logger with a `get_child` method
        mock_logging = MagicMock()
        mock_logging.get_child = MagicMock(return_value=MagicMock())

        # Pass the mock logger to the constructor
        mock_hass = MockHass()
        mock_hass.logger = mock_logging
        mock_hass.args = app_config_valid  # Assuming app_config_valid is a fixture returning valid config

        # Mock other Hass methods used by your app as needed
        mock_hass.get_state = MagicMock(return_value="on")
        mock_hass.set_state = MagicMock()

        # Now create an instance of your app, passing the mocked Hass as the hass argument
        app_instance = SafetyFunctions(
            mock_hass,
            "dummy_namespace",
            mock_logging,
            mock_hass.args,
            "mock_config",
            "dummy_app_config",
            "dummy_global_vars",
        )

        # Initialize the SafetyFunctions instance
        app_instance.initialize()

        # Yield both the app instance and the mocked objects
        yield app_instance, mock_hass, MockRecoveryManager


@pytest.fixture
def mocked_hass_app_window_component(app_config_valid):
    with patch("appdaemon.plugins.hass.hassapi.Hass") as MockHass, patch(
        "shared.window_component.WindowComponent"
    ) as MockWindowComponent:
        # Setup MockHass and mock logger
        mock_hass = MockHass()
        mock_logging = MagicMock()
        mock_logging.get_child = MagicMock(return_value=MagicMock())
        mock_hass.logger = mock_logging
        mock_hass.args = app_config_valid

        # Setup MockWindowComponent
        MockWindowComponent.return_value = MagicMock(spec=WindowComponent)

        # Create an instance of SafetyFunctions
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
    app_instance, mock_hass = mocked_hass_app

    # A function to decide the return value based on the call arguments
    def call_service_side_effect(service, *args, **kwargs):
        if service == "light/turn_on":
            return {"result": "light turned on"}
        elif service == "notify/notify":
            return {"result": "notification sent"}
        # Add more conditions as needed
        return None

    # Assign the side effect to the call_service method
    mock_hass.call_service.side_effect = call_service_side_effect

    yield mock_hass.call_service
