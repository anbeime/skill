"""Deterministic seven-parameter damped least-squares camera solver."""

from __future__ import annotations

from collections.abc import Sequence

from forge.stage1_intake.camera_fitting_math import (
    residual_components,
    rms_reprojection_error,
)
from forge.stage1_intake.camera_fitting_types import (
    CameraParameters,
    FitState,
    NormalizedCorrespondence,
    ParameterVector,
    SolverLimits,
)


def fit_parameters(
    correspondences: Sequence[NormalizedCorrespondence],
    initial_camera: CameraParameters,
    limits: SolverLimits,
) -> FitState:
    """Fit FOV, Euler angles, and position with fixed finite-difference steps."""
    initial_residuals = residual_components(correspondences, initial_camera)
    if initial_residuals is None:
        raise RuntimeError("validated initial camera must be projectable before solver entry")
    camera = initial_camera
    residuals = initial_residuals
    rms_error = rms_reprojection_error(residuals)
    damping = limits.initial_damping
    accepted_steps = 0
    rejected_steps = 0
    for iteration in range(1, limits.maximum_iterations + 1):
        jacobian = _central_difference_jacobian(correspondences, camera, limits.finite_difference_steps)
        if jacobian is None:
            return FitState(camera, rms_error, iteration, accepted_steps, rejected_steps, damping, "stalled")
        accepted = False
        for _ in range(limits.maximum_damping_retries):
            hessian, gradient = _normal_equations(jacobian, residuals, damping, limits.finite_difference_steps)
            delta = _solve_linear_system(hessian, gradient)
            if delta is None:
                damping = min(damping * 10.0, limits.maximum_damping)
                rejected_steps += 1
                continue
            candidate = _parameters_from_vector(
                _vector_with_addition(_parameter_vector(camera), delta),
                camera.image_width,
                camera.image_height,
            )
            candidate_residuals = residual_components(correspondences, candidate)
            if candidate_residuals is None:
                damping = min(damping * 10.0, limits.maximum_damping)
                rejected_steps += 1
                continue
            candidate_error = rms_reprojection_error(candidate_residuals)
            if candidate_error < rms_error:
                camera = candidate
                residuals = candidate_residuals
                rms_error = candidate_error
                damping = max(damping / 3.0, 1e-12)
                accepted_steps += 1
                accepted = True
                if rms_error <= limits.converged_rms_pixels or _scaled_step_is_small(delta):
                    return FitState(camera, rms_error, iteration, accepted_steps, rejected_steps, damping, "converged")
                break
            damping = min(damping * 10.0, limits.maximum_damping)
            rejected_steps += 1
        if not accepted:
            return FitState(camera, rms_error, iteration, accepted_steps, rejected_steps, damping, "stalled")
    status = "converged" if rms_error <= limits.converged_rms_pixels else "max-iterations"
    return FitState(camera, rms_error, limits.maximum_iterations, accepted_steps, rejected_steps, damping, status)


def _parameter_vector(camera: CameraParameters) -> ParameterVector:
    return (
        camera.fov_degrees,
        camera.yaw_degrees,
        camera.pitch_degrees,
        camera.roll_degrees,
        camera.position[0],
        camera.position[1],
        camera.position[2],
    )


def _parameters_from_vector(vector: ParameterVector, image_width: int, image_height: int) -> CameraParameters:
    return CameraParameters(
        image_width=image_width,
        image_height=image_height,
        fov_degrees=vector[0],
        yaw_degrees=vector[1],
        pitch_degrees=vector[2],
        roll_degrees=vector[3],
        position=(vector[4], vector[5], vector[6]),
    )


def _vector_with_delta(vector: ParameterVector, index: int, delta: float) -> ParameterVector:
    values = list(vector)
    values[index] += delta
    return values[0], values[1], values[2], values[3], values[4], values[5], values[6]


def _vector_with_addition(vector: ParameterVector, delta: ParameterVector) -> ParameterVector:
    return (
        vector[0] + delta[0],
        vector[1] + delta[1],
        vector[2] + delta[2],
        vector[3] + delta[3],
        vector[4] + delta[4],
        vector[5] + delta[5],
        vector[6] + delta[6],
    )


def _central_difference_jacobian(
    correspondences: Sequence[NormalizedCorrespondence],
    camera: CameraParameters,
    steps: ParameterVector,
) -> list[list[float]] | None:
    vector = _parameter_vector(camera)
    columns: list[tuple[float, ...]] = []
    for parameter_index, step in enumerate(steps):
        positive_camera = _parameters_from_vector(
            _vector_with_delta(vector, parameter_index, step), camera.image_width, camera.image_height
        )
        negative_camera = _parameters_from_vector(
            _vector_with_delta(vector, parameter_index, -step), camera.image_width, camera.image_height
        )
        positive_residuals = residual_components(correspondences, positive_camera)
        negative_residuals = residual_components(correspondences, negative_camera)
        if positive_residuals is None or negative_residuals is None:
            return None
        columns.append(
            tuple(
                (positive - negative) / (2.0 * step)
                for positive, negative in zip(positive_residuals, negative_residuals, strict=True)
            )
        )
    return [[column[row] for column in columns] for row in range(len(columns[0]))]


def _normal_equations(
    jacobian: list[list[float]],
    residuals: tuple[float, ...],
    damping: float,
    steps: ParameterVector,
) -> tuple[list[list[float]], list[float]]:
    dimension = len(steps)
    hessian = [[0.0 for _ in range(dimension)] for _ in range(dimension)]
    gradient = [0.0 for _ in range(dimension)]
    for row, residual in zip(jacobian, residuals, strict=True):
        for column, value in enumerate(row):
            gradient[column] += value * residual
            for secondary_column in range(column, dimension):
                hessian[column][secondary_column] += value * row[secondary_column]
    for column in range(dimension):
        for secondary_column in range(column):
            hessian[column][secondary_column] = hessian[secondary_column][column]
        hessian[column][column] += damping * max(hessian[column][column], 1.0)
    return hessian, [-value for value in gradient]


def _solve_linear_system(matrix: list[list[float]], right_hand_side: list[float]) -> ParameterVector | None:
    dimension = len(right_hand_side)
    augmented = [row.copy() + [right_hand_side[index]] for index, row in enumerate(matrix)]
    largest_entry = max(abs(value) for row in matrix for value in row)
    pivot_tolerance = max(1.0, largest_entry) * 1e-12
    for column in range(dimension):
        pivot_row = column
        for candidate_row in range(column + 1, dimension):
            if abs(augmented[candidate_row][column]) > abs(augmented[pivot_row][column]):
                pivot_row = candidate_row
        pivot = augmented[pivot_row][column]
        if abs(pivot) <= pivot_tolerance:
            return None
        augmented[column], augmented[pivot_row] = augmented[pivot_row], augmented[column]
        pivot = augmented[column][column]
        for row in range(column + 1, dimension):
            factor = augmented[row][column] / pivot
            augmented[row][column] = 0.0
            for secondary_column in range(column + 1, dimension + 1):
                augmented[row][secondary_column] -= factor * augmented[column][secondary_column]
    solution = [0.0 for _ in range(dimension)]
    for row in range(dimension - 1, -1, -1):
        remaining = sum(augmented[row][column] * solution[column] for column in range(row + 1, dimension))
        solution[row] = (augmented[row][dimension] - remaining) / augmented[row][row]
    return (
        solution[0], solution[1], solution[2], solution[3], solution[4], solution[5], solution[6]
    )


def _scaled_step_is_small(delta: ParameterVector) -> bool:
    scale = (30.0, 10.0, 10.0, 10.0, 1.0, 1.0, 1.0)
    return max(abs(value) / scale[index] for index, value in enumerate(delta)) <= 1e-8
