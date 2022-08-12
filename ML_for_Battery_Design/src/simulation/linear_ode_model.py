import os
from typing import Tuple, Type

import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from ML_for_Battery_Design.src.simulation.simulation_model import SimulationModel


class LinearODEsystem(SimulationModel):
    """Simulation model represented by a system of two linear ODEs

        du_dt = a * u + b * v
        dv_dt = c * u + d * v

    Attributes:
        hidden_params (dict): boolean values for if each hidden parameter should be sampled or stay constant
        simulation_settings (dict): settings for generating simulation data
        sample_boundaries (dict): sampling boundaries for each hidden parameter
        default_param_values (dict): default values of hidden parameters, if not sampled
        dt0 (float): time step size for discretization in time direction
        max_time_iter (int): number of iterations after which the simulation stops
        nr (int): number of discretization points in space dimension (only for PDE)
        reject_sampling (bool): If True, rejection sampling will be performed
        is_pde (bool): if the simulation model is described by PDEs or ODEs
        t (npt.NDArray[Any]): time points at which the solutions should be evaluated
        hidden_param_names (list): list of hidden parameter names
        default_param_kwargs (dict): not-sampled parameters default values as keyword arguments
        num_features (int): number of features in simulation data per time point
        prior (bayesflow.Prior): prior sample generator wrapped in bayesflow Prior object
        simulator (bayesflow.Simulator): simulation data generator wrapped in bayesflow Simulator object
        generative_model (bayesflow.GenerativeModel): generator for both prior samples and simulation data wrapped in bayesflow GenerativeModel object
        prior_means (npt.NDArray[Any]): estimated mean of joint prior
        prior_stds (npt.NDArray[Any]): estimated standard deviation of joint prior
    """

    def __init__(
        self,
        hidden_params: dict,
        simulation_settings: dict,
        sample_boundaries: dict,
        default_param_values: dict,
        plot_settings: dict,
    ) -> None:
        """Initializes a :class:LinearODEsystem simulation model

        Args:
            hidden_params (dict): boolean values for if each hidden parameter should be sampled or stay constant
            simulation_settings (dict): settings for generating simulation data
            sample_boundaries (dict): sampling boundaries for each hidden parameter
            default_param_values (dict): default values of hidden parameters, if not sampled
            plot_settings (dict): settings for plotting simulation data
        """
        super().__init__(
            hidden_params, simulation_settings, sample_boundaries, default_param_values
        )
        self.num_features = 4
        self.plot_settings = plot_settings
        (
            self.prior,
            self.simulator,
            self.generative_model,
        ) = self.get_bayesflow_amortizer()
        self.print_internal_settings()

    def get_sim_data_dim(self) -> tuple:
        """Return dimensions of simulation data

        Returns:
            sim_data_dim (tuple): dimensions of simulatoin data (time points, features)
        """
        sim_data_dim = (self.max_time_iter, self.num_features)
        return sim_data_dim

    def reject_sampler(self, sample: npt.NDArray[np.float64]) -> bool:
        """Reject sample if it will lead to unstable solutions

        Args:
            sample (npt.NDArray[np.float64]): uniform prior sample

        Returns:
            bool: If sample should be rejected or not
        """
        sample_kwargs = self.sample_to_kwargs(sample)
        A = np.array(
            [
                [sample_kwargs["a"], sample_kwargs["b"]],
                [sample_kwargs["c"], sample_kwargs["d"]],
            ]
        )
        eigenvalues, _ = np.linalg.eig(A)
        if np.any(eigenvalues.real > 0):
            return True
        else:
            return False

    def solver(self, params: npt.NDArray[np.float32]) -> npt.NDArray[np.float32]:
        """Returns analytical solutions u and v of linear ODE system

        Args:
           params (npt.NDArray[np.float32]): hidden prior paramters

        Returns:
            solution (npt.NDArray[np.float32]): ODE solutions of size (time points, 4) with entries (u(t).real, v(t).real, u(t).imag, v(t).imag) at each time point t
        """
        param_kwargs = self.sample_to_kwargs(params)
        A = np.array(
            [
                [param_kwargs["a"], param_kwargs["b"]],
                [param_kwargs["c"], param_kwargs["d"]],
            ]
        )
        boundary_conditions = np.array([param_kwargs["u0"], param_kwargs["v0"]])
        eigenvalues, eigenvectors = np.linalg.eig(A)
        C = np.linalg.inv(eigenvectors) @ boundary_conditions
        solution = eigenvectors @ np.array(
            [
                C[0] * np.exp(eigenvalues[0] * self.t),
                C[1] * np.exp(eigenvalues[1] * self.t),
            ]
        )
        solution = np.concatenate((solution.T.real, solution.T.imag), axis=1)
        return solution.astype(np.float32)

    def plot_sim_data(
        self, filename: str = None
    ) -> Tuple[
        Type[Figure], Type[Axes], npt.NDArray[np.float32], npt.NDArray[np.float32]
    ]:
        """Generate simulation data plots

        Args:
            filename (str, optional): If given, save plot under results/filename/plots/filename-sim_data.png. Defaults to None.

        Returns:
            fig (plt.Figure) : matplotlib Figure instance for external access
            ax (plt.Axes) : matplotlib Axes instance for external access
            params (npt.NDArray[np.float32]): prior samples used to generate the plots
            sim_data (npt.NDArray[np.float32]): simulation data used to generate the plots
        """
        plt.rcParams["font.size"] = self.plot_settings["font_size"]

        data_dict = self.generative_model(batch_size=self.plot_settings["num_plots"])
        params = data_dict["prior_draws"]
        sim_data = data_dict["sim_data"]

        n_row = int(np.ceil(len(params) / 6))
        n_col = int(np.ceil(len(params) / n_row))

        fig, ax = plt.subplots(n_row, n_col, figsize=self.plot_settings["figsize"])
        if n_row > 1:
            ax = ax.flat

        if self.plot_settings["num_plots"] == 1:
            ax.plot(self.t, sim_data[0, :, 0], label="u(t) real part", c="orange")
            ax.plot(self.t, sim_data[0, :, 1], label="v(t) real part", c="blue")
            ax.plot(
                self.t,
                sim_data[0, :, 2],
                label="u(t) complex part",
                c="orange",
                linestyle="--",
            )
            ax.plot(
                self.t,
                sim_data[0, :, 3],
                label="v(t) complex part",
                c="blue",
                linestyle="--",
            )
            if self.plot_settings["show_params"]:
                for j, param_name in enumerate(self.hidden_param_names):
                    ax.text(
                        0.1,
                        0.7 - 0.025 * j,
                        "{}={:.3f}".format(param_name, params[0, j]),
                        horizontalalignment="left",
                        verticalalignment="center",
                        transform=ax.transAxes,
                        size=10,
                    )
            if self.plot_settings["show_eigen"]:
                param_kwargs = self.sample_to_kwargs(params[0])
                A = np.array(
                    [
                        [param_kwargs["a"], param_kwargs["b"]],
                        [param_kwargs["c"], param_kwargs["d"]],
                    ]
                )
                eigenvalues, eigenvectors = np.linalg.eig(A)
                ax.text(
                    0.1,
                    0.7 + 0.1,
                    "Eigenvalue 1={:.3f}".format(eigenvalues[0]),
                    horizontalalignment="left",
                    verticalalignment="center",
                    transform=ax.transAxes,
                    size=10,
                )
                ax.text(
                    0.1,
                    0.7 + 0.075,
                    "Eigenvalue 2={:.3f}".format(eigenvalues[1]),
                    horizontalalignment="left",
                    verticalalignment="center",
                    transform=ax.transAxes,
                    size=10,
                )
                ax.text(
                    0.1,
                    0.7 + 0.05,
                    "Eigenvector 1=({:.3f}, {:.3f})".format(
                        eigenvectors[0, 0], eigenvectors[1, 0]
                    ),
                    horizontalalignment="left",
                    verticalalignment="center",
                    transform=ax.transAxes,
                    size=10,
                )
                ax.text(
                    0.1,
                    0.7 + 0.025,
                    "Eigenvector 2=({:.3f}, {:.3f})".format(
                        eigenvectors[0, 1], eigenvectors[1, 1]
                    ),
                    horizontalalignment="left",
                    verticalalignment="center",
                    transform=ax.transAxes,
                    size=10,
                )
            ax.set_xlabel("Time t[s]")
            ax.set_ylabel("Function u(t)/v(t)")
            ax.grid(True)
            ax.legend()
        elif self.plot_settings["num_plots"] > 1:
            for i, param in enumerate(params):
                ax[i].plot(
                    self.t, sim_data[i, :, 0], label="u(t) real part", c="orange"
                )
                ax[i].plot(self.t, sim_data[i, :, 1], label="v(t) real part", c="blue")
                ax[i].plot(
                    self.t,
                    sim_data[i, :, 2],
                    label="u(t) complex part",
                    c="orange",
                    linestyle="--",
                )
                ax[i].plot(
                    self.t,
                    sim_data[i, :, 3],
                    label="v(t) complex part",
                    c="blue",
                    linestyle="--",
                )
                if self.plot_settings["show_params"]:
                    for j, param_name in enumerate(self.hidden_param_names):
                        ax[i].text(
                            0.1,
                            0.7 - 0.05 * j,
                            "{}={:.3f}".format(param_name, param[j]),
                            horizontalalignment="left",
                            verticalalignment="center",
                            transform=ax[i].transAxes,
                            size=8,
                        )
                if self.plot_settings["show_eigen"]:
                    param_kwargs = self.sample_to_kwargs(param)
                    A = np.array(
                        [
                            [param_kwargs["a"], param_kwargs["b"]],
                            [param_kwargs["c"], param_kwargs["d"]],
                        ]
                    )
                    eigenvalues, eigenvectors = np.linalg.eig(A)
                    ax[i].text(
                        0.1,
                        0.7 + 0.2,
                        "Eigenvalue 1={:.2f}".format(eigenvalues[0]),
                        horizontalalignment="left",
                        verticalalignment="center",
                        transform=ax[i].transAxes,
                        size=8,
                    )
                    ax[i].text(
                        0.1,
                        0.7 + 0.15,
                        "Eigenvalue 2={:.2f}".format(eigenvalues[1]),
                        horizontalalignment="left",
                        verticalalignment="center",
                        transform=ax[i].transAxes,
                        size=8,
                    )
                    ax[i].text(
                        0.1,
                        0.7 + 0.1,
                        "Eigenvector 1=({:.2f}, {:.2f})".format(
                            eigenvectors[0, 0], eigenvectors[1, 0]
                        ),
                        horizontalalignment="left",
                        verticalalignment="center",
                        transform=ax[i].transAxes,
                        size=8,
                    )
                    ax[i].text(
                        0.1,
                        0.7 + 0.05,
                        "Eigenvector 2=({:.2f}, {:.2f})".format(
                            eigenvectors[0, 1], eigenvectors[1, 1]
                        ),
                        horizontalalignment="left",
                        verticalalignment="center",
                        transform=ax[i].transAxes,
                        size=8,
                    )
                ax[i].set_xlabel("Time t[s]")
                ax[i].set_ylabel("Function u(t)/v(t)")
                ax[i].grid(True)
                handles, labels = ax[i].get_legend_handles_labels()
            fig.legend(handles, labels)

        if self.plot_settings["show_title"]:
            fig.suptitle("Linear ODE system simulation data examples")

        plt.tight_layout()

        if filename is not None:
            save_path = os.path.join(
                "results", filename, "plots", filename + "-sim_data.png"
            )
            if not os.path.exists(os.path.dirname(save_path)):
                os.makedirs(os.path.dirname(save_path))

            fig.savefig(
                save_path,
                transparent=True,
                bbox_inches="tight",
                pad_inches=0,
            )

        if self.plot_settings["show_plot"]:
            plt.show()

        return fig, ax, params, sim_data
