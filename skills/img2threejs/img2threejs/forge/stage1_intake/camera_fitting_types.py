"""Typed camera-fitting contracts and public validation errors."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, Literal, Protocol, TypeAlias, TypedDict

Point2: TypeAlias = tuple[float, float]
Point3: TypeAlias = tuple[float, float, float]
ParameterVector: TypeAlias = tuple[float, float, float, float, float, float, float]
NumericScalar: TypeAlias = int | float
SolverStatus: TypeAlias = Literal["converged", "stalled", "max-iterations"]

MINIMUM_CORRESPONDENCES: Final = 6
MINIMUM_FOV_DEGREES: Final = 10.0
MAXIMUM_FOV_DEGREES: Final = 120.0
MINIMUM_CAMERA_DEPTH: Final = 1e-8
DEFAULT_MAXIMUM_ITERATIONS: Final = 80
DEFAULT_MAXIMUM_DAMPING_RETRIES: Final = 12
INITIAL_DAMPING: Final = 1e-3
MAXIMUM_DAMPING: Final = 1e12
CONVERGED_RMS_PIXELS: Final = 1e-6
FINITE_DIFFERENCE_STEPS: Final[ParameterVector] = (1e-3, 1e-4, 1e-4, 1e-4, 1e-5, 1e-5, 1e-5)


class CameraInitialization(Protocol):
    @property
    def image_width(self) -> int: ...

    @property
    def image_height(self) -> int: ...

    @property
    def fov_degrees(self) -> float: ...

    @property
    def yaw_degrees(self) -> float: ...

    @property
    def pitch_degrees(self) -> float: ...

    @property
    def roll_degrees(self) -> float: ...

    @property
    def position(self) -> Point3: ...


class LandmarkCorrespondence(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def world(self) -> Point3: ...

    @property
    def observed(self) -> Point2: ...


@dataclass(frozen=True, slots=True)
class InsufficientCorrespondencesError(Exception):
    required: int
    actual: int

    def __str__(self) -> str:
        return f"camera fit requires at least {self.required} correspondences; received {self.actual}"


@dataclass(frozen=True, slots=True)
class DegenerateCorrespondencesError(Exception):
    correspondence_count: int

    def __str__(self) -> str:
        return f"camera fit requires non-collinear 3D landmarks; received {self.correspondence_count} degenerate correspondences"


@dataclass(frozen=True, slots=True)
class InvalidInitialCameraError(Exception):
    correspondence_name: str

    def __str__(self) -> str:
        return f"initial camera cannot project correspondence {self.correspondence_name!r}"


@dataclass(frozen=True, slots=True)
class InvalidCameraDimensionsError(Exception):
    image_width: int
    image_height: int

    def __str__(self) -> str:
        return f"camera image dimensions must be positive finite integers; received {self.image_width}x{self.image_height}"


@dataclass(frozen=True, slots=True)
class NonFiniteCameraInputError(Exception):
    field: str

    def __str__(self) -> str:
        return f"camera input field {self.field!r} must be a finite non-boolean number"


@dataclass(frozen=True, slots=True)
class CameraParameters:
    image_width: int
    image_height: int
    fov_degrees: float
    yaw_degrees: float
    pitch_degrees: float
    roll_degrees: float
    position: Point3


@dataclass(frozen=True, slots=True)
class NormalizedCorrespondence:
    name: str
    world: Point3
    observed: Point2


@dataclass(frozen=True, slots=True)
class NormalizedFitInput:
    correspondences: tuple[NormalizedCorrespondence, ...]
    initial_camera: CameraParameters


@dataclass(frozen=True, slots=True)
class FitState:
    parameters: CameraParameters
    rms_error: float
    iterations: int
    accepted_steps: int
    rejected_steps: int
    damping: float
    status: SolverStatus


@dataclass(frozen=True, slots=True)
class SolverLimits:
    maximum_iterations: int
    maximum_damping_retries: int
    initial_damping: float
    maximum_damping: float
    converged_rms_pixels: float
    finite_difference_steps: ParameterVector


class ScalarField(TypedDict):
    value: float
    source: str
    agentFill: bool


class FovField(ScalarField):
    rationale: str


class OrientationDescriptor(TypedDict):
    yawDegrees: ScalarField
    pitchDegrees: ScalarField
    rollDegrees: ScalarField
    note: str


class PositionDescriptor(TypedDict):
    hint: list[float]
    distance: ScalarField
    note: str


class AspectDescriptor(TypedDict):
    value: float
    source: str
    agentFill: bool


class FitCameraParameters(TypedDict):
    fovDegrees: float
    yawDegrees: float
    pitchDegrees: float
    rollDegrees: float
    position: list[float]


class ResidualDiagnostic(TypedDict):
    name: str
    errorPixels: float


class ConvergenceDiagnostic(TypedDict):
    status: SolverStatus
    iterations: int
    acceptedSteps: int
    rejectedSteps: int
    damping: float


class FitDiagnostic(TypedDict):
    method: str
    cameraParameters: FitCameraParameters
    initialReprojectionError: float
    finalReprojectionError: float
    residuals: list[ResidualDiagnostic]
    convergence: ConvergenceDiagnostic


class CameraFitDescriptor(TypedDict):
    version: str
    sourceImage: str
    solver: str
    method: str
    imageWidth: int
    imageHeight: int
    fovDegrees: FovField
    aspect: AspectDescriptor
    orientation: OrientationDescriptor
    position: PositionDescriptor
    confidence: float
    limitations: list[str]
    note: str
    fit: FitDiagnostic


def normalize_fit_input(
    correspondences: Sequence[LandmarkCorrespondence],
    initial_camera: CameraInitialization,
) -> NormalizedFitInput:
    """Parse the public fitting inputs before any geometry arithmetic occurs."""
    correspondence_items = tuple(correspondences)
    if len(correspondence_items) < MINIMUM_CORRESPONDENCES:
        raise InsufficientCorrespondencesError(required=MINIMUM_CORRESPONDENCES, actual=len(correspondence_items))
    normalized_camera = _normalize_initial_camera(initial_camera)
    normalized_correspondences = tuple(
        _normalize_correspondence(correspondence, index)
        for index, correspondence in enumerate(correspondence_items)
    )
    return NormalizedFitInput(normalized_correspondences, normalized_camera)


def _normalize_initial_camera(camera: CameraInitialization) -> CameraParameters:
    if not _is_positive_dimension(camera.image_width) or not _is_positive_dimension(camera.image_height):
        raise InvalidCameraDimensionsError(image_width=camera.image_width, image_height=camera.image_height)
    return CameraParameters(
        image_width=camera.image_width,
        image_height=camera.image_height,
        fov_degrees=_finite_scalar(camera.fov_degrees, "initial_camera.fov_degrees"),
        yaw_degrees=_finite_scalar(camera.yaw_degrees, "initial_camera.yaw_degrees"),
        pitch_degrees=_finite_scalar(camera.pitch_degrees, "initial_camera.pitch_degrees"),
        roll_degrees=_finite_scalar(camera.roll_degrees, "initial_camera.roll_degrees"),
        position=_point3(camera.position, "initial_camera.position"),
    )


def _normalize_correspondence(correspondence: LandmarkCorrespondence, index: int) -> NormalizedCorrespondence:
    prefix = f"correspondences[{index}]"
    return NormalizedCorrespondence(
        name=correspondence.name,
        world=_point3(correspondence.world, f"{prefix}.world"),
        observed=_point2(correspondence.observed, f"{prefix}.observed"),
    )


def _is_positive_dimension(value: int) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _finite_scalar(value: NumericScalar, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise NonFiniteCameraInputError(field=field)
    return float(value)


def _point2(values: Sequence[NumericScalar], field: str) -> Point2:
    if not _is_numeric_sequence(values, 2):
        raise NonFiniteCameraInputError(field=field)
    return _finite_scalar(values[0], f"{field}[0]"), _finite_scalar(values[1], f"{field}[1]")


def _point3(values: Sequence[NumericScalar], field: str) -> Point3:
    if not _is_numeric_sequence(values, 3):
        raise NonFiniteCameraInputError(field=field)
    return (
        _finite_scalar(values[0], f"{field}[0]"),
        _finite_scalar(values[1], f"{field}[1]"),
        _finite_scalar(values[2], f"{field}[2]"),
    )


def _is_numeric_sequence(values: Sequence[NumericScalar], length: int) -> bool:
    return isinstance(values, Sequence) and not isinstance(values, str | bytes) and len(values) == length
