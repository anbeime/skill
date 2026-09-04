"""Runtime material-reference contracts for the img2threejs forge."""

from .reference import (
    MaterialReferenceError,
    build_assignment,
    load_reference,
    resolve_material,
    validate_reference,
)

__all__ = [
    "MaterialReferenceError",
    "build_assignment",
    "load_reference",
    "resolve_material",
    "validate_reference",
]
