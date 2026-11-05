import { create, type Figure, type HairlineOptions } from "./mount";
import { mount as basketEngine } from "./figures/basket";
import { mount as branchesEngine } from "./figures/branches";
import { mount as cabinetEngine } from "./figures/cabinet";
import { mount as dishEngine } from "./figures/dish";
import { mount as drawerEngine } from "./figures/drawer";
import { mount as elevatorEngine } from "./figures/elevator";
import { mount as explodedEngine } from "./figures/exploded";
import { mount as formatEngine } from "./figures/format";
import { mount as hubEngine } from "./figures/hub";
import { mount as keyboardEngine } from "./figures/keyboard";
import { mount as laptopEngine } from "./figures/laptop";
import { mount as lockersEngine } from "./figures/lockers";
import { mount as loupeEngine } from "./figures/loupe";
import { mount as padlockEngine } from "./figures/padlock";
import { mount as patchEngine } from "./figures/patch";
import { mount as phoneEngine } from "./figures/phone";
import { mount as phosphorEngine } from "./figures/phosphor";
import { mount as plotEngine } from "./figures/plot";
import { mount as plugEngine } from "./figures/plug";
import { mount as queryEngine } from "./figures/query";
import { mount as railEngine } from "./figures/rail";
import { mount as rebuildEngine } from "./figures/rebuild";
import { mount as relayEngine } from "./figures/relay";
import { mount as riffleEngine } from "./figures/riffle";
import { mount as routerEngine } from "./figures/router";
import { mount as settleEngine } from "./figures/settle";
import { mount as sieveEngine } from "./figures/sieve";
import { mount as slowEngine } from "./figures/slow";
import { mount as stackEngine } from "./figures/stack";
import { mount as terminalEngine } from "./figures/terminal";
import { mount as terrainEngine } from "./figures/terrain";
import { mount as turntableEngine } from "./figures/turntable";
import { mount as vaultEngine } from "./figures/vault";

/**
 * @lucasmarkes/hairline — thirty-three isometric line figures that answer the pointer.
 *
 * One function per figure. Each takes an element and the same options, draws
 * into the element, and returns `{ update, destroy }`. Each function names
 * its engine itself, so a bundle that imports one figure carries one.
 */

export type { Figure, HairlineOptions } from "./mount";

/** A tray of eight cards. The card under the pointer stands up; the arrow keys walk the cards. `intensity` spreads the ripple further from the pulled card. */
export function riffle(el: HTMLElement, options?: HairlineOptions): Figure {
  return create({
    id: "riffle",
    label: "A tray of eight cards. Hover or use the arrow keys to pull a card.",
    rest: "rest",
    engine: riffleEngine,
    focusable: true,
  }, el, options);
}

/** Eighty-one pillars on a plinth that rise around the pointer. `intensity` widens the area that rises. */
export function terrain(el: HTMLElement, options?: HairlineOptions): Figure {
  return create({
    id: "terrain",
    label: "Eighty-one pillars on a plinth that rise around the pointer and rest as a dune with two rises.",
    rest: "rest",
    engine: terrainEngine,
  }, el, options);
}

/** An app window in four layers. Moving across opens the gap; moving down picks a layer. `intensity` opens the layers further. */
export function exploded(el: HTMLElement, options?: HairlineOptions): Figure {
  return create({
    id: "exploded",
    label: "An app window taken apart into four layers. Moving across opens the gap; moving down picks a layer.",
    rest: "",
    engine: explodedEngine,
  }, el, options);
}

/** A seven by seven dot matrix that plays a loop, and fades like phosphor where the pointer paints it. `intensity` makes the trail linger longer. */
export function phosphor(el: HTMLElement, options?: HairlineOptions): Figure {
  return create({
    id: "phosphor",
    label: "A seven by seven dot matrix on a floating tile that plays a loop, and fades like phosphor where you paint it.",
    rest: "loop",
    engine: phosphorEngine,
  }, el, options);
}

/** Crates riding a belt through a gate. Hovering slows the clock without stopping it. `intensity` slows it more. */
export function slow(el: HTMLElement, options?: HairlineOptions): Figure {
  return create({
    id: "slow",
    label: "Crates riding a belt through a gate. Hovering slows the clock without stopping it.",
    rest: "rate 1.00×",
    engine: slowEngine,
  }, el, options);
}

/** Blocks on a turntable. A flick across it spins it; it settles on the nearest quarter turn. `intensity` makes the spin coast longer. */
export function turntable(el: HTMLElement, options?: HairlineOptions): Figure {
  return create({
    id: "turntable",
    label: "Blocks on a turntable. Flick across it to spin it; it settles on the nearest quarter turn.",
    rest: "az 045° · el 30°",
    engine: turntableEngine,
  }, el, options);
}

/** A sixty-key board. The key under the pointer sinks, and its neighbours follow it down, less the further away. `intensity` widens how far the press reaches. */
export function keyboard(el: HTMLElement, options?: HairlineOptions): Figure {
  return create({
    id: "keyboard",
    label: "A sixty-key board. The key under the pointer sinks, and its neighbours follow it down, less the further away.",
    rest: "rest",
    engine: keyboardEngine,
  }, el, options);
}

/** Four floors beside an open shaft. The pointer's height picks a floor, and the car travels there through the ones between. `intensity` makes the car travel faster. */
export function elevator(el: HTMLElement, options?: HairlineOptions): Figure {
  return create({
    id: "elevator",
    label: "Four floors beside an open shaft. The pointer's height picks a floor, and the car travels there through the ones between.",
    rest: "rest",
    engine: elevatorEngine,
  }, el, options);
}

/** A phone in layers: glass, board, battery, shell. Moving across opens the gap; moving down picks a layer. `intensity` opens the layers further. */
export function phone(el: HTMLElement, options?: HairlineOptions): Figure {
  return create({
    id: "phone",
    label: "A phone in layers: glass, board, battery, shell. Moving across opens the gap; moving down picks a layer.",
    rest: "rest",
    engine: phoneEngine,
  }, el, options);
}

/** A thin laptop: the pointer's height sets how far the lid stands open, and the lid follows it on a spring. `intensity` lets the lid open wider. */
export function laptop(el: HTMLElement, options?: HairlineOptions): Figure {
  return create({
    id: "laptop",
    label: "A thin laptop: the pointer's height sets how far the lid stands open, and the lid follows it on a spring.",
    rest: "rest",
    engine: laptopEngine,
  }, el, options);
}

/** A terminal window: the pointer's height scrolls back through its history, and the line under it lifts off the screen. `intensity` spreads the lift over more lines. */
export function terminal(el: HTMLElement, options?: HairlineOptions): Figure {
  return create({
    id: "terminal",
    label: "A terminal window: the pointer's height scrolls back through its history, and the line under it lifts off the screen.",
    rest: "rest",
    engine: terminalEngine,
  }, el, options);
}

/** A rack of twelve blades: the pointer's height pulls the nearest ones out on their rails, the farther the less. `intensity` pulls out more blades. */
export function cabinet(el: HTMLElement, options?: HairlineOptions): Figure {
  return create({
    id: "cabinet",
    label: "A rack of twelve blades: the pointer's height pulls the nearest ones out on their rails, the farther the less.",
    rest: "rest",
    engine: cabinetEngine,
  }, el, options);
}

/** A commit graph on a board: the commit under the pointer rises, and its history rises after it, the farther back the less. `intensity` raises more of the history. */
export function branches(el: HTMLElement, options?: HairlineOptions): Figure {
  return create({
    id: "branches",
    label: "A commit graph on a board: the commit under the pointer rises, and its history rises after it, the farther back the less.",
    rest: "rest",
    engine: branchesEngine,
  }, el, options);
}

/** A vault door: circling the pointer turns its dial, which coasts and catches every ten; on forty its three bolts draw back. `intensity` lets the dial coast longer. */
export function vault(el: HTMLElement, options?: HairlineOptions): Figure {
  return create({
    id: "vault",
    label: "A vault door: circling the pointer turns its dial, which coasts and catches every ten; on forty its three bolts draw back.",
    rest: "rest",
    engine: vaultEngine,
  }, el, options);
}

/** A bank of twelve lockers, one ajar at rest: the locker under the pointer opens, and the one open before it swings shut. `intensity` opens the door wider. */
export function lockers(el: HTMLElement, options?: HairlineOptions): Figure {
  return create({
    id: "lockers",
    label: "A bank of twelve lockers, one ajar at rest: the locker under the pointer opens, and the one open before it swings shut.",
    rest: "rest",
    engine: lockersEngine,
  }, el, options);
}

/** A stand loupe over a blank ruled sheet: the pointer drags it across, and the rules pass enlarged under the glass with nothing between them. `intensity` magnifies more. */
export function loupe(el: HTMLElement, options?: HairlineOptions): Figure {
  return create({
    id: "loupe",
    label: "A stand loupe over a blank ruled sheet: the pointer drags it across, and the rules pass enlarged under the glass with nothing between them.",
    rest: "rest",
    engine: loupeEngine,
  }, el, options);
}

/** A padlock: as the pointer nears, the shackle springs up out of the body and swings open about its long leg. `intensity` swings the shackle further. */
export function padlock(el: HTMLElement, options?: HairlineOptions): Figure {
  return create({
    id: "padlock",
    label: "A padlock: as the pointer nears, the shackle springs up out of the body and swings open about its long leg.",
    rest: "rest",
    engine: padlockEngine,
  }, el, options);
}

/** A patch panel of twenty-four ports: the cable under the pointer lifts, and its neighbours lean away, less the further away. `intensity` spreads the lean over more ports. */
export function patch(el: HTMLElement, options?: HairlineOptions): Figure {
  return create({
    id: "patch",
    label: "A patch panel of twenty-four ports: the cable under the pointer lifts, and its neighbours lean away, less the further away.",
    rest: "rest",
    engine: patchEngine,
  }, el, options);
}

/** A parabolic dish on a two-axis gimbal: the pointer aims it, and it follows on a spring. `intensity` swings the dish further. */
export function dish(el: HTMLElement, options?: HairlineOptions): Figure {
  return create({
    id: "dish",
    label: "A parabolic dish on a two-axis gimbal: the pointer aims it, and it follows on a spring.",
    rest: "rest",
    engine: dishEngine,
  }, el, options);
}

/** A wifi router whose antennas lean toward the pointer, the nearest the most and the others less the further away. `intensity` spreads the lean over more antennas. */
export function router(el: HTMLElement, options?: HairlineOptions): Figure {
  return create({
    id: "router",
    label: "A wifi router whose antennas lean toward the pointer, the nearest the most and the others less the further away.",
    rest: "rest",
    engine: routerEngine,
  }, el, options);
}

/** Three test sieves stacked over a pan: the pointer's height picks one, it rises clear of the stack, and every mesh is bare. `intensity` opens the gap further. */
export function sieve(el: HTMLElement, options?: HairlineOptions): Figure {
  return create({
    id: "sieve",
    label: "Three test sieves stacked over a pan: the pointer's height picks one, it rises clear of the stack, and every mesh is bare.",
    rest: "rest",
    engine: sieveEngine,
  }, el, options);
}

/** A garment rail with seven bare hangers: the pointer brushes them, and each rocks away from it, the nearest most, and settles. `intensity` reaches more hangers. */
export function rail(el: HTMLElement, options?: HairlineOptions): Figure {
  return create({
    id: "rail",
    label: "A garment rail with seven bare hangers: the pointer brushes them, and each rocks away from it, the nearest most, and settles.",
    rest: "rest",
    engine: railEngine,
  }, el, options);
}

/** A wall socket and a plug lying on the floor at the end of its cord: the pointer draws the plug up toward the socket, and it stops short. `intensity` brings it nearer. */
export function plug(el: HTMLElement, options?: HairlineOptions): Figure {
  return create({
    id: "plug",
    label: "A wall socket and a plug lying on the floor at the end of its cord: the pointer draws the plug up toward the socket, and it stops short of it.",
    rest: "rest",
    engine: plugEngine,
  }, el, options);
}

/** A question mark built as a solid on a plinth, its dot a loose ball: the hook turns about its stem toward the pointer, and the ball rolls after it. `intensity` turns the hook further. */
export function query(el: HTMLElement, options?: HairlineOptions): Figure {
  return create({
    id: "query",
    label: "A question mark built as a solid on a plinth, its dot a loose ball: the hook turns about its stem toward the pointer, and the ball rolls after it.",
    rest: "rest",
    engine: queryEngine,
  }, el, options);
}

/** A filing cabinet of three drawers: the pointer's height picks one, it slides out, and inside are two dividers and nothing between them. `intensity` pulls the drawer further out. */
export function drawer(el: HTMLElement, options?: HairlineOptions): Figure {
  return create({
    id: "drawer",
    label: "A filing cabinet of three drawers: the pointer's height picks one, it slides out, and inside are two dividers and nothing between them.",
    rest: "rest",
    engine: drawerEngine,
  }, el, options);
}

/** An empty wire shopping basket under a bail handle: the pointer tilts it toward itself on a spring, so the bare floor shows, and the handle swings after it, late. `intensity` tilts it further. */
export function basket(el: HTMLElement, options?: HairlineOptions): Figure {
  return create({
    id: "basket",
    label: "An empty wire shopping basket under a bail handle: the pointer tilts it toward itself on a spring, so the bare floor shows, and the handle swings after it, late.",
    rest: "rest",
    engine: basketEngine,
  }, el, options);
}

/** A bar chart with no data: seven flat tabs on its base, before a plate of grid lines. The pointer brushes them, and each lifts a little, the nearest most, and drops back to zero. `intensity` lifts them higher. */
export function plot(el: HTMLElement, options?: HairlineOptions): Figure {
  return create({
    id: "plot",
    label: "A bar chart with no data: seven flat tabs on its base, before a plate of grid lines. The pointer brushes them, and each lifts a little, the nearest most, and drops back to zero.",
    rest: "rest",
    engine: plotEngine,
  }, el, options);
}

/** A hub and eight tiles on a grid: the tile under the pointer rises and its link turns solid, and its neighbours rise less. `intensity` raises the tiles higher. */
export function hub(el: HTMLElement, options?: HairlineOptions): Figure {
  return create({
    id: "hub",
    label: "A hub and eight tiles on a grid: the tile under the pointer rises and its link turns solid; its neighbours rise less.",
    rest: "rest",
    engine: hubEngine,
    tour: [[205, 112], [260, 144], [328, 179], [263, 207], [201, 243], [131, 209], [76, 177], [136, 141], null],
  }, el, options);
}

/** A hub and four branches of tiles: the path to the leaf under the pointer lights hop by hop, each tile rising in turn. `intensity` makes each hop wait longer. */
export function relay(el: HTMLElement, options?: HairlineOptions): Figure {
  return create({
    id: "relay",
    label: "A hub and four branches of tiles: the path to the leaf under the pointer lights hop by hop, each tile rising in turn.",
    rest: "rest",
    engine: relayEngine,
    tour: [[45, 145], [140, 253], [271, 258], [355, 216], [344, 151], null],
  }, el, options);
}

/** Twelve tiles lie crooked round a hub; as the pointer nears it they slide into a tree and the links draw in. `intensity` starts the tree from further away. */
export function settle(el: HTMLElement, options?: HairlineOptions): Figure {
  return create({
    id: "settle",
    label: "Twelve tiles lie crooked round a hub; as the pointer nears it they slide into a tree and the links draw in.",
    rest: "rest",
    engine: settleEngine,
    tour: [[360, 40], [320, 120], [203, 155], null],
  }, el, options);
}

/** A file of ten crooked lines: the pointer runs the formatter down it, and every line above snaps square to its indent. `intensity` starts the lines more crooked. */
export function format(el: HTMLElement, options?: HairlineOptions): Figure {
  return create({
    id: "format",
    label: "A file of ten crooked lines: the pointer runs the formatter down it, and every line above snaps square to its indent.",
    rest: "rest",
    engine: formatEngine,
    tour: [[290, 162], [199, 168], [135, 200], null],
  }, el, options);
}

/** A tree of package tiles: the one touched rises, and every package that depends on it rises after it along the links. `intensity` raises them higher. */
export function rebuild(el: HTMLElement, options?: HairlineOptions): Figure {
  return create({
    id: "rebuild",
    label: "A tree of package tiles: the one touched rises, and every package that depends on it rises after it along the links.",
    rest: "rest",
    engine: rebuildEngine,
    tour: [[47, 236], [276, 172], [181, 106], null],
  }, el, options);
}

/** A call stack of five frames: the pointer's height picks one, and the frames above lift away to open it. `intensity` lifts them further. */
export function stack(el: HTMLElement, options?: HairlineOptions): Figure {
  return create({
    id: "stack",
    label: "A call stack of five frames: the pointer's height picks one, and the frames above lift away to open it.",
    rest: "rest",
    engine: stackEngine,
    tour: [[200, 250], [200, 216], [200, 199], null],
  }, el, options);
}
