import pytest


@pytest.fixture(scope="module")
def app_config_valid():
    return {
        "log_level": "DEBUG",
        "faults": {
            "RiskyTemperature": {
                "name": "Unsafe temperature",
                "priority": 2,
                "related_sms": ["sm_wmc_1"],
            },
            "RiskyTemperatureForecast": {
                "name": "Unsafe temperature forecast",
                "priority": 3,
                "related_sms": ["sm_wmc_2"],
            },
        },
        "notification": {
            "light_entity": "light.warning_light"},
        "prefaults": {
            "RiskyTemperatureOffice": {
                "name": "RiskyTemperatureOffice",
                "safety_mechanism": "sm_wmc_1",
                "parameters": {
                    "CAL_LOW_TEMP_THRESHOLD": 28.0,
                    "temperature_sensor": "sensor.office_temperature",
                },
                "component_name": "WindowComponent",
                "recovery_actions": "RiskyTemperatureRecovery",
            },
            "RiskyTemperatureKitchen": {
                "name": "RiskyTemperatureKitchen",
                "safety_mechanism": "sm_wmc_1",
                "parameters": {
                    "CAL_LOW_TEMP_THRESHOLD": 28.0,
                    "temperature_sensor": "sensor.kitchen_temperature",
                },
                "component_name": "WindowComponent",
                "recovery_actions": "RiskyTemperatureRecovery",
            },
            "RiskyTemperatureOfficeForeCast": {
                "name": "RiskyTemperatureOfficeForeCast",
                "safety_mechanism": "sm_wmc_2",
                "parameters": {
                    "CAL_LOW_TEMP_THRESHOLD": 28.0,
                    "CAL_FORECAST_TIMESPAN": 60.0,  # seconds
                    "temperature_sensor": "sensor.office_temperature",
                    "temperature_sensor_rate": "sensor.office_temperature_rate",  # sampling_rate = 1min
                },
                "component_name": "WindowComponent",
                "recovery_actions": "RiskyTemperatureRecovery",
            },
        },
    }
    
@pytest.fixture(scope="module")
def app_config_2_faults_to_single_prefault():
    return {
        "log_level": "DEBUG",
        "faults": {
            "RiskyTemperature": {
                "name": "Unsafe temperature",
                "priority": 2,
                "related_sms": ["sm_wmc_1"],
            },
            "RiskyTemperatureForecast": {
                "name": "Unsafe temperature forecast",
                "priority": 3,
                "related_sms": ["sm_wmc_1"],
            },
        },
        "notification": {
            "light_entity": "light.warning_light"},
        "prefaults": {
            "RiskyTemperatureOffice": {
                "name": "RiskyTemperatureOffice",
                "safety_mechanism": "sm_wmc_1",
                "parameters": {
                    "CAL_LOW_TEMP_THRESHOLD": 28.0,
                    "temperature_sensor": "sensor.office_temperature",
                },
                "component_name": "WindowComponent",
                "recovery_actions": "RiskyTemperatureRecovery",
            },
            "RiskyTemperatureKitchen": {
                "name": "RiskyTemperatureKitchen",
                "safety_mechanism": "sm_wmc_1",
                "parameters": {
                    "CAL_LOW_TEMP_THRESHOLD": 28.0,
                    "temperature_sensor": "sensor.kitchen_temperature",
                },
                "component_name": "WindowComponent",
                "recovery_actions": "RiskyTemperatureRecovery",
            },
            "RiskyTemperatureOfficeForeCast": {
                "name": "RiskyTemperatureOfficeForeCast",
                "safety_mechanism": "sm_wmc_2",
                "parameters": {
                    "CAL_LOW_TEMP_THRESHOLD": 28.0,
                    "CAL_FORECAST_TIMESPAN": 60.0,  # seconds
                    "temperature_sensor": "sensor.office_temperature",
                    "temperature_sensor_rate": "sensor.office_temperature_rate",  # sampling_rate = 1min
                },
                "component_name": "WindowComponent",
                "recovery_actions": "RiskyTemperatureRecovery",
            },
        },
    }
    
@pytest.fixture(scope="module")
def app_config_fault_withou_smc():
    return {
        "log_level": "DEBUG",
        "faults": {
            "RiskyTemperature": {
                "name": "Unsafe temperature",
                "priority": 2,
                "related_sms": ["sm_wmc_9999"],
            },
            "RiskyTemperatureForecast": {
                "name": "Unsafe temperature forecast",
                "priority": 3,
                "related_sms": ["sm_wmc_9999"],
            },
        },
        "notification": {
            "light_entity": "light.warning_light"},
        "prefaults": {
            "RiskyTemperatureOffice": {
                "name": "RiskyTemperatureOffice",
                "safety_mechanism": "sm_wmc_1",
                "parameters": {
                    "CAL_LOW_TEMP_THRESHOLD": 28.0,
                    "temperature_sensor": "sensor.office_temperature",
                },
                "component_name": "WindowComponent",
                "recovery_actions": "RiskyTemperatureRecovery",
            },
            "RiskyTemperatureKitchen": {
                "name": "RiskyTemperatureKitchen",
                "safety_mechanism": "sm_wmc_1",
                "parameters": {
                    "CAL_LOW_TEMP_THRESHOLD": 28.0,
                    "temperature_sensor": "sensor.kitchen_temperature",
                },
                "component_name": "WindowComponent",
                "recovery_actions": "RiskyTemperatureRecovery",
            },
            "RiskyTemperatureOfficeForeCast": {
                "name": "RiskyTemperatureOfficeForeCast",
                "safety_mechanism": "sm_wmc_2",
                "parameters": {
                    "CAL_LOW_TEMP_THRESHOLD": 28.0,
                    "CAL_FORECAST_TIMESPAN": 60.0,  # seconds
                    "temperature_sensor": "sensor.office_temperature",
                    "temperature_sensor_rate": "sensor.office_temperature_rate",  # sampling_rate = 1min
                },
                "component_name": "WindowComponent",
                "recovery_actions": "RiskyTemperatureRecovery",
            },
        },
    }