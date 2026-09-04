MAX_SUBDIVISION_ITERATIONS = 4
MAX_SUBDIVISION_QUAD_FACES = 100_000

CYLINDER_RADIAL_SEGMENTS = 48
CYLINDER_HEIGHT_SEGMENTS = 16
ATTACHMENT_CYLINDER_RADIAL_SEGMENTS = 32
ATTACHMENT_CYLINDER_HEIGHT_SEGMENTS = 12
CONE_SUBDIVISION_TOP_RADIUS = 0.0001
# A tapering ConeGeometry, unlike a constant-radius CylinderGeometry, does not weld
# cleanly at CYLINDER_HEIGHT_SEGMENTS (16): measured 2448 raw / 2160 welded boundary
# edges (a real topology defect, not a benign UV seam -- box/cylinder/sphere/torus/
# ellipsoid all weld to 0/0 at their own segment counts). A cone built with
# heightSegments=1 (three.js's own default) welds cleanly to 0/0, verified directly;
# a solid cone's lateral surface does not need internal height rings for shading or
# silhouette quality at rest, only the subdivision-requested substitute (a near-
# degenerate CylinderGeometry, unaffected by this constant) needs a denser cage.
CONE_HEIGHT_SEGMENTS = 1
SPHERE_WIDTH_SEGMENTS = 64
SPHERE_HEIGHT_SEGMENTS = 40
CAPSULE_CAP_SEGMENTS = 16
CAPSULE_RADIAL_SEGMENTS = 32
TORUS_TUBULAR_SEGMENTS = 24
TORUS_RADIAL_SEGMENTS = 96
PLANE_WIDTH_SEGMENTS = 24
PLANE_HEIGHT_SEGMENTS = 24


# --- Tessellation tiers -------------------------------------------------------
#
# The constants above are the `hero` tier and stay the module-level defaults, so
# every existing caller keeps its current output byte-for-byte. A spec that wants
# a cheaper mesh selects a tier via `performanceBudget.targetTriangles`, which
# was already in the schema and read by nothing (`lodPlan` has the same problem;
# see decimate.py's docstring).
#
# Two floors are load-bearing and are asserted by `validate_tier()`:
#
# * HEIGHT segments >= MIN_JOINT_HEIGHT_SEGMENTS on anything a bone deforms. One
#   quad spanning a joint leaves no vertex at the pivot, so the influenced region
#   skips the joint entirely and the elbow collapses instead of bending.
#
#   The value is 4, not the 3 of the standard "rule of three" (one loop on the
#   joint plane, one supporting loop each side). External practice says 3 is the
#   minimum; this repository already decided 3 was not enough. `emit_rig.py:399`
#   derives its own ring count as `max(4, ceil(cyl_length / target_ring_spacing))`
#   -- a hard floor of 4 -- in the same module whose NOTES.md documents the
#   single-quad-band joint-pinch failure this floor exists to prevent. Where an
#   in-repo measurement and an external rule of thumb disagree, the measurement
#   wins, so this matches emit_rig.py rather than the textbook.
# * RADIAL segments >= MIN_RADIAL_SEGMENTS, below which a swept primitive stops
#   reading as a round limb and the silhouette goes visibly polygonal.
MIN_JOINT_HEIGHT_SEGMENTS = 4
MIN_RADIAL_SEGMENTS = 6

# Deliberately NOT tiered. A tapering cone does not weld cleanly at higher height
# segment counts -- 2448 raw / 2160 welded boundary edges, a real topology defect,
# see the comment on CONE_HEIGHT_SEGMENTS above -- and 1 is the value that welds to
# 0/0. `validate_tier()` pins it so a future tier cannot quietly reintroduce that
# defect while chasing a triangle budget.
REQUIRED_CONE_HEIGHT_SEGMENTS = 1

TESSELLATION_TIERS: dict[str, dict[str, int]] = {
    "low": {
        "CYLINDER_RADIAL_SEGMENTS": 10,
        "CYLINDER_HEIGHT_SEGMENTS": 4,
        "ATTACHMENT_CYLINDER_RADIAL_SEGMENTS": 8,
        "ATTACHMENT_CYLINDER_HEIGHT_SEGMENTS": 4,
        "CONE_HEIGHT_SEGMENTS": 1,
        "SPHERE_WIDTH_SEGMENTS": 16,
        "SPHERE_HEIGHT_SEGMENTS": 10,
        "CAPSULE_CAP_SEGMENTS": 4,
        "CAPSULE_RADIAL_SEGMENTS": 8,
        "TORUS_TUBULAR_SEGMENTS": 8,
        "TORUS_RADIAL_SEGMENTS": 16,
        "PLANE_WIDTH_SEGMENTS": 4,
        "PLANE_HEIGHT_SEGMENTS": 4,
        "BOX_SEGMENTS": 1,
        "SDF_MAX_RESOLUTION": 24,
    },
    "standard": {
        "CYLINDER_RADIAL_SEGMENTS": 24,
        "CYLINDER_HEIGHT_SEGMENTS": 8,
        "ATTACHMENT_CYLINDER_RADIAL_SEGMENTS": 16,
        "ATTACHMENT_CYLINDER_HEIGHT_SEGMENTS": 6,
        "CONE_HEIGHT_SEGMENTS": 1,
        "SPHERE_WIDTH_SEGMENTS": 32,
        "SPHERE_HEIGHT_SEGMENTS": 20,
        "CAPSULE_CAP_SEGMENTS": 8,
        "CAPSULE_RADIAL_SEGMENTS": 16,
        "TORUS_TUBULAR_SEGMENTS": 12,
        "TORUS_RADIAL_SEGMENTS": 48,
        "PLANE_WIDTH_SEGMENTS": 12,
        "PLANE_HEIGHT_SEGMENTS": 12,
        "BOX_SEGMENTS": 4,
        "SDF_MAX_RESOLUTION": 40,
    },
    "hero": {
        "CYLINDER_RADIAL_SEGMENTS": CYLINDER_RADIAL_SEGMENTS,
        "CYLINDER_HEIGHT_SEGMENTS": CYLINDER_HEIGHT_SEGMENTS,
        "ATTACHMENT_CYLINDER_RADIAL_SEGMENTS": ATTACHMENT_CYLINDER_RADIAL_SEGMENTS,
        "ATTACHMENT_CYLINDER_HEIGHT_SEGMENTS": ATTACHMENT_CYLINDER_HEIGHT_SEGMENTS,
        "CONE_HEIGHT_SEGMENTS": CONE_HEIGHT_SEGMENTS,
        "SPHERE_WIDTH_SEGMENTS": SPHERE_WIDTH_SEGMENTS,
        "SPHERE_HEIGHT_SEGMENTS": SPHERE_HEIGHT_SEGMENTS,
        "CAPSULE_CAP_SEGMENTS": CAPSULE_CAP_SEGMENTS,
        "CAPSULE_RADIAL_SEGMENTS": CAPSULE_RADIAL_SEGMENTS,
        "TORUS_TUBULAR_SEGMENTS": TORUS_TUBULAR_SEGMENTS,
        "TORUS_RADIAL_SEGMENTS": TORUS_RADIAL_SEGMENTS,
        "PLANE_WIDTH_SEGMENTS": PLANE_WIDTH_SEGMENTS,
        "PLANE_HEIGHT_SEGMENTS": PLANE_HEIGHT_SEGMENTS,
        "BOX_SEGMENTS": 12,
        "SDF_MAX_RESOLUTION": 64,
    },
}

DEFAULT_TESSELLATION_TIER = "hero"

# Measured, not guessed: a 61-component humanoid spec generated at `hero` builds
# 14,208 triangles (counted by constructing the emitted factory under node, not
# by parsing the source). The same primitive mix at each tier, using three.js's
# own triangle formulas, is what these thresholds are drawn from.
TIER_TRIANGLE_CEILINGS: tuple[tuple[int, str], ...] = (
    (6_000, "low"),
    (60_000, "standard"),
)


def tier_for_target_triangles(target_triangles: object) -> str:
    """Pick a tessellation tier from `performanceBudget.targetTriangles`.

    Anything missing, non-numeric or non-positive keeps the current behaviour
    (`hero`), so specs written before this existed are unaffected.
    """
    if isinstance(target_triangles, bool) or not isinstance(target_triangles, (int, float)):
        return DEFAULT_TESSELLATION_TIER
    if target_triangles <= 0:
        return DEFAULT_TESSELLATION_TIER
    for ceiling, tier in TIER_TRIANGLE_CEILINGS:
        if target_triangles <= ceiling:
            return tier
    return DEFAULT_TESSELLATION_TIER


def validate_tier(name: str) -> dict[str, int]:
    """Return a tier's segment table, refusing one that would break deformation."""
    if name not in TESSELLATION_TIERS:
        raise ValueError(
            f"unknown tessellation tier {name!r}; expected one of {sorted(TESSELLATION_TIERS)}"
        )
    table = TESSELLATION_TIERS[name]
    for key in ("CYLINDER_HEIGHT_SEGMENTS", "ATTACHMENT_CYLINDER_HEIGHT_SEGMENTS"):
        if table[key] < MIN_JOINT_HEIGHT_SEGMENTS:
            raise ValueError(
                f"tier {name!r} sets {key}={table[key]}, below the "
                f"{MIN_JOINT_HEIGHT_SEGMENTS}-segment floor a bone needs to deform a joint"
            )
    for key in (
        "CYLINDER_RADIAL_SEGMENTS",
        "ATTACHMENT_CYLINDER_RADIAL_SEGMENTS",
        "CAPSULE_RADIAL_SEGMENTS",
    ):
        if table[key] < MIN_RADIAL_SEGMENTS:
            raise ValueError(
                f"tier {name!r} sets {key}={table[key]}, below the "
                f"{MIN_RADIAL_SEGMENTS}-segment floor a swept primitive needs to read as round"
            )
    if table["CONE_HEIGHT_SEGMENTS"] != REQUIRED_CONE_HEIGHT_SEGMENTS:
        raise ValueError(
            f"tier {name!r} sets CONE_HEIGHT_SEGMENTS={table['CONE_HEIGHT_SEGMENTS']}; a cone "
            f"only welds cleanly at {REQUIRED_CONE_HEIGHT_SEGMENTS} and this is not a budget knob"
        )
    return table


def segments_for_spec(spec: object) -> dict[str, int]:
    """Resolve the segment table a spec should generate with."""
    budget = spec.get("performanceBudget") if isinstance(spec, dict) else None
    target = budget.get("targetTriangles") if isinstance(budget, dict) else None
    return validate_tier(tier_for_target_triangles(target))


def cylinder_source_face_count(radial_segments: int, height_segments: int) -> int:
    return radial_segments * (height_segments + 1)


def capsule_source_face_count(cap_segments: int, radial_segments: int, height_segments: int = 1) -> int:
    """Return the exact triangle count emitted by `buildWatertightCapsule` in
    generate_threejs_factory.py, which replaced THREE.CapsuleGeometry as the capsule
    primitive's construction (see that file's `geometry_for()` and the
    `buildWatertightCapsule` helper it emits). Raw THREE.CapsuleGeometry duplicates
    every UV-seam vertex, same benign pattern as box/cylinder/sphere/torus -- it is
    NOT actually non-manifold (a naive vertex-only mergeVertices() reports 64 such
    edges, but that is a counting artifact from degenerate near-pole triangles, not
    a real defect; confirmed by replicating subdivideCatmullClark's own degenerate-
    aware vertex identity). `buildWatertightCapsule` is worth having regardless: it
    is closed by construction (shared poles, radial index taken `% radialSegments`)
    rather than relying on a weld, and has a smaller, exact triangle count: 2 pole
    fans of `radial_segments` triangles each, plus `(2*cap_segments + height_segments
    - 2)` ring bands of `2*radial_segments` triangles each -- fewer vertices for the
    per-vertex skinning weight pass to visit. `height_segments` defaults to 1,
    matching the one call site.
    """
    return 2 * radial_segments * (2 * cap_segments + height_segments - 1)


def resolve_instanced_cluster_base(
    primitive: str,
    descriptor: dict[str, object],
    valid_primitives: set[str],
) -> str:
    if primitive != "instanced-cluster":
        return primitive
    base = descriptor.get("baseGeometry")
    if isinstance(base, str) and base not in {"", "instanced-cluster"} and base in valid_primitives:
        return base
    return "box"


SUBDIVISION_SOURCE_FACE_ESTIMATES: dict[str, int] = {
    "box": 6,
    "sphere": 2 * SPHERE_WIDTH_SEGMENTS * SPHERE_HEIGHT_SEGMENTS,
    "ellipsoid": 2 * SPHERE_WIDTH_SEGMENTS * SPHERE_HEIGHT_SEGMENTS,
    "cylinder": cylinder_source_face_count(CYLINDER_RADIAL_SEGMENTS, CYLINDER_HEIGHT_SEGMENTS),
    "cone": cylinder_source_face_count(CYLINDER_RADIAL_SEGMENTS, CYLINDER_HEIGHT_SEGMENTS),
    "capsule": capsule_source_face_count(CAPSULE_CAP_SEGMENTS, CAPSULE_RADIAL_SEGMENTS),
    "torus": 2 * TORUS_TUBULAR_SEGMENTS * TORUS_RADIAL_SEGMENTS,
    "plane-card": 2 * PLANE_WIDTH_SEGMENTS * PLANE_HEIGHT_SEGMENTS,
}
ATTACHMENT_CYLINDER_SUBDIVISION_SOURCE_FACES = cylinder_source_face_count(
    ATTACHMENT_CYLINDER_RADIAL_SEGMENTS,
    ATTACHMENT_CYLINDER_HEIGHT_SEGMENTS,
)
