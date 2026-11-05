import { afterEach, beforeEach, vi } from "vitest";
import { terrain } from "../src/index";

/**
 * What jsdom lacks and the figures need: an IntersectionObserver, matchMedia,
 * and frames that run when the test says so. Import it for the side effect;
 * it installs before each test and puts everything back after.
 */

type Frame = (now: number) => void;
let queue = new Map<number, Frame>();
let id = 0;
let now = 1000;

/** The observers alive right now: one while any figure is mounted, none after the last is destroyed. */
export const observers = new Set<FakeObserver>();

class FakeObserver {
  targets = new Set<Element>();
  constructor(private cb: IntersectionObserverCallback) { observers.add(this); }
  observe(el: Element) {
    this.targets.add(el);
    this.cb([{ target: el, isIntersecting: true } as IntersectionObserverEntry], this as unknown as IntersectionObserver);
  }
  unobserve(el: Element) { this.targets.delete(el); }
  disconnect() { this.targets.clear(); observers.delete(this); }
  /** Reports the element on or off screen, as the real observer does when the page scrolls. */
  show(el: Element, on: boolean) {
    if (this.targets.has(el)) this.cb([{ target: el, isIntersecting: on } as IntersectionObserverEntry], this as unknown as IntersectionObserver);
  }
}

/** Runs n frames of 1/60 s. A frame that nobody asked for still moves the clock. */
export function frames(n = 1) {
  for (let i = 0; i < n; i++) {
    now += 1000 / 60;
    const run = [...queue.values()];
    queue = new Map();
    for (const fn of run) fn(now);
  }
}

/** How many frames are waiting. Zero means the loop is asleep. */
export const pending = () => queue.size;

/** Scrolls `el` on or off screen for every observer that watches it. */
export const seen = (el: Element, on: boolean) => { for (const o of observers) o.show(el, on); };

beforeEach(() => {
  queue = new Map(); id = 0; now = 1000;
  vi.stubGlobal("IntersectionObserver", FakeObserver);
  vi.stubGlobal("matchMedia", (query: string) => ({ matches: false, media: query, addEventListener() {}, removeEventListener() {} }));
  vi.stubGlobal("requestAnimationFrame", (fn: Frame) => { queue.set(++id, fn); return id; });
  vi.stubGlobal("cancelAnimationFrame", (n: number) => { queue.delete(n); });
  vi.spyOn(performance, "now").mockImplementation(() => now);
});

afterEach(() => {
  // the loop is module state: empty it, or the next test starts with this one's figures still in it.
  // Mounting on an element destroys the figure it had.
  for (const el of hosts) terrain(el).destroy();
  hosts = [];
  document.body.replaceChildren();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

let hosts: HTMLElement[] = [];

/** A host in the document, 400 × 320 at the origin, so a client point is a viewBox point. */
export function host(): HTMLDivElement {
  const el = document.createElement("div");
  el.getBoundingClientRect = () => ({ left: 0, top: 0, width: 400, height: 320, right: 400, bottom: 320, x: 0, y: 0, toJSON() {} });
  document.body.appendChild(el);
  hosts.push(el);
  return el;
}
