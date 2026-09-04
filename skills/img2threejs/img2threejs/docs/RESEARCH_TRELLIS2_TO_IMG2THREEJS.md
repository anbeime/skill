# TRELLIS.2 → img2threejs: what transfers, what must not

Research note, 2026-07-30. Question asked: *how does img2threejs get closer to the fidelity of an
image-to-3D generative system like TRELLIS.2 while its output stays a semantic, editable,
animation-ready `THREE.Group`?*

Sources read for TRELLIS.2: the repo README, the project page, the paper (arXiv 2512.14692,
*Native and Compact Structured Latents for 3D Generation*), and
`trellis2/pipelines/trellis2_image_to_3d.py`. I did **not** clone or run the CUDA source
(FlexGEMM / CuMesh / o-voxel); claims about internals below come from the paper and that pipeline
file, and are labelled where they are inference rather than quotation.

Sources read for img2threejs: this checkout — `SKILL.md`, `docs/ARCHITECTURE.md`, `ROADMAP.md`,
`forge/stage1_intake/*`, `forge/stage2_spec/validate_sculpt_spec.py` (the real schema),
`forge/stage3_build/*`, `forge/stage4_review/*`, `forge/_shared/*`, and the working review
apparatus in the sibling `img2threejs-showcase` checkout.

---

## 0. Thesis

The two systems fail in opposite directions.

- **TRELLIS.2 has maximal representational capacity and zero semantics.** Its output is one
  `MeshWithVoxel`. No parts, no pivots, no sockets, no skeleton. Any shape is representable; nothing
  is editable.
- **img2threejs has maximal semantics and minimal representational capacity.** Its output is a
  `THREE.Group` of named parts drawn from **14 primitive kinds**
  (`VALID_PRIMITIVES` in `validate_sculpt_spec.py:38`). Everything is editable; a large class of
  shapes is not representable — and, critically, **nothing in the pipeline detects
  "inexpressible"**. It only detects "this render scored low", which is a different fact.

So the fidelity gap is not primarily a review-loop problem. It is:

1. a **representation-expressiveness** problem (§2.1, §4), and
2. a **correction-granularity** problem — the loop re-decides at whole-object fidelity and
   regenerates the whole factory (§6).

Three transfers close most of the gap without giving up the Group:

- **A two-layer representation.** Add a dense per-part field layer that is a *fitting and measuring
  target*, never the output. The semantic layer stays authoritative for hierarchy; the dense layer
  becomes authoritative for shape. That is O-Voxel's role, scoped per part, at 32³–128³ instead of
  1536³ — cheap enough for stdlib Python.
- **TRELLIS's conditional stage ordering.** structure → geometry → appearance, where appearance is
  *conditioned on final geometry* and is never allowed to compensate for it.
- **Localized correction.** Move the loop's unit of decision from the object to the
  `(view, component, feature)` cell, and regenerate only the failing part's module.

None of this requires running TRELLIS.2 or O-Voxel.

---

## 1. What TRELLIS.2 actually does

### 1.1 Geometry — O-Voxel ("omni-voxel")

A sparse voxel grid where each occupied voxel carries a tuple: **geometry features** (dual vertex
position, edge-intersection flags, splitting weights) + **material features** (base colour, metallic,
roughness, opacity) + integer coordinates on an N³ grid.

The load-bearing property is stated in the abstract: O-Voxel *"can robustly model arbitrary topology,
including open, non-manifold, and fully-enclosed surfaces"*. It is **field-free** — no SDF, no
Flexicubes, no iso-surface. That is why it handles cloth and leaves.

**This is the single most relevant claim for img2threejs.** An SDF cannot represent a zero-thickness
membrane; it must thicken it. img2threejs's `implicit` topologyClass and
`_shared/sdf_primitives.py` inherit exactly that limit, and it is precisely the limit that bites on a
dragon wing membrane, a cape, a leaf, or a fin.

The *Flexible Dual Grid* — "one vertex per primal cell and one quadrilateral face per primal edge" —
is what preserves sharp edges where marching cubes would round them.

Conversion mesh↔O-Voxel is described as instant, "fully rendering-free and optimization-free".

### 1.2 Compression — Sparse Compression VAE

16× spatial downsampling, sparse residual autoencoding (eight children aggregated into the channel
dimension), early-pruning upsampling. A 1024³ textured asset becomes ~9.6K latent tokens.

The transferable point is not the VAE. It is that **the inter-stage message is compact and lossy in a
characterised way**. img2threejs's inter-stage message is the spec JSON, which is compact — but its
loss of shape information is *uncharacterised*. Nobody can say how much of the subject the spec
cannot express.

### 1.3 Stage decomposition — from the source, not the README

`trellis2/pipelines/trellis2_image_to_3d.py`:

```
preprocess_image  →  get_cond
  → sample_sparse_structure(cond, resolution)              # occupancy layout only
  → sample_shape_slat / sample_shape_slat_cascade(cond, coords)
  → decode_shape_slat                                      # mesh + substructures
  → sample_tex_slat(cond, shape_slat as concat_cond)        # PBR, conditioned on geometry
  → decode_tex_slat → decode_latent
```

Three facts worth stealing outright:

- **(a) Structure is solved before shape.** A separate, cheap model decides *where matter is* before
  anything decides *what shape it has*.
- **(b) Appearance is conditioned on final geometry**, passed in as `concat_cond`. Materials are
  never sampled concurrently with geometry.
- **(c) The `_cascade` variants exist only for 1024/1536.** High resolution is reached by *refining a
  converged lower-resolution result*, never by generating at target resolution directly.

### 1.4 PBR

`baseColor`, `metallic`, `roughness`, `alpha` as **per-voxel surface attributes**, not a UV texture —
relightable by construction. Note the honest caveat in their README: the exported `.glb` is
`OPAQUE` by default even though alpha survives in the texture. Even TRELLIS treats transparency as a
downstream authoring decision rather than a solved output property.

### 1.5 What must not transfer

4B parameters, H100-class GPU, ≥24 GB VRAM, CUDA 12.4, Linux, FlexGEMM/CuMesh/nvdiffrast. And more
importantly the *shape of the output*: one mesh. Running TRELLIS.2 inside img2threejs would hand
img2threejs exactly the artifact it exists to avoid. Its only legitimate role is as an **optional
dense evidence layer to fit against** (MA4 in §10).

---

## 2. Transferable ideas, and where each lands

| TRELLIS.2 mechanism | Why it works | img2threejs transfer | Touches |
|---|---|---|---|
| Field-free representation | open / non-manifold / enclosed surfaces are native | new `open-shell` topology class + a **part-shell field** with an explicit two-sided zero-thickness mode; SDF stays for solids only | new `_shared/part_shell.py`; `validate_sculpt_spec.py:58` (`VALID_TOPOLOGY_CLASSES`) |
| Sparse-structure stage runs first | proportion and layout are settled before detail | promote `visual_hull.py` from an optional `geometryDescriptor` to a **mandatory Stage-S1 occupancy artifact**, and use it as the bbox/proportion oracle | `stage3_build/visual_hull.py` → new `forge/stage2_structure/` |
| Dual grid preserves sharp edges | no marching-cubes rounding | never mesh-extract as the primary path: keep the parametric profile and *fit* it to the field | `_shared/subdivision.py`, new fitter |
| `_cascade` refinement | refine what has converged, not everything | **per-component refinement budget**: only components whose cell failed get re-generated | `stage3_build/orchestrate_passes.py`, `stage3_build/module_cache.py` |
| Appearance conditioned on geometry | material cannot paper over shape error | **hard ordering gate**: `material-pass` is illegal for a component whose geometry cell has not converged | `orchestrate_passes.py:387-420` |
| Compact structured latent as the only inter-stage message | stages cannot reach behind each other | S3S (§3) becomes the *only* channel between stages, hashed per stage | `stage2_spec/*`, new provenance block |
| PBR as per-point attributes | relightable, channels independent | per-part attribute maps (vertex colour / small `DataTexture`) with per-channel `source` + `confidence` | `stage1_intake/extract_pbr_evidence.py`, `analyze_texture.py` |

---

## 3. The Structured 3D Spec (S3S)

Design it as a **strict superset of `ObjectSculptSpec`**, `schemaVersion: 2`, so every v1.5 spec
migrates by addition. Emit two artifacts from one source of truth: TypeScript interfaces for the
runtime/codegen contract, JSON Schema for the Python validator.

```ts
export interface StructuredSpec {
  schemaVersion: 2;
  provenance: Provenance;
  subject: Subject;                 // class, complexity tier, qualityContract (unchanged)
  frame: Frame;                     // NEW — explicit world contract
  structure: Structure;             // NEW — the S1 occupancy solve
  parts: Part[];                    // replaces componentTree (tree via parentId)
  materials: MaterialSpec[];
  articulation: Articulation;       // NEW — was scattered across actionProfile/attachment
  evidence: EvidenceBundle;         // detailInventory, referencePbr, localSpecSearch, cs2Intake
  review: ReviewBlock;              // featureReviewTargets + reviewHistory (unchanged)
}

export interface Provenance {
  referenceHashes: Record<string, string>;   // path → sha256
  specHash: string;
  stageStamps: Array<{ stage: StageId; inputHash: string; outputHash: string }>;
  /** A stage may read ONLY the previous stage's outputHash artifact + evidence. */
  sealed: true;
}

export interface Frame {
  unit: 'meter' | 'model-height-1';
  up: [number, number, number];
  forward: [number, number, number];
  worldBounds: { min: Vec3; max: Vec3 };
  referenceCameras: ReferenceCamera[];        // from solve_camera_pose.py
}

export interface ReferenceCamera {
  viewId: string;                             // 'front-primary', 'side', ...
  azimuthDeg: number; elevationDeg: number;
  fovDeg: number | null;                      // null ⇒ UNSOLVED, must not be faked
  /** Discriminator for the bbox-inflation vs perspective-mismatch ambiguity — see §6.4 */
  fovEvidence: 'solved' | 'assumed' | 'ambiguous-with-part-inflation';
}

export interface Structure {
  /** The coarse "where is matter" solve. Deliberately low resolution. */
  occupancy: {
    resolution: number;                       // 32 → 128
    boundsSpace: 'model' | 'world';
    views: Array<{ axis: 'front' | 'side' | 'top'; maskRef: string; confidence: number }>;
    hiddenRegions: Array<{ region: string; confidence: number }>;
  };
  proportionAnchors: Array<{ id: string; position: Vec3; source: 'landmark' | 'occupancy' | 'assumed' }>;
  symmetryPlanes: Array<{ normal: Vec3; origin: Vec3; enforced: boolean }>;
}

export interface Part {
  id: string;
  parentId: string | null;
  semanticRole: string;                       // 'wing-left', 'horn-r', 'tail-dart'
  level: 'macro' | 'meso' | 'micro';
  transform: { position: Vec3; rotation: Vec3; scale: Vec3 };

  topologyClass: TopologyClass;               // + 'open-shell'
  topologyRationale: string;
  geometry: GeometryRepr;                     // §4 — discriminated union

  materialIds: string[];
  pivot?: Vec3;
  sockets?: Socket[];
  collider?: Collider;
  attachment?: Attachment;                    // unchanged contract
  articulationBinding?: { boneId?: string; jointId?: string; skinWeightHint?: string };

  confidence: PartConfidence;
  editability: {
    tier: GeometryRepr['kind'];
    /** For baked tiers: how to regenerate. Never emit opaque vertex data. */
    refitCommand?: string;
  };
}

export interface PartConfidence {
  /** Per axis, because a single view constrains x/y far better than z. */
  shape: { x: number; y: number; z: number };
  material: number;
  occluded: boolean;
  /** Set when the reference cannot resolve a declared feature at all. */
  insufficientReferenceResolution?: { featureId: string; referencePx: number; requiredPx: number };
}

export interface MaterialSpec {
  id: string;
  /** Every channel independent, with its own provenance. One extractor call ⇒ one channel. */
  channels: {
    baseColor?: Channel; roughness?: Channel; metalness?: Channel;
    normal?: Channel;    opacity?: Channel;   transmission?: Channel;
    ao?: Channel;        emissive?: Channel;
  };
  /** True when reference lighting is unsolved ⇒ roughness/metalness are REPORT-ONLY, never gated. */
  lightingUnknown: boolean;
  doubleSided?: boolean;                      // required for open-shell parts
}

export interface Channel {
  source: 'delit-reference-projection' | 'reference-inference' | 'procedural' | 'authored-map' | 'assumed';
  value?: number | [number, number, number];
  mapRef?: string;
  colorSpace?: 'srgb' | 'linear';
  confidence: number;                          // < 0.7 ⇒ refine-input, not a pass
  gating: 'hard' | 'soft' | 'report-only';
}

export interface Articulation {
  skeleton?: { bones: Bone[]; bindMode: 'attached' | 'detached' };
  joints: Joint[];                             // hinge/ball/slider + limits
  blendshapes?: Array<{ id: string; targetPartIds: string[]; driver: string }>;
  deformationStack?: DeformationOp[];
  rootMotionNode?: string;
}
```

Notes on the two fields that carry the most weight:

- **`Channel.gating`** is what makes confidence *actionable*. The rule established the hard way in
  the showcase build is: **never hard-gate a signal you cannot measure** — a dark-pixel ratio on a
  concave part measures cavity shading, not material; roughness from an unknown-lighting photo
  measures the photographer, not the surface. `lightingUnknown: true` must mechanically demote
  roughness/metalness to `report-only`.
- **`editability.refitCommand`** is what keeps the philosophy intact at the T5 escape hatch (§4). A
  baked `BufferGeometry` is acceptable *only* if it is regenerable and still wears a name, a pivot, a
  socket and a material.

---

## 4. Hybrid geometry system

A ladder, cheapest and most editable first. A part declares exactly one tier.

| Tier | Kind | What it is | Editable by | Example |
|---|---|---|---|---|
| T0 | `primitive` | box, sphere, ellipsoid, cylinder, cone, capsule, torus | changing a scalar | a gold ring, a bolt |
| T1 | `parametric` | lathe / extrude+bevel / ground-blade / tube | profile2D, bevel, spine | a knife blade, a horn |
| T2 | `sweep` | station list (position + radius) swept along a spine | editing one station | a tail, a wing spar |
| T3 | `proceduralSurface` | deterministic generator layered on T1/T2 (displacement, noise, tear notches) | generator parameters + seed | wing tears, knurling, scales |
| T4 | `field` | SDF union/subtract **or** open-shell field | primitive + op list | a continuous organic torso; a **membrane** |
| T5 | `fittedBuffer` | baked vertex data fitted to a field/mask | `refitCommand` re-derives it | a shape nothing above can express |

Routing keyed to the existing `topologyClass` (extends
`DISALLOWED_TOPOLOGY_PRIMITIVE_PAIRS`, `validate_sculpt_spec.py:71`):

| topologyClass | allowed tiers | forbidden |
|---|---|---|
| `assembled-solid` | T0, T1 | T4 (an assembly is not one field) |
| `continuous-sculpt` | T2, T4 | T0 box/cylinder/cone (already), thin straight extrude (already) |
| `conforming-shell` | T4 open-shell | closed SDF |
| `open-shell` *(new)* | T4 open-shell only | **SDF** — it cannot express zero thickness |
| `surface-relief` | T3 on the parent's surface | standalone T0 |
| `fiber-strand` | T1 tube, T0 instanced-cluster | box, plane-card (already) |
| `material-only` | none | any geometry |

Two rules matter more than the ladder itself:

**Promotion (toward T5) requires two agreeing instruments.** A part may only escalate its
representation when its cell has failed **twice, on converged measurements**, and the failure is a
*shape* failure rather than a measurement artefact. In the showcase build three geometry changes were
reverted by the silhouette ratchet, and at least one of them (thinning the wing spars ×0.72) was
chasing a measurement error — the isolation render was showing wing root that the reference cannot
see. Escalating representation on one instrument's word bakes that error into geometry, where it is
much harder to retract.

**Demotion is a required step, not an aspiration.** At `optimization-pass`, attempt to lift each T5
back to T4/T2 and accept the lift if the cell does not regress. Without this the model accumulates
baked geometry over its lifetime and quietly stops being editable — which is the failure mode that
would make img2threejs into the thing it is trying not to be.

---

## 5. Stage separation

| Stage | Owns | Reads | Emits | Where |
|---|---|---|---|---|
| **S0 Intake** | admission, camera solve, de-light, detail inventory, **reference resolution budget** | images | `evidence.json` | `forge/stage1_intake/` (exists) |
| **S1 Structure** | occupancy, proportion anchors, symmetry, part inventory + confidence | S0 | `structure.json` | **new** `forge/stage2_structure/` (promote `visual_hull.py`) |
| **S2 Geometry** | tier choice per part + parameter fitting to the occupancy field and silhouettes | S1 | `parts[].geometry` | `stage2_spec/derive_geometry.py` + **new** fitter |
| **S3 Material** | PBR channels, per-channel confidence and gating | S2 (**gated on per-part geometry convergence**) | `materials[]` | `stage1_intake/extract_pbr_evidence.py`, `analyze_texture.py` |
| **S4 Articulation** | pivots, sockets, colliders, joints, skeleton, skin weights, blendshape stubs | S2/S3 | `articulation` | **new** `forge/stage5_rig/` |
| **S5 Optimization** | merge/instance/LOD + **T5→T4 demotion attempt** | S4 | final spec + factory | `stage3_build/` |

The discipline that makes this worth doing is the one the showcase apparatus proved: each stage reads
**only** the previous stage's artifact plus the evidence bundle, and each stamps an input and output
hash. A stage that can reach behind its predecessor cannot be regression-tested, and a pipeline whose
artifacts are not hash-linked will silently measure a stale render — five separate stale-artifact
paths were found and closed in the showcase build, all from one root cause.

Note the gap this exposes: **S4 does not exist today.** `actionProfile`, `attachment`, `sockets`,
`joints` and `deformationStack` are all in the schema, `docs/PLAN_1.5_ANIMATION_READY_RIGS.md`
describes the intent, and the "action-ready" gate checks that `root.userData.sculptRuntime` is
populated — but nothing measures whether the rig is *correct*. That is the v1.5/v1.8 theme and it is
the least-defended part of the "animation-ready" promise.

---

## 6. The localized correction loop

### 6.1 What is there now

`stage4_review/correction_loop.py::decide(history, target_fidelity=0.85, max_iter=6, min_delta=0.02)`
takes a history of **whole-object fidelity scalars plus tags**. It is a sound bounded loop — hard
gates route to `refine-code`, oscillation to `refine-spec`, plateau and ceiling to `request-input` —
but it structurally *cannot say which part to fix*, so every correction regenerates the whole factory.

`divine_eye.py` measures the whole image on a 64×64 luma grid and a 96×96 edge grid
(`LUMA_SIZE`/`EDGE_SIZE`, lines 73-74). `per_feature.py` gates correctly per feature but consumes a
scores dict and never opens an image. So the tier machinery is sound and starved — exactly as
`grimoire/review/divine_eye_microscope.md` already records.

### 6.2 The loop to build

```
for each planned view:
    capture beauty pass
    capture object-ID pass          # flat unique emissive colour per component,
                                    # lights and environment OFF, depth testing ON
    for each declared component:
        footprint = pixels where this component's ID is frontmost   # occlusion-correct
        for each declared feature:
            patch   = setViewOffset crop, ≥128 px, projection UNCHANGED
            metrics = { sdf, directionalChamfer, curvatureExtrema, deltaE00 }

aggregate:  worst patch → worst component → worst view → verdict     # never average
route:      failing cells NAME the parts to edit
regenerate: only those parts' factory modules
```

`module_cache.py` already does per-module codegen caching with neighbour invalidation, so the last
line is a smaller change than it looks: make a failing cell invalidate exactly one module.

### 6.3 There is already a working implementation — promote it

The sibling `img2threejs-showcase` checkout contains the only working build of this loop. These are
production-tested and should move into the skill rather than be rewritten:

| Showcase file | What it does | Suggested home |
|---|---|---|
| `scripts/capture-views.mjs` | plan-driven capture, per-component object-ID pass, white-background hard fail | `forge/runtime/capture/` |
| `scripts/multiview_gate.py` | per-view silhouette IoU with coarse-to-fine alignment + **convergence status** | `forge/stage4_review/microscope/` |
| `scripts/component_report.py` | per-component footprint from the ID pass, fail-closed in both directions | `forge/stage4_review/microscope/` |
| `scripts/correction_loop.mjs` | bounded runner, 7 proven exit paths, stagnation detected via `renderSetHash` | merge into `correction_loop.py` |
| `scripts/provenance.mjs` | content-derived `runId`, `planHash` / `modelHash` / `shadingHash` | `forge/_shared/provenance.py` |
| `scripts/gate_record.py` | self-describing gate JSON; invariant `verdict == 'pass'` iff `blockers == []` | `forge/_shared/gate_record.py` |

### 6.4 Four rules that were learned the expensive way

These belong in the skill because each one produced a *confident false finding* before it was
understood, and each generalises past the dragon.

1. **Measure the visible footprint via an object-ID pass — not an isolation render, and not
   full-minus-hidden.** An isolation render shows geometry the reference cannot see: the dragon's
   wings measured 0.4362 dark-share against a reference 0.2240 ("the spars are twice too thick"), and
   at the *original* radii, measured correctly, 0.1891 against 0.2240 — inside tolerance. The spars
   were never too thick. The obvious fix, full-frame minus component-hidden-frame, is also wrong:
   71% of that pixel difference is indirect-lighting change, not occlusion. Only a flat-colour ID
   pass with depth testing gives the true frontmost footprint.
2. **Normalise robustly — 2nd–98th percentile of foreground mass — identically on both sides.**
   min/max bbox normalisation penalised every view by roughly 0.10 IoU and produced a width finding
   that was not merely wrong in magnitude but **reversed in direction**: 5.34× "too wide" was
   actually 0.85× narrower. The tell was self-consistency: across five views the min/max ratios read
   5.34 / 1.39 / 2.70 / 2.56 / 0.26 (incoherent) while the robust ratios read 0.85 / 0.50 / 0.59 /
   0.59 / 0.60.
3. **Refuse to decide on an unconverged or clamped alignment.** Every locked per-view floor in the
   showcase was derived from a clamped search. The "worst view", chased for ~50 iterations at a
   locked 0.4838, reads 0.5002 converged and 0.6112 under robust normalisation — **with no geometry
   change at all.** A ratchet anchored to a search boundary is anchored to the boundary, not to an
   optimum.
4. **Two instruments disagreeing is information, and the newer one is not automatically right.**
   Thinning the spars improved the new feature metric and cost the trusted silhouette ratchet 0.0075
   IoU on one view — twice its tolerance. The ratchet was right. Investigate the disagreement; never
   let a freshly written metric override a regression in one already trusted.

And one open discriminator worth encoding in the camera solve, because it is general to any
image-matched pipeline: **part bbox-inflation and a capture-FOV perspective mismatch predict the same
signature** ("shift down and magnify"). They separate on locality — part inflation is LOCAL, so
excluding the suspect part should collapse `dy` toward zero and leave `scale` alone; perspective
mismatch is GLOBAL, so `dy` tracks view angle and persists with all parts included. That belongs in
`ReferenceCamera.fovEvidence`.

---

## 7. PBR: what to take from TRELLIS.2

- **Opacity as a first-class channel.** TRELLIS carries `alpha` per voxel. img2threejs has
  `transmission`/`ior` via `analyze_texture.py` but no way to *declare* "thin, translucent,
  double-sided surface" as a topology + material pair. A wing membrane, a leaf, a cape and a lampshade
  all need it. This pairs with the new `open-shell` topology class and `MaterialSpec.doubleSided`.
- **Geometry-conditioned appearance, enforced.** TRELLIS passes the shape latent into
  `sample_tex_slat` as `concat_cond`. The enforceable version here: if a component's geometry cell is
  failing, the router must **reject** `refine-code` on that component's material. A material change
  is not allowed to be the fix for a shape error — and under a whole-image gate it very often looks
  like one.
- **Keep channels independent, structurally.** The rule already exists in
  `grimoire/feedback/shading_realism.md` ("never alias albedo into roughness/normal/AO"). Make it
  mechanical: one extractor call writes one channel, each with its own `source` and `confidence`.
- **Roughness and metalness from a single unknown-lighting photograph stay report-only.** Already the
  rule; `lightingUnknown` makes it automatic instead of a matter of discipline.
- **Prefer generated surface detail to a photo-derived normal map.** A normal map baked from the
  reference is entangled with the reference's lighting. Where one is unavoidable, require the de-lit
  albedo (`delight_albedo.py`) as its source, never the raw crop.
- **Add a relighting self-check.** Render the same part under two different environments; if the two
  ΔE00 scores against the reference differ by more than a threshold, the material is *compensating
  for lighting* rather than describing a surface. This is cheap, it is directly inspired by TRELLIS's
  relightability claim, and it catches the most common PBR cheat.

---

## 8. Concrete file-level change list

### New

| Path | Purpose |
|---|---|
| `forge/stage2_structure/solve_occupancy.py` | S1: promote `visual_hull.py` into a mandatory occupancy artifact; raise the 32³ cap |
| `forge/stage2_structure/proportion_anchors.py` | proportion + symmetry solve, the bbox oracle |
| `forge/_shared/part_shell.py` | open-shell / two-sided zero-thickness field; sibling to `sdf_primitives.py` |
| `forge/_shared/geometry_tiers.py` | the T0–T5 ladder, routing table, promotion/demotion rules |
| `forge/_shared/provenance.py` | content-derived run IDs and stage hashes (port from showcase) |
| `forge/_shared/gate_record.py` | self-describing gate JSON with the pass/blockers invariant |
| `forge/stage4_review/microscope/` | feature-level patches, SDF + directional Chamfer + curvature + ΔE00, worst-patch aggregation |
| `forge/stage4_review/microscope/id_pass.py` | object-ID footprint extraction |
| `forge/stage5_rig/` | S4: skeleton, skin weights, joint limits, blendshape stubs, and their gates |
| `forge/runtime/capture/` | plan-driven multi-view capture with the ID pass and a background hard fail |

### Modified

| Path | Change |
|---|---|
| `forge/stage2_spec/validate_sculpt_spec.py` | `schemaVersion: 2`; add `open-shell` to `VALID_TOPOLOGY_CLASSES:58`; extend `DISALLOWED_TOPOLOGY_PRIMITIVE_PAIRS:71` with the tier routing table; validate `Part.confidence`, `Channel.gating`, `editability.refitCommand` |
| `forge/stage2_spec/new_sculpt_spec.py` | author S3S; per-part confidence; per-channel material provenance |
| `forge/stage2_spec/derive_geometry.py` | tier selection + parameter fitting against the occupancy field |
| `forge/stage3_build/orchestrate_passes.py` | **per-component** pass state; geometry-before-material ordering gate (`:387-420`) |
| `forge/stage3_build/module_cache.py` | a failing cell invalidates exactly one module |
| `forge/stage3_build/generate_threejs_factory.py` | emit T4 field meshing and T5 `refitCommand`; keep every tier a named part with pivot/socket/material |
| `forge/stage3_build/visual_hull.py` | move to S1; raise `MAX_VISUAL_HULL_RESOLUTION:7` from 32 |
| `forge/stage4_review/divine_eye.py` | robust foreground-mass normalisation; emit alignment convergence; keep `LUMA_SIZE`/`EDGE_SIZE` as the *macro* tier only |
| `forge/stage4_review/per_feature.py` | consume microscope metrics, not just a precomputed scores dict (`:59`) |
| `forge/stage4_review/correction_loop.py` | cell-level history; refuse to decide on unconverged alignment; route by named part |
| `forge/stage4_review/make_comparison_sheet.py` | per-feature zoom panels alongside the whole-image sheet (`:216`) |
| `forge/stage1_intake/build_detail_inventory.py` | named-ROI authoring as the default path, not the upper/middle/lower thirds of `DEFAULT_COMPONENT_ZONES:38` (used at `:198`) |
| `forge/stage1_intake/solve_camera_pose.py` | emit `fovEvidence`; run the locality discriminator in §6.4 |
| `forge/stage1_intake/extract_pbr_evidence.py` | one call ⇒ one channel, each with `source`/`confidence`/`gating` |
| `forge/stage4_review/fit_params.py` | extend `fit_against_divine_eye()` to fit T1/T2 parameters against the occupancy field, not only against gate scalars |

---

## 9. Prioritised roadmap

### Quick wins — days, no architecture change

1. **Emit `insufficient-reference-resolution` per declared feature.** It is specified in
   `grimoire/review/divine_eye_microscope.md` and unimplemented. It prevents an entire class of false
   gates: a feature the reference cannot resolve currently scores badly instead of being excluded.
2. **Object-ID capture pass + per-component footprint.** Port `capture-views.mjs` and
   `component_report.py`. This is the single highest-value port — it is what turns a whole-image score
   into a per-part one.
3. **Robust foreground-mass normalisation everywhere a silhouette is normalised** (`divine_eye.py`,
   `diagnose_render.py`), and bump the metric version so cached comparisons are invalidated.
4. **Refuse to decide on unconverged alignment** in `correction_loop.py`, and surface the convergence
   status in the record.
5. **Per-channel `source`/`confidence`/`gating` + `lightingUnknown`**, mechanically demoting
   roughness/metalness to report-only when lighting is unsolved.

### Medium term

6. **S3S schema v2** — additive superset, with a migration test proving every v1.5 spec still validates.
7. **S1 Structure stage** — occupancy as a mandatory artifact and the proportion oracle.
8. **Per-component pass state + the geometry-before-material ordering gate.**
9. **Localized regeneration** — one failing cell invalidates one module.
10. **The T0–T5 tier ladder** with routing and the two-instrument promotion rule.
11. **Feature-level microscope** — `setViewOffset` patches, SDF/directional Chamfer/curvature/ΔE00,
    worst-patch aggregation, no averaging.

### Major architectural

12. **The part-shell field layer** (`open-shell` + field fitting). This is the change that actually
    raises the fidelity ceiling for organic and membrane subjects, because it removes the SDF's
    zero-thickness limit — the same limit TRELLIS.2 removed with O-Voxel.
13. **Analysis-by-synthesis fitting at scale** — finite-difference fitting of T1/T2 parameters
    against the occupancy field and silhouettes. `fit_params.py` and
    `grimoire/build/analysis_by_synthesis_fitting.md` are the seed.
14. **S4 Articulation stage** with rig-correctness gates. The "animation-ready" promise is currently
    checked structurally (`sculptRuntime` is populated) but never for correctness.
15. **Optional dense-evidence adapter.** If a TRELLIS-class output is available offline, ingest it as
    a **dense evidence layer to fit semantic parts against** — never as the output, never as a
    dependency. The pipeline must produce the same artifact without it.

### Top 10 by impact

| # | Change | Impact | Cost |
|---|---|---|---|
| 1 | Object-ID pass + per-component footprint | turns every score per-part; unblocks localized correction | S |
| 2 | Robust normalisation + convergence reporting | ~+0.10 IoU of pure measurement error removed; stops false findings | S |
| 3 | Cell-level correction loop routing by named part | corrections stop being whole-object rewrites | M |
| 4 | Feature-level microscope with worst-patch aggregation | small identity features become measurable at all | M |
| 5 | Part-shell field / `open-shell` topology | removes the zero-thickness limit — the actual ceiling | L |
| 6 | S1 Structure stage as the proportion oracle | fixes proportion/bbox errors before any detail work | M |
| 7 | Geometry-before-material ordering gate | stops material from papering over shape error | S |
| 8 | S3S v2 with actionable confidence and per-channel gating | makes "don't gate what you can't measure" mechanical | M |
| 9 | T0–T5 ladder with two-instrument promotion | expressiveness grows without losing editability | M |
| 10 | S4 articulation stage + rig gates | makes "animation-ready" a measured claim | L |

---

## 10. The answer to the question

**img2threejs closes the fidelity gap by borrowing TRELLIS.2's *representation strategy* and
*conditional stage ordering*, while keeping the semantic tree as the output and demoting the dense
representation to a measuring and fitting target.**

Concretely, three inversions of the current design:

1. **Dense where you measure, semantic where you emit.** TRELLIS is dense end-to-end; img2threejs is
   semantic end-to-end. Neither is right. Solve a cheap dense occupancy field per subject and a shell
   field per part, then *fit* named parametric parts to it. The field is never shipped. The Group is.
   This is what lets a wing membrane exist without an SDF having to thicken it, and it is the change
   that actually moves the ceiling.

2. **Order the stages by conditioning, not by convenience.** TRELLIS's pipeline settles occupancy
   before shape and shape before appearance, and passes the shape latent forward as an explicit
   condition. img2threejs's eight passes run in a fixed order but are not *conditioned*: a material
   pass can visually compensate for a geometry error and the whole-image gate will accept it. Make
   the ordering a gate rather than a convention.

3. **Refine cells, not objects.** TRELLIS's cascade refines the tokens that need refining.
   img2threejs regenerates the whole factory and re-decides on one scalar. Move the decision unit to
   `(view, component, feature)`, keep the aggregation worst-first with no averaging, and regenerate
   one module. The working implementation of this already exists in the showcase checkout — the
   remaining work is promotion, not invention.

What must not be traded away, and is not traded away by any of the above: every part keeps a name, a
transform, a pivot, its sockets and colliders, its material references, and its articulation binding.
The escape hatch at T5 bakes *vertex data*, never *hierarchy*, and it carries the command that
regenerates it. Editability degrades at the leaf, never at the tree.

The honest limit, which should be stated in any report this feeds: **a dense field fitted from one
photograph is still one photograph's worth of information.** Higher-resolution measurement does not
create evidence the reference never contained. That is why item 1 in the quick wins is
`insufficient-reference-resolution` — the pipeline needs to be able to say "this cannot be resolved
from this image" before it is given sharper instruments to say it more confidently.

---

## Sources

- [microsoft/TRELLIS.2](https://github.com/microsoft/TRELLIS.2)
- [TRELLIS.2 project page](https://microsoft.github.io/TRELLIS.2/)
- [Native and Compact Structured Latents for 3D Generation (arXiv 2512.14692)](https://huggingface.co/papers/2512.14692)
- [microsoft/TRELLIS.2-4B on Hugging Face](https://huggingface.co/microsoft/TRELLIS.2-4B)
- [img2threejs](https://github.com/img2threejs/img2threejs) — plus this local checkout, which is the
  authority for the file paths and schema line numbers cited above.
