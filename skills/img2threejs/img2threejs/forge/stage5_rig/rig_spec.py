"""RigSpec data model for the Milestone 0 rig kill test.

This is the schema from docs/PLAN_1.5_ANIMATION_READY_RIGS.md §6, transcribed
as-is (field names, optionality, semantics). It is NOT a competing schema —
where the plan's TypeScript type left something ambiguous for a 3-bone case,
the ambiguity and the reading chosen are called out explicitly below and in
forge/tests/test_rig_milestone0.py.

Pure Python 3.10+ stdlib. No pip installs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

BindPose = Literal["T", "A"]
Forward = Literal["+Z", "-Z"]
Role = Literal["skinned", "attachment"]
Chain = Literal["spine", "head", "arm", "leg", "tail", "wing", "digit", "prop"]


@dataclass
class Ellipsoid:
    center: tuple[float, float, float]
    axis: tuple[float, float, float]
    semi_axes: tuple[float, float, float]


@dataclass
class IkSpec:
    is_effector: bool
    target_bone_id: Optional[str] = None
    rotation_min: Optional[tuple[float, float, float]] = None
    rotation_max: Optional[tuple[float, float, float]] = None


@dataclass
class BoneSpec:
    """Mirrors PLAN_1.5 §6 `BoneSpec` field-for-field."""

    id: str
    parent: Optional[str]
    joint_pos: tuple[float, float, float]
    component: Optional[str]
    role: Role
    chain: Chain
    # Optional. "Defaults to the child's jointPos" per the plan. That default
    # is well-defined only when the bone has exactly one child. See
    # RigSpec.resolve_tip_positions() for the reading chosen when a bone has
    # zero children (a leaf) or more than one.
    tip_pos: Optional[tuple[float, float, float]] = None
    ellipsoids: list[Ellipsoid] = field(default_factory=list)
    ik: Optional[IkSpec] = None


@dataclass
class RigSpec:
    """Mirrors PLAN_1.5 §6 `RigSpec` field-for-field."""

    version: str
    bind_pose: BindPose
    forward: Forward
    bones: list[BoneSpec]

    def bone_by_id(self) -> dict[str, BoneSpec]:
        return {b.id: b for b in self.bones}

    def children_of(self, bone_id: str) -> list[BoneSpec]:
        return [b for b in self.bones if b.parent == bone_id]

    def root(self) -> BoneSpec:
        roots = [b for b in self.bones if b.parent is None]
        if len(roots) != 1:
            raise ValueError(
                f"RigSpec must have exactly one root bone (parent: null), found {len(roots)}"
            )
        return roots[0]

    def resolve_tip_positions(self) -> dict[str, tuple[float, float, float]]:
        """Resolve every bone's segment end point.

        READING CHOSEN (schema ambiguity, PLAN_1.5 §6):

        The plan says tipPos "Defaults to the child's jointPos" but does not
        say what happens for a bone with zero children (a leaf) or more than
        one child. The minimal reading adopted here, applied uniformly and
        fail-closed rather than silently guessing:

          - exactly one child, no explicit tipPos  -> default to that child's jointPos
          - explicit tipPos given                  -> always wins, no defaulting
          - zero children (leaf) and no tipPos      -> REJECTED. A leaf skinned
            bone has nothing to default from, so the spec author must supply
            tipPos explicitly. This is a spec-authoring responsibility, not
            something the emitter may invent (Pillar 2 — the emitter is
            deterministic code, it does not propose geometry).
          - more than one child and no tipPos        -> REJECTED. "the child's
            jointPos" is only well-defined for a single child; defaulting to
            an arbitrary one would be a silent, unreproducible choice.
        """
        by_id = self.bone_by_id()
        resolved: dict[str, tuple[float, float, float]] = {}
        for bone in self.bones:
            if bone.tip_pos is not None:
                resolved[bone.id] = bone.tip_pos
                continue
            children = self.children_of(bone.id)
            if len(children) == 1:
                resolved[bone.id] = by_id[children[0].id].joint_pos
            elif len(children) == 0:
                raise ValueError(
                    f"bone '{bone.id}' is a leaf with no tipPos: leaf bones must "
                    "author tipPos explicitly (PLAN_1.5 §6 default only covers "
                    "the single-child case)"
                )
            else:
                raise ValueError(
                    f"bone '{bone.id}' has {len(children)} children and no explicit "
                    "tipPos: the child-default is only well-defined for exactly one child"
                )
        return resolved


def validate_rig_spec(spec: RigSpec) -> list[str]:
    """Minimal semantic gate for Milestone 0 (a scaled-down stand-in for the
    full Joint Admission Gate Half A in PLAN_1.5 §5.2 — WS-B is out of scope
    here). Returns a list of error strings; empty list means valid.
    Fail-closed: callers must treat a non-empty list as a hard rejection.
    """
    errors: list[str] = []

    ids = [b.id for b in spec.bones]
    if len(ids) != len(set(ids)):
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        errors.append(f"NAME_UNIQUENESS: duplicate bone id(s) {dupes}")

    roots = [b for b in spec.bones if b.parent is None]
    if len(roots) != 1:
        errors.append(f"exactly one root bone required (parent: null), found {len(roots)}")

    id_set = set(ids)
    for bone in spec.bones:
        if bone.parent is not None and bone.parent not in id_set:
            errors.append(f"bone '{bone.id}' has unresolved parent '{bone.parent}'")

    if spec.version != "1.0":
        errors.append(f"unsupported RigSpec version '{spec.version}', expected '1.0'")

    if not errors:
        try:
            spec.resolve_tip_positions()
        except ValueError as exc:
            errors.append(str(exc))

    return errors


def derive_envelope_radius(
    width: float,
    depth: float,
    overlap_factor: float = 1.2,
) -> float:
    """PLAN_1.5 §4.3 — envelope radius is DERIVED, never proposed.

        R_b = 0.5 * max(W_component, D_component) * F

    `width`/`depth` are the component bounding-box extents perpendicular to
    the bone axis; `overlap_factor` is F (plan default 1.2).
    """
    if width <= 0 or depth <= 0:
        raise ValueError(f"component extents must be positive, got width={width} depth={depth}")
    if overlap_factor <= 0:
        raise ValueError(f"overlap_factor must be positive, got {overlap_factor}")
    return 0.5 * max(width, depth) * overlap_factor
