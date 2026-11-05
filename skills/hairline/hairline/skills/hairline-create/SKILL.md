---
name: hairline-create
description: Use when someone asks for a new Hairline figure, or runs /hairline-create with an idea. Draws one isometric line figure that answers the pointer, in the style and on the engine of @lucasmarkes/hairline, and hands it over as a single self-contained HTML file.
argument-hint: "[idea]"
---

# Hairline: create a figure

You are making one figure in the Hairline style: an isometric line drawing, built from rounded solids in a single stroke, that answers the pointer. It ships as one HTML file with nothing to install. The six figures of `@lucasmarkes/hairline` are the bar; `examples/terrain.js` and `examples/riffle.js` are two of them, in the format you will write.

You write one thing: the figure. The engine (`kernel.js`) and the page (`bench.html`) are fixed. Never edit them, never paste a changed copy of them, and never write again what the kernel already gives you.

Every file named below is in this skill's folder. The figure and the page are written in the person's working directory: run `build.mjs`, `validate.mjs` and `look.mjs` from there, by their path in this folder.

## 0. Source

Only when the request came with an `.svg` file. Run `node read.mjs <file.svg>`: it writes the SVG as a picture and a card of what it measured, both in the working directory. Then read `source.md` and answer its questions. The object and its parts are now fixed: every concept in step 1 keeps them.

## 1. Concept

Read `concepts.md`. It has a section for an empty state and one for a figure drawn from a mark. Then offer two or three concepts, one line each:

> **Name.** The object. What the pointer does to it. What the read-out says. Where the tour stops.

Wait for the person to pick. Skip this step only when they arrived with the object and the gesture already chosen. If there is nobody to ask, take the concept with the strongest rest pose and say which you took.

With a source (step 0), every concept keeps the object and its parts: they differ in the gesture, or, when the gesture came with the request, in the form and the read-out.

One figure, one idea. A concept that needs a label to be understood is not a concept yet.

## 2. Build

1. Read `rules.md`. The ten rules are not advice: a figure that breaks one is not finished.
2. Read the index at the top of `kernel.js`: the comment under the hash line, down to `var HL`. It lists everything you may call. Do not read the code under it.
3. Read the example nearer your concept: `examples/terrain.js` for a continuous field, `examples/riffle.js` for discrete items.
4. Write the figure as `<name>.js` in the person's working directory, in the shape of the examples: take what you need from `HL`, define `mount({ stage, svg, read }, value)` returning `{ set, destroy }`, and end the file with `hairline({ name, means, rules, range, tour, mount })`.
   - `name`: lowercase, one word or hyphenated.
   - `means`: one sentence, 140 characters at most, saying what the figure shows. It is the line under the stage.
   - `rules`: the numbers of the rules this figure leans on most.
   - `range`: the one number the slider drives, at intensity 0, 0.5 and 1. The middle one is the default, and the three move one way. `mount`'s `value`, and the `value` that `set(value)` gets when the slider moves, is this number: the figure's own, read on `range`, not 0 to 1.
   - `tour`: the three to six viewBox points the unseen pointer visits when the page plays, or `null` to leave; the lap a stranger sees with no hand on the page. Literal `[x, y]` numbers, at least one of them a point. The figure never plays itself: the page's play button and the package do.
5. Assemble it: `node build.mjs <name>.js` writes `hairline-<name>.html`, and so does each run of `look.mjs` in step 3. Without Node, copy `bench.html` and put the contents of `kernel.js` where `/*KERNEL*/` is and your figure where `/*FIGURE*/` is, by file operation, changing nothing else.

## 3. Check

1. `node look.mjs <name>.js --answer x,y,z --edge x,y,z`, and `--source <file.svg>` when there is one, the points being world points of your figure, as `look.md` says. It builds the page, validates it, takes the eight pictures on one sheet, `hairline-<name>-look.png`, and checks the frame, the read-out and the console. Fix every line it prints as failed, and run it again until it exits 0.
2. Read `look.md`, then the sheet, and answer its questions. Fix what fails, then go back to 1.

`look.mjs` needs a browser and installs `playwright-core` once, outside this folder. Without one, check with `node validate.mjs hairline-<name>.html` after each build and do the look as `look.md` says under "Without a browser". Without Node, read the list of checks at the top of `validate.mjs` and answer each one from your code.

Do not hand over a page the validator rejects. Do not say the look is done if you did not look.

## 4. Hand over

Publish `hairline-<name>.html` as an artifact if you can. If you cannot, leave the file where the person can open it and say where it is. Then say, one line each:

- the metaphor: what the object is, and what the pointer does to it;
- the rules it leans on;
- the tour: where it stops, in order;
- anything you could not verify (no Node, no browser), plainly.

Then ask the person to press play on the page, or open it with `?play=1`, and say whether the lap tells the figure's story. If there is nobody to ask, say the tour was not judged.

## 5. Adjust

When the person asks for a change, edit only `<name>.js`, then run `look.mjs` again and read the new sheet. The tenth version is held to the same bar as the first. A change to the lap is a change to `tour` alone.

## What goes wrong

| If you catch yourself | Do this instead |
| --- | --- |
| adding a label, a number or a letter to the drawing | say it with geometry (rule 10); names go to `read.textContent` |
| reaching for a colour, a fill or a glow | move one stroke from `sil` to `hi` (rule 04) |
| writing a timer, a `requestAnimationFrame` or a CSS animation | `register(stage, tick)`, with springs or tweens (rules 07 and 08) |
| testing the pointer against what is drawn right now | test it against the rest or target pose (rule 01) |
| drawing a box with twelve edges | `prism` of two rounded rings: a silhouette and one crease (rule 09) |
| drawing a part as a plain rounded block | give it the features that make it what it is, the ones you named in the concept (`concepts.md`) |
| leaving rest flat, empty, or symmetric because that was easy | compose it: rest is the thumbnail (rule 05) |
| stamping a mark on a box to say whose it is | build the mark as the object, or leave it out (`concepts.md`, "From a mark") |
| editing the kernel or the bench to make something work | the figure is wrong; change the figure |
| making the tour visit every part in turn | three stops that each show a different answer, then a leave: a lap is a sentence, not an inventory |
| letting in a second idea | cut it: one figure, one idea |
| tracing a path from the SVG, or copying its coordinates | build the part as a solid with the proportions the card gives (`source.md`) |
| keeping a part of the SVG that is decoration | drop it: two or three parts make the object |
