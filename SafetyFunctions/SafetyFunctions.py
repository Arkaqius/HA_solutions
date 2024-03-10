import appdaemon.plugins.hass.hassapi as hass
from shared.window_component import WindowComponent
from shared.fault_manager import FaultManager, Fault, PreFault
from shared.notification_manager import NotificationManager
from shared.recovery_manager import RecoveryManager
import shared.cfg_parser as cfg_pr
from remote_pdb import RemotePdb


class SafetyFunctions(hass.Hass):
    """
    Main class for managing safety functions in the Home Assistant environment.
    """

    def initialize(self):
        """
        Initialize the SafetyFunctions app and its components.
        This method sets up the window sensor component and initializes the health status.
        """
        # Disable all the no-member violations in this function
        # pylint: disable=attribute-defined-outside-init
        # RemotePdb('172.30.33.4', 5050).set_trace()
        self.sm_modules: dict = {}
        self.prefaults: dict[str, PreFault] = {}
        self.faults: dict[str, Fault] = {}

        # Get and verify cfgs
        prefault_dict = self.args["prefaults"]
        fault_dict = self.args["faults"]
        notification_cfg = self.args["notification"]
        
        # Initialize notification manager
        self.notify_man : NotificationManager = NotificationManager(self,notification_cfg)
        
        # Initialize recovery manager
        self.reco_man : RecoveryManager = RecoveryManager()
        
        # Initalize SM modules
        self.sm_modules["WindowComponent"] = WindowComponent(self)

        # Initialize prefaults
        self.prefaults: dict[str, PreFault] = cfg_pr.get_prefaults(
            self.sm_modules, prefault_dict
        )

        # Initialize faults
        self.faults: dict[str, PreFault] = cfg_pr.get_faults(fault_dict)

        # Initialize fault manager
        self.fm: FaultManager = FaultManager(
            self.notify_man,
            self.reco_man,
            self.sm_modules, self.prefaults, self.faults
        )

        # Register fm to safety components
        for sm in self.sm_modules.values():
            sm.register_fm(self.fm)
                
        # Enable prefaults
        self.fm.enable_prefaults()

        # Set the health status after initialization
        self.set_state("sensor.safety_app_health", state="good")
        self.log("Safety app started")
