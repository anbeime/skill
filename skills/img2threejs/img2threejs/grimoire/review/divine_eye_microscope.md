# Divine Eye Microscope — four-tier fidelity review

Divine Eye today scores a whole silhouette against a whole silhouette. That answers "is this the
right shape" and cannot answer "is tear-04 on the right wing the right width", because the two
questions live at different scales. This document specifies the microscope: a review that descends
macro → component → feature → micro, and where **one critical feature failing fails the iteration
regardless of a high global score**.

## Audit first — what is already here

Do not re-implement these. Verified against the code, not assumed:

| Capability | State | Where |
|---|---|---|
| Critical-feature AND gate | **already implemented** | `stage4_review/per_feature.py` — `is_gating()` returns true for `tier == "critical"` or `mustPass`, and `passed` is false if any gating feature is missing or below threshold |
| Arbitrary named ROIs in the inventory | **already implemented** | `stage1_intake/build_detail_inventory.py` — `component-zones` mode plus `--components` takes named normalized regions. The *default* (`DEFAULT_COMPONENT_ZONES`) is only upper/middle/lower thirds, which is what makes it feel grid-only |
| Chamfer distance | referenced | `stage4_review/divine_eye.py` |
| ΔE colour difference | present | `stage4_review/diagnose_render.py` |
| SSIM | present | `stage4_review/divine_eye.py` |

Genuinely absent, and therefore the actual work: `setViewOffset` zoom patches, render targets, SDF,
Hausdorff, ID/depth/normal/albedo passes, per-ROI ΔE2000, and **occlusion masking in stage 4**
(occlusion appears in stage 2 spec and stage 1 intake, nowhere in review).

## The resolution problem, stated exactly

`divine_eye.py` sets `LUMA_SIZE = 64` and `EDGE_SIZE = 96`. Every SSIM, tonal, blowout and
edge-overlap signal is computed on those grids. A tear a few pixels wide in a 1920px reference is
sub-pixel at 64×64 — it is not scored badly, it is **absent**. No threshold tuning recovers it; the
information is gone before any comparison happens.

`per_feature.py` cannot compensate: `evaluate_features(feature_targets, feature_scores)` consumes a
scores dict. It never opens an image. So the tier machinery is sound and starved — it gates
faithfully on numbers nothing produces at feature scale.

`make_comparison_sheet.py` composites whole reference beside whole render. At sheet scale a
few-pixel tear is invisible to a human reviewer and to a VLM alike.

## Tier structure

1. **Macro** — whole model, every required view.
2. **Component** — wing-left, wing-right, head, torso, tail.
3. **Feature** — individual spar, ear, eye, fang, tear.
4. **Micro** — contour, tear edge, bevel, roughness, colour gradient.

## Microscope plan — the feature descriptor

```json
{
  "featureId": "wing-right-tear-04",
  "componentId": "wing-right",
  "criticality": "critical",
  "requiredViews": ["front-primary", "rear", "side"],
  "referenceRoi": [0.61, 0.22, 0.73, 0.39],
  "localAnchor": [0.68, 0.91],
  "minimumProjectedPixels": 128,
  "captureResolution": 512,
  "metrics": ["directionalChamfer", "sdf", "curvature", "deltaE00"]
}
```

Missing ROI, missing render, missing camera, or a missing required feature **fails closed**. Exit
nonzero — never a printed complaint and a zero exit.

## Active zoom in Three.js

Do **not** move the camera closer and do **not** switch to orthographic. Both change the
projection, so the patch no longer shows what the reference view shows. NotebookLM's orthographic
suggestion is only correct when the reference itself is orthographic.

- `PerspectiveCamera.setViewOffset()` — crop a sub-rectangle of the *original* projection.
- `WebGLRenderTarget` — render the patch at 512² or 1024².
- `camera.layers` or visibility masks — isolate the component. **See the occlusion warning below.**
- Object-ID pass — one flat unique colour per mesh.
- Depth and normal passes — separate geometry error from material error.
- `readRenderTargetPixelsAsync()` for pixel readback.
- DPR pinned to 1. Hardware antialias **off**; supersample 2×/4× and downsample deterministically.
- Camera, viewport, FOV, target, near/far, tone mapping and exposure all frozen.

### Occlusion warning — isolation renders are not what the reference sees

**This one is empirically established, not theoretical.** It produced a confident false finding in
the mini-dragon build and cost a full correction cycle before it was caught.

Isolating a component by layers or `visible` hides everything else, so the render reveals parts of
the component that are **hidden in the real frame**. Measured that way the dragon's wings read
`darkShare` 0.4362 against a reference 0.2240 — "the spars are twice too thick". Spar radii were
scaled to 0.72× on the strength of it. Measured correctly at the *original* radii the same wings
read 0.1891 against 0.2240, a delta of 0.0349, comfortably inside tolerance. **The spars were never
too thick.**

The cause: the reference's wing material spans 0.924–2.135 face widths from the centre, the model's
spans 0.519–1.739 — the same span to within 1%, but reaching 0.405 face widths further inboard,
because in the isolation render nothing occluded the wing root. That root carries the thickest spars
and the arm spar, so the model was charged for dark geometry the reference photograph cannot contain.

The fix, and the rule:

> A fidelity comparison must measure the component's **visible footprint**: render the full frame,
> render it again with only that component hidden, and take the pixels that differ. Those are the
> pixels where the component is the frontmost thing drawn — which is exactly what a photograph of
> the same pose shows of it. Keep isolation renders for *structural* questions (is the spar present,
> are left and right consistent), where seeing occluded geometry is a feature rather than a bias.

Note also which instrument caught this. Thinning the spars improved the new feature metric and cost
the older silhouette ratchet 0.0075 IoU on one view, twice its tolerance. **Two instruments
disagreeing is information, and the newer one is not automatically right.** Never let a freshly
written metric override a regression in one already trusted; investigate the disagreement instead.

## Micro algorithms

- **Image pyramid / MS-SSIM** — compare at multiple scales rather than one.
- **Patch-wise comparison** — so a large correct skin area cannot mask a small wrong tear edge.
- **3-SSIM** — weight edge and texture above smooth regions.
- **SDF** — signed distance between two contours.
- **Bidirectional / directional Chamfer** — position *and* orientation of a tear edge.
- **Curvature extrema** — locate each notch's apex and lobes.
- **Hausdorff / worst-edge distance** — catch the worst local error, which averages hide.
- **Occlusion mask** — never score a hidden region. See the warning above.
- **Multi-view correspondence** — the same tear must sit consistently across views.
- **Adaptive subdivision** — subdivide ROIs that are edge-dense or uncertain.

Saliency alone is insufficient: a small tear need not be salient. Combine three sources — the
declared feature inventory (mandatory), automatic edge/curvature discovery, and saliency/uncertainty
for finding regions worth zooming that nobody declared.

## Tear descriptor

Store each tear independently; never mirror descriptors between wings.

Centre in normalized u/v · mouth width · tear depth · mouth angle · apex position · left and right
edge angle · curvature at apex · distance to previous and next tear · profile (V, U, slit, scallop) ·
edge thickness and bevel · roughness/fray amplitude · relation to nearest spar · side and asymmetry ·
visibility and occlusion per view.

That is what lets the review say "tear-04 is 12% too wide, 8% too shallow, 6px off its spar" instead
of "wing score low".

## Colour microscope

Three separate passes:

1. **Geometry pass** — unlit, no tone mapping. Silhouette, ID, depth, normal.
2. **Albedo pass** — neutral light or map-stripped, to check base colour.
3. **Beauty/PBR pass** — fixed lighting/HDRI/tone mapping, to check appearance.

Colour metrics: convert sRGB to linear properly · de-light the reference before comparing albedo ·
CIELAB/ΔE2000 per ROI · mask highlights, shadows and occluded regions · check hue, chroma and
luminance separately · derive roughness/specular from highlight width and intensity under controlled
relighting only.

**Do not hard-gate roughness from an image whose lighting is unknown.** `hueZoneParity` and specular
signals stay report-only until a calibration corpus exists.

### Corollary — a dark ratio cannot separate material from shadow on a concave part

Also empirically established. The mini-dragon's reference ear reads 14.3% "dark keratin" even along
its own axis corridor, so it is not a crop artefact. But bucketing those pixels by `min(r,g,b)` shows
only 14% near-black, peaking at 60–79 — a gradient. The wing's dark over the same classifier is 32.9%
near-black. The ear's dark is **cavity shading**, and the model reading 0.0% is not a missing
material. Gating on it would have driven a dark inner-ear material to be invented to match a shadow.

> Before promoting any ROI to a colour-gating metric, bucket its reference dark pixels by
> `min(r,g,b)`. A material clusters near-black; shading spreads mid-grey. Concave, unlit features are
> report-only.

## Aggregation

Never average globally.

```
critical feature AND gate
       ↓
   worst patch
       ↓
 worst component
       ↓
   worst view
       ↓
 overall verdict
```

One missing critical tear fails the whole iteration.

## Acceptance criteria

- [ ] Divine Eye accepts a view × component × feature manifest.
- [ ] Zoom patches rendered via `setViewOffset`, projection unchanged.
- [ ] Every critical feature rendered at ≥128–256 px.
- [ ] ID, depth, normal, albedo and beauty outputs produced.
- [ ] SDF + directional Chamfer for contours.
- [ ] Per-ROI ΔE2000 for colour.
- [ ] Any missing required patch exits nonzero.
- [ ] **Fidelity metrics measured on the visible footprint (full minus component-hidden), not on an isolation render.**
- [ ] A fixture identical everywhere but missing one small tear **fails**.
- [ ] A VLM may not override a geometry or micro-detail hard gate.
- [ ] Overall verdict from worst patch/view, not an average.
- [ ] Every artifact carries plan hash, model hash, camera, renderer config and iteration ID.

## The hard limit

**Zoom cannot create information the reference does not contain.** If a tear occupies 1–2 pixels in
the source image, Divine Eye must return `insufficient-reference-resolution`. Super-resolution output
is never ground truth — it is a plausible invention, and gating a model against an invention is worse
than not gating it at all.
