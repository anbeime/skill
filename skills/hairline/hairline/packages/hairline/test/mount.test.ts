// @vitest-environment jsdom
import { describe, expect, it, vi } from "vitest";
import { frames, host, observers, pending } from "./dom";
import { basket, branches, cabinet, dish, drawer, elevator, exploded, format, hub, keyboard, laptop, lockers, loupe, padlock, patch, phone, phosphor, plot, plug, query, rail, rebuild, relay, riffle, router, settle, sieve, slow, stack, terminal, terrain, turntable, vault } from "../src/index";
import { css } from "../src/core/styles";
import { create } from "../src/mount";

const ALL = { riffle, terrain, exploded, phosphor, slow, turntable, keyboard, elevator, phone, laptop, terminal, cabinet, branches, vault, lockers, padlock, patch, dish, router, loupe, sieve, rail, plug, query, drawer, basket, plot, hub, relay, settle, format, rebuild, stack };
const key = (el: Element, k: string) => el.dispatchEvent(new KeyboardEvent("keydown", { key: k, bubbles: true, cancelable: true }));

describe("mount", () => {
  it.each(Object.entries(ALL))("%s draws into the element and takes it all back", (id, mount) => {
    const el = host();
    el.className = "mine";
    const f = mount(el);
    expect(el.getAttribute("data-hairline")).toBe(id);
    expect(el.querySelectorAll(":scope > svg")).toHaveLength(1);
    expect(el.querySelector("svg")!.getAttribute("viewBox")).toBe("0 0 400 320");
    expect(el.querySelector("svg")!.childElementCount).toBeGreaterThan(0);
    expect(el.getAttribute("aria-label")).toBeTruthy();
    f.destroy();
    expect(el.outerHTML).toBe('<div class="mine"></div>');
  });

  it("makes Riffle a focusable group with a live region, and the others images", () => {
    const a = host(), b = host();
    riffle(a); terrain(b);
    expect(a.getAttribute("role")).toBe("group");
    expect(a.getAttribute("tabindex")).toBe("0");
    expect(a.querySelector("[data-hairline-live]")!.getAttribute("aria-live")).toBe("polite");
    expect(b.getAttribute("role")).toBe("img");
    expect(b.hasAttribute("tabindex")).toBe(false);
    expect(b.querySelector("[data-hairline-live]")).toBeNull();
  });

  it("leaves the host's own attributes alone, at mount and at destroy", () => {
    const el = host();
    el.setAttribute("role", "figure");
    el.setAttribute("tabindex", "-1");
    el.setAttribute("aria-label", "My cards");
    const f = riffle(el, { label: "ignored" });
    expect(el.getAttribute("role")).toBe("figure");
    expect(el.getAttribute("tabindex")).toBe("-1");
    expect(el.getAttribute("aria-label")).toBe("My cards");
    f.destroy();
    expect(el.getAttribute("role")).toBe("figure");
    expect(el.getAttribute("tabindex")).toBe("-1");
    expect(el.getAttribute("aria-label")).toBe("My cards");
  });

  it("does not name an element that aria-labelledby already names", () => {
    const el = host();
    el.setAttribute("aria-labelledby", "caption");
    const f = terrain(el);
    expect(el.hasAttribute("aria-label")).toBe(false);
    f.destroy();
    expect(el.getAttribute("aria-labelledby")).toBe("caption");
  });

  it("drops its own name when the element gains aria-labelledby", () => {
    const el = host();
    const f = terrain(el);
    el.setAttribute("aria-labelledby", "caption");
    f.update({});
    expect(el.hasAttribute("aria-label")).toBe(false);
  });

  it("throws a TypeError for something that is not an element", () => {
    expect(() => riffle(null as unknown as HTMLElement)).toThrow(TypeError);
    expect(() => riffle("#cards" as unknown as HTMLElement)).toThrow(/takes an element/);
  });

  it("replaces a figure already on the element", () => {
    const el = host();
    riffle(el);
    terrain(el);
    expect(el.querySelectorAll(":scope > svg")).toHaveLength(1);
    expect(el.getAttribute("data-hairline")).toBe("terrain");
    expect(el.getAttribute("role")).toBe("img");
    expect(el.hasAttribute("tabindex")).toBe(false);
    expect(el.querySelector("[data-hairline-live]")).toBeNull();
  });

  it("draws no hit bands on Riffle, and the stylesheet has no rules for them", () => {
    const el = host();
    riffle(el);
    expect(el.querySelector(".bands")).toBeNull();
    expect(css(true) + css(false)).not.toMatch(/bands/);
  });

  it("puts the stylesheet in the document once, however many figures mount", () => {
    riffle(host()); terrain(host()); slow(host());
    const sheets = document.adoptedStyleSheets?.length ?? 0;
    expect(sheets + document.querySelectorAll("style[data-hairline-style]").length).toBe(1);
  });

  // Review Focus 2 and 3: the new figures at both ends of the slider, with the pointer at the stage's corners, then gone
  it.each(["loupe", "sieve", "rail", "plug", "query", "drawer", "basket", "plot"] as const)("%s stays whole at the corners and returns to rest", async (id) => {
    for (const intensity of [0, 1]) {
      const el = host(), reads: string[] = [];
      const f = ALL[id](el, { intensity, onRead: (t) => reads.push(t) });
      for (const [x, y] of [[0, 0], [400, 0], [0, 320], [400, 320], [200, 160]]) {
        el.dispatchEvent(new MouseEvent("pointermove", { clientX: x, clientY: y, bubbles: true }));
        frames(4);
      }
      expect(reads[reads.length - 1]).not.toBe("rest");
      /* a mouse leaving acts on the next task; jsdom's MouseEvent has no pointerType of its own */
      el.dispatchEvent(Object.assign(new MouseEvent("pointerleave"), { pointerType: "mouse" }));
      await new Promise((r) => setTimeout(r, 0));
      frames(240);
      expect(reads[reads.length - 1]).toBe("rest");
      expect(el.querySelector("svg")!.innerHTML).not.toMatch(/NaN|Infinity|undefined/);
      f.destroy();
    }
  });
});

describe("options", () => {
  it("sets and clears the theme attribute", () => {
    const el = host();
    const f = terrain(el, { theme: "dark" });
    expect(el.getAttribute("data-hairline-theme")).toBe("dark");
    f.update({ theme: "light" });
    expect(el.getAttribute("data-hairline-theme")).toBe("light");
    f.update({ theme: "auto" });
    expect(el.hasAttribute("data-hairline-theme")).toBe(false);
    f.update({ theme: "dark" });
    f.update({ theme: undefined });
    expect(el.hasAttribute("data-hairline-theme")).toBe(false);
  });

  it("updates the label, and goes back to the default when it is removed", () => {
    const el = host();
    const f = terrain(el);
    const standard = el.getAttribute("aria-label");
    f.update({ label: "Dunes" });
    expect(el.getAttribute("aria-label")).toBe("Dunes");
    f.update({ label: undefined });
    expect(el.getAttribute("aria-label")).toBe(standard);
  });

  // Review Focus 1: a caller without types passes what it has
  it.each(["0.8", -3, 7, NaN, null, "fast", {}, Infinity])("mounts, updates and draws with %o as the intensity", (v) => {
    const el = host();
    const bad = v as unknown as number;
    for (const mount of Object.values(ALL)) {
      const f = mount(el, { intensity: bad });
      el.dispatchEvent(new MouseEvent("pointermove", { clientX: 200, clientY: 160, bubbles: true }));
      f.update({ intensity: bad });
      frames(3);
      expect(el.querySelector("svg")!.innerHTML).not.toMatch(/NaN|Infinity|undefined/);
      f.destroy();
    }
  });
});

describe("intensity", () => {
  /* the same input for every host: a point, or a number of frames */
  const PLAY: Record<keyof typeof ALL, Array<[number, number] | number>> = {
    riffle: [[150, 120], 12],
    terrain: [[200, 160], 20],
    exploded: [[100, 80], 30],
    phosphor: [[240, 140], 2, [260, 145], 2, [280, 150], 15],
    slow: [[200, 160], 60],
    turntable: [[50, 176], 1, [120, 176], 1, [200, 176], 1, [280, 176], 1, [350, 176], 40],
    keyboard: [[200, 160], 20],
    elevator: [[200, 60], 8],
    phone: [[100, 80], 100],
    laptop: [[200, 60], 60],
    terminal: [[200, 120], 20],
    cabinet: [[200, 120], 8],
    branches: [[200, 160], 8],
    vault: [[260, 170], 2, [200, 230], 2, [140, 170], 2, [200, 110], 8],
    lockers: [[200, 160], 8],
    loupe: [[200, 170], 60],
    padlock: [[200, 170], 60],
    patch: [[200, 160], 8],
    dish: [[300, 100], 12],
    router: [[300, 120], 12],
    sieve: [[200, 90], 80],
    rail: [[200, 150], 12],
    plug: [[140, 125], 60],
    query: [[330, 120], 60],
    drawer: [[200, 90], 60],
    basket: [[90, 260], 60],
    plot: [[200, 160], 6],
    hub: [[260, 144], 12],
    relay: [[271, 258], 12],
    settle: [[320, 120], 30],
    format: [[199, 168], 12],
    rebuild: [[276, 172], 12],
    stack: [[200, 216], 12],
  };
  const svg = (el: Element) => el.querySelector("svg")!.innerHTML.replace(/hl-fd\d+/g, "hl-fd");

  /* the hosts run side by side on one clock, so the default and an explicit 0.5 must draw alike: that is the control */
  it.each(Object.keys(ALL) as Array<keyof typeof ALL>)("reaches %s's engine, at mount and through update", (id) => {
    const mount = ALL[id];
    const els = Array.from({ length: 6 }, host);
    const [base, half, none, full, text, reset] = els;
    mount(base);
    mount(half, { intensity: 0.5 });
    mount(none, { intensity: 0 });
    mount(full, { intensity: 1 });
    mount(text, { intensity: "1" as unknown as number });
    mount(reset, { intensity: 1 }).update({ intensity: undefined });
    for (const step of PLAY[id]) {
      if (typeof step === "number") frames(step);
      else for (const el of els) el.dispatchEvent(new MouseEvent("pointermove", { clientX: step[0], clientY: step[1], bubbles: true }));
    }
    expect(svg(half)).toBe(svg(base));
    expect(svg(reset)).toBe(svg(base));
    expect(svg(none)).not.toBe(svg(base));
    expect(svg(full)).not.toBe(svg(base));
    expect(svg(text)).toBe(svg(full));
  });

  it("keeps the intensity when update leaves it out", () => {
    const els = [host(), host()];
    terrain(els[0], { intensity: 1 }).update({ theme: "dark" });
    terrain(els[1], { intensity: 1 });
    for (const el of els) el.dispatchEvent(new MouseEvent("pointermove", { clientX: 200, clientY: 160, bubbles: true }));
    frames(20);
    expect(svg(els[0])).toBe(svg(els[1]));
  });
});

describe("the caption", () => {
  it("calls onRead once at mount with the rest caption", () => {
    for (const [id, rest] of [["riffle", "rest"], ["terrain", "rest"], ["slow", "rate 1.00×"]] as const) {
      const onRead = vi.fn();
      ALL[id](host(), { onRead });
      expect(onRead.mock.calls).toEqual([[rest]]);
    }
  });

  it("does not repeat a caption that has not changed", () => {
    const onRead = vi.fn();
    slow(host(), { onRead });
    frames(30);
    expect(onRead.mock.calls).toEqual([["rate 1.00×"]]);
  });

  it("reads a pulled card out by its number alone, in the caption and the live region", () => {
    const el = host(), onRead = vi.fn();
    /* the old option, from a caller without types: ignored */
    const f = riffle(el, { onRead, labels: ["Radial menu", "Drum"] } as never);
    key(el, "ArrowLeft");
    expect(onRead).toHaveBeenLastCalledWith("01");
    expect(el.querySelector("[data-hairline-live]")!.textContent).toBe("01");
    f.update({ labels: ["Radial menu"] } as never);
    key(el, "ArrowRight");
    expect(onRead).toHaveBeenLastCalledWith("02");
    for (let i = 0; i < 7; i++) key(el, "ArrowRight");
    expect(onRead).toHaveBeenLastCalledWith("08");
    expect(el.querySelector("[data-hairline-live]")!.textContent).toBe("08");
    key(el, "Escape");
    expect(onRead).toHaveBeenLastCalledWith("rest");
  });

  // Review Focus 2: every figure on the page shares one frame loop
  it("reports an onRead that throws and keeps every figure running", () => {
    const reported = vi.fn();
    vi.stubGlobal("reportError", reported);
    const boom = new Error("consumer bug");
    const other = vi.fn();
    const a = host(), b = host();
    expect(() => slow(a, { onRead: () => { throw boom; } })).not.toThrow();
    slow(b, { onRead: other });
    a.dispatchEvent(new MouseEvent("pointermove", { clientX: 200, clientY: 160 }));
    b.dispatchEvent(new MouseEvent("pointermove", { clientX: 200, clientY: 160 }));
    expect(() => frames(120)).not.toThrow();
    expect(reported.mock.calls.length).toBeGreaterThan(1);
    expect(reported).toHaveBeenCalledWith(boom);
    expect(other.mock.calls.length).toBeGreaterThan(1);
    expect(other.mock.calls[other.mock.calls.length - 1][0]).toMatch(/^rate 0\.20×/);
  });
});

describe("teardown", () => {
  it("destroys twice without complaint", () => {
    const f = riffle(host());
    f.destroy();
    expect(() => f.destroy()).not.toThrow();
  });

  // Review Focus 3: a handle kept after its figure is gone
  it("ignores update on a destroyed figure", () => {
    const el = host();
    const f = terrain(el);
    f.destroy();
    f.update({ theme: "dark", label: "late", intensity: 1 });
    expect(el.outerHTML).toBe("<div></div>");
  });

  it("ignores a stale handle once another figure has taken the element", () => {
    const el = host();
    const old = riffle(el);
    terrain(el);
    old.update({ theme: "dark", label: "late" });
    old.destroy();
    expect(el.getAttribute("data-hairline")).toBe("terrain");
    expect(el.hasAttribute("data-hairline-theme")).toBe(false);
    expect(el.getAttribute("aria-label")).not.toBe("late");
    expect(el.querySelectorAll(":scope > svg")).toHaveLength(1);
    expect(el.querySelector("svg")!.childElementCount).toBeGreaterThan(0);
  });

  it("leaves no frame and no observer behind the last figure", () => {
    const a = slow(host()), b = phosphor(host());
    frames(2);
    expect(pending()).toBe(1);
    expect(observers.size).toBe(1);
    a.destroy();
    frames(2);
    expect(pending()).toBe(1);
    b.destroy();
    expect(pending()).toBe(0);
    expect(observers.size).toBe(0);
  });

  it("stops listening to the element", () => {
    const el = host(), onRead = vi.fn();
    riffle(el, { onRead }).destroy();
    onRead.mockClear();
    key(el, "ArrowLeft");
    expect(onRead).not.toHaveBeenCalled();
  });
});

describe("sieve", () => {
  /* the sieves' silhouettes, bottom to top: the pan's is first */
  const sils = (el: Element) => [...el.querySelectorAll("svg .sil")].slice(1) as SVGPathElement[];
  /** The middle of a silhouette's box: for a drum, the point over its axis halfway up. */
  const centre = (p: SVGPathElement): [number, number] => {
    const n = p.getAttribute("d")!.match(/-?\d+(\.\d+)?/g)!.map(Number), xs = n.filter((_, i) => i % 2 === 0), ys = n.filter((_, i) => i % 2 === 1);
    return [(Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...ys) + Math.max(...ys)) / 2];
  };

  it.each([0, 0.5, 1])("picks the sieve drawn under the pointer at rest, at intensity %s", (intensity) => {
    const el = host(), onRead = vi.fn();
    sieve(el, { intensity, onRead });
    frames(2);
    const at = sils(el).map(centre);
    expect(at).toHaveLength(3);
    for (const [i, [x, y]] of at.entries()) {
      el.dispatchEvent(new MouseEvent("pointermove", { clientX: x, clientY: y, bubbles: true }));
      expect(onRead).toHaveBeenLastCalledWith(`sieve ${3 - i} · 0`);
      frames(60);
    }
  });

  it("leaves a sieve alone while only the ones above it move", () => {
    const el = host(), onRead = vi.fn();
    sieve(el, { onRead });
    frames(2);
    const bottom = sils(el)[0], d = bottom.getAttribute("d"), set = vi.spyOn(bottom, "setAttribute");
    el.dispatchEvent(new MouseEvent("pointermove", { clientX: 200, clientY: 90, bubbles: true }));
    expect(onRead).toHaveBeenLastCalledWith("sieve 1 · 0");
    frames(60);
    expect(set).not.toHaveBeenCalled();
    expect(bottom.getAttribute("d")).toBe(d);
  });
});

describe("loupe", () => {
  it("reads every row from the far rule to the near one", () => {
    const el = host(), onRead = vi.fn();
    loupe(el, { onRead });
    for (let y = 0; y <= 320; y += 4) el.dispatchEvent(new MouseEvent("pointermove", { clientX: 200, clientY: y, bubbles: true }));
    const rows = new Set(onRead.mock.calls.map((c) => c[0]));
    expect([...rows].filter((t) => t !== "rest")).toEqual(["row 1 · 0", "row 2 · 0", "row 3 · 0", "row 4 · 0", "row 5 · 0", "row 6 · 0", "row 7 · 0"]);
  });

  it("redraws only what the glass shows when only the magnification changes", () => {
    const el = host();
    const f = loupe(el);
    frames(2);
    const paths = [...el.querySelectorAll("svg path")], seen = paths[paths.length - 1];
    const sets = paths.map((p) => vi.spyOn(p, "setAttribute"));
    f.update({ intensity: 1 });
    frames(60);
    for (const [i, set] of sets.entries()) {
      if (paths[i] === seen) expect(set).toHaveBeenCalled();
      else expect(set).not.toHaveBeenCalled();
    }
  });
});

describe("rail", () => {
  /* the hangers' silhouettes, from the far end: after the far foot's and upright's, before the rail's */
  const hangers = (el: Element) => [...el.querySelectorAll("svg .sil")].slice(2, 9) as SVGPathElement[];
  const centre = (p: SVGPathElement): [number, number] => {
    const n = p.getAttribute("d")!.match(/-?\d+(\.\d+)?/g)!.map(Number), xs = n.filter((_, i) => i % 2 === 0), ys = n.filter((_, i) => i % 2 === 1);
    return [(Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...ys) + Math.max(...ys)) / 2];
  };

  it("reads each hanger as holding nothing, and gives the bright back to the rest one on leave", async () => {
    const el = host(), onRead = vi.fn();
    rail(el, { onRead });
    frames(2);
    const at = hangers(el).map(centre), lit = () => hangers(el).map((h) => h.classList.contains("hi"));
    expect(at).toHaveLength(7);
    expect(lit()).toEqual([false, false, false, true, false, false, false]);
    for (const [i, p] of at.entries()) {
      el.dispatchEvent(new MouseEvent("pointermove", { clientX: p[0], clientY: p[1], bubbles: true }));
      expect(onRead).toHaveBeenLastCalledWith(`hanger ${i + 1} · 0`);
      expect(lit().indexOf(true)).toBe(i);
      frames(10);
    }
    el.dispatchEvent(Object.assign(new MouseEvent("pointerleave"), { pointerType: "mouse" }));
    await new Promise((r) => setTimeout(r, 0));
    frames(240);
    expect(onRead).toHaveBeenLastCalledWith("rest");
    expect(lit()).toEqual([false, false, false, true, false, false, false]);
  });
});

describe("plot", () => {
  /* the tabs' silhouettes, far to near: the base's and the plate's come first */
  const tabs = (el: Element) => [...el.querySelectorAll("svg .sil")].slice(2) as SVGPathElement[];
  const nums = (p: SVGPathElement) => p.getAttribute("d")!.match(/-?\d+(\.\d+)?/g)!.map(Number);
  const top = (p: SVGPathElement) => Math.min(...nums(p).filter((_, i) => i % 2 === 1));
  const centre = (p: SVGPathElement): [number, number] => {
    const n = nums(p), xs = n.filter((_, i) => i % 2 === 0), ys = n.filter((_, i) => i % 2 === 1);
    return [(Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...ys) + Math.max(...ys)) / 2];
  };
  const move = (el: Element, [x, y]: [number, number]) => el.dispatchEvent(new MouseEvent("pointermove", { clientX: x, clientY: y, bubbles: true }));

  it("reads each tab as a bar holding zero, and gives the bright back to the proud one on leave", async () => {
    const el = host(), onRead = vi.fn();
    plot(el, { onRead });
    frames(2);
    const at = tabs(el).map(centre);
    expect(at).toHaveLength(7);
    expect(tabs(el).map((t) => t.classList.contains("hi"))).toEqual([false, false, false, false, true, false, false]);
    for (const [i, p] of at.entries()) {
      move(el, p);
      expect(onRead).toHaveBeenLastCalledWith(`bar ${i + 1} · 0`);
      expect(tabs(el).filter((t) => t.classList.contains("hi"))).toEqual([tabs(el)[i]]);
      frames(10);
    }
    el.dispatchEvent(Object.assign(new MouseEvent("pointerleave"), { pointerType: "mouse" }));
    await new Promise((r) => setTimeout(r, 0));
    frames(240);
    expect(onRead).toHaveBeenLastCalledWith("rest");
    expect(tabs(el).map((t) => t.classList.contains("hi"))).toEqual([false, false, false, false, true, false, false]);
  });

  it("lifts the tab it brushes by the slider's 3 · 6 · 12, then drops it back to zero under a still pointer", () => {
    const peaks: number[] = [];
    for (const intensity of [0, 0.5, 1]) {
      const el = host();
      plot(el, { intensity });
      frames(2);
      const tab = tabs(el)[1], flat = tab.getAttribute("d"), y0 = top(tab);
      move(el, centre(tab));
      let peak = 0;
      for (let k = 0; k < 60; k++) { frames(1); peak = Math.max(peak, y0 - top(tab)); }
      frames(120);
      expect(tab.getAttribute("d")).toBe(flat);
      peaks.push(peak);
    }
    expect(peaks[0]).toBeGreaterThan(0);
    expect(peaks[1] / peaks[0]).toBeCloseTo(2, 1);
    expect(peaks[2] / peaks[0]).toBeCloseTo(4, 1);
  });
});

describe("drawer", () => {
  /* the drawers' fronts, bottom to top: the filled silhouettes after the plinth's and the carcass's, each followed by its pull's */
  const fronts = (el: Element) => ([...el.querySelectorAll("svg .sil:not(.nf)")] as SVGPathElement[]).slice(2).filter((_, i) => i % 2 === 0);
  const centre = (p: SVGPathElement): [number, number] => {
    const n = p.getAttribute("d")!.match(/-?\d+(\.\d+)?/g)!.map(Number), xs = n.filter((_, i) => i % 2 === 0), ys = n.filter((_, i) => i % 2 === 1);
    return [(Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...ys) + Math.max(...ys)) / 2];
  };
  const move = (el: Element, [x, y]: [number, number]) => el.dispatchEvent(new MouseEvent("pointermove", { clientX: x, clientY: y, bubbles: true }));

  it.each([0, 0.5, 1])("picks the drawer drawn under the pointer at rest, at intensity %s, and finds it empty", (intensity) => {
    const el = host(), onRead = vi.fn();
    drawer(el, { intensity, onRead });
    frames(2);
    const at = fronts(el).map(centre);
    expect(at).toHaveLength(3);
    for (const [k, p] of at.entries()) {
      move(el, p);
      expect(onRead).toHaveBeenLastCalledWith(`drawer ${3 - k} · 0`);
      frames(60);
      expect(fronts(el).map((f, i) => f.classList.contains("hi") && i)).toEqual([0, 1, 2].map((i) => i === k && i));
    }
  });

  /* A closed front on screen: its left edge is upright and its top falls half a unit for each unit across (the 2:1 view). */
  it.each([0, 1, 2])("picks drawer %s from the bottom near its front's right end, in its lower third", (k) => {
    const el = host(), onRead = vi.fn();
    drawer(el, { onRead });
    frames(2);
    const n = fronts(el)[k].getAttribute("d")!.match(/-?\d+(\.\d+)?/g)!.map(Number), xs = n.filter((_, i) => i % 2 === 0), ys = n.filter((_, i) => i % 2 === 1);
    const x0 = Math.min(...xs), w = Math.max(...xs) - x0, top = Math.min(...ys), h = Math.max(...ys) - top - w / 2;
    move(el, [x0 + 0.85 * w, top + 0.85 * w / 2 + 0.75 * h]);
    expect(onRead).toHaveBeenLastCalledWith(`drawer ${3 - k} · 0`);
  });

  it("draws again only the drawers that move, and takes the slider at rest", () => {
    const el = host(), onRead = vi.fn();
    const f = drawer(el, { onRead });
    frames(2);
    const [bottom, middle, top] = fronts(el), sets = [bottom, middle, top].map((p) => vi.spyOn(p, "setAttribute"));
    move(el, centre(top));
    frames(60);
    expect(sets[0]).not.toHaveBeenCalled();
    expect(sets[1]).toHaveBeenCalled();
    expect(sets[2]).toHaveBeenCalled();
    el.dispatchEvent(Object.assign(new MouseEvent("pointerleave"), { pointerType: "mouse" }));
    return new Promise<void>((done) => setTimeout(() => {
      frames(60);
      const rest = middle.getAttribute("d");
      f.update({ intensity: 1 });
      frames(60);
      expect(middle.getAttribute("d")).not.toBe(rest);
      expect(onRead).toHaveBeenLastCalledWith("rest");
      expect(el.querySelector("svg")!.innerHTML).not.toMatch(/NaN|Infinity|undefined/);
      done();
    }, 0));
  });
});

describe("query", () => {
  const move = (el: Element, x: number) => el.dispatchEvent(new MouseEvent("pointermove", { clientX: x, clientY: 160, bubbles: true }));

  it.each([[0, 20], [0.5, 40], [1, 55]])("turns the hook as far as intensity %s allows, either way, and reads the turn to a zero", async (intensity, most) => {
    const el = host(), onRead = vi.fn();
    query(el, { intensity, onRead });
    frames(2);
    const rest = el.querySelector("svg")!.innerHTML;
    move(el, 400);
    expect(onRead).toHaveBeenLastCalledWith(`turn ${most}° · 0`);
    move(el, 200);
    expect(onRead).toHaveBeenLastCalledWith("turn 0° · 0");
    move(el, 0);
    expect(onRead).toHaveBeenLastCalledWith(`turn ${most}° · 0`);
    frames(30);
    expect(el.querySelector("svg")!.innerHTML).not.toBe(rest);
    el.dispatchEvent(Object.assign(new MouseEvent("pointerleave"), { pointerType: "mouse" }));
    await new Promise((r) => setTimeout(r, 0));
    frames(300);
    expect(onRead).toHaveBeenLastCalledWith("rest");
    expect(el.querySelector("svg")!.innerHTML).toBe(rest);
  });

  it("rolls the ball after the hook has settled, and leaves the hook alone meanwhile", () => {
    const el = host();
    query(el, { intensity: 1 });
    frames(2);
    const paths = [...el.querySelectorAll("svg path")], ball = paths[2], bar = paths[paths.length - 1];
    move(el, 400);
    frames(80);
    const b = vi.spyOn(ball, "setAttribute"), h = vi.spyOn(bar, "setAttribute");
    frames(20);
    expect(h).not.toHaveBeenCalled();
    expect(b).toHaveBeenCalled();
  });
});

describe("plug", () => {
  /** The socket on screen: the middle of the path that holds its two holes. */
  const socket = (el: Element): [number, number] => {
    const n = el.querySelector('svg path[class="nf"]')!.getAttribute("d")!.match(/-?\d+(\.\d+)?/g)!.map(Number), xs = n.filter((_, i) => i % 2 === 0), ys = n.filter((_, i) => i % 2 === 1);
    return [(Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...ys) + Math.max(...ys)) / 2];
  };
  const move = (el: Element, [x, y]: [number, number]) => el.dispatchEvent(new MouseEvent("pointermove", { clientX: x, clientY: y, bubbles: true }));
  const leave = (el: Element) => el.dispatchEvent(Object.assign(new MouseEvent("pointerleave"), { pointerType: "mouse" }));

  it("stops short of the socket at every pull, nearer the further the slider", () => {
    const gaps = [0, 0.5, 1].map((intensity) => {
      const el = host(), onRead = vi.fn();
      plug(el, { intensity, onRead });
      move(el, socket(el));
      const m = /^gap (\d+) · 0 V$/.exec(onRead.mock.calls[onRead.mock.calls.length - 1][0]);
      expect(m).not.toBeNull();
      return Number(m![1]);
    });
    expect(gaps[0]).toBeGreaterThan(gaps[1]);
    expect(gaps[1]).toBeGreaterThan(gaps[2]);
    expect(gaps[2]).toBeGreaterThan(0);
  });

  it("closes the gap as the pointer goes from the plug to the socket, and no further than the pull", () => {
    const el = host(), onRead = vi.fn();
    plug(el, { onRead });
    const [sx, sy] = socket(el), gaps: number[] = [];
    for (let k = 0; k <= 10; k++) { move(el, [sx + (10 - k) * 9, sy + (10 - k) * 11]); gaps.push(Number(/\d+/.exec(onRead.mock.calls[onRead.mock.calls.length - 1][0])![0])); }
    for (let k = 1; k < gaps.length; k++) expect(gaps[k]).toBeLessThanOrEqual(gaps[k - 1]);
    expect(gaps[0]).toBeGreaterThan(gaps[10]);
    expect(gaps.slice(-3)).toEqual([gaps[10], gaps[10], gaps[10]]);
  });

  it("takes the slider at rest and engaged, leaves the plate alone, and lies back down on leaving", async () => {
    const el = host(), onRead = vi.fn();
    const f = plug(el, { onRead });
    frames(2);
    const rest = el.querySelector("svg")!.innerHTML, plate = el.querySelector("svg .sil")!, set = vi.spyOn(plate, "setAttribute");
    f.update({ intensity: 1 });
    frames(60);
    expect(el.querySelector("svg")!.innerHTML).toBe(rest);
    expect(onRead).toHaveBeenLastCalledWith("rest");
    move(el, socket(el));
    const near = onRead.mock.calls[onRead.mock.calls.length - 1][0];
    f.update({ intensity: 0 });
    expect(onRead.mock.calls[onRead.mock.calls.length - 1][0]).not.toBe(near);
    for (const p of [[0, 0], [400, 0], [0, 320], [400, 320]] as const) { move(el, [...p]); frames(4); }
    leave(el);
    await new Promise((r) => setTimeout(r, 0));
    frames(240);
    expect(onRead).toHaveBeenLastCalledWith("rest");
    expect(el.querySelector("svg")!.innerHTML).toBe(rest);
    expect(set).not.toHaveBeenCalled();
    expect(rest).not.toMatch(/NaN|Infinity|undefined/);
  });
});

describe("basket", () => {
  const move = (el: Element, x: number, y: number) => el.dispatchEvent(new MouseEvent("pointermove", { clientX: x, clientY: y, bubbles: true }));
  const last = (fn: ReturnType<typeof vi.fn>) => fn.mock.calls[fn.mock.calls.length - 1][0];

  it.each([[0, 8], [0.5, 16], [1, 28]])("tilts toward the pointer by the slider's %s, %s° at most, and lies level again on leaving", async (intensity, most) => {
    const el = host(), onRead = vi.fn();
    basket(el, { intensity, onRead });
    frames(2);
    const rest = el.querySelector("svg")!.innerHTML;
    move(el, 200, 320);
    expect(onRead).toHaveBeenLastCalledWith(`tilt ${most}° · 0`);
    frames(30);
    expect(el.querySelector("svg")!.innerHTML).not.toBe(rest);
    /* tipped away from the camera it goes half as far, so the mouth stays open to it */
    move(el, 200, 0);
    expect(Number(/\d+/.exec(last(onRead))![0])).toBeLessThan(most);
    move(el, 200, 166);
    expect(last(onRead)).toMatch(/^tilt \d+° · 0$/);
    el.dispatchEvent(Object.assign(new MouseEvent("pointerleave"), { pointerType: "mouse" }));
    await new Promise((r) => setTimeout(r, 0));
    frames(240);
    expect(onRead).toHaveBeenLastCalledWith("rest");
    expect(el.querySelector("svg")!.innerHTML).toBe(rest);
  });

  it("takes the slider at rest without redrawing, and engaged at once", () => {
    const el = host(), onRead = vi.fn();
    const f = basket(el, { onRead });
    frames(2);
    const sets = [...el.querySelectorAll("svg path")].map((p) => vi.spyOn(p, "setAttribute"));
    f.update({ intensity: 1 });
    frames(60);
    for (const set of sets) expect(set).not.toHaveBeenCalled();
    move(el, 200, 320);
    expect(onRead).toHaveBeenLastCalledWith("tilt 28° · 0");
    f.update({ intensity: 0 });
    expect(onRead).toHaveBeenLastCalledWith("tilt 8° · 0");
    frames(120);
    expect(el.querySelector("svg")!.innerHTML).not.toMatch(/NaN|Infinity|undefined/);
  });
});

describe("play", () => {
  it("walks the figure on its own: the read-out leaves rest, and update({ play: false }) brings it back", () => {
    const el = host(), reads: string[] = [];
    const f = terrain(el, { play: true, onRead: (t) => reads.push(t) });
    let n = 0;
    while (reads.at(-1) === "rest" && n++ < 800) frames();
    expect(reads.at(-1)).not.toBe("rest");
    f.update({ play: false });
    frames(60);
    expect(reads.at(-1)).toBe("rest");
    f.destroy();
  });

  it("update with the same play value does not restart the tour", () => {
    const el = host(), reads: string[] = [];
    const f = terrain(el, { play: true, onRead: (t) => reads.push(t) });
    let n = 0;
    while (reads.at(-1) === "rest" && n++ < 800) frames();
    f.update({ play: true, intensity: 0.7 });
    frames(5);
    expect(reads.at(-1)).not.toBe("rest");
    f.destroy();
  });

  it("plays only for true", () => {
    const el = host(), reads: string[] = [];
    const f = terrain(el, { play: 1 as unknown as boolean, onRead: (t) => reads.push(t) });
    frames(800);
    expect(reads).toEqual(["rest"]);
    f.destroy();
  });

  it("destroy stops the tour with the figure", () => {
    const f = terrain(host(), { play: true });
    frames(10);
    f.destroy();
    expect(pending()).toBe(0);
  });

  it("update({ play: true }) starts the tour on a figure mounted without it", () => {
    const el = host(), reads: string[] = [];
    const f = terrain(el, { onRead: (t) => reads.push(t) });
    frames(800);
    expect(reads).toEqual(["rest"]);
    f.update({ play: true });
    let n = 0;
    while (reads.at(-1) === "rest" && n++ < 800) frames();
    expect(reads.at(-1)).not.toBe("rest");
    f.destroy();
  });

  it("a playing Riffle keeps quiet in its live region while it walks itself; the keyboard and a hand on it still speak there", () => {
    const el = host(), reads: string[] = [];
    const f = riffle(el, { play: true, onRead: (t) => reads.push(t) });
    const live = el.querySelector("[data-hairline-live]")!;
    const said = new Set<string | null>();
    for (let i = 0; i < 1500; i++) { frames(); said.add(live.textContent); }
    /* 25 s: the tour walked the cards, the caption followed, the live region did not */
    expect(new Set(reads).size).toBeGreaterThan(2);
    expect([...said]).toEqual(["rest"]);

    el.focus();
    key(el, "Escape");
    key(el, "ArrowLeft");
    expect(live.textContent).toBe("01");
    el.blur();
    expect(live.textContent).toBe("rest");

    /* jsdom never matches :hover, so a hand over the figure is stood in for */
    vi.spyOn(el, "matches").mockImplementation((s: string) => s.includes(":hover"));
    el.dispatchEvent(new PointerEvent("pointermove", { pointerType: "mouse", pointerId: 1, bubbles: true, clientX: 150, clientY: 120 }));
    frames(30);
    expect(live.textContent).not.toBe("rest");
    expect(live.textContent).toBe(reads.at(-1));
    f.destroy();
  });

  it("with play off the live region follows every caption, a hand or not", () => {
    const el = host(), reads: string[] = [];
    const f = riffle(el, { onRead: (t) => reads.push(t) });
    const live = el.querySelector("[data-hairline-live]")!;
    el.dispatchEvent(new PointerEvent("pointermove", { pointerType: "mouse", pointerId: 1, bubbles: true, clientX: 150, clientY: 120 }));
    frames(30);
    expect(reads.at(-1)).not.toBe("rest");
    expect(live.textContent).toBe(reads.at(-1));
    f.destroy();
  });

  it("an engine that throws at mount leaves no tour behind", () => {
    const boom = new Error("engine bug");
    const el = host();
    expect(() => create({ id: "terrain", label: "x", rest: "rest", engine: () => { throw boom; } }, el, { play: true })).toThrow(boom);
    frames(5);
    expect(pending()).toBe(0);
  });
});

