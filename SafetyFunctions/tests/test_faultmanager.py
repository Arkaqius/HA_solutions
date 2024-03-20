from shared.fault_manager import FaultState


def test_faults_set_prefaults(mocked_hass_app):

    app_instance, _ = mocked_hass_app

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
    
    app_instance, _ = mocked_hass_app
    
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