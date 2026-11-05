# The look

The validator reads text. This is what only eyes can check. Do it every time the figure changes.

## One command

From the person's working directory:

`node <skill folder>/look.mjs <name>.js --answer x,y,z --edge x,y,z [--source <file.svg>]`

It builds `hairline-<name>.html` and validates it, as `build.mjs` and `validate.mjs` do. If the validator rejects the page, it prints the lines to fix and stops before opening a browser. Otherwise it opens the eight pictures of the table below at once, in one browser, takes each once its drawing holds still, and writes them, labelled, on one sheet: `hairline-<name>-look.png`. Then it prints one line for each of items 9, 8, 12 and 4, and the sheet's path. It exits 1 when the validator rejects the page or item 9, 8 or 12 fails, and 0 otherwise. Read every line it prints, then read the sheet and answer the rest.

- `--answer x,y,z` is a world point on the part that should answer the pointer: a point on the part's top in its rest pose. `look.mjs` runs it through the `P` your figure made with its own camera and prints the `?at=` point it got. For the riffle example, the top edge of card 05 at rest: `--answer 42,28,52` prints `answer 42,28,52 -> at=220,120`, and the answering pictures read `05`.
- `--edge x,y,z` is a world point at the figure's edge, for the slider's two ends (item 9). Give it twice for a point per end: the first is taken at intensity 0, the second at 1. Without it, the ends hold the `--answer` point.
- Either takes a viewBox point `x,y` instead, used as it is.
- Without `--answer`, the answering pictures are taken at rest, and it says so. That is not a finished look.
- `--zoom <shot>` also writes one picture's stage at three times the pixels, as `hairline-<name>-<shot>.png`, for what is too small on the sheet: a crease, a far edge, a dot. The shots are `rest`, `answer`, `small`, `small-answer`, `low`, `high`, `dark` and `light`, in the table's order.
- `--source <file.svg>`, for a figure made from a drawing the person brought (`source.md`), adds a first row to the sheet: that drawing beside the rest picture, at the same size, labelled `source`. It exits 2, before building anything, when the file cannot be read as an SVG.
- In place of `<name>.js` it takes a page already built, `hairline-<name>.html`.

A change that moves the fit or the scale moves every `?at=` point with it. The world points stay where they are: give the same ones again and the new `?at=` points come out.

The first run installs `playwright-core` once, into a cache folder of yours (`~/Library/Caches/hairline-look` on macOS, `%LOCALAPPDATA%\hairline-look` on Windows, `~/.cache/hairline-look` elsewhere; `HAIRLINE_LOOK_CACHE` moves it), and never into the skill or the working directory. It drives your Chrome, or Playwright's Chromium when there is no Chrome. With neither, it prints the one command that installs Chromium and exits 2. It exits 2 as well when it cannot install; then do the look as "Without a browser" says.

## The pictures

These are the eight `look.mjs` takes. Four parameters in the address make them, and they work in any browser, for a look by hand; join two with `&`:

- `?w=240` narrows the page to 240px, the size of a thumbnail.
- `?at=x,y` holds the pointer at a point of the 400 × 320 viewBox, for tools that cannot hover. x runs to the right and y down, from the viewBox's top-left corner. Take the point from your own figure: the screen point `P(x, y, z)` of the part you want answered, rounded. `P` exists only inside the page; `look.mjs` prints it for you.
- `?intensity=` sets the slider, from 0 to 1, before the figure mounts.
- `?theme=light` or `?theme=dark` sets the theme, as pressing its button does.

| Shot | Picture | Address |
| --- | --- | --- |
| `rest` | full size, at rest | `hairline-<name>.html` |
| `answer` | full size, answering | `hairline-<name>.html?at=<x>,<y>` |
| `small` | 240px, at rest | `hairline-<name>.html?w=240` |
| `small-answer` | 240px, answering | `hairline-<name>.html?w=240&at=<x>,<y>` |
| `low` | slider at 0, pointer at the figure's edge (item 9) | `hairline-<name>.html?intensity=0&at=<x>,<y>` |
| `high` | slider at 1, pointer at the figure's edge (item 9) | `hairline-<name>.html?intensity=1&at=<x>,<y>` |
| `dark` | dark theme, answering (item 10) | `hairline-<name>.html?theme=dark&at=<x>,<y>` |
| `light` | light theme, answering (item 10) | `hairline-<name>.html?theme=light&at=<x>,<y>` |

By hand, keep the window at least 800 × 900 for every picture. `?w=240` narrows the page, not the window. A headless Chrome window narrower than 500px still lays the page out 500px wide and keeps only its left part, so the small picture comes out cropped. And wait 1.5 seconds after loading before each picture: strokes fade over 260ms, tweens take 700ms and springs about a second, so a picture taken sooner catches the figure mid-way.

On the sheet, `rest` and `answer` are large; `small` and `small-answer` are at their own size, 240px, beside `dark` and `light`; `low` and `high` close it. Each picture keeps the plate, the controls and the line under the stage, and its label holds the address and the read-out.

## What to see

Answer each with yes or no. A no is fixed in the figure before anything is handed over. `look.mjs` answers 8, 9 and 12, and measures part of 4; the rest are answered from the sheet. Zoom when a line is too small to judge.

1. **The silhouette reads at 240px.** You can say what the object is from the small picture alone. You know what you drew, so do not ask yourself whether it looks like it: for each kind of part, point in the `small` picture to the features you named for it in the concept (`concepts.md`, step 2). A part that shows none of them there is a no, however it looks at full size.
2. **Rest is a composition** (rule 05). Not flat, not empty, not a regular grid; something is bright where the eye should start.
3. **The answer falls off with distance, or spreads out from the pointer** (rules 02 and 03). It is not everything at once, and not one part alone.
4. **Nothing flickers** (rule 01). With the pointer held on a part that moves when touched, the drawing comes to rest. `look.mjs` waits 1.5 seconds after each page loads, then until its drawing holds still for a quarter of a second, for 5 seconds at most. `still` is a yes, and says how long the slowest took. `moving` names the pictures that never held still: answering pictures moving while rest held still is a flicker loop; every picture moving is an ambient figure, or a loop that never ends. A machine too busy to keep up says `moving` too, so run it again before you believe it. `at` moves the pointer once, so also read the hit test: it picks from the rest pose or the target, never from the pose on screen.
5. **Bright outside, dim inside** (rule 09). Every solid is a silhouette and one crease; no vertical corner is drawn; no corner is sharp.
6. **Nothing shows through** (rule 06). No far edge crosses a near solid; no guide crosses its own plate.
7. **One highlight** (rule 04). At rest, one bright mark says where the eye should start. When the pointer chooses, the bright goes to what it chose and the rest mark gives it up. One highlight may cover the parts of one thing, a tray's rim and its beads, but it marks one place and means one thing. It is a stroke or a dot, never a fill.
8. **The read-out names what is under the pointer**, in a few characters, and says `rest` at rest. `look.mjs` prints every picture's read-out, and fails when the rest picture's is not `rest`. A warning that an answering picture still says `rest` means the `--answer` point misses the part, or the hit test does. Whether the name is right is for you to say.
9. **Nothing leaves the frame.** With the slider at each end (`?intensity=0`, `?intensity=1`) and the pointer at the figure's edges, every part stays inside the plate. `look.mjs` fails when the drawing's box leaves the 400 × 320 viewBox in any picture. The box is the geometry: a stroke reaches half its width past it, so a line on the frame's edge is still a no. It also says how much of the frame the rest pose covers, and warns below a quarter; the examples cover 36%.
10. **Both themes.** In `?theme=dark` and `?theme=light`, nothing vanishes and nothing is left the wrong colour.
11. **No words** (rule 10). Nothing in the drawing is a letter, a digit, an arrow or an icon. In a figure made from a mark, the mark itself and a glyph that is part of it are the exception, and so is a glyph built as a solid that is the figure's whole subject; anything else still fails.
12. **The page is clean.** No line under the stage reporting an error, and nothing on the console. `look.mjs` reads both, on every picture, and fails on any console error, console warning or page error.
13. **An empty state says something is missing.** Only for an empty state: in the smallest picture, at rest, with no read-out, can you say what the object would hold and that it holds none?
14. **Rest still reads as the source.** Only for a figure made from a drawing, with `--source`: side by side, a person who knows the drawing names the figure without being told. Check the proportions `source.md` said must survive, one by one; a part the source has and the rest pose lacks is a no, unless you called it decoration.

If you are unsure whether the figure's weight is right, build an example the same way and put the two side by side: `node <skill folder>/build.mjs <skill folder>/examples/terrain.js`. Or look at it: `node <skill folder>/look.mjs <skill folder>/examples/terrain.js --answer 30,90,0` writes its sheet beside yours.

## Without a browser

Answer the same questions from the code, each with the line that makes it true: the rest values for 2, the falloff or stagger for 3, the hit test for 4, the paint order for 6. Then say at hand-over, in these words, that the figure was **not looked at in a browser**. Do not skip the list and do not guess a yes.
