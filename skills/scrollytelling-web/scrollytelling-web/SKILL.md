---
name: scrollytelling-web
description: "Design and implement cinematic scroll-driven web narratives: pinned scenes, scrubbed timelines, product decomposition, image sequences, section transitions, spatial storytelling, and progressive 3D reveals. Use when scroll itself drives the story."
---

# Scrollytelling Web

Build scroll experiences as authored narratives, not a pile of parallax effects. Scroll is the user's timeline controller; every pinned section, camera move, reveal, and product transformation must advance understanding or emotion.

## 1. Storyboard before code

Convert the page into **beats**. For every beat define:

- what the user should understand or feel;
- what remains spatially stable;
- what changes with scroll progress;
- the entry and exit state;
- whether the user can stop at any intermediate frame without seeing a broken composition;
- mobile/reduced-motion alternative.

For a product-decomposition sequence, a useful structure is:

1. establish the intact product;
2. isolate the key assembly;
3. explode parts along authored axes;
4. hold long enough for labels/copy to explain them;
5. move camera or product only after the part relationship is understood;
6. reassemble or transition into the next narrative state.

Do not make everything move simultaneously. Choreography needs hierarchy.

## 2. Pick the smallest correct engine

Use the simplest tool that can express the intended motion **well**:

- **CSS transitions / native scroll-driven animation** — simple reveals, progress-linked decoration, sticky sections with modest transforms.
- **Motion (`motion/react`)** — local React interactions, springs, component transitions, lightweight viewport effects.
- **GSAP + ScrollTrigger** — default for serious scrollytelling: pinned/scrubbed timelines, coordinated multi-element chapters, horizontal story tracks, image-sequence scrubbing, long-form section handoffs, precise start/end markers.
- **Lenis / smooth-scroll layer** — only when the choreography materially benefits from controlled smoothing. Never add scroll hijacking as decorative infrastructure.
- **Lottie / Rive** — authored 2D/vector animations with well-defined state machines or timelines.
- **Three.js / React Three Fiber** — real 3D camera work, lighting, materials, exploded assemblies, depth, product rotations, particles, or scenes where flat DOM transforms would be a fake substitute.

If a 2D solution communicates the product just as well, do not pay the 3D complexity/performance tax.

## 3. Scroll model

Normalize complex scroll experiences around a semantic progress value (`0..1`) or named chapter states. Keep narrative state separate from raw browser events.

Do **not** wire dozens of independent `scroll` listeners that each call layout reads and state updates. Prefer one timeline/controller that owns the sequence.

For GSAP, pair with `gsap-scrolltrigger`. For React, also apply the project's lifecycle/cleanup conventions and keep hot continuous values out of React render state.

## 4. Pinned scene rules

Pinned scenes work when the user understands why the page temporarily stops moving in document space.

- Pin a stable wrapper/stage; animate descendants or scene state rather than fighting the pinned element's own transform.
- Give the sequence enough scroll distance to read, but do not make the user grind through empty motion.
- Design the exact first and last frame so the handoff back to normal document flow is seamless.
- Avoid multiple nested pins unless there is a compelling reason and tested behavior.
- Recompute positions after asset/font/layout changes when the animation engine requires it.
- Test browser resize, dynamic address bars, and orientation changes.

## 5. Product exploded views

When the brief asks to “descompose/despiezar/explotar” a product:

### Asset preparation

Prefer a properly authored GLB/glTF with meaningful node names and pivots. Parts that must separate independently need separate meshes/groups. Preserve a hierarchy that matches the product's conceptual assemblies.

If only a flattened render/image exists, do not pretend it is genuine 3D. Use an image-sequence/masked 2.5D treatment or request/produce the missing 3D asset through the project's asset workflow.

### Explosion choreography

- Define an intact pose and an exploded pose for each semantic part.
- Use authored local axes or vectors; random radial explosions look like a debug visualization.
- Stagger related assemblies in logical order.
- Keep labels anchored to the relevant part and readable through camera motion.
- Let camera movement support the part motion, not compete with it.
- Reserve depth, rotation, focus changes, and lighting shifts for explanatory emphasis.

### Scene quality

For premium product work, lighting/material/camera quality matters as much as the scroll linkage. Use physically plausible materials when the object demands realism, intentional environment/reflections, restrained post-processing, and consistent tone mapping. Avoid excessive bloom and “tech neon” unless the brand actually calls for it.

Use `threejs-product-storytelling` for the scene-specific craft layer.

## 6. Image-sequence scrollytelling

For photorealistic product transformation without real-time 3D, pre-rendered sequences are often the best solution.

- Decode/preload intelligently around the current frame instead of loading hundreds of full-size frames synchronously.
- Prefer modern formats where the delivery pipeline supports them.
- Draw to a canvas sized for the displayed resolution, not the original camera master.
- Map scroll progress monotonically to frame index; avoid jitter from repeated rounding around boundaries.
- Provide a poster/static state before the sequence is ready.
- On constrained mobile/network conditions, fall back to a short video/static milestone sequence if needed.

## 7. Typography and narrative layering

Copy is part of the choreography. Avoid forcing users to read paragraphs while the visual target is still moving aggressively.

A reliable pattern is: movement → settle/hold → explanation → movement. Keep text spatially stable during reading moments unless kinetic type itself is the concept.

## 8. Performance budget

Cinematic does not mean unbounded.

- Prefer transforms/opacity and engine-managed transforms on hot paths.
- Avoid synchronous layout thrashing.
- Lazy-load below-the-fold heavy scenes.
- For WebGL, cap device pixel ratio deliberately, especially on mobile/high-DPR devices.
- Compress textures and geometry; use sensible texture dimensions and mipmaps.
- Pause rendering/animation when a scene is no longer visible where possible.
- Dispose GPU resources when scenes unmount.
- Do not make a full Three.js render loop run forever for a static offscreen scene.
- Keep DOM overlay count reasonable inside long pinned scenes.
- Profile the actual target browser/device instead of assuming 60 fps from a desktop dev machine.

Pair with `gsap-performance` for GSAP-heavy work and normal frontend performance tooling for the rest.

## 9. Accessibility and input

Scroll storytelling must remain content, not a trap.

- Honor `prefers-reduced-motion`; provide a meaningful static/chapter-based version rather than merely setting durations to zero while preserving bizarre intermediate states.
- Do not make essential content exist only at one transient animation frame.
- Preserve normal page scrolling unless there is an exceptional, justified experience mode.
- Touch users need an equally understandable composition without hover assumptions.
- Keyboard users must be able to reach interactive content inside/around pinned sequences without focus disappearing behind layers.
- Avoid rapid flashing and vestibularly aggressive camera moves.

## 10. Verification contract

Before claiming done:

1. verify the sequence from start to finish at a desktop viewport;
2. verify at a narrow mobile viewport;
3. inspect at important scroll milestones (start, 25%, 50%, 75%, end or semantic beats);
4. verify reverse scrolling;
5. resize mid-sequence;
6. test reduced-motion;
7. inspect console/runtime errors;
8. check that sticky/pinned sections do not leave blank gaps or jump on handoff;
9. profile obvious frame drops and memory leaks;
10. confirm content remains understandable with motion disabled.

A screenshot of only the hero is not evidence that scrollytelling works.

## Pairing

Use with:

- `design-taste-frontend` — art direction;
- `impeccable` — composition/craft;
- `emil-design-eng` — motion feel;
- `gsap-scrolltrigger` — scroll mechanics;
- `gsap-performance` — hot-path correctness;
- `threejs-product-storytelling` — genuine 3D product scenes;
- `browser-testing-with-devtools` — rendered verification.
