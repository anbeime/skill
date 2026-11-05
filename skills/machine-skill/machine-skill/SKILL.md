---
name: machine
description: Turn one line ("a turbofan jet engine", "a mechanical watch", "an LVAD heart pump") into a photoreal, physics based, interactive 3D simulation of that machine in a single HTML file, plus a 20 to 30 second film to post it. Real proportions in metres, real materials (PBR metals, paints, polymers, glass), studio lighting with soft shadows, moving parts driven by a small solver that computes real numbers (thrust, torque, rpm, flow, pressure, efficiency), and modes to explode it, cut it open with clean section caps, x-ray it, slow it down, label it and break it. Use this whenever someone asks to build, simulate, visualise, explain or "show how X works" for any machine, engine, mechanism, device, instrument or piece of hardware, wants an interactive 3D model or a cutaway, or wants a video of a machine for a post, even if they never say "simulation" or "three.js".
---

# Machine Skill

You build a machine the way a product studio photographs one and an engineer explains one: the real thing at its real size, in real materials, on a clean studio set, running on real equations. One line in, one HTML file out, and a film in one command.

The output is always:

1. `<name>.html`: a single self contained page (three.js 0.170 from jsDelivr, the kit inlined). It opens from disk, from any static host, or inside an iframe.
2. A film: `node scripts/record.mjs <name>.html out/<name>.mp4 --music freepd:<Category>/<Name>`.

Open `examples/` first. Every example was made from the one line at the top of its page. `examples/turbofan.html` is the reference: read it end to end before you write anything.

## The bar

Before you start, picture the frame a viewer sees after three seconds. It must already look like a studio product photograph of the real machine: correct silhouette and proportions, metal that reads as metal, a soft shadow on a paper floor, nothing floating, nothing clipping, nothing placeholder. Then it moves, and every number on screen is computed.

A result is not done while any of these is true:

- a part a mechanic would expect is missing (no fuel nozzles in a combustor, no escapement in a watch, no valves in an engine)
- something floats, intersects, or has a visible seam or gap at a joint
- a material looks like plastic when it should be metal, or everything is one grey
- a number on screen is typed in rather than computed by the solver
- the cutaway shows hollow shells instead of solid section faces
- the first frame of the film is not beautiful

## Workflow

### 1. Research the real machine (5 minutes, no code)

Write down, in a comment block at the top of the machine script, from what you know (and the web if you have it):

- **The real dimensions** in metres of the 5 to 10 parts that define the silhouette (a turbofan: fan diameter 2.85 m, length 4.9 m, nacelle max diameter 3.44 m).
- **The parts list** in assembly order, each with its material. Aim for 15 to 40 named parts; repeated parts (blades, teeth, bolts, coils) count individually.
- **The physics** that makes it work, as 3 to 6 equations you will actually compute, with real constants and the operating point (a turbofan: Brayton cycle, take-off at N1 100 %, OPR 42, T4 1,750 K, about 330 kN).
- **The one number** a viewer cares about: the hero (thrust, torque, beats per hour, flow, power). It gets a huge serif readout and a thin bar.
- **The input** a viewer wants to drive: one slider (throttle, wind speed, rpm, pump speed, grind size).
- **The break**: the failure an engineer worries about, and what the solver says happens (fan blade off and the imbalance load, valve float above the redline, a stalled pump, overpressure). This must be a computed consequence, not an animation.

### 2. Build the page from the template

Copy `kit/template.html` to `<name>.html`. It has the import map (pinned three@0.170.0), the fonts, a marked block where the kit goes, and the four sections you fill in:

```js
const { THREE, Lab, MAT, GEO, heatGlow, clamp, lerp, approach, fmt } = window.LabKit
const lab = new Lab({ prompt, no, title, sub, size, view, cut })   // 1. the lab
// 2. the parts      lab.mesh(GEO..., MAT..., { name, pos, explode, xray, count })
// 3. the solver     lab.hero(...); lab.slider(...); lab.onTick((dt, lab) => { ... lab.setHero(...) })
// 4. break, explain, film      lab.breakIt(...); lab.how(...); lab.autoFilm(...); lab.start()
```

Right after copying, run `node <skill dir>/scripts/inline.mjs <name>.html`: it pastes the kit into the marked block so the page is one self contained file wherever it lives (the template's `src="../kit/lab-kit.js"` only resolves inside this repo). Then write your machine in the second script block.

### 3. Geometry: real solids at real size

Work in metres in the machine's own frame, Y up, the floor at y = 0 unless you set `ground`. Set `size` to the longest real dimension; the kit scales the display so every machine sits the same on the set, and the scale bar shows real size.

- **Round parts** (shafts, discs, casings, nozzles, cones, spinners, pistons, bezels): `GEO.lathe([[r, y], ...])` with a CLOSED profile. Walls: `GEO.shell(profile, thickness)`, tubes: `GEO.tube(rOut, rIn, h)`, chamfered discs: `GEO.disc(r, h)`. Corners stay crisp and curves shade smooth automatically.
- **Blades and vanes**: `GEO.rotor({ count, axis, r0, r1, chord, thick, camber, twist, pitch, sweep })` builds real cambered, twisted airfoils (NACA thickness) as closed solids and rings them. Use `[root, tip]` arrays for chord, thick and camber.
- **Gears**: `GEO.gear({ teeth, module, width, bore, helix, spokes, rim })`. Mesh two gears at centre distance `(z1 + z2) * module / 2` and turn them at the inverse tooth ratio, offset by half a tooth.
- **Pipes, hoses, wires**: `GEO.pipe(points, r)` (closed, capped). Route them along the structure from port to port, never through a part.
- **Fasteners**: `GEO.bolts(n, R, size, h)` on every flange. Springs: `GEO.spring(R, wire, turns, len)`. Boxes: `GEO.rbox(w, h, d, r)` (always rounded, never sharp). Plates with holes: `GEO.extrude(shape, depth)`.
- **Masses and inertias** come from the geometry: `GEO.volume(geo)` gives volume and centroid, multiply by the real density.

Rules that keep it clean:

- **Every part is a closed solid** (lathe profiles closed, shells with thickness, pipes capped). That is what lets the cutaway draw solid section faces. Open surfaces show as hollow when cut.
- **Nothing intersects visibly and nothing floats.** Every part touches what holds it (a flange sits on a face, a shaft runs in a bearing, a post reaches the floor). Check joints in close ups.
- **Detail where the eye goes**: bolt circles on flanges, chamfers, a lip, a label plate, fuel lines, a harness. Big flat areas get a seam, a panel line or a texture finish.
- **Give the machine a base**: a stand, cradle, plinth, bench or mount with feet on the floor. Machines rarely float in real life.
- **Budget**: up to about 700k triangles and 200 meshes. Merge repeated static parts with `GEO.merge` / `GEO.ring`; keep moving groups separate.

### 4. Materials: never one grey

Use `MAT.*` presets; they carry measured reflectances so steel, titanium, aluminium, brass and copper look different side by side. Every preset takes overrides (`color`, `roughness`, `clearcoat`, any MeshPhysicalMaterial field) and a `finish` (micro roughness texture: `turned` rings on lathe parts, `brushed` streaks, `cast` blotches, `smudge`, `knurl`).

| Use | Preset |
|---|---|
| shafts, discs, machined parts | `MAT.steel`, `MAT.stainless`, `MAT.chrome` |
| housings, castings | `MAT.aluminium`, `MAT.castIron`, `MAT.steelDark` |
| blades, aerospace | `MAT.titanium`, `MAT.inconel` (+ `heatGlow`) |
| fittings, wiring | `MAT.brass`, `MAT.copper`, `MAT.gold` |
| painted bodies | `MAT.paint({ color })`, `MAT.satin`, `MAT.anodised({ color })` |
| polymers | `MAT.plastic`, `MAT.rubber`, `MAT.carbon` |
| windows, crystals | `MAT.glass`, `MAT.sapphire`, `MAT.ruby`, `MAT.enamel` |
| light, flame, hot gas | `MAT.glow`, `heatGlow(material, kelvin)` |

Pick a palette like an industrial designer: mostly metals and one or two painted colours, one accent at most. Hot parts glow from the solver's temperature (`material.userData.heat.value = T`).

### 5. The solver: real numbers or nothing

Write a small pure function from the input and state to every number you show, with real units and real constants. Integrate dynamics with `approach` (first order lag: spool up, thermal mass) or `rk4` (springs, escapements, pendulums). Then drive the motion from it: an rpm from the solver turns the shaft, a flow from the solver moves the particles, a temperature heats the metal.

- One hero: `lab.hero({ label, unit, max })` then `lab.setHero(value, { state, sub, bad })` each tick. `state` is two or three words (spooling up, take-off, choked flow). `sub` is one line with 2 or 3 more numbers.
- One slider: `lab.slider({ id, label, min, max, value, unit, ends })`. A second only if the machine truly needs it.
- Labels hang on static parts at points on the section planes: `lab.label(obj, 'HP turbine', { at: [x, y, z], value: () => '12,979 rpm' })`.
- `lab.how(words, equations)` fills "How it is computed": the model in plain words and the equations as written in the code. Say what is simplified.
- If a motion is too fast to see (a 2,700 rpm fan), show it slowed and say so in `how` ("spin shown 1:60"). Never slow the numbers.
- Sanity check the operating point against the public figure you wrote down in step 1. If you are off by more than about 20 %, fix the model, not the number.

### 6. Flow, heat and effects

- `lab.flow({ paths, count, length, color, parent })`: streaks that ride along paths you build from the real flowpath (air through a duct, blood through a pump, water through a puck). Set `.speed` from the solver and `.opacity` from `lab.state.cut` so they show inside the cutaway. Colour by a computed quantity (temperature, pressure).
- `lab.plume({ radius, length, dir, color: 'rocket' | 'jet', shocks })`: an exhaust with Mach diamonds; set `.power` from the solver.
- `lab.sparks.emit(worldPos, n, speed)` and `lab.shed(mesh, v, w)` for breaks: sparks fall with gravity and bounce; a shed part becomes a rigid body that lands on the floor.

### 7. Modes (the kit does them; you set them up)

- **Explode**: each `lab.add`/`lab.mesh` takes `explode: [dx, dy, dz]` in the parent's frame (metres). Move parts along their assembly axis, outer shells furthest, and keep the core in place. Nothing should cross anything on the way out.
- **Cutaway**: `cut: { a, b, center, reach }` on the Lab. `a` and `b` are the directions of the removed region: `a = [0,0,1], b = [0,1,0]` removes the quarter toward the viewer and up (best for things with an axis); `b = a` removes a half. Section faces are drawn automatically for every closed solid, with a faint hatch.
- **X-ray**: `xray: 'shell'` on outer casings turns them to glass with fine edges, so the core shows while it runs.
- **Slow motion, labels, pause** come for free (keys S, L, Space). The interactive parts are mouse orbit, the slider and the buttons.
- **Break it**: `lab.breakIt({ label, run(lab), reset(lab) })`. `run` changes the solver state (a blade released, a valve stuck, a seal blown) and the solver computes the consequence. Show it in the hero (`bad: true`) and with sparks, debris or shake.

### 8. Look at it like a critic (required)

Render and READ every image you make. Use the scripts:

```sh
node scripts/shot.mjs <name>.html out/review.png                               # the first look
node scripts/shot.mjs <name>.html out/cut.png --js "lab.toggle('cut', true); lab.toggle('labels', true)"
node scripts/shot.mjs <name>.html out/near.png --js "lab.setView({ az: 70, el: 8, dist: 0.8, target: [x, y, z] })"
node scripts/shot.mjs <name>.html out/film --film 1,4,8,12,17,22,26                 # film stills
```

Do at least four review rounds. In each: whole view, cutaway with labels, exploded, two close ups of joints, and the film stills. Compare against real product photography of the machine in your memory: proportions, part count, materials, how light falls on it. List what is wrong, fix it, render again. Stop only when the list is empty. The shot script prints fps, part count and triangles; keep interactive frame rates above 30.

### 9. The film

`lab.autoFilm({ runBeat, runSub, breakBeat, breakSub, sliderTo })` writes the standard 28 second story from your machine, in numbered beats with the editorial captions:

1. One sentence is the whole brief (the prompt bar types itself).
2. Claude builds the machine (parts fly in by assembly order while the counter climbs: "84 of 3,597 parts").
3. It runs (a cursor drags the slider; the hero number climbs from the solver).
4. Cut it open (section caps, labels with live values).
5. Take it apart (explode).
6. Break it (the cursor clicks the break button; the solver decides what fails).

It loops: the last camera key returns to the first. For a custom film use `lab.film('name', { len, assemble, shots, events })`: shots are camera keys `{ t, az, el, dist, target, fov }`, events are `{ t, beat: ['07', 'Bold sentence.', 'Grey sentence.'], set: { cut: 1 }, slider: { id, to, dur }, cursor: { to: 'slider:id:0.8' | 'button:break' | [x, y], click: true }, do(lab) {} }`.

Record (needs Node 18+, Playwright with Chromium, ffmpeg):

```sh
node scripts/record.mjs <name>.html out/<name>.mp4 --music freepd:Classical/Easy_Lemon
node scripts/record.mjs <name>.html out/<name>-portrait.mp4 --w 1080 --h 1350
```

The page runs in film mode (`?film=1`): its clock only moves when the recorder steps it, so every frame is complete and the film is identical every take. The recorder guards every screenshot against the magenta frames a stalled headless GPU can return, and scans the finished film; it exits non zero if any frame is pink. Music from FreePD is CC0; credit the track anyway.

## Writing on screen

The page is editorial, not a dashboard: a prompt bar, a serif title with an italic subtitle, one huge number with italic units and a thin bar, one line of supporting numbers, one slider. Write like a good caption: short, concrete, no hype, real units with a space (`338 kN`, `1,750 K`, `4.2 L/min`), thousands separated. Beat captions are a bold sentence and a grey sentence.

## What to say when you hand it over

Give the path of the HTML file, the film command, the operating point the solver reaches against the public figure, and anything you simplified. Offer the next machine.
