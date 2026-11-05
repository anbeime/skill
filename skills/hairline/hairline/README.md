# hairline

Thirty-three isometric line figures that answer the pointer. For React and for anything with a DOM.

[![npm](https://img.shields.io/npm/v/@lucasmarkes/hairline)](https://www.npmjs.com/package/@lucasmarkes/hairline)
[![CI](https://github.com/lucasmarkes/hairline/actions/workflows/ci.yml/badge.svg)](https://github.com/lucasmarkes/hairline/actions/workflows/ci.yml)
[![license](https://img.shields.io/github/license/lucasmarkes/hairline)](./LICENSE)

![The six figures: a tray of cards, a field of pillars, a window in layers, a dot matrix, a conveyor belt and a turntable](https://raw.githubusercontent.com/lucasmarkes/hairline/main/assets/hero.gif)

Live, with a slider for `intensity`: **[hairline.lucasmarkes.com](https://hairline.lucasmarkes.com)**

## Install

```sh
npm i @lucasmarkes/hairline
```

No dependencies. ESM only. React 18 or later is an optional peer, needed only by `@lucasmarkes/hairline/react`.

With shadcn, which adds the package and a wrapper that reads your theme's tokens:

```sh
npx shadcn@latest add https://hairline.lucasmarkes.com/r/hairline.json
```

## Use

### React

```tsx
import { Terrain } from "@lucasmarkes/hairline/react";

export function Hero() {
  return <Terrain />;
}
```

The figure fills its parent's width at a 5:4 aspect ratio. The entry is a client module, so a Server Component can render it with no `"use client"` of its own. Every component takes the options below and every `<div>` attribute, and forwards its ref to the `<div>`.

### Anything else

```ts
import { terrain } from "@lucasmarkes/hairline";

const figure = terrain(document.getElementById("figure")!, { play: true });

figure.update({ intensity: 0.8 });
figure.destroy();
```

A figure draws into the element you give it, at the element's width and a 5:4 aspect ratio. `update` changes options on the running figure; `destroy` removes what the figure added. That is the shape of a Svelte action, so `use:terrain={{ intensity }}` works as it is.

## The figures

| Function | Component | What it is | A stronger `intensity` |
| --- | --- | --- | --- |
| `riffle` | `Riffle` | A tray of eight cards. The card under the pointer stands up; the arrow keys walk the cards. | The ripple spreads further from the pulled card. |
| `terrain` | `Terrain` | Eighty-one pillars on a plinth that rise around the pointer. | A wider area rises. |
| `exploded` | `Exploded` | An app window in four layers. Moving across opens the gap; moving down picks a layer. | The layers open further. |
| `phosphor` | `Phosphor` | A dot matrix that plays a loop, and fades like phosphor where the pointer paints it. | The trail lingers longer. |
| `slow` | `Slow` | Crates riding a belt through a gate. Hovering slows the clock without stopping it. | Time slows down more. |
| `turntable` | `Turntable` | Blocks on a turntable. A flick spins it; it settles on the nearest quarter turn. | The spin coasts longer. |
| `keyboard` | `Keyboard` | A sixty-key board. The key under the pointer sinks, and its neighbours follow it down. | A wider patch of keys sinks. |
| `elevator` | `Elevator` | Four floors beside an open shaft. The pointer's height picks a floor; the car travels there. | The car travels faster between floors. |
| `phone` | `Phone` | A phone in layers: glass, board, battery, shell. Moving across opens the gap; moving down picks a layer. | The layers open further. |
| `laptop` | `Laptop` | A thin laptop, open on its hinge. The pointer's height sets the lid; it follows on a spring. | The lid opens wider. |
| `terminal` | `Terminal` | A terminal window with its history in rows. The pointer's height scrolls back; the line under it lifts and its neighbours follow. | The lift spreads further. |
| `cabinet` | `Cabinet` | A rack of twelve blades, a few half out. The pointer's height pulls the nearest ones out, the farther the less. | More blades come out. |
| `branches` | `Branches` | A commit graph with a branch forking off main and merging back. The commit under the pointer rises, and its history rises after it. | More of the history rises. |
| `vault` | `Vault` | A vault door with a dial and three bolts. The pointer turns the dial; detents catch every ten, and on the combination the bolts draw back. | The dial coasts longer. |
| `lockers` | `Lockers` | A bank of twelve lockers, one ajar at rest. The locker under the pointer opens; the one at rest closes. | The door opens wider. |
| `padlock` | `Padlock` | A padlock with its shackle in. As the pointer comes near the shackle lifts out and swings open. | The shackle swings further. |
| `patch` | `Patch` | A patch panel of twenty-four ports with cables. The cable under the pointer lifts and its neighbours lean away. | The lean spreads further. |
| `dish` | `Dish` | A parabolic dish on a two-axis gimbal. The pointer aims the dish; it follows on a spring. | The dish swings further. |
| `router` | `Router` | A router with its antennas up. Each antenna leans toward the pointer, the nearest most. | The lean spreads further. |
| `loupe` | `Loupe` | A stand loupe on a blank ruled sheet. The pointer drags it across; the rules pass enlarged under the glass, with nothing between them. | The glass magnifies more. |
| `sieve` | `Sieve` | Three test sieves stacked over a pan. The pointer's height picks one; it rises clear of the stack, and every mesh is bare. | The gap opens further. |
| `rail` | `Rail` | A garment rail with seven bare hangers. The pointer brushes them; each rocks away, the nearest most, and settles. | The brush reaches more hangers. |
| `plug` | `Plug` | A wall socket, and a plug lying on the floor at the end of its cord. The pointer draws the plug up toward the socket; it stops short, and falls back. | The plug comes closer to the socket. |
| `query` | `Query` | A question mark built as a bent bar over a loose ball. The hook turns toward the pointer, and the ball rolls after it. | The hook turns further. |
| `drawer` | `Drawer` | A cabinet of three drawers. The pointer's height picks one; it slides out and shows two dividers with nothing between them. | The drawer opens further. |
| `basket` | `Basket` | A wire basket under a bail handle. It tilts toward the pointer and shows its bare floor; the handle swings after it. | The basket tilts further. |
| `plot` | `Plot` | A bar chart with seven flat tabs where the bars would stand. The pointer brushes them; each lifts a little and drops back to zero. | The tabs lift higher. |
| `hub` | `Hub` | A hub with eight tiles around it on dashed links. The tile under the pointer rises and its link turns solid. | The tiles rise higher. |
| `relay` | `Relay` | A hub with four branches of tiles. The path to the leaf under the pointer lights hop by hop. | Each hop waits longer. |
| `settle` | `Settle` | Twelve tiles lie crooked round a hub. As the pointer nears it, they slide into a tree and the links draw in. | The tree forms from further away. |
| `format` | `Format` | A file of ten crooked lines. The pointer runs the formatter down it, and every line above snaps square. | The lines start more crooked. |
| `rebuild` | `Rebuild` | A tree of packages. The one under the pointer rises, and every package that depends on it rises after it. | The packages rise higher. |
| `stack` | `Stack` | A call stack of five frames. The pointer's height picks one, and the frames above lift away to open it. | The frames above lift further. |

## Options

Every figure takes the same five, all optional:

| Option | Type | Default | |
| --- | --- | --- | --- |
| `intensity` | `number` | `0.5` | How strongly the figure answers the pointer, from 0 (subtle) to 1 (strong). A number outside 0…1 is clamped; anything that is not a number is 0.5. |
| `theme` | `"auto" \| "light" \| "dark"` | `"auto"` | `"auto"` follows the page: an ancestor with class `dark` or `data-theme="dark"`, then the page's `color-scheme`. |
| `label` | `string` | a description in English | The accessible name. In React, `aria-label` does the same. |
| `onRead` | `(text: string) => void` | | The figure's caption, each time it changes: `"03"`, `"gap 28.0"`, `"rate 0.20×"`. |
| `play` | `boolean` | `false` | Walks the figure through its answer on its own, in a loop, until the pointer or focus arrives; it resumes after they leave. |

In `update`, a key set to `undefined` goes back to its default, and a key left out stays as it is.

## Theme

Six custom properties, set on the figure or on anything above it:

```css
.figures {
  --hairline-plate: #101014; /* the fill of every plate: the colour the figure sits on */
  --hairline-hi: #fafafa;    /* what is lit */
  --hairline-edge: #a1a1aa;  /* silhouettes */
  --hairline-mid: #52525b;   /* every other stroke */
  --hairline-lo: #27272a;    /* what recedes */
  --hairline-stroke: 0.9;    /* stroke width, in CSS pixels at any size */
}
```

`--hairline-plate` is the one to get right. Plates are filled, not transparent, because a plate hides what is drawn behind it; on a background that is neither white nor `#08090a`, set it to that background.

The figure's styles have no specificity, so any rule of yours wins without `!important`.

## Notes

- **Accessibility.** A figure is an image with a description you can replace with `label`. Riffle is the exception: it is a focusable group, the arrow keys walk its cards, and a live region reads the card out.
- **Reduced motion.** With `prefers-reduced-motion`, the figures that play on their own (Phosphor and Slow) hold still, a figure given `play` rests, and every figure still answers the pointer.
- **Performance.** Every figure on a page shares one `requestAnimationFrame` loop. A figure off screen, or at rest, does no work, and the loop stops when nothing is moving; a figure given `play` keeps it running while it is on screen.
- **Server rendering.** On the server a component is an empty box with a 5:4 aspect ratio, so nothing shifts when it draws. The functions need a DOM: call them in an effect, in `onMount`, or in a script after the element.
- **Shadow DOM.** A figure mounted inside a shadow root styles itself there.

## Make your own

`hairline-create` is a skill for coding agents. Give it an idea and it draws a new figure to Hairline's ten rules, on the same engine as the thirty-three above, as one HTML file. Every figure it makes declares a tour, the stops a hand would visit, and the page it writes has a play button that walks it.

```sh
npx skills add lucasmarkes/hairline
```

Then type the command with an idea in the agent:

```
/hairline-create a sales funnel
```

It offers two or three concepts, draws the one you pick, checks it against the rules and in a browser, and hands over `hairline-<name>.html`: one file with no dependencies that opens from disk. It runs on any agent that reads skills: Claude Code, Cursor, Codex and others.

With a drawing you already have, an icon or a logo as an SVG, `hairline-adopt` reads it, rebuilds its object as a figure with its proportions and its parts, and proposes what the pointer does to it:

```
/hairline-adopt icons/deploy.svg
```

What both skills drew, each beside its prompt: [hairline.lucasmarkes.com/skills](https://hairline.lucasmarkes.com/skills).

## More

- [hairline.lucasmarkes.com](https://hairline.lucasmarkes.com): every figure live, an inspector that writes the snippet for you, and a CDN example.
- [How Hairline was made](https://hairline.lucasmarkes.com/inspo): the brief, the arguing, and every correction written down as a rule.
- [The essay](https://lucasmarkes.com/lab/hairline): how the figures are drawn, and why with lines.
- [CHANGELOG.md](https://github.com/lucasmarkes/hairline/blob/main/CHANGELOG.md) and [CONTRIBUTING.md](https://github.com/lucasmarkes/hairline/blob/main/CONTRIBUTING.md).

## License

MIT © Lucas Marques
