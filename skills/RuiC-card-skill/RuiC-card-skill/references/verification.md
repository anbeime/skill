# Finish by observing the result

A `ready` flag, a saved file or a matching grep is never evidence that the card looks right. Open the thing, look at it, and compare what you see with what was asked for.

## Assets and configuration

- `asset-validation.json` was produced by `scripts/validate_assets.py` and reports every layer: equal canvases, minimum size, real transparency where required (subject, text, and the optional effects overlay), dark contours on white for the line art, and no empty layers. Read it; do not just check that it exists.
- Inspect the layers yourself too: exact names, spelled titles, edition numbering, clipping, registration between subject and line art, and text overlap. Non-Latin glyphs must be glyphs.

## Blender

- The scene keeps X=90° as an **object transform** on the image planes, uses relative paths with packed assets, carries the requested parameters, assigns the edge material to its own slot, and has the compositor glow connected.
- Look at the renders: the front view, and both tilt directions. A tilt render is where inverted parallax, smeared UVs and layers crossing each other show up.
- If a visible Blender window was requested, confirm the window really shows the requested interface language. A saved preference or a live process does not prove a window opened.

## Exported geometry

- Parse `web/assets/card.glb` and confirm it carries meshes and the browser material-role names: `web_front`, `web_edge`, `web_back`, `web_gold` (relief mode adds `web_subject`, `web_effects`, `web_text`). The export is geometry plus role materials, not a render of the finished card.
- Confirm `web/card-config.json` was rewritten with the resolved asset paths and the layer depths the page should start from.

## The running page

- `node scripts/verify_web.mjs <project>` automates the list below: it launches its own headless Chromium and its own viewer server, runs a desktop pass and a 390 px pass, compares real captured frames, and writes `verification/report.json` with screenshots next to it. Run it first, then read the failures it names instead of re-checking by hand. It needs no GUI — on Linux it starts Chromium with the sandbox disabled, so root and container runs work — and no browser needs to be installed by hand: an explicit `--browser`/`RUIC_BROWSER` wins, then the usual install locations, PATH and Playwright's cache are searched. It still does not judge beauty — look at the saved frames and at the live page yourself.
- Serve it, open it in a real browser with WebGL, and wait for textures and the model before judging the picture. Fail on shader compilation errors, missing model or asset requests, and a fallback to the CSS-3D card when the shader engine is what you meant to test.
- Test the interactions and every control: pointer drag, wheel zoom, flip to the back and back to the front, reset, auto motion, the finish options, the screenshot download, the keyboard arrows, and each depth slider — 画面比例, 画面景深, **特效景深**, 底纹景深 — plus 镭射. Confirm each slider actually changes the render, not just its own readout. The download check judges the downloaded bytes — PNG header, byte count, capture size — so a fallback file name from headless Chromium (a non-ASCII title under a non-UTF-8 locale lands as an extensionless `download`) is reported, not failed: only a missing file or a file that is not a full-size PNG is a defect.
- Check both tilt directions for every depth: a signed depth that works one way and smears or inverts the other way usually means the wrong reference frame. In particular, computing `uView` from the exported front mesh instead of the canonical card root frame turns local Y into the normal and smears the UVs.
- Check layout around 390 px and at desktop width, and confirm the reduced-motion setting is respected.
- `window.__holo` (`ready`, `config`, `renderer`, `root`, `uniforms`, `reset`, `flip`, `getState`) exists for scripted checks: drive a view, grab two frames and compare them. Image comparisons have to show observable rotation and a visible change after a depth or foil adjustment.

## Delivery and wording

- glTF cannot carry the custom Blender node graph: the page reproduces the effect in GLSL. Say that plainly, and never advertise pixel-identical offline and real-time output without proving it.
- For text-only distribution run `scripts/package_skill.py`, then inspect every archive member and confirm no image data travelled — no artwork generated for any card, no image-bearing `.blend`/`.glb`/`.gltf`, no video. A PNG base64-encoded inside JavaScript is still image content.
- Report what was actually verified, and name what could not be, instead of implying it was.
