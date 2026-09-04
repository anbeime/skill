#!/usr/bin/env python3
"""Safety contracts for camera-fitting input validation."""

from __future__ import annotations

import math
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from forge.stage1_intake import solve_camera_pose as camera_fit  # noqa: E402
from forge.stage1_intake.camera_fitting_types import Point2, Point3  # noqa: E402


@dataclass(frozen=True, slots=True)
class FixtureCamera:
    image_width: int
    image_height: int
    fov_degrees: float
    yaw_degrees: float
    pitch_degrees: float
    roll_degrees: float
    position: Point3


@dataclass(frozen=True, slots=True)
class FixtureCorrespondence:
    name: str
    world: Point3
    observed: Point2


WORLD_POINTS: tuple[Point3, ...] = (
    (-0.55, -0.35, -0.20),
    (0.45, -0.40, 0.10),
    (-0.50, 0.35, 0.05),
    (0.60, 0.30, -0.15),
    (-0.15, -0.10, 0.45),
    (0.25, 0.15, 0.35),
)

OBSERVED_POINTS: tuple[Point2, ...] = (
    (260.0, 280.0),
    (390.0, 285.0),
    (265.0, 185.0),
    (405.0, 190.0),
    (325.0, 250.0),
    (370.0, 220.0),
)


def base_camera() -> FixtureCamera:
    return FixtureCamera(
        image_width=640,
        image_height=480,
        fov_degrees=38.0,
        yaw_degrees=1.0,
        pitch_degrees=-2.0,
        roll_degrees=0.5,
        position=(0.05, -0.05, 3.50),
    )


def base_correspondences() -> tuple[FixtureCorrespondence, ...]:
    return tuple(
        FixtureCorrespondence(f"point-{index}", point, OBSERVED_POINTS[index])
        for index, point in enumerate(WORLD_POINTS)
    )


def camera_with_dimensions(image_width: int, image_height: int) -> FixtureCamera:
    camera = base_camera()
    return FixtureCamera(
        image_width=image_width,
        image_height=image_height,
        fov_degrees=camera.fov_degrees,
        yaw_degrees=camera.yaw_degrees,
        pitch_degrees=camera.pitch_degrees,
        roll_degrees=camera.roll_degrees,
        position=camera.position,
    )


class CameraFittingSafetyTest(unittest.TestCase):
    def test_rejects_fewer_than_six_correspondences(self):
        correspondences = base_correspondences()[:5]

        with self.assertRaises(camera_fit.InsufficientCorrespondencesError) as raised:
            camera_fit.fit_camera_to_correspondences(correspondences, initial_camera=base_camera())

        self.assertEqual(raised.exception.required, camera_fit.MINIMUM_CORRESPONDENCES)
        self.assertEqual(raised.exception.actual, 5)

    def test_rejects_degenerate_world_landmarks(self):
        correspondences = tuple(
            FixtureCorrespondence(f"line-{index}", (float(index), 0.0, 0.0), (100.0 + index, 200.0))
            for index in range(camera_fit.MINIMUM_CORRESPONDENCES)
        )

        with self.assertRaises(camera_fit.DegenerateCorrespondencesError) as raised:
            camera_fit.fit_camera_to_correspondences(correspondences, initial_camera=base_camera())

        self.assertEqual(raised.exception.correspondence_count, camera_fit.MINIMUM_CORRESPONDENCES)

    def test_rejects_non_finite_correspondence_inputs(self):
        correspondences = list(base_correspondences())
        first = correspondences[0]
        correspondences[0] = FixtureCorrespondence(first.name, first.world, (math.nan, first.observed[1]))

        with self.assertRaises(camera_fit.NonFiniteCameraInputError) as raised:
            camera_fit.fit_camera_to_correspondences(tuple(correspondences), initial_camera=base_camera())

        self.assertEqual(raised.exception.field, "correspondences[0].observed[0]")

    def test_rejects_non_finite_initial_camera_inputs(self):
        camera = base_camera()
        initial_camera = FixtureCamera(
            image_width=camera.image_width,
            image_height=camera.image_height,
            fov_degrees=math.inf,
            yaw_degrees=camera.yaw_degrees,
            pitch_degrees=camera.pitch_degrees,
            roll_degrees=camera.roll_degrees,
            position=camera.position,
        )

        with self.assertRaises(camera_fit.NonFiniteCameraInputError) as raised:
            camera_fit.fit_camera_to_correspondences(base_correspondences(), initial_camera=initial_camera)

        self.assertEqual(raised.exception.field, "initial_camera.fov_degrees")

    def test_rejects_invalid_image_dimensions(self):
        with self.assertRaises(camera_fit.InvalidCameraDimensionsError) as raised:
            camera_fit.fit_camera_to_correspondences(
                base_correspondences(),
                initial_camera=camera_with_dimensions(0, 480),
            )

        self.assertEqual(raised.exception.image_width, 0)
        self.assertEqual(raised.exception.image_height, 480)

    def test_rejects_non_projectable_initial_camera(self):
        camera = base_camera()
        initial_camera = FixtureCamera(
            image_width=camera.image_width,
            image_height=camera.image_height,
            fov_degrees=camera.fov_degrees,
            yaw_degrees=camera.yaw_degrees,
            pitch_degrees=camera.pitch_degrees,
            roll_degrees=camera.roll_degrees,
            position=(0.0, 0.0, -2.0),
        )

        with self.assertRaises(camera_fit.InvalidInitialCameraError) as raised:
            camera_fit.fit_camera_to_correspondences(base_correspondences(), initial_camera=initial_camera)

        self.assertEqual(raised.exception.correspondence_name, "point-0")


if __name__ == "__main__":
    unittest.main(verbosity=2)
