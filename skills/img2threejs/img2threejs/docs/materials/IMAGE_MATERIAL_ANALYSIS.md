# Mandatory image material analysis

Material analysis is an admission gate for material authoring. A model may not enter or pass the
material build pass merely because every component has a material ID. Each critical visible region
must have evidence that the ID and rendered response are plausible for the reference.

## 1. Inputs

- admitted reference images with hashes, roles and camera metadata;
- component masks and material-region masks per usable view;
- prompt or authoritative metadata supplied by the user;
- named component and region IDs that remain stable through UV, skinning, morphs and LOD;
- crop resolution and visible-footprint coverage.

Reject empty, inverted, fragmented, duplicate or too-small crops before classification. Cropping a
nearby component is a failed gate, not low-confidence evidence.

## 2. Observation before classification

For each material region, record observable signals without naming the material first:

- de-lit base-colour distribution and colour variation;
- highlight colour, width, sharpness, elongation and view dependence;
- diffuse versus specular balance;
- fibre, grain, strand, brushing or machining direction;
- macro, meso and micro surface frequency bands;
- opacity, refraction, transmission and apparent thickness cues;
- edge wear, coating chips, oxidation, dirt, wetness and cavity response;
- component context: garment, skin surface, blade, trim, lens, hair mass, tyre, wood panel;
- occlusion and uncertainty per view.

Do not classify material from colour alone. Black plastic, rubber, leather and cloth can share an
albedo. Gold metal, brass and metallic yellow paint can share a hue. The light-response evidence is
the discriminator.

## 3. Hypothesis record

Every region emits:

```json
{
  "componentId": "jacket",
  "regionId": "body-cloth",
  "family": "fabric",
  "subtype": "woven",
  "finish": "matte",
  "confidence": 0.78,
  "evidenceViews": ["front-primary", "three-quarter-right"],
  "sourceCropPaths": ["jacket-front.png", "jacket-3q.png"],
  "observations": [],
  "alternatives": [
    {"materialId": "leather.matte", "confidence": 0.31}
  ],
  "status": "proceed"
}
```

Allowed status values are `proceed`, `probe`, `request-input` and `unknown`. Missing confidence,
crop, mask or evidence view fails closed.

## 4. Lookup and evidence reconciliation

Resolve the hypothesis against `material-reference.json`. Semantic vision provides candidate
identity; deterministic image analysis provides colour, gradient, highlight and frequency evidence.
Neither source decides alone.

- If both agree above the configured threshold, seed the candidate recipe.
- If identity is known but surface evidence is weak, retain the identity and mark PBR values for
  controlled-render fitting.
- If the highest candidates are materially different and the distinction is critical, request
  another view or explicit user metadata.
- Never raise confidence merely because a default recipe produced an attractive render.

## 5. Map and shader authoring

- `map`, `emissiveMap`, `sheenColorMap` and `specularColorMap` are colour data and use sRGB.
- Roughness, metalness, normal, AO, clearcoat, thickness, transmission, anisotropy and iridescence
  maps are mathematical data and use no colour-space transform.
- Albedo, roughness, metalness, normal/height and AO are independent signals.
- Coated surfaces represent the top layer correctly: intact paint is dielectric even when its
  substrate is metal; exposed chips may use a separate metallic region or mask.
- Geometry supplies silhouette-scale fibres, fur tufts, hair clumps, folds, facets and deep damage.
  Normal/bump maps supply sub-pixel or small-scale relief; albedo must not fake missing form.

## 6. Controlled validation views

Every critical material requires the views named by its lookup record:

- `albedo-unlit`: verifies de-lit colour and pattern;
- `neutral-studio`: verifies balanced diffuse/specular response;
- `grazing`: reveals roughness, normal strength, sheen and anisotropy;
- `environment-reflection`: distinguishes conductors and polished coatings;
- `backlight-transmission`: required for transmissive or thin materials;
- `reference-beauty`: verifies the final appearance at the solved camera.

Wait for every texture to load before capture. Save each image, read it back, and compare the
component's visible footprint rather than an isolation render that reveals occluded surface.

## 7. Gate policy

The material pass fails when:

- a critical visible region has no hypothesis or lookup result;
- one material is assigned across visibly incompatible regions;
- evidence confidence is below threshold and no explicit user identity resolves it;
- required maps or controlled views are missing;
- a conductor renders like a dielectric, fabric like smooth plastic, hair like rubber, or glass as
  alpha-blended air;
- a high global beauty score hides a failed critical material region;
- texture loading, colour space, environment preprocessing or screenshot readback fails.

Unknown is an acceptable analysis result. Silent substitution is not.
