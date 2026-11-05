# Changelog

Every release of `@lucasmarkes/hairline`. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow
[semver](https://semver.org/).

## 0.5.1 - 2026-10-14

### Added

- `hairline-adopt`, a skill that reads an existing SVG and hands it to
  `hairline-create`, which rebuilds it as a figure. `hairline-create` gains
  step 0, `read.mjs` and `source.md`; `look.mjs --source` puts the SVG beside
  the rest picture on the sheet.

### Fixed

- Figures in a frame that loaded late answer the pointer at once. Chrome's
  frame time there can trail `performance.now()` by seconds, and figures that
  timed their moves by both clocks waited that long. The loop now hands every
  tick `performance.now()`. The skill's `kernel.js` has the same fix.

## 0.5.0 - 2026-10-08

### Added

- `hub` and `Hub`: a hub and eight tiles on a grid. The tile under the pointer
  rises and its link turns solid; its neighbours rise less. A stronger
  `intensity` raises the tiles higher. Its tour visits all eight tiles in turn.
- `relay` and `Relay`: a hub and four branches of tiles. The path to the leaf
  under the pointer lights hop by hop, each tile rising in turn. A stronger
  `intensity` makes each hop wait longer.
- `settle` and `Settle`: twelve tiles lie crooked round a hub. As the pointer
  nears it they slide into a tree and the links draw in. A stronger `intensity`
  starts the tree from further away.
- `format` and `Format`: a file of ten crooked lines. The pointer runs the
  formatter down it, and every line above snaps square to its indent. A stronger
  `intensity` starts the lines more crooked.
- `rebuild` and `Rebuild`: a tree of package tiles. The one touched rises, and
  every package that depends on it rises after it along the links. A stronger
  `intensity` raises them higher.
- `stack` and `Stack`: a call stack of five frames. The pointer's height picks
  one, and the frames above lift away to open it. A stronger `intensity` lifts
  them further.
- The tiles, plates and frames of these six figures are slabs drawn whole: a
  thin body with small rounded corners, the full top edge and a closed inner
  lip.
- Site: the Connectivity and Coding shelves hold six figures each, and each new
  figure walks its own `tour` under `play`.

## 0.4.0 - 2026-10-07

### Added

- `play`, a fifth option: an unseen pointer walks the figure through its answer in a loop until the pointer or focus arrives, and resumes after they leave. Under `prefers-reduced-motion` the figure rests. In React, `<Terrain play />`.

### Changed

- `hairline-create`: every figure declares a `tour`, three to six stops in the viewBox, in its `hairline()` call, and `validate.mjs` requires it. The page it writes has a play button and `?play=1`, and the person is asked to judge the lap at handoff. The seven made pages on the site declare theirs.
- Site: the catalogue's tiles walk their figures until a hand arrives, and the docs list five options.

## 0.3.0 - 2026-10-05

### Added

- `loupe` and `Loupe`: a stand loupe over a blank ruled sheet. The pointer
  drags it across, and the rules pass enlarged under the glass with nothing
  between them. A stronger `intensity` magnifies more.
- `sieve` and `Sieve`: three test sieves stacked over a pan. The pointer's
  height picks one, it rises clear of the stack, and every mesh is bare. A
  stronger `intensity` opens the gap further.
- `rail` and `Rail`: a garment rail with seven bare hangers. The pointer
  brushes them, and each rocks away from it, the nearest most. A stronger
  `intensity` reaches more hangers.
- `plug` and `Plug`: a wall socket and a plug lying on the floor at the end of
  its cord. The pointer draws the plug up toward the socket; it stops short and
  falls back. A stronger `intensity` brings it closer.
- `query` and `Query`: a question mark built as a bent bar over a loose ball.
  The hook turns toward the pointer and the ball rolls after it. A stronger
  `intensity` turns it further.
- `drawer` and `Drawer`: a cabinet of three drawers. The pointer's height
  picks one, and it slides out to show two dividers with nothing between them.
  A stronger `intensity` opens it further.
- `basket` and `Basket`: a wire basket under a bail handle. It tilts toward
  the pointer and shows its bare floor. A stronger `intensity` tilts it
  further.
- `plot` and `Plot`: a bar chart with seven flat tabs where the bars would
  stand. The pointer brushes them, and each lifts a little and drops back to
  zero. A stronger `intensity` lifts them higher.

## 0.2.0 - 2026-10-03

### Added

- `keyboard` and `Keyboard`: a sixty-key board. The key under the pointer
  sinks, and its neighbours follow it down, less the further away. A stronger
  `intensity` sinks a wider patch of keys.
- `elevator` and `Elevator`: four floors beside an open shaft. The pointer's
  height picks a floor, and the car travels there through the ones between.
  A stronger `intensity` makes the car travel faster.
- `phone` and `Phone`: a phone in four layers. Moving across opens the gap
  between them, and moving down picks a layer. A stronger `intensity` opens
  the layers further.
- `laptop` and `Laptop`: a thin laptop. The pointer's height sets how far the
  lid stands open, and the lid follows it on a spring. A stronger `intensity`
  lets the lid open wider.
- `terminal` and `Terminal`: a terminal window. The pointer's height scrolls
  back through its history, and the line under it lifts off the screen. A
  stronger `intensity` lifts more lines with it.
- `cabinet` and `Cabinet`: a rack of twelve blades. The pointer's height pulls
  the nearest ones out on their rails, the farther the less. A stronger
  `intensity` pulls out more blades.
- `branches` and `Branches`: a commit graph on a board. The commit under the
  pointer rises, and its history rises after it, the farther back the less. A
  stronger `intensity` raises more of the history.
- `vault` and `Vault`: a vault door. Circling the pointer turns its dial,
  which coasts and catches every ten; on forty its three bolts draw back. A
  stronger `intensity` lets the dial coast longer.
- `lockers` and `Lockers`: a bank of twelve lockers, one ajar at rest. The
  locker under the pointer opens, and the one open before it swings shut. A
  stronger `intensity` opens the door wider.
- `padlock` and `Padlock`: a padlock. As the pointer nears, the shackle
  springs up out of the body and swings open about its long leg. A stronger
  `intensity` swings the shackle further.
- `patch` and `Patch`: a patch panel of twenty-four ports. The cable under the
  pointer lifts, and its neighbours lean away, less the further away. A
  stronger `intensity` spreads the lean over more ports.
- `dish` and `Dish`: a parabolic dish on a two-axis gimbal. The pointer aims
  it, and it follows on a spring. A stronger `intensity` swings the dish
  further.
- `router` and `Router`: a wifi router. Its antennas lean toward the pointer,
  the nearest the most and the others less the further away. A stronger
  `intensity` spreads the lean over more antennas.

## 0.1.0 - 2026-10-01

First release.

### Added

- Six isometric line figures, each a function that draws into an element:
  `riffle`, `terrain`, `exploded`, `phosphor`, `slow`, `turntable`.
- A React entry, `@lucasmarkes/hairline/react`, with one component per figure.
  It is a client module, so it can be rendered from a Server Component.
- An `intensity` option on every figure, from 0 (subtle) to 1 (strong).
- Theming with six CSS custom properties (`--hairline-plate`, `--hairline-hi`,
  `--hairline-edge`, `--hairline-mid`, `--hairline-lo`, `--hairline-stroke`),
  a `theme` option, and automatic light and dark.
- A shadcn registry item at `https://hairline.lucasmarkes.com/r/hairline.json`.
