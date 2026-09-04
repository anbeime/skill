# Character Structure Decomposition

Use this reference when `objectClass.primaryDomain` is `character` or `hybrid`, alongside
`grimoire/character/reconstruction.md`. That document fixes *proportions and landmarks*;
this one fixes *what parts exist and how each one is built and rigged*.

A character that has every part but no layer discipline produces the same failure every
time: rigid jewellery clipping through skin, membranes tearing at seams, holes that were
modelled as geometry instead of subtracted, and details invented from nothing. The layer
system exists to make each of those a classification error you can catch, not a judgement
call.

## The Layer Ontology

Nine layers. Every part of every character belongs to exactly one **primary geometry
layer** and may additionally carry **modifier layers**.

| Layer | Definition | Membership test | Build method | Rig treatment |
|---|---|---|---|---|
| **L-1 Proportion Scaffold** | Bounding volumes + head-unit system that fix overall silhouette | Not a part — a constraint every part is clamped into | Math bounds only | none |
| **L0 Core Volume** | The continuous central mass: head, torso, limbs | Crosses joints; cannot be detached | Implicit SDF smooth-union → marching cubes | `SkinnedMesh`, spatial `W(p)` falloff |
| **L1 Deformable Appendages** | Elongated parts extending off L0 that must bend along their length: tail, wings, long ears | Crosses joints; has its own bone chain reaching outside the core volume | Sweep / loft along a spline | `SkinnedMesh`, same skeleton, same `W(p)` |
| **L-Void Negative Space** | Subtractive volumes: mouth cavity, ear concha, torn hems, pierced holes | Produces no visible surface; only removes | SDF difference / CSG subtract | none |
| **L2 Internal Cavities** | Parts that sit inside an L-Void: eyes, teeth, tongue, gums | Only visible because something was subtracted | Primitives, inverted-normal shells | Tongue skinned; eyes/teeth single-bone (see L3) |
| **L3 Single-Bone Isolates** | Anything whose whole extent lies inside one bone's dominant region: horns, claws, hooves, cuffs, rings, tail spade | **Does not cross a joint** | Primitives, lathe, extrude, boolean | `SkinnedMesh` with weight forced to `(1,0,0,0)` |
| **L4 Cross-Joint Shells** | Offset layers over L0 that span a joint: loincloth, tunic, cape, armour plates spanning a limb | Crosses joints, sits outside the skin surface | Offset shell from L0 + trim | `SkinnedMesh`, spatial `W(p)` |
| **L5 Surface Markings** | Colour that does not change silhouette: stripes, scars, tattoos, gradients | Zero geometric footprint | Shader mixing on spatial function (§ Markings) | inherits host mesh |
| **L6 VFX / Ephemera** | Non-material elements: fire, smoke, glow | No solid geometry at all | Sprites, particles, scrolling-UV meshes | Emitter parented to a bone |
| **L-Proxy Collision** | Invisible primitives for raycast/physics | Never rendered | Box / capsule / sphere | Parented to bones; already modelled by `root.userData.sculptRuntime.colliders` |

## The Classification Test That Actually Matters

The naive test is "is this part hard or soft?" That test is wrong and it produces the
clipping bug.

The real test is **does this part cross a joint?**

Because weights are a pure spatial function `W(p_world)` (see
`docs/PLAN_1.5_ANIMATION_READY_RIGS.md` §3), a mesh lying entirely inside one bone's
dominant region *automatically* receives `≈(1,0,0,0)` and therefore *automatically* moves
rigidly. Rigid and skinned converge. There is no second code path.

Consequences:

- A gold cuff placed mid-forearm is skinned, and moves rigidly anyway. Nothing special
  needed.
- A gold cuff placed **at the wrist** picks up a blend of forearm and hand — the metal
  visibly squashes. Fix: tag it `L3` and **override** every one of its vertices to weight
  `1.0` on the bone nearest its bounding-box centre, bypassing the falloff. It stays a
  `SkinnedMesh` sharing one shader; it is simply permanently rigid.
- Do **not** solve clipping by making rigid parts skinned in the general case. That
  trades a clipping bug for a stretching-metal bug.

Soft goods (L4) need the opposite reasoning. A loincloth sits 1–2 cm off the skin, so its
vertices are not coincident with skin vertices — but that offset is deep inside the
hip/thigh envelope, so `W(p_cloth) ≈ W(p_skin)` and the cloth follows the leg correctly
without copying weights from anywhere. If the cloth gets its own secondary bones for
sway, those bones join the **same** skeleton but must be given a very small envelope
radius, so no skin vertex ever falls inside their influence.

## Primary + Modifier Rule

Some parts genuinely feel like they belong to two layers. Resolve it, don't debate it:

> Each part is assigned exactly **one** primary geometry layer (L0, L1, L2, L3, L4, L6),
> which determines how it is built and skinned. It may additionally carry any number of
> **modifier** layers (L-1, L-Void, L5, L-Proxy).

- Ear = primary **L1** + modifier **L-Void** (concha cavity)
- Loincloth = primary **L4** + modifier **L-Void** (torn hem)
- Tail spade and tail ring = primary **L3**, parented to the last bone of the tail's L1
  chain — a rigid tip on a deformable chain is not ambiguous, it is two parts
- Purple shoulder stripes = modifier **L5** on the L0 host

## Ontology Order ≠ Execution Order

The table above reads inside-out. The build DAG does not. In particular L-Void must enter
the SDF **before** meshing, so it cannot run "after" L1.

1. **Scaffold** — establish L-1 bounds; derive joint positions.
2. **Field construction** *(parallel)* — build the SDF equations for L0, L1, L4. No
   surfaces yet.
3. **Subtraction** *(choke point)* — apply every L-Void operator to those fields.
4. **Meshing** — marching cubes / dual contouring → `BufferGeometry`.
5. **Discrete geometry** *(parallel)* — instantiate L2 and L3 primitives.
6. **Skinning** — evaluate `W(p_world)` for every vertex; apply L3 weight overrides;
   attach L-Proxy colliders.
7. **Appearance** — apply L5 shader mixing and L6 emitters.

## Markings Without Textures

L5 must not use vertex colours on an implicit-surface mesh. Marching-cubes topology is
irregular, so vertex-interpolated colour bands and produces jagged transitions instead of
a gradient.

Mix in the shader from a spatial function instead, via `onBeforeCompile`:

```glsl
// object-space gradient, e.g. magenta body → orange muzzle/chin
float g = smoothstep(zStart, zEnd, vPosition.z) * smoothstep(yStart, yEnd, -vPosition.y);
diffuseColor.rgb = mix(colorBase, colorAccent, g);
```

This is topology-independent, needs no texture file, and stays diffable.

## Layers Deliberately Excluded

Studio pipelines carry these; a code-only Three.js generator should not.

| Excluded | Why |
|---|---|
| Strand-level hair / fur / feather grooming | Draw-call and simulation cost far beyond a code generator. Force it into solid masses under L1 or L3 |
| Secondary/tertiary form passes (wrinkle maps, pore maps) | Requires multi-million-poly sculpting and baking. Approximate in L5 material terms |
| LOD chains | Real in AAA, but the pipeline has no LOD concept and a showcase does not need one. Revisit only if a demo demonstrably needs it — do not make it a handoff gate |
| Bone naming as a *layer* | It is a rule, not a layer. Enforce it in L-1 metadata |

## Worked Coverage Test — stylized imp / mini-dragon

Reference: `vijay-ghume-mini-dragon-{ref,1..5}.jpg` — 2D concept plus five 3D views
(front, front-¾, rear-¾, side, rear). This character is the stress test for the system
because it contains at least one part from every layer.

| Part | Primary | Modifiers | Build | Bone | Material zone |
|---|---|---|---|---|---|
| Head, torso, arms, legs | L0 | L-1, L5 | SDF smooth-union | spine / limb chains | magenta skin |
| Tail (root → pre-tip) | L1 | — | curve sweep | tail chain | magenta skin |
| Wing membranes ×2 | L1 | L-Void (ragged trailing edge) | surface spanned between spar splines | wing chains | pink membrane |
| Wing leading edge + 3 spars ×2 | L1 | — | tube sweeps | wing chains | black |
| Ears ×2 | L1 | L-Void (concha) | flattened cone shell | ear bones | magenta / orange inner |
| Mouth bag | L2 | depends on L-Void | inverted-normal shell | head / jaw | dark interior |
| Eyes ×2 | L2 | L5 (iris/sclera) | spheres | eye or head | yellow-orange iris, violet corner |
| Fangs — 4 upper canines pointing **down**, 2 per side | L2 | — | cones | maxilla / head | white |
| Horns ×2 (long, swept back) | L3 | — | tapered tube | head | black |
| Hand claws | L3 | — | curved cones | finger bones | black |
| Wing wrist claws ×2 | L3 | — | curved cone | wing wrist | black |
| Cloven hooves ×2 | L3 | — | split solid | foot bones | black |
| Ear hoop | L3 | — | torus | ear bone | gold |
| Neck strap + hanging ring pendant | L3 | — | torus + strap loop | chest / neck | brown leather, gold |
| Forearm cuffs ×2 (gold ring / black band / gold ring) | L3 | — | stacked cylinders | lower arm | gold + black |
| Ankle rings ×2 | L3 | — | cylinder | lower leg | gold |
| Tail ring | L3 | — | cylinder | tail tip | gold |
| Tail spade | L3 | — | extruded arrow | tail tip | pink |
| Loincloth + brown belt | L4 | L-Void (torn hem, open back) | offset shell + trim | hips (+ optional sway bones) | navy cloth, brown leather |
| Purple stripes (3 per upper arm, 2 per scapula) | — | L5 on L0 | shader mix | inherits | violet |
| Fire | L6 | — | sprites / particles | head, hips, wrists, tail | emissive |
| Hitboxes | L-Proxy | — | capsules | major bones | not rendered |

### Two findings this test surfaced

- **There is no mane.** The black mass appearing between the horns in the rear-¾ view is
  the far wing folded forward — it has a hook (the wing wrist claw) and a sliver of pink
  membrane beside it. The pure rear view shows the nape and spine are smooth pink. A
  generator that emits a mane is hallucinating; reject it.
- **There are no scales.** All five 3D views show completely smooth skin with soft muscle
  forms only. The demo's `dragon-skin_*` / `dragon-body-skin_*` texture set contradicts the
  reference and should not be carried forward.

### Measured proportions

Total height `H` = crown to hoof, **excluding horns and wings**. These are read off the
front and rear views; the inferred rows are marked because the pose foreshortens them.

| Measure | Ratio of H | Source |
|---|---|---|
| Head height | **0.33** | measured |
| Skull width (no ears) | 0.25–0.28 | measured |
| Total width including flared ears | 0.45–0.50 | measured |
| Neck length | 0.05 | measured — chin nearly on chest |
| Torso, shoulder → hip | 0.35 | measured |
| Leg, hip → hoof | 0.27 | measured |
| Shoulder span | 0.35 | measured |
| Arm, shoulder → wrist | ~0.45 | inferred (foreshortened) |
| Wingspan | 1.5–1.8 | inferred (wings folded) |
| Tail length | 0.8–0.9 | inferred (curled) |

Total ≈ **3 head-units** — the chibi/figurine end of the scale in
`reconstruction.md`. Head height + neck + torso + legs sums to 1.00, which is the
consistency check.

**Use skull width, not total width, for the L-1 scaffold.** Ears are L1 and are explicitly
allowed to extend beyond the core volume's bounds. Scaffolding to the ear span produces a
head like a barrel.

### Material recipe for smooth stylized skin

`MeshPhysicalMaterial`: `roughness` 0.5–0.6, `metalness` 0.0, `clearcoat` 0.15 with
`clearcoatRoughness` 0.6, `sheen` 1.0 with a pink-violet `sheenColor` for the rim
falloff.

Forbidden for this character: any noise-derived `normalMap` or `bumpMap`. The surface
reads as smooth rubber; let the subdivided geometry carry the form.

## Structural Completeness Checklist

A character is structurally complete when all of the following hold. Every line is
checkable by code or by direct inspection.

1. Every component in the spec maps to exactly one primary geometry layer.
2. The core volume's bounding box fits entirely inside the L-1 proportion scaffold.
3. Every L-Void operator was applied to the SDF **before** meshing, not after.
4. No degenerate faces (area ≈ 0) along any L-Void-trimmed edge.
5. Bone names follow the project naming convention and are unique.
6. Every bone's `scale` is `(1,1,1)` at bind pose, with identity rest rotation.
7. No vertex has more than four non-zero influences.
8. Every vertex's weights sum to 1.0 within `1e-5`, and no vertex has a zero sum.
9. Every L3 part, and every rigid L2 part, carries a forced single weight of 1.0.
10. At L0↔L1 seams, paired vertices are spatially coincident within `1e-4`.
11. Pose sweep passes: at 90° joint flexion the bounding sphere neither collapses nor
    diverges, and no vertex lands on the origin.
12. Every joint centre lies inside the built volume (allow ≤5% of bbox outside for parts
    under armour or clothing).
13. No L4 shell clips through L0 anywhere in the pose sweep.
14. L-Proxy colliders exist for every physics- or raycast-relevant bone, exposed through
    `root.userData.sculptRuntime.colliders`.
15. Every part in the spec traces to an `evidenceRef` in an admitted reference view — and
    any part that cannot is deleted, not guessed.

## Predicted Failure Points

The three things a generator gets wrong most often on a character like this:

- **Wing membrane built as a flat sheet intersecting the spar tubes** instead of a surface
  spanned *between* the spars. Detect by checking normals at the membrane–spar boundary: a
  sudden perpendicular flip is an intersection, not an organic join.
- **Degenerate polygons along the torn loincloth hem**, from the boolean trim. Detect by
  scanning triangle areas on the emitted geometry.
- **Inner thighs webbing together.** The legs are short and thick, so left and right thigh
  are spatially close at bind pose and the spatial falloff bleeds weight across. Detect in
  the pose sweep: lift one leg and measure displacement on the other. If the planted leg
  moves, the envelope overlap factor `F` is too high.

## Gate Notes

Layer assignment is spec data and must be validated in
`forge/stage2_spec/validate_sculpt_spec.py` — a part with no primary layer, or with two,
is a rejected spec. Items 6–13 of the checklist are exactly what the pose-sweep rig gate
in `docs/PLAN_1.5_ANIMATION_READY_RIGS.md` §7 measures; item 15 is the existing
detail-inventory evidence discipline applied to structure.
