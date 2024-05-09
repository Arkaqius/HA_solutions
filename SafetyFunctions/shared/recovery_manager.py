"""
This module defines the RecoveryManager class, a central component of a safety management system designed to handle the recovery process from fault conditions. The RecoveryManager oversees executing recovery actions in response to detected faults, playing a pivotal role in maintaining the operational integrity and safety of the system.

Overview:
The RecoveryManager is built with flexibility in mind, enabling it to manage a wide array of fault conditions through customizable recovery actions. Each recovery action is encapsulated as a callable function, which can be dynamically invoked by the RecoveryManager along with relevant context or parameters necessary for addressing specific faults.

Key Features:
- **Dynamic Recovery Action Execution**: Allows for the invocation of any callable as a recovery action, offering the flexibility to implement a variety of recovery strategies tailored to specific fault scenarios.
- **Context-Aware Fault Mitigation**: Supports passing additional information to recovery actions, enabling context-aware processing and more effective fault mitigation strategies.
- **Simplified Fault Recovery Interface**: Provides a straightforward method (`recovery`) for triggering recovery actions, simplifying the integration of the RecoveryManager into larger safety management systems.

Usage:
The RecoveryManager is intended to be used within larger safety management or fault handling systems where specific recovery actions are defined for various types of faults. By encapsulating recovery logic within callable functions and associating them with particular fault conditions, system designers can create a comprehensive fault recovery framework capable of addressing a broad spectrum of operational anomalies.

Example:
```python
def cool_down_system(additional_info):
    # Logic to cool down an overheated system component
    print(f"Cooling down system with parameters: {additional_info}")

# Create a RecoveryManager instance
recovery_manager = RecoveryManager()

# Execute a recovery action for an overheated system
recovery_manager.recovery(cool_down_system, {'component': 'CPU', 'target_temp': 75})

This module's approach to fault recovery empowers developers to construct robust and adaptable safety mechanisms, enhancing the resilience and reliability of automated systems.
"""

from typing import NoReturn
import appdaemon.plugins.hass.hassapi as hass  # type: ignore
from shared.types_common import RecoveryAction, PreFault, SMState
from shared.common_entities import CommonEntities


class RecoveryManager:
    """
    Manages the recovery processes for faults within the safety management system.

    This class is responsible for executing recovery actions associated with faults. It acts upon
    the specified recovery actions by invoking callable functions designed to mitigate or resolve
    the conditions leading to the activation of faults. The RecoveryManager plays a critical role
    in the system's ability to respond to and recover from fault conditions, thereby maintaining
    operational integrity and safety.

    The RecoveryManager is designed to be flexible, allowing recovery actions to be defined as
    callable functions with associated additional information, facilitating customized recovery
    strategies for different fault scenarios.
    """

    def __init__(
        self,
        hass_app: hass.Hass,
        fm: 'FaultManager',
        recovery_actions: dict,
        common_entities: CommonEntities,
    ) -> None:
        """
        Initializes the RecoveryManager with the necessary application context and recovery configuration.

        The constructor sets up the RecoveryManager by assigning the Home Assistant application context and
        a dictionary that contains configuration details for various recovery actions. This configuration
        dictionary is expected to map fault identifiers or types to specific callable functions that
        represent the recovery actions for those faults.

        Args:
            hass_app (hass.Hass): The Home Assistant application context, providing access to system-wide
                functionality and enabling the RecoveryManager to interact with other components and entities
                within the Home Assistant environment.
            recovery_config (dict):

        This setup allows the RecoveryManager to dynamically execute the appropriate recovery actions
        based on the faults detected within the system, promoting a flexible and responsive fault management
        framework.
        """
        self.hass_app: hass.Hass = hass_app
        self.recovery_actions: dict[str, RecoveryAction] = recovery_actions
        self.common_entities: CommonEntities = common_entities
        self.fm: 'FaultManager' = fm

    def _isRecoveryConflict(self) -> NoReturn:
        raise NotImplementedError

    def _perform_recovery(self) -> NoReturn:
        raise NotImplementedError
    
    def _run_dry_test(self, entities_changes: dict[str, str] ) -> None:
        # Iterate all sms and check if any will result in fault
        
        for _, prefault_data in self.fm.get_all_prefault().items():
            if prefault_data.sm_state == SMState.ENABLED:
                # Force each sm to get state if possible
                sm_fcn = getattr(prefault_data.module, prefault_data.sm_name)
                sm_fcn(prefault_data.module.safety_mechanisms[prefault_data.name],entities_changes)
                
    def recovery(self, prefault: PreFault) -> None:
        """
        TODO
        """
        # 10. Check if rec actions exist
        if prefault.name in self.recovery_actions:
            # 40 Run recovery action to get potential changes
            entities_changes: dict[str, str] = self.recovery_actions[
                prefault.name
            ].rec_fun(
                self.hass_app,
                prefault,
                self.common_entities,
                **self.recovery_actions[prefault.name].params,
            )
            if entities_changes:
                # 20. Check if existing rec action can cause another faults
                self._run_dry_test(entities_changes)
                # 30. Check if existing rec action is not in conflicts with diffrent one
                if not self._isRecoveryConflict():
                    self._perform_recovery(entities_changes)
                else:
                    self.hass_app.log(
                        f"Recovery confict for {prefault.name}", level="DEBUG"
                    )
        else:
            self.hass_app.log(f"No recovery actions for {prefault.name}", level="DEBUG")
