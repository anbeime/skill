"""Projection, residual, and degeneracy math for camera fitting."""

from __future__ import annotations

import math
from collections.abc import Sequence

from forge.stage1_intake.camera_fitting_types import (
    MAXIMUM_FOV_DEGREES,
    MINIMUM_CAMERA_DEPTH,
    MINIMUM_FOV_DEGREES,
    CameraParameters,
    NormalizedCorrespondence,
    Point2,
    Point3,
)


def project_landmark(point: Point3, camera: CameraParameters) -> Point2 | None:
    """Project a world point using the established pitch, yaw, then roll convention."""
    if not MINIMUM_FOV_DEGREES <= camera.fov_degrees <= MAXIMUM_FOV_DEGREES:
        return None
    tangent = math.tan(math.radians(camera.fov_degrees) / 2.0)
    if not math.isfinite(tangent) or abs(tangent) <= MINIMUM_CAMERA_DEPTH:
        return None
    focal_length = (camera.image_height / 2.0) / tangent
    translated_x = point[0] - camera.position[0]
    translated_y = point[1] - camera.position[1]
    translated_z = camera.position[2] - point[2]

    pitch_radians = math.radians(camera.pitch_degrees)
    pitch_cosine = math.cos(pitch_radians)
    pitch_sine = math.sin(pitch_radians)
    pitched_x = translated_x
    pitched_y = translated_y * pitch_cosine - translated_z * pitch_sine
    pitched_z = translated_y * pitch_sine + translated_z * pitch_cosine

    yaw_radians = math.radians(camera.yaw_degrees)
    yaw_cosine = math.cos(yaw_radians)
    yaw_sine = math.sin(yaw_radians)
    yawed_x = pitched_x * yaw_cosine + pitched_z * yaw_sine
    yawed_y = pitched_y
    yawed_z = -pitched_x * yaw_sine + pitched_z * yaw_cosine

    roll_radians = math.radians(camera.roll_degrees)
    roll_cosine = math.cos(roll_radians)
    roll_sine = math.sin(roll_radians)
    rolled_x = yawed_x * roll_cosine - yawed_y * roll_sine
    rolled_y = yawed_x * roll_sine + yawed_y * roll_cosine
    if yawed_z <= MINIMUM_CAMERA_DEPTH:
        return None
    projected_x = (camera.image_width / 2.0) + (focal_length * rolled_x / yawed_z)
    projected_y = (camera.image_height / 2.0) - (focal_length * rolled_y / yawed_z)
    if not math.isfinite(projected_x) or not math.isfinite(projected_y):
        return None
    return projected_x, projected_y


def residual_components(
    correspondences: Sequence[NormalizedCorrespondence], camera: CameraParameters
) -> tuple[float, ...] | None:
    components: list[float] = []
    for correspondence in correspondences:
        projected = project_landmark(correspondence.world, camera)
        if projected is None:
            return None
        delta_x = projected[0] - correspondence.observed[0]
        delta_y = projected[1] - correspondence.observed[1]
        if not math.isfinite(delta_x) or not math.isfinite(delta_y):
            return None
        components.extend((delta_x, delta_y))
    return tuple(components)


def rms_reprojection_error(components: tuple[float, ...]) -> float:
    return math.sqrt(sum(component * component for component in components) / (len(components) // 2))


def has_degenerate_world_geometry(correspondences: Sequence[NormalizedCorrespondence]) -> bool:
    coordinate_scale = 1.0
    for correspondence in correspondences:
        coordinate_scale = max(coordinate_scale, *(abs(value) for value in correspondence.world))
    count = len(correspondences)
    centroid = (
        sum(correspondence.world[0] for correspondence in correspondences) / count,
        sum(correspondence.world[1] for correspondence in correspondences) / count,
        sum(correspondence.world[2] for correspondence in correspondences) / count,
    )
    span_square = 0.0
    first_index = 0
    second_index = 0
    for index, first in enumerate(correspondences):
        centered = (
            first.world[0] - centroid[0],
            first.world[1] - centroid[1],
            first.world[2] - centroid[2],
        )
        span_square = max(span_square, sum(component * component for component in centered))
        for candidate_index in range(index + 1, count):
            second = correspondences[candidate_index]
            delta_x = second.world[0] - first.world[0]
            delta_y = second.world[1] - first.world[1]
            delta_z = second.world[2] - first.world[2]
            separation_square = delta_x * delta_x + delta_y * delta_y + delta_z * delta_z
            if separation_square > span_square:
                span_square = separation_square
                first_index = index
                second_index = candidate_index
    minimum_span = coordinate_scale * 1e-9
    if span_square <= minimum_span * minimum_span:
        return True
    first_point = correspondences[first_index].world
    second_point = correspondences[second_index].world
    axis = (
        second_point[0] - first_point[0],
        second_point[1] - first_point[1],
        second_point[2] - first_point[2],
    )
    axis_square = sum(component * component for component in axis)
    maximum_perpendicular_square = 0.0
    for correspondence in correspondences:
        offset = (
            correspondence.world[0] - first_point[0],
            correspondence.world[1] - first_point[1],
            correspondence.world[2] - first_point[2],
        )
        projection = sum(offset[index] * axis[index] for index in range(3)) / axis_square
        perpendicular = tuple(offset[index] - projection * axis[index] for index in range(3))
        maximum_perpendicular_square = max(
            maximum_perpendicular_square,
            sum(component * component for component in perpendicular),
        )
    return maximum_perpendicular_square <= span_square * 1e-12
