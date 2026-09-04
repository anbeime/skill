#!/usr/bin/env python3
"""Contract tests for deterministic landmark camera fitting."""

from __future__ import annotations

import sys
import unittest
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from forge.stage1_intake import solve_camera_pose as camera_fit  # noqa: E402
from forge.stage1_intake import camera_fitting_types as camera_types  # noqa: E402
from forge.stage1_intake import camera_image_helpers as image_helpers  # noqa: E402
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


@dataclass(frozen=True, slots=True)
class KnownCameraCase:
    true_camera: FixtureCamera
    initial_camera: FixtureCamera
    correspondences: tuple[FixtureCorrespondence, ...]


WORLD_POINTS: tuple[Point3, ...] = (
    (-0.55, -0.35, -0.20),
    (0.45, -0.40, 0.10),
    (-0.50, 0.35, 0.05),
    (0.60, 0.30, -0.15),
    (-0.15, -0.10, 0.45),
    (0.25, 0.15, 0.35),
    (-0.35, 0.05, -0.45),
    (0.35, -0.15, -0.35),
)

GOLDEN_OBSERVATIONS: tuple[Point2, ...] = (
    (578.7401654634278, 379.751871427244),
    (808.3724977028866, 389.4016539586094),
    (574.4757073869129, 218.67838466422444),
    (833.1143917536056, 222.48567412558583),
    (654.6053614640265, 323.6375569741955),
    (757.573458961317, 254.25311289570504),
    (624.651608536512, 290.53788687932575),
    (775.5907395975036, 327.4459034756644),
)

def make_known_camera_case() -> KnownCameraCase:
    true_camera = FixtureCamera(
        image_width=1280,
        image_height=720,
        fov_degrees=42.0,
        yaw_degrees=5.0,
        pitch_degrees=-3.0,
        roll_degrees=2.0,
        position=(0.10, -0.05, 4.00),
    )
    initial_camera = FixtureCamera(
        image_width=true_camera.image_width,
        image_height=true_camera.image_height,
        fov_degrees=40.0,
        yaw_degrees=4.0,
        pitch_degrees=-2.0,
        roll_degrees=1.0,
        position=(0.05, -0.02, 3.80),
    )
    correspondences = tuple(
        FixtureCorrespondence(f"point-{index}", point, GOLDEN_OBSERVATIONS[index])
        for index, point in enumerate(WORLD_POINTS)
    )
    return KnownCameraCase(true_camera, initial_camera, correspondences)


class CameraFittingContractTest(unittest.TestCase):
    def test_known_camera_converges_with_low_reprojection_error(self):
        case = make_known_camera_case()

        descriptor = camera_fit.fit_camera_to_correspondences(
            case.correspondences,
            initial_camera=case.initial_camera,
        )

        fit = descriptor["fit"]
        self.assertEqual(fit["convergence"]["status"], "converged")
        self.assertLess(fit["finalReprojectionError"], 1e-4)
        self.assertLess(fit["finalReprojectionError"], fit["initialReprojectionError"])
        parameters = fit["cameraParameters"]
        self.assertAlmostEqual(parameters["fovDegrees"], case.true_camera.fov_degrees, delta=1e-5)
        self.assertAlmostEqual(parameters["yawDegrees"], case.true_camera.yaw_degrees, delta=1e-5)
        self.assertAlmostEqual(parameters["pitchDegrees"], case.true_camera.pitch_degrees, delta=1e-5)
        self.assertAlmostEqual(parameters["rollDegrees"], case.true_camera.roll_degrees, delta=1e-5)
        for actual, expected in zip(parameters["position"], case.true_camera.position, strict=True):
            self.assertAlmostEqual(actual, expected, delta=1e-6)
        self.assertEqual([item["name"] for item in fit["residuals"]], [item.name for item in case.correspondences])
        for residual in fit["residuals"]:
            self.assertLess(residual["errorPixels"], 1e-4)

    def test_camera_fit_output_is_deterministic(self):
        case = make_known_camera_case()

        first = camera_fit.fit_camera_to_correspondences(case.correspondences, initial_camera=case.initial_camera)
        second = camera_fit.fit_camera_to_correspondences(case.correspondences, initial_camera=case.initial_camera)

        self.assertEqual(first, second)

    def test_public_compatibility_exports_remain_available(self):
        exported_names = {
            "CONVERGED_RMS_PIXELS",
            "FINITE_DIFFERENCE_STEPS",
            "INITIAL_DAMPING",
            "MAXIMUM_DAMPING",
            "MAXIMUM_DAMPING_RETRIES",
            "MAXIMUM_FOV_DEGREES",
            "MAXIMUM_ITERATIONS",
            "MINIMUM_CAMERA_DEPTH",
            "MINIMUM_CORRESPONDENCES",
            "MINIMUM_FOV_DEGREES",
            "CameraFitDescriptor",
            "CameraInitialization",
            "DegenerateCorrespondencesError",
            "InsufficientCorrespondencesError",
            "InvalidCameraDimensionsError",
            "InvalidInitialCameraError",
            "LandmarkCorrespondence",
            "NonFiniteCameraInputError",
            "bmp_size",
            "build_camera",
            "clamp",
            "detect_size",
            "estimate_fov",
            "fit_camera_to_correspondences",
            "gif_size",
            "jpeg_size",
            "main",
            "png_size",
            "webp_size",
        }

        self.assertLessEqual(exported_names, set(camera_fit.__all__))
        identity_exports = {
            "CONVERGED_RMS_PIXELS": camera_types.CONVERGED_RMS_PIXELS,
            "FINITE_DIFFERENCE_STEPS": camera_types.FINITE_DIFFERENCE_STEPS,
            "INITIAL_DAMPING": camera_types.INITIAL_DAMPING,
            "MAXIMUM_DAMPING": camera_types.MAXIMUM_DAMPING,
            "MAXIMUM_FOV_DEGREES": camera_types.MAXIMUM_FOV_DEGREES,
            "MINIMUM_CAMERA_DEPTH": camera_types.MINIMUM_CAMERA_DEPTH,
            "MINIMUM_CORRESPONDENCES": camera_types.MINIMUM_CORRESPONDENCES,
            "MINIMUM_FOV_DEGREES": camera_types.MINIMUM_FOV_DEGREES,
            "CameraFitDescriptor": camera_types.CameraFitDescriptor,
            "CameraInitialization": camera_types.CameraInitialization,
            "DegenerateCorrespondencesError": camera_types.DegenerateCorrespondencesError,
            "InsufficientCorrespondencesError": camera_types.InsufficientCorrespondencesError,
            "InvalidCameraDimensionsError": camera_types.InvalidCameraDimensionsError,
            "InvalidInitialCameraError": camera_types.InvalidInitialCameraError,
            "LandmarkCorrespondence": camera_types.LandmarkCorrespondence,
            "NonFiniteCameraInputError": camera_types.NonFiniteCameraInputError,
            "bmp_size": image_helpers.bmp_size,
            "build_camera": image_helpers.build_camera,
            "clamp": image_helpers.clamp,
            "detect_size": image_helpers.detect_size,
            "estimate_fov": image_helpers.estimate_fov,
            "gif_size": image_helpers.gif_size,
            "jpeg_size": image_helpers.jpeg_size,
            "png_size": image_helpers.png_size,
            "webp_size": image_helpers.webp_size,
        }
        for name, expected in identity_exports.items():
            self.assertIs(getattr(camera_fit, name), expected, name)
        for name in ("build_camera", "detect_size", "estimate_fov", "fit_camera_to_correspondences", "main", "png_size"):
            self.assertTrue(callable(getattr(camera_fit, name)), name)

    def test_solver_termination_is_bounded_by_public_limits(self):
        case = make_known_camera_case()
        previous_iterations = camera_fit.MAXIMUM_ITERATIONS
        previous_retries = camera_fit.MAXIMUM_DAMPING_RETRIES
        camera_fit.MAXIMUM_ITERATIONS = 1
        camera_fit.MAXIMUM_DAMPING_RETRIES = 1
        try:
            descriptor = camera_fit.fit_camera_to_correspondences(
                case.correspondences,
                initial_camera=case.initial_camera,
            )
        finally:
            camera_fit.MAXIMUM_ITERATIONS = previous_iterations
            camera_fit.MAXIMUM_DAMPING_RETRIES = previous_retries

        convergence = descriptor["fit"]["convergence"]
        self.assertLessEqual(convergence["iterations"], 1)
        self.assertLessEqual(convergence["acceptedSteps"] + convergence["rejectedSteps"], 1)
        self.assertIn(convergence["status"], {"converged", "stalled", "max-iterations"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
