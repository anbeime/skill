"""Validation for opt-in implicit signed-distance-field descriptors."""

from __future__ import annotations

import math
from typing import Any


VALID_SDF_PRIMITIVES = {"sphere", "capsule", "box", "cone", "ellipsoid"}
VALID_SDF_OPERATIONS = {"smooth-union", "subtract", "intersect"}
MAX_SDF_PRIMITIVES = 64
MAX_SDF_OPERATIONS = 128
_PRIMITIVE_FIELDS = {"id", "type", "center", "radius", "height", "size", "dimensions", "radii", "transform"}
_VECTOR_FIELDS = {"center", "size", "radii"}
_TRANSFORM_FIELDS = {"position", "translation", "rotation", "scale"}
_OPERATION_FIELDS = {"id", "output", "type", "left", "right", "radius"}


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate_finite(value: Any, label: str, errors: list[str]) -> None:
    if _is_number(value):
        if not math.isfinite(float(value)):
            errors.append(f"{label} must be finite")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_finite(item, f"{label}[{index}]", errors)
    elif isinstance(value, dict):
        for key, item in value.items():
            _validate_finite(item, f"{label}.{key}", errors)


def _validate_vector(value: Any, label: str, errors: list[str], positive: bool = False) -> None:
    if not isinstance(value, list) or len(value) != 3:
        errors.append(f"{label} must be [number, number, number]")
        return
    for index, item in enumerate(value):
        if not _is_number(item):
            errors.append(f"{label}[{index}] must be numeric")
        elif positive and float(item) <= 0:
            errors.append(f"{label}[{index}] must be greater than 0")


def _validate_positive(value: Any, label: str, errors: list[str], allow_zero: bool = False) -> None:
    if not _is_number(value):
        errors.append(f"{label} must be numeric")
    elif float(value) < 0 or (not allow_zero and float(value) == 0):
        errors.append(f"{label} must be greater than {0 if allow_zero else 0}")


def _validate_primitive(primitive: Any, index: int, ids: set[str], errors: list[str]) -> None:
    label = f"geometryDescriptor.sdf.primitives[{index}]"
    if not isinstance(primitive, dict):
        errors.append(f"{label} must be an object")
        return
    primitive_id = primitive.get("id")
    if not isinstance(primitive_id, str) or not primitive_id.strip():
        errors.append(f"{label}.id is required")
    elif primitive_id in ids:
        errors.append(f"{label}.id duplicates {primitive_id!r}")
    else:
        ids.add(primitive_id)
    primitive_type = primitive.get("type")
    if primitive_type not in VALID_SDF_PRIMITIVES:
        errors.append(f"{label}.type must be one of: {', '.join(sorted(VALID_SDF_PRIMITIVES))}")
    for field in primitive:
        if field not in _PRIMITIVE_FIELDS:
            errors.append(f"{label}.{field} is not supported")
    for field in _VECTOR_FIELDS & set(primitive):
        _validate_vector(primitive[field], f"{label}.{field}", errors, positive=field in {"size", "radii"})
    transform = primitive.get("transform")
    if transform is not None:
        if not isinstance(transform, dict):
            errors.append(f"{label}.transform must be an object")
        else:
            for field in transform:
                if field not in _TRANSFORM_FIELDS:
                    errors.append(f"{label}.transform.{field} is not supported")
            for field in _TRANSFORM_FIELDS & set(transform):
                _validate_vector(
                    transform[field], f"{label}.transform.{field}", errors, positive=field == "scale"
                )
    if primitive_type in {"sphere", "capsule", "cone"}:
        _validate_positive(primitive.get("radius"), f"{label}.radius", errors)
    if primitive_type == "capsule":
        _validate_positive(primitive.get("height"), f"{label}.height", errors, allow_zero=True)
    if primitive_type == "cone":
        _validate_positive(primitive.get("height"), f"{label}.height", errors)
    if primitive_type == "box" and "size" not in primitive:
        _validate_vector(primitive.get("dimensions"), f"{label}.dimensions", errors, positive=True)
    if primitive_type == "ellipsoid" and "radii" not in primitive:
        _validate_vector(primitive.get("radius"), f"{label}.radius", errors, positive=True)
    _validate_finite(primitive, label, errors)


def _validate_operation(operation: Any, index: int, known_ids: set[str], errors: list[str]) -> None:
    label = f"geometryDescriptor.sdf.operations[{index}]"
    if not isinstance(operation, dict):
        errors.append(f"{label} must be an object")
        return
    for field in operation:
        if field not in _OPERATION_FIELDS:
            errors.append(f"{label}.{field} is not supported")
    operation_type = operation.get("type")
    if operation_type not in VALID_SDF_OPERATIONS:
        errors.append(f"{label}.type must be one of: {', '.join(sorted(VALID_SDF_OPERATIONS))}")
    for side in ("left", "right"):
        value = operation.get(side)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{label}.{side} must reference a primitive or previous operation")
        elif value not in known_ids:
            errors.append(f"{label}.{side} references unknown SDF id {value!r}")
    if operation_type == "smooth-union":
        _validate_positive(operation.get("radius"), f"{label}.radius", errors)
    if "id" in operation and "output" in operation:
        errors.append(f"{label}.id and output cannot both be set")
    output = operation.get("id", operation.get("output", f"operation-{index}"))
    if not isinstance(output, str) or not output.strip():
        errors.append(f"{label}.id/output must be a non-empty string when present")
    elif output in known_ids:
        field = "id" if "id" in operation else "output"
        errors.append(f"{label}.{field} duplicates existing SDF id {output!r}")
    else:
        known_ids.add(output)
    _validate_finite(operation, label, errors)


def validate_sdf_descriptor(component_id: str, descriptor: Any, errors: list[str]) -> None:
    """Append schema errors for an opt-in component SDF descriptor."""
    label = f"component {component_id!r} geometryDescriptor.sdf"
    if not isinstance(descriptor, dict):
        errors.append(f"{label} must be an object")
        return
    primitives = descriptor.get("primitives")
    if not isinstance(primitives, list) or not primitives:
        errors.append(f"{label}.primitives must be a non-empty array")
        return
    if len(primitives) > MAX_SDF_PRIMITIVES:
        errors.append(f"{label}.primitives must not contain more than {MAX_SDF_PRIMITIVES} entries")
    ids: set[str] = set()
    for index, primitive in enumerate(primitives):
        _validate_primitive(primitive, index, ids, errors)
    operations = descriptor.get("operations", [])
    if not isinstance(operations, list):
        errors.append(f"{label}.operations must be an array")
    else:
        if len(operations) > MAX_SDF_OPERATIONS:
            errors.append(f"{label}.operations must not contain more than {MAX_SDF_OPERATIONS} entries")
        for index, operation in enumerate(operations):
            _validate_operation(operation, index, ids, errors)
    resolution = descriptor.get("resolution")
    if not isinstance(resolution, int) or isinstance(resolution, bool) or resolution < 4:
        errors.append(f"{label}.resolution must be an integer from 4 to 64")
    elif resolution > 64:
        errors.append(f"{label}.resolution must not exceed 64")
    bounds = descriptor.get("bounds")
    if bounds is not None:
        if not isinstance(bounds, dict):
            errors.append(f"{label}.bounds must be an object")
        else:
            minimum = bounds.get("min")
            maximum = bounds.get("max")
            _validate_vector(minimum, f"{label}.bounds.min", errors)
            _validate_vector(maximum, f"{label}.bounds.max", errors)
            if isinstance(minimum, list) and isinstance(maximum, list) and len(minimum) == len(maximum) == 3:
                for index, (minimum_value, maximum_value) in enumerate(zip(minimum, maximum)):
                    if _is_number(minimum_value) and _is_number(maximum_value) and minimum_value >= maximum_value:
                        errors.append(f"{label}.bounds.min[{index}] must be less than bounds.max[{index}]")
    _validate_finite(descriptor, label, errors)
