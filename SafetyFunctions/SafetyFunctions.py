import appdaemon.plugins.hass.hassapi as hass
from shared.window_component import WindowComponent
from shared.fault_manager import FaultManager, Fault, PreFault
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
        # RemotePdb('172.30.33.4', 5050).set_trace()
        self.sm_modules: dict = {}
        self.prefaults: dict[str, PreFault] = {}
        self.faults: dict[str, PreFault] = {}

        # Get and verify cfgs
        prefault_dict = self.args["prefaults"]
        fault_dict = self.args["faults"]

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
            self.sm_modules, self.prefaults, self.faults
        )

        # Enable prefaults
        self.fm.enable_prefaults()

        # Set the health status after initialization
        self.set_state("sensor.safety_app_health", state="good")
        self.log("Safety app started")
