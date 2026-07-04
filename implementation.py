import numpy as np
import torch
from torch.nn import functional as F

class StableBoundaryElementMethod:
    def __init__(self, boundary_points, time_steps, c=343.0):
        """
        Initialize the Stable Boundary Element Method for acoustic wave propagation.

        Args:
            boundary_points (torch.Tensor): Tensor of shape (N, 3) representing boundary points in 3D space.
            time_steps (int): Number of time steps for the simulation.
            c (float): Speed of sound in the medium (default is 343 m/s for air).
        """
        self.boundary_points = boundary_points
        self.time_steps = time_steps
        self.c = c
        self.num_points = boundary_points.shape[0]
        self.dt = 1.0 / time_steps  # Time step size
        self.distance_matrix = self._compute_distance_matrix()

    def _compute_distance_matrix(self):
        """
        Compute the pairwise distance matrix for the boundary points.

        Returns:
            torch.Tensor: Distance matrix of shape (N, N).
        """
        diff = self.boundary_points.unsqueeze(1) - self.boundary_points.unsqueeze(0)
        distance_matrix = torch.sqrt(torch.sum(diff**2, dim=-1))
        return distance_matrix

    def _hypersingular_operator(self, u):
        """
        Apply the hypersingular boundary integral operator to the input.

        Args:
            u (torch.Tensor): Tensor of shape (N,) representing the boundary values.

        Returns:
            torch.Tensor: Result of applying the hypersingular operator.
        """
        G = 1 / (4 * np.pi * self.distance_matrix + 1e-6)  # Green's function
        G.fill_diagonal_(0)  # Remove self-interaction
        return torch.matmul(G, u)

    def time_step(self, u_prev, u_curr):
        """
        Perform a single time step of the simulation.

        Args:
            u_prev (torch.Tensor): Tensor of shape (N,) representing the solution at the previous time step.
            u_curr (torch.Tensor): Tensor of shape (N,) representing the solution at the current time step.

        Returns:
            torch.Tensor: Solution at the next time step.
        """
        laplacian_u = self._hypersingular_operator(u_curr)
        u_next = 2 * u_curr - u_prev + (self.c * self.dt)**2 * laplacian_u
        return u_next

    def simulate(self, initial_condition, num_steps):
        """
        Simulate the acoustic wave propagation over time.

        Args:
            initial_condition (torch.Tensor): Tensor of shape (N,) representing the initial boundary condition.
            num_steps (int): Number of time steps to simulate.

        Returns:
            torch.Tensor: Solution tensor of shape (num_steps, N).
        """
        solutions = torch.zeros((num_steps, self.num_points))
        solutions[0] = initial_condition
        solutions[1] = initial_condition  # Assuming zero initial velocity

        for t in range(1, num_steps - 1):
            solutions[t + 1] = self.time_step(solutions[t - 1], solutions[t])

        return solutions

if __name__ == '__main__':
    # Dummy data for testing
    torch.manual_seed(42)
    num_boundary_points = 10
    time_steps = 100
    boundary_points = torch.rand((num_boundary_points, 3))  # Random points in 3D space
    initial_condition = torch.sin(torch.linspace(0, 2 * np.pi, num_boundary_points))  # Example initial condition

    # Initialize and run the simulation
    sbem = StableBoundaryElementMethod(boundary_points, time_steps)
    results = sbem.simulate(initial_condition, num_steps=50)

    # Print the results
    print("Simulation results (shape):", results.shape)
    print("First time step solution:", results[0])
    print("Last time step solution:", results[-1])