# The ten rules

They come from the study behind the package (lucasmarkes.com/lab/hairline). Each has what it says, how to keep it with the kernel, and what gets a figure rejected.

## 01 · hit: hit areas don't move

Test the pointer against the rest pose, or the target pose, never the pose on screen. Otherwise the geometry lifts out from under the pointer, the hover drops, the geometry falls back, and the hover returns: a flicker loop.

- **Keep it:** `unproj(C, sx, sy, 0)` puts the pointer on the ground plane, which never moves; pick by world coordinates (Terrain). For items, test static bands along their resting edges (Riffle). When a choice depends on a moving value, read the spring's target (`.t`), not its position (`.x`).
- **Keep it, when parts stand at different heights or rise when chosen:** one fixed plane is not enough. The pointer over a raised top lands on that plane behind the part, and between parts at different heights it finds no part at all. Test each part's rest pose instead, as Riffle's bands do. For a single row, take the part whose rest centre, `P(…)[0]`, is nearest the pointer's screen x. For stepped parts, `unproj` onto each part's own rest top, `z` its height, and take the part that puts the pointer nearest its middle.
- **Rejected when:** the pointer held still on a moving edge makes the figure oscillate; picking reads a spring's current value; one fixed plane picks the part behind a raised one, or reads `rest` in the gap between parts at different heights; the figure measures the DOM (`getBoundingClientRect`, `elementFromPoint`, `:hover`) or adds its own pointer listeners.

## 02 · order: stagger by distance

`delay = |i − a| × step`. The motion spreads out from the pointer instead of running down a list.

- **Keep it:** `tset(tween, target, now, Math.abs(i - a) * step)`, with a step of 30–60ms so it reads as one gesture.
- **Rejected when:** items move in index order whatever was touched; all move at once when the concept is a spread; a step so long the last item starts after the first has landed and the gesture reads as a queue.

## 03 · reach: clamp the reach

The answer has a far end, and the figure is still composed there.

- **Keep it:** a falloff that reaches a floor (Terrain's is 1 → .31 at 42% of the radius → .09 beyond); `clamp` every lift, gap and lean; fit the camera to the most extreme pose (`fit` with the lifted points), so nothing leaves the 400 × 320 frame at intensity 1.
- **Rejected when:** at the slider's far end the figure comes apart, overlaps itself or leaves the frame; an unclamped value follows the pointer without limit.

## 04 · accent: the stroke is the only highlight

No fills, glows or shadows. The active edge goes from the silhouette's stroke to the bright one and nothing else changes colour, so the colour reads as information.

- **Keep it:** `el.sil.classList.toggle("hi", active)`. Dots change between `dot`, `dot m` and `dot off`. That is the whole palette. At rest, one bright mark says where the eye should start. When the pointer chooses, the bright goes to what it chose and the rest mark gives it up. One highlight may cover the parts of one thing, a tray's rim and its beads, a dune's top, but it marks one place and means one thing.
- **Rejected when:** the figure sets any colour, fill, opacity trick, gradient, filter, shadow or stroke width of its own; two places are bright at once; the rest mark stays lit beside the pointer's choice; bright is used as decoration.

## 05 · rest: rest is designed, never flat

Leaving returns the figure to a composition: a dune, a lean, a slight explode. The still frame is the thumbnail, so it has to hold up alone.

- **Keep it:** give every part a rest value that is not zero and not uniform (Terrain's dune is two Gaussians; Riffle's cards lean back 12°). Put one bright mark at rest where the eye should start. When the pointer chooses, the mark gives the bright up to what it chose (rule 04).
- **Keep it, when emptiness is the concept:** an empty state shows an object holding nothing. That is right when the object itself is composed, uneven and whole, and one bright mark says where to look. The tray is empty; the drawing is not.
- **Rejected when:** at rest the figure is a flat grid, a tray left empty because nothing was drawn in it, a perfectly regular row; at rest nothing says what the figure is about; rest and "nothing rendered yet" look alike.

## 06 · honesty: construction stays honest

Plates are opaque, filled with the ground colour. Guides and dashed lines are painted behind the plates they belong to, so the drawing never shows a line it should not.

- **Keep it:** append back to front (Terrain walks its grid diagonal by diagonal from the far corner); a shape that must hide what is behind it keeps its fill (no `nf`); guides use `dash` and are appended before their plate. When depth order changes, move the group (`a.after(b)`), do not redraw.
- **Rejected when:** a far edge shows through a near solid; paint order is the order the code happened to make things in; a dashed guide crosses the face of the plate it belongs to.

## 07 · cost: loops sleep offscreen

Only ambient motion runs without input, and only while visible.

- **Keep it:** all motion happens inside `register(stage, tick)`. Return `true` from `tick` only while something is still moving; call `wake()` after input. The loop stops when every figure has settled, sleeps offscreen, and lands springs and tweens at once under reduced motion.
- **Rejected when:** the figure has a timer, a `requestAnimationFrame` or a CSS animation of its own; `tick` always returns `true` in a figure that is not ambient; a path is rewritten on frames where its value did not change (keep the last drawn value and skip).

## 08 · clock: two clocks

A discrete change (which item) gets a long ease-out: 700ms on `(.32, .72, 0, 1)`. A continuous input (where the pointer is) gets a spring, `k 100 · c 18 · m 1`, because its target moves every frame and a timed ease would always be chasing it.

- **Keep it:** `tween` / `tset` / `tval` for which; `spring` / `stepS` for where. Use the defaults unless the figure has a reason you can state.
- **Rejected when:** a tween follows the pointer's position; a spring animates a choice between items; durations or spring constants are invented; anything is linear.

## 09 · radius: round every corner, then draw less

A solid is the hull of two rounded rings, its top and its base. The vertical corners are never drawn. The top edge becomes one dim crease a unit or two inside the silhouette. Bright outside, dim inside: that hierarchy is most of the polish.

- **Keep it:** `rings(x0, y0, x1, y1, r, b)` then `prism(P, front, ring, inner, z0, z1)` into `solid(parent)` with `put`. A thin plate gets a second line for its thickness, not a second solid. Round flat outlines with `fillet`. `rings` takes four steps round each corner, so a full round has sixteen sides, and they show once its radius on screen passes about 20 viewBox units (r × S; r 12 at S 1.9). For a large round, build the two rings yourself with more steps: `rrect(x0, y0, x1, y1, r, 14)` and `rrect(x0 + b, y0 + b, x1 - b, y1 - b, r - b, 14)`.
- **Keep it, when a solid's top is smaller than its foot** (a cabin, a roof, a tower that tapers): `prism` stands one ring straight up, so write its two strings yourself, from two rings. With `foot`, `top` and `inner` each an `rrect`, `inner` being `top` inset by b: the silhouette is `poly(hull(ringAt(P, foot, z0).concat(ringAt(P, top, z1))))` and the crease is `open(ringAt(P, run(inner, front), z1))`. Then `put(solid(parent), { sil, crease })`, as with `prism`. That is all `prism` does, so there is nothing to look up under the index.
- **Keep it, for a mark:** a mark keeps its own corners where rounding would make it another mark. Use the smallest radius that still reads as built, half a unit to two, and round everything that is not the mark as usual.
- **Rejected when:** a box shows twelve edges or any vertical corner line; a corner is sharp; inner lines are as bright as the silhouette; a solid has more than its silhouette, one crease, and at most a few marks the object would really have.

## 10 · quiet: no words inside the figure

Geometry carries identity: a punch on a card's tab, a dot code on a crate's lid, a bright edge instead of a label. Names go to the corner read-out, outside the drawing. Anything decorative has to be something the object would really have.

- **Keep it:** `read.textContent = …` names what is under the pointer, in a few characters (`cell 4·2`, `08`), and says `rest` when nothing is. Number things with dots.
- **Keep it, for a figure made from a mark:** logos stay out when they label something else. The one exception is a figure made from a mark, where the mark is the object: built as a solid, answering the pointer. A glyph that belongs to the mark is a relief on one face. Nothing else in that figure is a letter, and the mark's name still goes to the read-out's side, never into the drawing.
- **Keep it, when a glyph is the subject:** a glyph may be the object when it is built as a solid and is the figure's whole subject, as the package's Query is: a question mark made of a bent bar over a loose ball, answering the pointer. It is a thing in the scene, not a label on one, and nothing else in that figure is a letter.
- **Rejected when:** the svg holds text, letters or digits drawn as paths, icons, arrows or logos, other than the mark, and a glyph that belongs to it, in a figure made from a mark, or a glyph built as a solid that is the figure's whole subject; the figure cannot be understood without its read-out; the read-out is a sentence.

## The frame

Not a rule of the study, but every figure shares it.

- The viewBox is 400 × 320. Centre the figure near (200, 166) with `fit`.
- The camera is `Cam(45, 0.5, S)`: the 2:1 view. Change `S` to fit; leave the angle alone unless the camera is the concept.
- The silhouette must read at 240px wide. Past a hundred or so solids, or with parts under ten viewBox units, it will not.
- `mount` keeps no state outside itself, and `destroy` leaves the svg empty and nothing running: collect tear-down in `disposer()` and return `bag.dispose`.
- At most 200 lines. A longer figure is usually two ideas.
- The tour is three to six viewBox points, or `null` to leave. Pick stops on different parts, in the order a hand would reach them, and end with `null` so the lap returns to rest.
