# Procedural rigging contract — 1.5-alpha

The implementation-facing rig contract: what the payload owns, and what it deliberately does not.

## Payload ownership

The procedural TypeScript factory owns geometry and authored rig data. Python owns
deterministic validation and evidence packaging. The browser owns bone updates, skinning,
pose application, dynamic bounds, and final pixels.

| Layer | Required output | Failure action |
| --- | --- | --- |
| Spec | named joints, parent map, rest pose, sockets, pose probes | `refine-spec` |
| Forge | validated payload report and coverage warnings | block build |
| Three.js bind | one hierarchy, one skeleton, matching skin attributes | static fallback + `refine-code` |
| Deformation smoke | neutral plus stress poses, no NaN/Inf, bounded stretch/collapse | block likeness review |
| Browser evidence | fixed, orbit, profile and close-up screenshots | `request-input` or `refine-code` |

## Runtime invariants

- Use one shared `THREE.Skeleton` for all skinned meshes that share the character rig.
- Bind in rest pose before applying animation; do not treat a posed mesh as the bind pose.
- Update `skeleton.update()`/world matrices before measuring bounds or capturing a pose.
- Keep `skinIndex` and `skinWeight` attributes aligned with the geometry vertex count.
- Recompute or conservatively expand bounds after bone motion; a static load-time box may
  cull an animated limb or hair mass.
- Use semantic aliases only through an explicit map (`mixamo:LeftArm` → local joint id);
  never infer a joint from a string suffix alone.
- Keep auxiliary joints (ribbon, hair, skirt) explicitly tagged; their lack of direct
  surface influence is a warning, not an accidental missing bone.

## Pose probes before likeness

The first browser smoke set is intentionally mechanical:

- neutral rest pose;
- elbow flexion and shoulder abduction;
- hip/knee bend;
- wrist/ankle and hand/foot end-effector reach;
- head turn and spine bend;
- stylized hair/ribbon attachment check;
- `+35°`, `-35°`, profile and rear camera views.

These probes are deformation and attachment evidence, not reference likeness scores. A
rig must pass the deterministic payload gate and produce readable screenshots before
`diagnose_render.py`, comparison sheets, semantic scoring, or confidence claims.
