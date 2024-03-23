from shared.fault_manager import FaultState


def test_faults_set_prefaults(mocked_hass_app):

    app_instance, _ , __= mocked_hass_app

    # 0. Check before Prefault and Fault
    assert (
        app_instance.fm.check_prefault("RiskyTemperatureOffice")
        == FaultState.NOT_TESTED
    )
    assert app_instance.fm.check_fault("RiskyTemperature") == FaultState.NOT_TESTED

    # 1. Set Prefault and Fault
    app_instance.fm.set_prefault(
        "RiskyTemperatureOffice", additional_info={"location": "office"}
    )
    assert app_instance.fm.check_prefault("RiskyTemperatureOffice") == FaultState.SET
    assert app_instance.fm.check_fault("RiskyTemperature") == FaultState.SET

    # 2 Heal Prefault and Fault
    app_instance.fm.clear_prefault(
        "RiskyTemperatureOffice", additional_info={"location": "office"}
    )
    assert (
        app_instance.fm.check_prefault("RiskyTemperatureOffice") == FaultState.CLEARED
    )
    assert app_instance.fm.check_fault("RiskyTemperature") == FaultState.CLEARED

    # 3 Set Prefault and Fault
    app_instance.fm.set_prefault(
        "RiskyTemperatureOffice", additional_info={"location": "office"}
    )
    assert app_instance.fm.check_prefault("RiskyTemperatureOffice") == FaultState.SET
    assert app_instance.fm.check_fault("RiskyTemperature") == FaultState.SET

    # 4 Set Prefault and Fault
    app_instance.fm.set_prefault(
        "RiskyTemperatureOffice", additional_info={"location": "office"}
    )
    assert app_instance.fm.check_prefault("RiskyTemperatureOffice") == FaultState.SET
    assert app_instance.fm.check_fault("RiskyTemperature") == FaultState.SET
    
def test_faults_set_2_prefault_heal_one(mocked_hass_app):
    
    app_instance, _, __= mocked_hass_app
    
    # 0. Check before Prefault and Fault
    assert (
        app_instance.fm.check_prefault("RiskyTemperatureOffice")
        == FaultState.NOT_TESTED
    )
    assert (
        app_instance.fm.check_prefault("RiskyTemperatureKitchen")
        == FaultState.NOT_TESTED
    )
    assert app_instance.fm.check_fault("RiskyTemperature") == FaultState.NOT_TESTED

    # 1. Set first Prefault
    app_instance.fm.set_prefault(
        "RiskyTemperatureOffice", additional_info={"location": "office"}
    )
    
    assert app_instance.fm.check_prefault("RiskyTemperatureOffice") == FaultState.SET
    assert app_instance.fm.check_prefault("RiskyTemperatureKitchen") == FaultState.NOT_TESTED
    assert app_instance.fm.check_fault("RiskyTemperature") == FaultState.SET
    
    # 2. Clear first Prefault
    app_instance.fm.clear_prefault(
        "RiskyTemperatureOffice", additional_info={"location": "office"}
    )
    
    assert app_instance.fm.check_prefault("RiskyTemperatureOffice") == FaultState.CLEARED
    assert app_instance.fm.check_prefault("RiskyTemperatureKitchen") == FaultState.NOT_TESTED
    assert app_instance.fm.check_fault("RiskyTemperature") == FaultState.CLEARED
    
    
    # 3. Set both Prefaults
    app_instance.fm.set_prefault(
        "RiskyTemperatureOffice", additional_info={"location": "office"}
    )
    app_instance.fm.set_prefault(
        "RiskyTemperatureKitchen", additional_info={"location": "office"}
    )
    
    assert app_instance.fm.check_prefault("RiskyTemperatureOffice") == FaultState.SET
    assert app_instance.fm.check_prefault("RiskyTemperatureKitchen") == FaultState.SET
    assert app_instance.fm.check_fault("RiskyTemperature") == FaultState.SET

    # 4. Clear one Prefault
    app_instance.fm.clear_prefault(
        "RiskyTemperatureOffice", additional_info={"location": "office"}
    )
    
    assert app_instance.fm.check_prefault("RiskyTemperatureOffice") == FaultState.CLEARED
    assert app_instance.fm.check_prefault("RiskyTemperatureKitchen") == FaultState.SET
    assert app_instance.fm.check_fault("RiskyTemperature") == FaultState.SET
    
    # 5. Clear second Prefault
    app_instance.fm.clear_prefault(
        "RiskyTemperatureKitchen", additional_info={"location": "office"}
    )
    
    assert app_instance.fm.check_prefault("RiskyTemperatureOffice") == FaultState.CLEARED
    assert app_instance.fm.check_prefault("RiskyTemperatureKitchen") == FaultState.CLEARED
    assert app_instance.fm.check_fault("RiskyTemperature") == FaultState.CLEARED
    
    
def test_faults_invalid_cfg_2_smc(mocked_hass_app_2_flts_1_sm):

    app_instance, _, mock_log_method = mocked_hass_app_2_flts_1_sm

    # 1. Set Prefault and Fault
    app_instance.fm.set_prefault(
        "RiskyTemperatureOffice", additional_info={"location": "office"}
    )
    mock_log_method.assert_called_with("Error: Multiple faults found associated with prefault_id 'RiskyTemperatureOffice', indicating a configuration error.", level='ERROR')
    
def test_faults_invalid_cfg_no_smc(mocked_hass_app_flt_0_sm):

    app_instance, _, mock_log_method = mocked_hass_app_flt_0_sm

    # 1. Set Prefault and Fault
    app_instance.fm.set_prefault(
        "RiskyTemperatureOffice", additional_info={"location": "office"}
    )
    mock_log_method.assert_called_with("Error: No faults associated with prefault_id 'RiskyTemperatureOffice'. This may indicate a configuration error.", level='ERROR')