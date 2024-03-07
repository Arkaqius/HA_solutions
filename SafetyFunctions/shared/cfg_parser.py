from shared.fault_manager import FaultManager, Fault, PreFault
from typing import Callable


def get_faults(faults_dict) -> dict[str, PreFault]:
    """
    Add all faults from config file, prefaults will be adde later.
    """
    ret_val: dict[str, Fault] = {}

    for fault_name, fault_data in faults_dict.items():
        ret_val[fault_name] = Fault(
            fault_name, fault_data["related_sms"], fault_data["priority"]
        )
    return ret_val


def get_prefaults(sm_modules: list, prefault_dict: dict) -> dict[str, PreFault]:
    """
    Load configuration from a YAML file and populate the prefaults and faults dictionaries.
    """
    ret_val: dict[str, PreFault] = {}
    # Initialize all prefaults
    print(prefault_dict)
    for prefault_name, prefault_data in prefault_dict.items():
        sm_name = prefault_data["safety_mechanism"]
        module = prefault_data["component_name"]
        recovery_func = prefault_data["recovery_actions"]
        rec_action_fun: Callable = getattr(sm_modules[module], recovery_func)
        parameters: dict = prefault_data["parameters"]

        ret_val[prefault_name] = PreFault(
            prefault_name, sm_name, sm_modules[module], parameters, rec_action_fun
        )
    return ret_val
