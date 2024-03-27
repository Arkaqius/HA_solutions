from shared.fault_manager import FaultState
from .fixtures.state_mock import MockBehavior, mock_get_state


def test_temp_comp_smtc1(mocked_hass_app_get_state):
   app_instance, mock_hass, _ = mocked_hass_app_get_state

   # Preparations
   temperature_behavior = MockBehavior(
   'sensor.office_temperature', iter(["5", "6", "7", "8", "9"])
   )
   humidity_behavior = MockBehavior("sensor.office_humidity", iter(["45", "50"]))
   mock_behaviors = [temperature_behavior, humidity_behavior]

   # Manually set the side_effect of the mocked `get_state` to use our custom mock_get_state function
   app_instance.get_state.side_effect = lambda entity_id: mock_get_state(entity_id, mock_behaviors)

   
   app_instance.sm_modules["TemperatureComponent"].sm_tc_1(app_instance.sm_modules["TemperatureComponent"].safety_mechanisms['RiskyTemperatureOffice'])
   app_instance.sm_modules["TemperatureComponent"].sm_tc_1(app_instance.sm_modules["TemperatureComponent"].safety_mechanisms['RiskyTemperatureOffice'])
   app_instance.sm_modules["TemperatureComponent"].sm_tc_1(app_instance.sm_modules["TemperatureComponent"].safety_mechanisms['RiskyTemperatureOffice'])

   assert app_instance.fm.check_prefault("RiskyTemperatureOffice") == FaultState.SET
   assert app_instance.fm.check_fault("RiskyTemperature") == FaultState.SET