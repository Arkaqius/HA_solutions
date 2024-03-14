"""
This module provides utilities for loading fault and pre-fault configurations from dictionaries, typically derived from YAML configuration files. 
It supports getting Fault and PreFault objects, which are essential components of the safety management system within a Home Assistant environment.
These utilities facilitate the dynamic setup of safety mechanisms based on external configurations.
"""

from typing import Callable, Any
from shared.fault_manager import Fault, PreFault


def get_faults(faults_dict: dict) -> dict[str, Fault]:
    """
    Parses a dictionary of fault configurations and initializes Fault objects for each.

    Each fault configuration must include 'related_sms' (related safety mechanisms) and
    a 'priority' level. The function creates a Fault object for each entry and collects them
    into a dictionary keyed by the fault name.

    Args:
        faults_dict: A dictionary with fault names as keys and dictionaries containing
                     'related_sms' and 'priority' as values.

    Returns:
        A dictionary mapping fault names to initialized Fault objects.
    ret_val: dict[str, Fault] = {}
    """
    ret_val: dict[str, Fault] = {}
    for fault_name, fault_data in faults_dict.items():
        ret_val[fault_name] = Fault(
            fault_name, fault_data["related_sms"], fault_data["priority"]
        )
    return ret_val


def get_prefaults(
    sm_modules: dict[str, Any], prefault_dict: dict
) -> dict[str, PreFault]:
    """
    Parses a dictionary of pre-fault configurations and initializes PreFault objects for each.

    This function requires access to loaded safety mechanism modules to bind recovery actions properly.
    Each pre-fault configuration must specify the 'safety_mechanism', 'component_name', 'recovery_actions',
    and 'parameters'. It initializes a PreFault object for each entry, associating it with the specified
    recovery function and parameters from the given module.

    Args:
        sm_modules: A dictionary mapping module names to loaded module objects, where recovery actions can be found.
        prefault_dict: A dictionary with pre-fault names as keys and their configurations as values.

    Returns:
        A dictionary mapping pre-fault names to initialized PreFault objects.
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
