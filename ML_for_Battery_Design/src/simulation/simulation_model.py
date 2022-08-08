from abc import ABC  # , abstractmethod


class SimulationModel(ABC):
    """Simulation model abstract class for hidden parameter sampling and simulation data generation

    Attributes:
        hidden_params (dict): boolean values for if each hidden parameter should be sampled or stay constant
        simulation_settings (dict): settings for generating simulation data
        sample_boundaries (dict): sampling boundaries for each hidden parameter
        default_param_values (dict): default values of hidden parameters, if not sampled
    """

    def __init__(
        self,
        hidden_params: dict,
        simulation_settings: dict,
        sample_boundaries: dict,
        default_param_values: dict,
    ) -> None:
        """Initializes parent :class:SimulationModel

        Args:
            hidden_params (dict): boolean values for if each hidden parameter should be sampled or stay constant
            simulation_settings (dict): settings for generating simulation data
            sample_boundaries (dict): sampling boundaries for each hidden parameter
            default_param_values (dict): default values of hidden parameters, if not sampled
        """
        self.hidden_params = hidden_params
        self.simulation_settings = simulation_settings
        self.sample_boundaries = sample_boundaries
        self.default_param_values = default_param_values

        # unpach simulation parameters
        self.dt0 = self.simulation_settings["dt0"]
        self.max_time_iter = self.simulation_settings["max_time_iter"]
        if "nr" in simulation_settings:
            self.nr = self.simulation_settings["nr"]
            self.is_pde = True
        else:
            self.is_pde = False
