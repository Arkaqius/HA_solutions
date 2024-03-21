"""
TODO
"""
from shared.safety_component import SafetyComponent, safety_mechanism_decorator
from shared.safety_mechanism import SafetyMechanism


class WindowComponent(SafetyComponent):
    """Component handling safety mechanisms for windows."""

    # Static class variables to keep debounce
    sm_wmc1_debounce = 0
    sm_wmc1_inhibit = False
    sm_wmc2_debounce = 0
    sm_wmc2_inhibit = False

    def __init__(self, hass_app):
        """
        Initialize the window component.

        :param hass_app: The Home Assistant application instance.
        """
        super().__init__(hass_app)

    def init_sm_wmc_1(self, name: str, parameters: dict):
        """Method to init safet mechanism 1"""
        print("parameters\n\n")
        print(parameters)
        safety_mechanisms = []
        is_param_ok = True

        try:
            temperature_sensor = parameters["temperature_sensor"]
            cold_thr = parameters["CAL_LOW_TEMP_THRESHOLD"]
        except KeyError as e:
            self.hass_app.log(f"Key not found in sm_cfg: {e}", level="ERROR")
            is_param_ok = False
        else:
            is_param_ok = self.validate_entities(
                {"temperature_sensor": temperature_sensor, "cold_thr": cold_thr},
                {"temperature_sensor": str, "cold_thr": float},
            )
        if is_param_ok:
            safety_mechanisms.append(
                SafetyMechanism(
                    self.hass_app,
                    self.sm_wmc_1,
                    name,
                    temperature_sensor=temperature_sensor,
                    cold_thr=cold_thr,
                )
            )
        else:
            self.hass_app.log(f"SM {name} was not created due error", level="ERROR")
        return safety_mechanisms

    def init_sm_wmc_2(self, name: str, parameters: dict):
        """Method to init safet mechanism 2"""
        safety_mechanisms = []
        is_param_ok = True
        # Iterate throught all safety mechanism instances
        try:
            temperature_sensor = parameters["temperature_sensor"]
            cold_thr = parameters["CAL_LOW_TEMP_THRESHOLD"]
            forecast_timespan = parameters["CAL_FORECAST_TIMESPAN"]
            temperature_sensor_rate = parameters["temperature_sensor_rate"]
        except KeyError as e:
            self.hass_app.log(f"Key not found in sm_cfg: {e}", level="ERROR")
            is_param_ok = False
        else:
            is_param_ok = self.validate_entities(
                {
                    "temperature_sensor": temperature_sensor,
                    "cold_thr": cold_thr,
                    "forecast_timespan": forecast_timespan,
                    "temperature_sensor_rate": temperature_sensor_rate,
                },
                {
                    "temperature_sensor": str,
                    "cold_thr": float,
                    "forecast_timespan": float,
                    "temperature_sensor_rate": str,
                },
            )
        if is_param_ok:
            safety_mechanisms.append(
                SafetyMechanism(
                    self.hass_app,
                    self.sm_wmc_2,
                    name,
                    temperature_sensor=temperature_sensor,
                    cold_thr=cold_thr,
                    forecast_timespan=forecast_timespan,
                    temperature_sensor_rate=temperature_sensor_rate,
                )
            )
        else:
            self.hass_app.log(f"SM {name} was not created due error", level="ERROR")
        return safety_mechanisms

    @safety_mechanism_decorator
    def sm_wmc_1(self, sm: SafetyMechanism, **kwargs):
        """
        Safety mechanism specific for window monitoring.

        :param kwargs: Keyword arguments containing 'window_sensors' and 'temperature_sensor'.
        """
        temperature: float = 0.0
        # 10. Get inputs
        try:
            temperature = float(
                self.hass_app.get_state(sm.sm_args["temperature_sensor"])
            )
        except ValueError as e:
            self.hass_app.log(f"Float conversion error: {e}", level="ERROR")

        # 30. Perform SM logic
        (WindowComponent.sm_wmc1_debounce, WindowComponent.sm_wmc1_inhibit) = (
            self.process_prefault(
                12,
                WindowComponent.sm_wmc1_debounce,
                temperature < sm.sm_args["cold_thr"],
                {'location' : 'office'}
            )
        )

        if WindowComponent.sm_wmc1_inhibit:
            self.hass_app.run_in(self.sm_wmc_1, 30, sm, inhib=True)

    @safety_mechanism_decorator
    def sm_wmc_2(self, sm: SafetyMechanism, **kwargs):
        """
        Safety mechanism specific for window monitoring.

        :param kwargs: Keyword arguments containing 'window_sensors' and 'temperature_sensor'.
        """
        temperature: float = 0.0
        # 10. Get inputs
        try:
            temperature = float(
                self.hass_app.get_state(sm.sm_args["temperature_sensor"])
            )
            temperature_rate = float(
                self.hass_app.get_state(sm.sm_args["temperature_sensor_rate"])
            )
        except ValueError as e:
            self.hass_app.log(f"Float conversion error: {e}", level="ERROR")

        # 30. Perform SM logic
        forecasted_temperature = (
            temperature + temperature_rate * sm.sm_args["forecast_timespan"]
        )

        # 30. Perform SM logic
        (WindowComponent.sm_wmc2_debounce, WindowComponent.sm_wmc2_inhibit) = (
            self.process_prefault(
                12,
                WindowComponent.sm_wmc2_debounce,
                forecasted_temperature < sm.sm_args["cold_thr"],
                {'location' : 'office'}
            )
        )

        if WindowComponent.sm_wmc2_inhibit:
            self.hass_app.run_in(self.sm_wmc_2, 30, sm)

    @staticmethod
    def RiskyTemperatureRecovery(self):
        print("RiskyTemperatureRecovery called!")
