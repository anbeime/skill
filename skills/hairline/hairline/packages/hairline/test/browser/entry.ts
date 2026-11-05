import * as hairline from "../../src/index";

/**
 * The harness page's script: the package, on `window`, with one figure at a
 * time on #host. Tests drive it through page.evaluate.
 */
type Id = "riffle" | "terrain" | "exploded" | "phosphor" | "slow" | "turntable" | "keyboard" | "elevator" | "phone" | "laptop" | "terminal" | "cabinet" | "branches" | "vault" | "lockers" | "padlock" | "patch" | "dish" | "router" | "loupe" | "sieve" | "rail" | "plug" | "query" | "drawer" | "basket" | "plot" | "hub" | "relay" | "settle" | "format" | "rebuild" | "stack";
type Loose = Record<string, unknown>;
type Mount = (el: HTMLElement, options?: Loose) => { update(o: Loose): void; destroy(): void };

const api = {
  hairline,
  /** Every caption the current figure has written, in order. */
  reads: [] as string[],
  figure: null as ReturnType<Mount> | null,
  /** Mounts a figure on `el` (default #host), recording its captions. */
  mount(id: Id, options: Loose = {}, el: HTMLElement = document.getElementById("host")!) {
    api.reads = [];
    api.figure = (hairline[id] as unknown as Mount)(el, { ...options, onRead: (text: string) => api.reads.push(text) });
    return api.figure;
  },
  read: () => api.reads[api.reads.length - 1] ?? null,
};

declare global {
  interface Window {
    __hl: typeof api;
    /** test/parity/clock.js, when a test adds it */
    __realTimeout: typeof setTimeout;
    __advance(ms: number): number;
  }
}
window.__hl = api;
