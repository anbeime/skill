---
name: RuiC-card-skill
description: Generate interactive 3D holographic collectible-card websites from a user description or reference image, using layered artwork, Blender and Three.js. Includes project-local Blender installation, reusable parallax materials and browser verification. Host-agnostic — any harness that runs a multimodal model can use it, since the model draws the layer artwork and inspects the rendered frames. Use when the user asks for 全息闪卡, 镭射卡, 3D 卡牌网页, a holographic collectible card site, or an editable card.blend.
---

# RuiC Card Skill

Turn the user's description or uploaded reference into a finished, editable Blender card and an interactive Three.js page. Preserve the requested subject, style, typography and destination. This skill contains code and text only; generated artwork belongs in the user's output project. It is host-agnostic — nothing in it is specific to one harness or one vendor's model — and it needs a multimodal model: you produce the layer artwork and you look at the rendered frames, so the host has to be able to generate and inspect images.

## The layer stack

All layers share one canvas, normally 1024×1536 portrait. Each layer has one job and one depth, and the depth differences are what make the card read as stacked planes instead of one flat picture.

| layer | file | job | depth |
|---|---|---|---|
| subject | `assets/subject.png` | the character or hero object, real alpha, composited over the background | `subjectDepth` (0.4) |
| effects | `assets/effects.png` (optional) | a pre-cut decorative overlay — petals, sparks, thorn work — that floats **between** the subject and the typography | `effectsDepth` (0.5 forward, or negative to sink it) |
| background | `assets/background.png` | the opaque environment behind everything | `backgroundDepth` (−0.25) |
| lineart | `assets/lineart.png` | dark contours on white; drives the glowing ink glints that appear inside the subject's silhouette | follows the subject |
| text | `assets/text.png` | typography and card furniture. The viewer samples this layer **without parallax**, so a border or frame painted here stays nailed to the card edge | 0 |

Give the layers clearly different depths. Two layers at the same depth fuse into one plane and the parallax stops reading as depth; that is the single most common way a card ends up looking flat.

## Working sequence

1. Establish the output project and a compact card specification: subject, title, subtitle, technique or tagline, edition, palette, medium, destination. Infer harmless missing details and state them. Read [references/art-direction.md](references/art-direction.md) for the per-layer quality bars and reference handling. Do not assume every card is anime, Japanese, or a copy of the example that inspired this skill.
2. Produce the layers. For an uploaded reference, inspect it first and preserve the requested identity and composition; use the available image tool and never silently substitute an API that needs a key or a paid service. Subject and text (and the optional effects overlay) must be genuinely transparent RGBA; the background must be fully opaque. Save them under the output project's `assets/` as `subject.png`, `background.png`, `lineart.png`, `text.png`, plus `effects.png` when used. Keep every layer on the same canvas. Never package generated artwork into this skill.
3. Derive `lineart.png` from the same source as the subject — the same draw calls, or an edge/threshold pass over the finished subject — so the contours register exactly. Never ask for a fresh line drawing from a text description: a regenerated pose drifts and produces glowing outlines in the wrong place.
4. Write `<project>/card-config.json` from [references/config.example.json](references/config.example.json): metadata, the asset paths, and one depth per layer. Then run `scripts/validate_assets.py <project>` and inspect the result by eye as well as numerically — equal canvases, real transparency where it is required, dark contours on white for the line art, and no empty layers. A painted checkerboard is not transparency: `validate_assets.py` converts a painted board to a true alpha channel through `scripts/checkerboard_to_alpha.py` (logged in `asset-validation.json`), but asking the tool for a genuine RGBA PNG is still the better outcome.
5. Run `scripts/run_pipeline.py --project <project>`. It validates, locates Blender and installs an official portable copy into `<project>/tools/` when absent, builds the editable scene, renders the preview, exports the geometry, copies the viewer from `assets/web-template/`, and installs the viewer's dependencies. Python with Pillow, Node.js with npm, and network access for the first Blender download are required. Read the errors instead of retrying the same blocker.
6. Start the site with `node <project>/web/server.mjs`, keep it alive, and open the URL it prints. Read [references/verification.md](references/verification.md), then run `node scripts/verify_web.mjs <project>`: it launches its own headless Chromium and its own copy of the viewer, drives drag, flip, reset, zoom, the keyboard, every slider (including 特效景深), the finish options, the screenshot download, a ~390 px viewport and the reduced-motion setting, compares real captured frames, writes `<project>/verification/report.json` plus screenshots, and exits non-zero on any failure. It needs no GUI and runs as root, so a container or CI session is not a reason to skip it. A green report is evidence about controls, not about looks: still open the page and look at the render, both tilts and the layers yourself. A `ready` flag proves none of that.
7. Deliver the working URL, the source project, the editable `.blend` and the renders. Say plainly that the Blender node graph is rebuilt in GLSL for the browser — glTF carries geometry and material roles only — so the two are close but not pixel-identical. Publish a website or repository only when that is asked for. For a requested skill ZIP, run `scripts/package_skill.py`: it enforces a text-only allowlist, and output projects, artwork, models with embedded images, credentials, dependencies and caches never belong in it.

## Non-obvious invariants

- All image planes are created in XY with object rotation X=90 degrees. Keep that rotation unapplied; faking it in the mesh breaks the local axes the parallax maths depends on.
- The shared group is `视差效果` with inputs `缩放` and `深度` and one output. Defaults: subject scale 1.25 and subject depth 0.4, background depth −0.25, text scale 1 and depth 0. A fixed layout safety mapping (`safeArea`) can hold room for typography; keep it separate from the user's parallax controls.
- UV centring plus a normal transform is not enough for view-dependent parallax. Transform the viewing direction into the card plane, divide by a bounded normal component, and apply it as a signed depth offset — the same expression on both sides: `(p − 0.5)·s + 0.5 + uView.xy / max(|uView.z|, 0.35) · d · 0.14`.
- The face mixes the background and subject BSDF by the subject's alpha. Keep metallic=1 and roughness=1 where the design asks for it, keep the subject BSDF emission black, and never bury a bad material under extreme emission.
- Foil is a material, not a painting: mapped bands (wave scale ≈0.55, distortion 7, mapping Y ≈32°) with their own pattern-image mapping, Multiply/Add, a pink→yellow→blue→white ramp and Overlay. The spectrum phase has to follow the viewing angle — a phase driven only by time looks like a looping video, not like foil.
- Stripe emission and the desaturated, thresholded line emission stay separate nodes. The line node may use strength 40 but must be sparsely masked, or it eats the printed detail underneath. Stars combine Voronoi distance-to-edge with animated noise. Card sides get their own material slot, and the compositor glow stays high quality.
- Do not bake the holographic effect into the artwork. If the picture already contains rainbow sweeps and glitter, the material has nothing left to do and the parallax planes turn into soup.
- Export real card geometry from the scene — never a flat screenshot presented as an imported model. The browser contract is the material names `web_front`, `web_edge`, `web_back`, `web_gold` (relief mode adds `web_subject`, `web_effects`, `web_text`), and the page composites the image layers with UV formulas that match the Blender graph.
- glTF's Y-up conversion changes Blender's local axes. Compute `uView` in the canonical card root frame rather than the converted front mesh's frame, and restore the exported V coordinate exactly once. Test both turn directions: one direction will smear the UVs or invert the parallax if the frame is wrong.
- The viewer exposes `window.__holo` (`ready`, `config`, `renderer`, `root`, `uniforms`, `reset`, `flip`, `getState`) for testing, and falls back to a CSS-3D card when WebGL is unavailable. Use the hook for scripted checks; a page that renders does not prove the shaders compiled.

## Resources

- `scripts/run_pipeline.py`: one command from prepared assets to a served card — validate, Blender build, render, GLB export, viewer assembly, dependency install.
- `scripts/ensure_blender.py`: official-release discovery, SHA-256 validation, project-local extraction. If the release index is unreachable but a verified package already sits in `<project>/tools/`, extracting it there is enough — the script returns as soon as it finds `tools/blender*/blender.exe`.
- `scripts/build_card.py`, `scripts/export_web.py`: the editable Blender scene (parallax groups, foil, ink glints, stars, glow) and the geometry/material-role export.
- `scripts/validate_assets.py`, `scripts/generate_typography.py`: layer validation (including the optional effects layer) and accurate transparent typography.
- `scripts/verify_web.mjs`: end-to-end browser verification over the DevTools Protocol — locates a Chromium-family browser (an explicit `--browser`/`RUIC_BROWSER` wins, then the usual install locations, PATH, and Playwright's own downloads; on Linux it passes `--no-sandbox --disable-dev-shm-usage` so root and container runs work), starts the viewer on a free port, exercises every control in a desktop and a 390 px pass, compares captured frames, and writes `<project>/verification/report.json` plus screenshots. Node only, no dependencies.
- `scripts/checkerboard_to_alpha.py`, `scripts/test_checkerboard.py`: deterministic conversion of checkerboard-painted fake transparency, with regression tests.
- `assets/web-template/`: the responsive Three.js viewer: drag, wheel zoom, flip to the back, auto-play, four finishes, and sliders for 镭射 and the layer depths (画面比例 / 画面景深 / 特效景深 / 底纹景深). It ships as a single bundled file so per-module URLs cannot be blocked; rebuild it with `assets/web-template/bundle.sh` (bun, or esbuild when bun is absent) after editing `app.js`.
- `scripts/package_skill.py`: text-only allowlist, content checks and ZIP verification for sharing the skill itself.
