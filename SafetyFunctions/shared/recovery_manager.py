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

import appdaemon.plugins.hass.hassapi as hass  # type: ignore
from shared.types_common import Fault
from shared.types_common import RecoveryAction, PreFault, SMState
from shared.common_entities import CommonEntities
from shared.fault_manager import FaultManager
from shared.notification_manager import NotificationManager


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
        fm: FaultManager,
        recovery_actions: dict,
        common_entities: CommonEntities,
        nm: NotificationManager,
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
        self.fm: FaultManager = fm
        self.nm: NotificationManager = nm

    def _isRecoveryConflict(self, prefault: PreFault) -> bool:
        matching_actions: list[str] = self._get_matching_actions(prefault)

        if not matching_actions:
            rec_fault: Fault | None = self.fm.found_mapped_fault(
                prefault.name, prefault.sm_name
            )
            if rec_fault:
                rec_fault_prio: int = rec_fault.priority
                return self._check_conflict_with_matching_actions(
                    matching_actions, rec_fault_prio, prefault
                )

        return False

    def _get_matching_actions(self, prefault: PreFault) -> list[str]:
        return [
            name
            for name, action in self.recovery_actions.items()
            if action.name in self.recovery_actions[prefault.name].name
        ]

    def _check_conflict_with_matching_actions(
        self, matching_actions: list[str], rec_fault_prio: int, prefault: PreFault
    ) -> bool:
        for found_prefault_name in matching_actions:
            found_prefault: PreFault = self.fm.prefaults[found_prefault_name]
            if found_prefault:
                found_fault: Fault | None = self.fm.found_mapped_fault(
                    prefault.name, prefault.sm_name
                )
                if found_fault and found_fault.priority > rec_fault_prio:
                    return True
        return False

    def _perform_recovery(
        self, prefault: PreFault, notifications: list, entities_changes: dict[str, str]
    ) -> None:
        # Perform notify
        for notification in notifications:
            fault: Fault | None = self.fm.found_mapped_fault(
                prefault.name, prefault.sm_name
            )
            if fault:
                self.nm._add_recovery_action(notification, fault.name)
        # Set recovery entity
        rec: RecoveryAction | None = self._find_recovery(prefault.name)
        if rec:
            self._set_rec_entity(rec)
            # Set entitity actions as recovery
            for entity, value in entities_changes.items():
                try:
                    self.hass_app.set_state(entity, value)
                except Exception as err:
                    self.hass_app.log(
                        f"Exception during setting {entity} to {value} value. {err}",
                        level="ERROR",
                    )
        else:
            self.hass_app.log(
                f"Recovery action for {prefault.name} was not found!", level="WARNING"
            )

    def _find_recovery(self, prefault_name: str) -> RecoveryAction | None:
        for name, rec in self.recovery_actions.items():
            if name == prefault_name:
                return rec
        return None

    def _set_rec_entity(self, recovery: RecoveryAction) -> None:
        sensor_name: str = f"sensor.{recovery.name}"
        sensor_value: str = str(recovery.current_status.name)
        self.hass_app.set_state(sensor_name, sensor_value)

    def _run_dry_test(
        self, prefaul_name: str, entities_changes: dict[str, str]
    ) -> bool:
        # Iterate all sms and check if any will result in fault

        for _, prefault_data in self.fm.get_all_prefault().items():
            if prefault_data.sm_state == SMState.ENABLED:
                # Force each sm to get state if possible
                sm_fcn = getattr(prefault_data.module, prefault_data.sm_name)
                isFaultTrigged = sm_fcn(
                    prefault_data.module.safety_mechanisms[prefault_data.name],
                    entities_changes,
                )
                if isFaultTrigged and prefault_data.sm_name is not prefaul_name:
                    return True
        return False

    def recovery(self, prefault: PreFault) -> None:
        """
        TODO
        """
        # 10. Check if rec actions exist
        if prefault.name in self.recovery_actions:
            # 40 Run recovery action to get potential changes
            entities_changes, notifications = self.recovery_actions[
                prefault.name
            ].rec_fun(
                self.hass_app,
                prefault,
                self.common_entities,
                **self.recovery_actions[prefault.name].params,
            )
            if entities_changes:
                # 20. Check if existing rec action can cause another faults
                if not self._run_dry_test(prefault.name, entities_changes):
                    # 30. Check if existing rec action is not in conflicts with diffrent one
                    if not self._isRecoveryConflict(prefault):
                        self._perform_recovery(
                            prefault, notifications, entities_changes
                        )
                    else:
                        self.hass_app.log(
                            f"Recovery confict for {prefault.name}", level="DEBUG"
                        )
                else:
                    self.hass_app.log(
                        "Recovery will raise another fault.", level="DEBUG"
                    )
        else:
            self.hass_app.log(f"No recovery actions for {prefault.name}", level="DEBUG")
