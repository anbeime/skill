# Stylized 3D Hair for Three.js

Version: 1.0
Scope: code-only procedural character hair, Three.js r169 / WebGL, fixed hero view plus meaningful orbit views.
Target case: Zenonia Chronobreak warrior.

## Provenance and distillation status

NotebookLM deep research was completed for this topic under notebook `d397a9fe-a8a8-49d8-92ac-56eb92e623c3` and research task `560deabc-c7d1-4c5c-be68-c5548c9b3087`. NotebookLM reported 120 imported sources. The local facts supplied to that notebook were sanitized and contained only visual observations; internal workspace paths were not uploaded.

The NotebookLM `ask` distill response was submitted but could not be read back after the environment's escalation usage limit was reached. Therefore this file is an explicitly labelled local distillation of the completed research task, the imported-source summary, the sanitized reference facts, and the official Three.js/paper sources listed below. It is not claimed to be a verbatim NotebookLM answer. Refresh this document with a successful NotebookLM ask before treating it as a final research publication.

## 1. Requirement classification

| Label | Zenonia hair requirement or decision | Evidence / confidence |
|---|---|---|
| REQUIREMENT | Keep the model code-only and procedural; do not download hair meshes or art packs. | img2threejs contract; high |
| REQUIREMENT | Support the installed Three.js r169 / WebGL runtime. | project constraint; high |
| REQUIREMENT | Review a fixed hero view and at least two non-degenerate orbit views. | img2threejs visual gate; high |
| OBSERVATION | The hairstyle is a large blonde crown mass made of broad layered locks, not realistic individual fibers. | sanitized multi-view facts; high |
| OBSERVATION | Front bangs frame the face; the eyes must remain readable in the hero view. | sanitized multi-view facts; high |
| OBSERVATION | Three-quarter/profile views show real depth, rear locks and overlap. | sanitized multi-view facts; medium-high |
| INFERENCE | A hybrid clustered-lock system is a better representation than a strand groom or one flat card. | synthesis of observations and implementation research; high |
| IMPLEMENTATION | Use a scalp mass, custom tapered volumetric ribbon locks, and curved tube/loft locks for secondary depth. | geometry decision; high |
| APPROXIMATION | Hidden backside topology, exact strand count and exact fiber scattering are not observable and must be parameterized as inferred. | multi-view coverage; medium |
| ACCEPTANCE | Geometry and material are evaluated separately; a blonde shader cannot compensate for a wrong silhouette or detached lock. | review policy; high |

## 2. Hairstyle taxonomy and route selection

### Clustered anime/spiky locks

Visual signature: a few large, deliberate masses with tapered tips, controlled asymmetry and readable negative space. The silhouette is designed in image space but each lock has enough depth to survive an orbit.

Recommended representation: custom tapered ribbon/loft geometry around a 3D centerline, backed by a low-poly scalp mass.

Failure mode: cones or repeated straight spikes create a porcupine silhouette; identical lengths and angles destroy the reference's designed rhythm.

### Ribbon or strip locks

Visual signature: broad graphic surfaces with a strong front-facing contour and a narrow edge profile.

Recommended representation: custom `BufferGeometry` with two or more width samples per curve section, front/back faces, side thickness, UVs and stable normals. This is the primary route for the Zenonia crown and bangs.

Failure mode: a single flat extruded panel reads as a petal or card. The ribbon needs a changing width, thickness, normal frame and root overlap.

### Curve-tube locks

Visual signature: round or semi-round secondary strands that wrap around the scalp and preserve profile depth.

Recommended representation: `CatmullRomCurve3` plus `TubeGeometry`, or a custom elliptical tube when the section needs to be flattened or tapered. Three.js `TubeGeometry` takes one constant constructor radius, so a procedural taper requires per-ring scaling or custom geometry.

Failure mode: constant-radius tubes look like noodles; an overly small radius produces wires; too many radial segments make stylized hair visually soft and expensive.

### Hair cards

Visual signature: many thin locks or wisps represented by alpha-cut planes.

Recommended representation: small numbers of oriented cards with an alpha map and hard cutout (`alphaTest`) for micro-strands only.

Failure mode: transparent cards sort incorrectly, self-overlap, or reveal their plane at orbit angles. Three.js documentation explicitly treats perfect transparency as difficult; alpha-tested cutouts are safer when the edge can be hard.

### Shell/fur layers

Visual signature: dense short fur or fuzzy volume produced by concentric shells and alpha detail.

Recommended representation: layered shells with alpha-tested textures.

Failure mode: overdraw, sorting, noisy silhouette and excessive detail. This is inappropriate for the broad, graphic Zenonia crown except perhaps for a tiny soft root fringe.

### Groomed individual strands

Visual signature: realistic fiber field, many fine curves, anisotropic strand highlights and natural clumping.

Recommended representation: strand curves, cards, or a dedicated hair renderer.

Failure mode: high authoring/runtime cost and poor return for stylized reference matching. Physical hair scattering improves material realism, not the large-scale crown silhouette.

### Hybrid route selected for Zenonia

Use one continuous scalp/crown mass, 10–16 primary custom ribbon-loft locks, 4–6 front bangs, 8–14 secondary curved locks, and optional 0–24 micro-cards only where a screenshot proves they are needed. The counts are starting ranges, not a universal rule; fit them to the silhouette and performance budget.

## 3. Zenonia hair analysis

### Observable

- Blonde/golden palette with soft highlight bands and darker occlusion between locks.
- Broad crown volume with locks rising upward and fanning outward from a central root region.
- Front bangs are separated and frame the face.
- Side and rear locks change the silhouette in three-quarter/profile views.
- Tips are tapered, curved and varied in length and direction.
- Roots visually merge into the scalp/crown mass; floating pieces are not acceptable.
- Stylization depends on large readable masses more than individual fiber count.

### Inferred construction

- The crown should be layered front-to-back: rear mass first, middle silhouette locks second, bangs last.
- Each primary lock should have 3–5 control points, a broad root, a narrowing middle, a near-zero tip width and small twist.
- The scalp mass should be hidden but overlap each root enough to prevent visible seams.
- A slight lock-to-lock color variation is useful, but the palette must remain a unified warm blonde family.
- The rear topology and exact number of strands remain medium-confidence inference; validate them from orbit renders rather than treating them as reference truth.

### Hair/face constraints

- No primary bang may cross both eye centres in the hero view.
- A bang may overlap a small part of the forehead or outer eye region only if the reference shows it.
- The nose-to-hair clearance visible in profile must remain open.
- Hair depth should be visible in the positive and negative orbit, but the head must not become hollow between locks.

## 4. Three.js design recipe

### Build order

1. Create the head-local scalp/crown mass.
2. Add rear locks that establish depth and back silhouette.
3. Add primary crown locks with custom tapered ribbon-loft geometry.
4. Add side locks and front bangs with explicit face-occlusion limits.
5. Add secondary tube/elliptical locks only where they improve profile or root continuity.
6. Tune hair materials and lighting after silhouette review.
7. Add micro-cards or instanced wisps only after a screenshot shows a missing scale band.

### Custom tapered ribbon-loft

For each sampled centerline point, compute a tangent `T`, a stable side vector `B`, and a surface normal `N`. Emit front/back vertices using width `w(t)` and thickness `d(t)`, connect adjacent sections, assign `u` across the lock and `v` along its length, then compute normals. Use a stable frame or parallel-transport-like update when the tangent approaches the world-up vector; do not allow the frame to flip at a bend.

Recommended profiles:

```text
width:     1.00 -> 0.80 -> 0.40 -> 0.03
thickness: 1.00 -> 0.75 -> 0.35 -> 0.08
```

Those are normalized shape profiles, not world-unit constants. The first section should be embedded into the scalp; the last section should be capped or closed cleanly.

### When to use each Three.js primitive

- `CatmullRomCurve3`: control a lock centreline through artist-readable points.
- `TubeGeometry`: secondary rounded locks; scale ring radii manually for taper, or author an elliptical custom section.
- `ExtrudeGeometry`: small fixed graphic trims or a temporary blockout, not the final crown system.
- `BufferGeometry`: primary crown/bang locks, because width, thickness, twist and normals must vary per section.
- `InstancedMesh`: repeated micro-strands that share geometry and material; never use it to hide different primary silhouettes inside one generic instance.
- Hair cards: only hard-cut micro detail, with controlled orientation and `alphaTest`; avoid large transparent overlapping planes.

### Material route

Start with a non-metal physical material: `metalness: 0`, mid roughness, restrained `sheen`, warm sheen colour and moderate specular intensity. Use darker materials or vertex/lock colour at roots and occluded overlaps. Material tuning cannot repair wrong lock topology.

The physically based hair literature explains tangent-oriented highlights and multiple scattering lobes, but a full Marschner implementation is beyond the current r169/WebGL scope. A custom tangent-aware shader is a later material experiment, not a prerequisite for fixing Zenonia likeness. TSL/WebGPU should remain optional because the current deliverable is WebGL r169.

## 5. Parameter contract

The machine-readable contract lives in `grimoire/character/threejs_hair_parameter_contract.json`. It is intentionally head-local and deterministic so a script can generate both a spec artifact and TypeScript factory inputs.

Coordinate convention:

- `headHeight = 1` is the visible head height from crown scalp to chin.
- `x` is character-left/right, `y` is up, `z` is forward.
- `root` and `controlPoints` are in head-local units.
- Camera fit parameters are separate from geometry parameters.
- Values labelled as starting ranges must be fitted against screenshots, not copied as universal constants.

Important fields:

- `scalpMass`: ellipsoid/low-poly anchor that receives roots.
- `locks[].family`: `primary`, `bang`, `secondary`, `rear` or `micro`.
- `locks[].layer`: depth ordering for deterministic assembly.
- `locks[].controlPoints`: 3–5 centreline points in head-local space.
- `locks[].widthProfile` and `thicknessProfile`: normalized profiles from root to tip.
- `locks[].rootEmbedDepth`: overlap into the scalp mass, not a visual gap.
- `locks[].twistDegrees`: controlled section rotation, clamped to avoid flips.
- `locks[].visibility`: hero-view eye/face occlusion constraints.
- `materials`: base, root shadow and highlight variants.
- `lod`: sample/radial budgets for hero and orbit views.
- `reviewCameras`: fixed plus positive/negative orbit contracts.

## 6. Acceptance and diagnosis

### Fixed hero view

Inspect the saved PNG, not an inline preview. Score separately:

- crown top/side silhouette;
- width and spacing of primary locks;
- bang-to-eye clearance;
- root continuity;
- taper and tip direction;
- warm blonde palette and root occlusion.

### Two orbit views

Use one positive and one negative orbit. Confirm the crown retains volume, rear locks remain attached, the profile has a believable depth order, and no flat card or hollow head is exposed.

### Side-by-side and semantic review

Create a side-by-side sheet with the matching reference view. Use semantic feature labels rather than a single global score: `crown-silhouette`, `bang-eye-clearance`, `side-depth`, `rear-attachment`, `root-continuity`, `tip-taper`, `hair-palette`.

### Pixel/feature review

Use hair-specific ROIs or a visible-footprint comparison. A global 64×64 score can miss a bang that covers an eye or a small detached root. Do not use isolation renders that show geometry hidden in the reference; measure the visible footprint instead.

### Background warning

Brown studio gradients can be classified as foreground by simple segmentation. In that condition, IoU/area/aspect results may look excellent while measuring the background rather than the hair. Use a neutral, separable capture background or an explicit foreground mask for diagnosis, and record the warning instead of claiming a visual pass.

## 7. Ordered implementation backlog

1. Add a dedicated hair parameter object to the Zenonia model factory; keep it separate from renderer objects.
2. Implement `createTaperedHairRibbon()` with a stable frame, variable width, thickness, twist, UVs and normals.
3. Replace crown/bang `ExtrudeGeometry` blades with parameterized volumetric ribbon locks.
4. Keep `TubeGeometry` only for secondary/profile locks and apply true ring taper.
5. Add scalp overlap and root shadow material; remove any lock that floats or terminates visibly at the scalp.
6. Encode eye-clearance constraints and reject/adjust any front lock that crosses both eye centres in the fixed camera.
7. Tune non-metal blonde hair material only after the geometry review.
8. Capture fixed plus two orbit PNGs, read them back with the image-capable tool, create the comparison sheet, run semantic/pixel feature checks and `diagnose_render.py`, then record the honest next action.

## Source register

- Three.js `TubeGeometry`: https://threejs.org/docs/pages/TubeGeometry.html
- Three.js `CatmullRomCurve3`: https://threejs.org/docs/pages/CatmullRomCurve3.html
- Three.js custom `BufferGeometry`: https://threejs.org/manual/en/custom-buffergeometry.html
- Three.js transparency and `alphaTest`: https://threejs.org/manual/en/transparency.html
- Three.js `MeshPhysicalMaterial`: https://threejs.org/docs/pages/MeshPhysicalMaterial.html
- Three.js `InstancedMesh`: https://threejs.org/docs/pages/InstancedMesh.html
- Kajiya and Kay, *Rendering Fur with Three Dimensional Textures*: https://doi.org/10.1145/74333.74361
- Marschner et al., *Light Scattering from Human Hair Fibers*: https://www.cs.cornell.edu/~srm/publications/SG03-hair-abstract.html
- CHARM, *Control-point-based 3D Anime Hairstyle Auto-Generation*: https://arxiv.org/abs/2509.21111
