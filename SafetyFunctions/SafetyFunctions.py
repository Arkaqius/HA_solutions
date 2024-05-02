"""
This module integrates various safety functions into the Home Assistant environment, focusing on the management of safety-related components, fault conditions, and recovery processes. It defines the `SafetyFunctions` class, which serves as the main entry point for initializing and managing the safety mechanisms within Home Assistant.

Features and Components:
- **Safety Mechanisms**: Supports the implementation of domain-specific safety mechanisms, such as temperature monitoring through the `TemperatureComponent`.
- **Fault and PreFault Management**: Utilizes `FaultManager` to handle fault and pre-fault conditions, allowing for systematic detection, notification, and recovery from potential safety issues.
- **Notifications**: Leverages `NotificationManager` for sending alerts or messages in response to safety events or fault conditions.
- **Recovery Actions**: Incorporates `RecoveryManager` to define and execute recovery actions for mitigating detected fault conditions.
- **Configuration Parsing**: Employs configuration parsing (via `cfg_pr`) to initialize safety mechanisms, fault conditions, and recovery actions based on predefined settings.

Key Functionalities:
- **Initialization**: On initialization, the module sets up safety mechanisms, fault conditions, pre-fault conditions, and recovery managers according to configurations specified in Home Assistant's app configuration.
- **Safety Mechanism Registration**: Registers the `FaultManager` with each safety mechanism component, ensuring integrated fault and recovery management.
- **State Monitoring and Management**: Monitors the state of various components and updates Home Assistant's state machine with the health status of the safety app.

Usage:
The `SafetyFunctions` class is designed to be used as an AppDaemon app within Home Assistant. It requires configuration settings for prefaults, faults, notifications, and any domain-specific safety mechanisms to be provided in the AppDaemon app's YAML configuration file.

Example Configuration (YAML):
```yaml
SafetyFunctions:
  module: safety_functions_module
  class: SafetyFunctions
  prefaults: {...}
  faults: {...}
  notification: {...}
  
This module exemplifies a holistic approach to safety management within Home Assistant, 
offering a framework for the development and integration of comprehensive safety features.

Note:

- Ensure that all required configurations are provided and correctly formatted.
- The module is designed for extensibility, allowing for the integration of additional safety mechanisms as needed.

"""

import appdaemon.plugins.hass.hassapi as hass
from shared.safety_component import SafetyComponent
from shared.temperature_component import TemperatureComponent
from shared.fault_manager import FaultManager
from shared.notification_manager import NotificationManager
from shared.recovery_manager import RecoveryManager
from shared.types_common import Fault, PreFault, RecoveryAction
import shared.cfg_parser as cfg_pr

DEBUG = False

if DEBUG:
    from remote_pdb import RemotePdb

COMPONENT_DICT: dict[str, SafetyComponent] = {
    "TemperatureComponent": TemperatureComponent
}


class SafetyFunctions(hass.Hass):
    """
    Main class for managing safety functions in the Home Assistant environment.
    """

    def initialize(self) -> None:
        """
        Initialize the SafetyFunctions app and its components.
        This method sets up the temperature sensor component and initializes the health status.
        """
        # Disable all the no-member violations in this function
        # pylint: disable=attribute-defined-outside-init
        self.set_state("sensor.safety_app_health", state="init")
        if DEBUG:
            RemotePdb("172.30.33.4", 5050).set_trace()
        self.sm_modules: dict = {}
        self.prefaults: dict[str, PreFault] = {}
        self.faults: dict[str, Fault] = {}
        self.recovery_actions: dict[str, RecoveryAction] = {}

        # 10. Get and verify cfgs
        self.fault_dict = self.args["app_config"]["faults"]
        self.safety_components_cfg = self.args["user_config"]["safety_components"]
        self.notification_cfg = self.args["user_config"]["notification"]
        self.recovery_cfg = self.args["app_config"]["recovery_actions"]  

        # 20. Initialize SM modules and get prefaults and recovery data
        for component_name, component_cls in COMPONENT_DICT.items():
            if component_name in self.safety_components_cfg:
                # Instantiate the component with 'self' passed to its constructor
                component_instance = component_cls(  # type: ignore
                    self
                )  # Assuming the constructor expects a reference to `self`

                # Store the instance in a dictionary
                self.sm_modules[component_name] = component_instance

                # Get configuration for this component
                component_cfg = self.safety_components_cfg[component_name]

                # Get pre-faults from the component instance
                prefaults_data, recovery_data = component_instance.get_prefaults_data(
                    self.sm_modules, component_cfg
                )

                # Update the prefaults dictionary with new PreFaults
                self.prefaults.update(prefaults_data)
                self.recovery_actions.update(recovery_data)

        # 30. Get faults data
        self.faults = cfg_pr.get_faults(self.fault_dict)

        # 50. Initialize notification manager
        self.notify_man: NotificationManager = NotificationManager(
            self, self.notification_cfg
        )

        # 60. Initialize recovery manager
        self.reco_man: RecoveryManager = RecoveryManager(self, self.recovery_cfg, self.recovery_actions)

        # 40. Initialize fault manager
        self.fm: FaultManager = FaultManager(
            self,
            self.notify_man,
            self.reco_man,
            self.sm_modules,
            self.prefaults,
            self.faults,
        )

        # 70. Register fm to safety components
        for sm in self.sm_modules.values():
            sm.register_fm(self.fm)

        # 80. Register all prefaults
        self.register_entities(self.faults)

        # 90. Init safety mechanisms
        self.fm.init_safety_mechanisms()

        # 100. Enable safety mechanisms
        self.fm.enable_all_prefaults()

        # 110. Set the health status after initialization
        self.set_state("sensor.safety_app_health", state="good")
        self.log("Safety app started", level="DEBUG")

    def register_entities(self, faults: dict[str, Fault]) -> None:
        for name, data in faults.items():
            self.set_state(
                "sensor.fault_" + name,
                state="Not_tested",
                attributes={"friendly_name": name, "location": "None"},
            )
