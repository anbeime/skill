# Printable sheets (A4)

A finished figure can also be printed: one A4 (or US Letter) PDF that explains the machine on paper, drawn from the same page and the same model as the live figure. Make one only when the user asks for something printable: a handout, a poster, a PDF, an A4 or Letter sheet, something for a classroom wall or a binder.

`scripts/print.mjs` does the work. It opens the built light page in headless Chrome, plays the poses you list, and freezes each pose as vector SVG (WebGL layers as a 2× PNG). Then it lays the stills out in one of three formats and prints the PDF with Chrome.

```bash
node scripts/print.mjs examples/raptor-engine/sheet.mjs                 # poster, A4
node scripts/print.mjs examples/raptor-engine/sheet.mjs --format all --png
node scripts/print.mjs examples/arcade-cabinet/sheet.mjs --format detailed --letter
```

It writes `<out>-<format>-a4.pdf` and `.html` next to the spec (`-letter` with `--letter`), plus a preview `.png` with `--png`. It exits 1 when a format runs past its page count.

## The three formats

| Format | Pages | What is on it | Use it for |
|---|---|---|---|
| `poster` (default) | 1 | The name set large, the question and a short lead, a column of big numbers, the figure with numbered pins, then every part with one line on what it does | A wall, a cover sheet, a first look |
| `drawing` | 1 | A drawing header with a number, the figure with pins, a parts list, a specification, a small inset of another pose, then a strip of steps with the parts at work lit | A technical handout |
| `detailed` | 2 | Page 1: the figure with pins and lettered close-up marks, the question, lead, numbers, every part with its line, and round close-ups under the figure. Page 2: each step as a large lit still with two or three sentences, the why, and the specification | Homework, a binder, someone who wants to understand it fully |

All three are minimal and print well in black and white: hairline rules, one sans for words, mono uppercase only for labels, black pins, and the figure in the light theme on white paper.

## The spec

A sheet is a module next to the example, `sheet.mjs`, whose default export says where the page is, what to capture and what to say. Every number and sentence in it must come from the figure's model or caption, the same truth rule as the figure itself.

```js
export default {
  page: "raptor-engine-light.html",             // the built light page, relative to this file
  out: "raptor-engine",                         // output base name
  layers: ".rp-stage > svg.rp-back, .rp-stage > svg.rp-front", // the SVG layers to freeze, back to front
  rasterSelector: ".rp-stage",                  // the box that WebGL shots are cropped from
  strip: [".rp-deckglow"],                      // elements to drop from every still
  reduced: true,                                // emulate reduced motion (calm, no tour); false to catch animation
  views: {                                      // poses, captured in this order, each after its actions
    rest: {},
    apart: { actions: [["key", " "], ["wait", 2500]], reset: [["key", " "], ["wait", 2500]] },
    firing: { actions: [["key", "i"], ["wait", 3500]], raster: { region: [250, 150, 432, 530] } },
  },
  name, title, number, tagline, question, lead, quote,
  numbers: [["230", "tf", "thrust at sea level"]],
  spec: [["Chamber", "300 bar"]],
  why: { title: "Why full flow?", text: "…" },
  parts: [{ id: "otp", name: "Oxygen turbopump", say: "…", select: '.it[data-piece="otp"]', at: [x, y] }],
  main: { view: "apart", crop: [x, y, w, h], layers: [1], hide: ["stand"] },
  inset: { label: "Assembled", view: "rest", crop: [x, y, w, h] },
  steps: [{ view: "apart", title: "…", text: "…", focus: ["otp", "ftp"] }],
  details: [{ title: "…", text: "…", around: ["otp"], focus: ["otp"] }],
};
```

- **Actions** are `drive.mjs` actions. `["slow", 0.03]` then `["until", js]` catches a moment of an animation exactly (the arcade's coin in the chute); `reset` puts the page back before the next view.
- **Parts** are CSS selectors over the live SVG, so any figure works: the Raptor's assemblies are `.it[data-piece]` groups, the arcade's are `[data-name^="mech"]` prefixes from its recorder names. A part without a `name` is not listed or pinned, but steps can still light it (`coin`) or hide it (`stand`). The pin sits at the centre of the part's largest shape; give `at` (viewBox units) where that lands in empty space. Pins that crowd each other spread apart and draw a hairline back to their point.
- **Focus** lights the listed parts (black lines) and greys everything else, labelled or not. **Hide** removes a part from that still: hide what stands in front of a close-up (the arcade's coin door in front of the mech).
- **Crops** are in the figure's viewBox units. Without one, the main view crops to its drawn content; steps and close-ups crop around their focus or `around` parts, never below 42% of the main crop's width.
- **Rasters** are for WebGL only. Mark the view `raster` with the viewBox `region` to shoot; the plume prints as a 2× PNG inside the vector page.
- **Text** has to fit: titles of five words or fewer for steps, one line per part, two or three sentences per step. The script fails when a format runs onto another page.

## Check it

1. Build the light page first (`node build.mjs --light`).
2. Run with `--format all --png` and read every PNG. Look for pins on empty space, a close-up that shows the wrong part, a lit part hidden behind another, and text cut at the foot of the page.
3. Zoom into the PDF or the HTML at 4× (`drive.mjs` `["shot", out, ".ps", 4, [x, y, w, h]]` on `<name>.html?print`): lines must be vector and crisp, and the lit parts must stand out at the size of a step still.
4. Print one page if you can. Light-grey dims and hairlines must still read on an office laser printer.

## A PDF link on the figure

`kit/pdf-button.mjs` exports `pdfButton(href)`: a small "PDF" link with an icon at the top right of the card, carrying its own CSS so pages without it are unchanged. Put it first inside the plate body and only when the file exists (`examples/push-button/build.mjs`). Order: build the light page, print, then rebuild so the button appears.

## Longer detailed sheets

`detailed` runs 2–4 pages, chosen from the spec:

1. Overview (always): pinned figure, numbers, parts with a line each, round close-ups (`details`).
2. How it works: steps six to a page, the `why` taking the last slot; more steps flow onto another page.
3. Assemblies (when the spec has `assemblies`): up to four per page, each `{ title, text, parts: [ids] }` drawn as a large lit close-up with its own pins and part numbers. Give a figure with ten or more parts three or four groups.
4. The specification closes the last page.

`maxPages` (2–4, default 4) caps the count: assembly pages drop first, and too many steps for the cap is an error. `examples/raptor-engine/sheet.mjs` (3 pages) is the reference; `push-button` and `arcade-cabinet` stay at 2.
