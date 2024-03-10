from typing import Callable

class RecoveryManager:
    def __init__(self):
        """
        Initialize the Recovery Manager.
        """

    def recovery(self, recovery_action : Callable, additional_info):
        """
        Execute the recovery process for a given fault.

        :param fault: The Fault object containing recovery information.
        """  
        recovery_action(additional_info)