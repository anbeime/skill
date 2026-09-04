# Reference-fidelity tooling

This integration layer strengthens image matching without changing the core contract: output remains
procedural, reviewable Three.js code. External tools may produce evidence and diagnostics; they may
not silently provide meshes, decide hidden geometry, mutate the accepted source, or approve a pass.

## Default routing

| Need | Primary tool | Output | Authority boundary |
| --- | --- | --- | --- |
| Browser render, console, network and performance trace | Chrome DevTools MCP | screenshot, trace, console/network evidence | diagnostic only |
| Three.js scene/material/renderer inspection | threejs-devtools MCP | scene tree, material/texture state, renderer metrics | read-only findings until reflected in code |
| Cross-browser reproduction | Playwright MCP | Chrome/Firefox/WebKit screenshot and trace | fallback; do not duplicate the default Chrome loop |
| Version-aware Three.js documentation | Context7 | cited, version-specific API context | local installed Three.js and typecheck remain authoritative |
| Thin/complex foreground or component mask | SAM2 adapter | binary PNG mask + provenance JSON | agent confirms the intended subject/component |
| Character face or body evidence | MediaPipe adapter | normalized landmark JSON | anatomy/spec review required |
| Weak front/back depth cues | Depth Anything V2 adapter | 16-bit relative-depth PNG + provenance JSON | relative prior only, never metric or hidden geometry |

## Codex MCP configuration

The intended user-level servers are pinned:

```text
chrome-devtools  chrome-devtools-mcp@1.6.0
threejs-devtools threejs-devtools-mcp@0.4.1
playwright          @playwright/mcp@0.0.78 (Chromium)
playwright-firefox  @playwright/mcp@0.0.78
playwright-webkit   @playwright/mcp@0.0.78
context7         @upstash/context7-mcp@3.2.5
```

For the reference loop, use Chrome DevTools in an isolated, headless profile with usage statistics
and CrUX URL lookup disabled. Use a 1600x900 viewport unless the reference contract specifies
another size. The repository's own screenshot harness remains the evidence producer; MCP captures
are for diagnosis or a host fallback.

The three Playwright routes use isolated, headless 1600x900 profiles with service workers blocked.
Use Chromium for the default reproduction and call the Firefox/WebKit server only when validating a
cross-browser discrepancy.

### Chrome DevTools MCP

Use during render and optimization:

1. Navigate to the exact local preview URL.
2. Wait for `window.__IMG2THREEJS_READY__ === true`.
3. Confirm texture/asset readiness and collect console/network failures.
4. Disable controls and set the named review camera.
5. Capture a PNG at the reference viewport.
6. Read `window.__IMG2THREEJS_VIEWER__.renderer.info` and record draw calls, triangles,
   geometries, textures and programs.
7. Run a performance trace only after the visual pass is accepted.

Never accept an MCP-only scene edit. Copy the proven parameter change into the spec or generated
TypeScript, rebuild, and recapture.

### threejs-devtools MCP

Use the read-only tools first: scene tree, object/geometry details, material and texture details,
camera, renderer info, performance snapshot and memory diagnostics. Mutation tools are scratch
experiments. A changed transform, material, light, camera or renderer setting has no standing until
the source/spec contains it and the deterministic capture loop reproduces it.

### Playwright MCP

Use the `playwright` server for the normal Chromium fallback. Repeat an already-failing case with
`playwright-firefox` or `playwright-webkit`; do not run three browsers on every refinement cycle.
Cross-browser captures diagnose runtime portability and cannot replace the named-camera fidelity
gate.

### Context7

Ask for the installed Three.js version explicitly. The companion showcase currently controls the
runtime version; its `package-lock.json`, local `.d.ts`, typecheck and runtime smoke tests override
live documentation. WebGPU/TSL advice must not be applied to the WebGL/r169 path without an explicit
version migration.

## Local vision environment

Install:

```bash
uv sync --project integrations/vision --python 3.11
python3 forge/stage1_intake/run_vision_adapter.py prefetch
python3 forge/stage1_intake/run_vision_adapter.py health
```

### SAM2 component masks

Use one positive point inside the visible subject or component:

```bash
python3 forge/stage1_intake/run_vision_adapter.py \
  segment reference.png --point 512 320 --out evidence/body-mask.png
```

Inspect the PNG before recording it. Store the JSON sidecar as an evidence record. Use separate
masks for identity systems such as body, wing, blade, handle, hair or face; do not treat one global
foreground mask as component decomposition.

### Depth Anything V2

```bash
python3 forge/stage1_intake/run_vision_adapter.py \
  depth reference.png --out evidence/relative-depth.png
```

Use the result to propose front/back ordering, thickness candidates and camera hypotheses. Do not
use its values as metric dimensions or invent unseen backsides.

### MediaPipe

```bash
python3 forge/stage1_intake/run_vision_adapter.py \
  landmarks face reference.png --out evidence/face-landmarks.json

python3 forge/stage1_intake/run_vision_adapter.py \
  landmarks pose reference.png --out evidence/pose-landmarks.json
```

Normalize and map accepted landmarks into `preSpecAssessment.anatomy`; keep the source image and
model hashes in evidence refs. On macOS, MediaPipe Tasks creates a Metal graphics context even when
the inference delegate is CPU, so a restricted/headless sandbox must grant graphics access.

## Loop placement

```text
reference admission
  -> optional SAM2 / MediaPipe / relative-depth evidence
  -> pre-spec assessment and local spec search
  -> camera solve, de-light and projection bake
  -> strict ObjectSculptSpec
  -> pass-gated Three.js generation
  -> deterministic repository capture
  -> MCP diagnosis when needed
  -> Divine Eye + feature microscope
  -> refine-spec / refine-code / request-input / continue
  -> performance trace after fidelity acceptance
```

The reference view and meaningful orbit views remain separate gates. Projection can make the
reference camera match closely, but it cannot substitute for thickness, attachment, component
coverage or multi-angle 3D truth.
