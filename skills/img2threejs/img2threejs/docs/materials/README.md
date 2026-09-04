# img2threejs material reference library

This directory is the canonical bridge between image material analysis and Three.js material
authoring. It is deliberately split into a human contract and machine-readable data:

- `THREEJS_MATERIAL_REFERENCE.md` explains the rendering rules and the starter recipes.
- `IMAGE_MATERIAL_ANALYSIS.md` defines the mandatory per-component analysis gate.
- `material-reference.json` is the versioned lookup table consumed by future analyzer/spec wiring.

The library stores **starting priors**, not universal truth. Roughness, clearcoat, transmission and
other appearance parameters depend on finish, wear, scale, lighting and the actual reference. The
pipeline must first classify a visible material region, then use the matching record as a bounded
starting point, fit it against the admitted image evidence, and verify it under controlled renders.

## Lookup contract

The image analyzer must emit a structured hypothesis rather than a bare word:

```json
{
  "componentId": "torso-armor",
  "regionId": "gold-trim",
  "family": "metal",
  "subtype": "brass",
  "finish": "polished",
  "confidence": 0.81,
  "alternatives": ["metal.gold.polished", "coating.metallic-paint"]
}
```

Resolution order:

1. Exact canonical `materialId` supplied by authoritative metadata or a reviewed spec.
2. Exact `family + subtype + finish` match.
3. Alias match, retaining every matching candidate rather than choosing silently.
4. Family fallback with reduced confidence.
5. `unknown` and `request-input` when the distinction affects a critical visible region.

User-supplied material identity has precedence over image inference. A low-confidence visual guess
must not overwrite explicit metadata. Conversely, a textual material name supplies identity but not
the final colour, wear or roughness; those still come from image evidence.

## Application contract

After lookup:

1. Copy the record's `renderPrior` into a candidate material, never directly into an accepted spec.
2. Derive colour and pattern from the admitted, de-lit component crop. Do not use the reference's
   baked shadow or highlight as albedo.
3. Keep colour maps in `THREE.SRGBColorSpace`; keep roughness, metalness, normal, AO, thickness,
   anisotropy and other data maps in `THREE.NoColorSpace`.
4. Author every `requiredMap`; an explicit documented constant may replace a map only when the
   surface is genuinely uniform at the target resolution.
5. Fit only inside the prior range initially. Expanding beyond a range requires a recorded reason
   such as coating, weathering, stylization or contradictory reference evidence.
6. Capture every `validationView` and compare the component's visible footprint. Beauty alone is
   never sufficient material evidence.

## Hard limits

- A single RGB image does not uniquely separate illumination, reflectance, roughness and geometry.
- Steel versus aluminium, real versus synthetic leather, and gold versus metallic paint may remain
  ambiguous without context, multiple views or controlled light.
- `MeshPhysicalMaterial` approximates skin, hair, fur and layered textiles; it is not a spectral,
  subsurface or strand renderer.
- Environment intensity and exposure are scene calibration controls, not intrinsic material
  constants. They are intentionally excluded from per-material physical identity.
- Hidden regions inherit only a low-confidence family prior until additional evidence is available.

## Research provenance

NotebookLM notebook:

```text
ThreeJS Materials Textures PBR
34554cd6-c897-4077-9561-308876bf2716
```

The contract was distilled from official Three.js material, texture, colour-management, renderer
and PMREM documentation plus Khronos glTF material specifications. Two NotebookLM deep-research
runs then covered (1) PBR foundations, specialist skin/hair models and image material recognition,
and (2) current Three.js/Khronos property contracts and production recipes. They found 101 and 100
sources, importing 73 and 52 cited sources respectively.

Only the source hierarchy recorded in `material-reference.json` may influence the canonical
contract: official Three.js first, Khronos specifications second, primary research/reference
implementations third, and established industry PBR guides fourth. Search-result blogs, forums and
uncited preset lists are not canonical sources. No generated numerical recipe becomes authoritative
until it is represented here as a bounded prior, carries source references and passes repository
tests.

## Future pipeline wiring

The intended hand-off is:

```text
component/material-region mask
  -> semantic material hypothesis
  -> material-reference.json lookup
  -> image-derived colour/PBR evidence
  -> ObjectSculptSpec material assignment
  -> Three.js material generation
  -> controlled render and component microscope
```

This directory defines that hand-off. The current wiring is implemented by
`forge/stage1_intake/material_region_analysis.py`,
`forge/stage2_spec/apply_material_analysis.py`, the generated factory provenance hooks, and the
material review/gate scripts. Specs without `materialPipeline` remain backward-compatible; a spec
that opts into the contract is blocked until its regions, crops, controlled comparisons and
geometry/UV/rig/LOD compatibility evidence pass.
