import { inject } from "./core/styles";
import { LAP, tour, type FigureHandle, type FigureMount, type Readout, type Tour, type TourHandle } from "./core/stage";
import { parameter, type FigureId } from "./intensity";

/**
 * Hairline — the public wrapper around an engine. An engine draws into an svg
 * it is handed and writes its caption to a read-out; this file makes both,
 * dresses the host element, and gives back the two calls a consumer needs.
 *
 * It only ever removes what it added: the svg, the live region, and the
 * attributes the host did not already have.
 */

/** What every figure takes. */
export type HairlineOptions = {
  /** How strongly the figure answers the pointer, from 0 (subtle) to 1 (strong). Default 0.5. */
  intensity?: number;
  /** `"auto"` follows the page: an ancestor with class `dark` or `data-theme="dark"`, then the page's `color-scheme`. Default `"auto"`. */
  theme?: "auto" | "light" | "dark";
  /** The accessible name. Each figure has a default description in English. */
  label?: string;
  /** The figure's caption, each time it changes. Called once at mount with the rest caption. */
  onRead?: (text: string) => void;
  /**
   * Walks the figure through its answer on its own, in a loop, until the
   * pointer or focus arrives; it resumes after they leave. Only `true` plays.
   * Under prefers-reduced-motion the figure rests. Default false.
   */
  play?: boolean;
};

export type Figure = {
  /** Changes options on the running figure. A key set to `undefined` goes back to its default; a key left out stays as it was. */
  update(options: HairlineOptions): void;
  /** Stops the figure and removes what it added to the element. Safe to call twice. */
  destroy(): void;
};

/** What a figure is: its engine, and what it says about itself. */
export type Spec = {
  id: FigureId;
  /** The default accessible name. */
  label: string;
  /** The caption at rest, for an engine that writes none until it is touched. */
  rest: string;
  engine: FigureMount;
  /** Operable from the keyboard: a focusable group with a live region, not an image. */
  focusable?: boolean;
  /** Where play stops, in viewBox units; null leaves the stage. LAP when unset. */
  tour?: Tour;
};

const NS = "http://www.w3.org/2000/svg";
const mounted = new WeakMap<Element, () => void>();

/** An error from a consumer's callback, reported as uncaught without unwinding the frame loop every figure shares. */
const report = (err: unknown) => {
  if (typeof reportError === "function") reportError(err);
  else setTimeout(() => { throw err; });
};

export function create(spec: Spec, el: HTMLElement, options?: HairlineOptions): Figure {
  if (typeof document === "undefined") {
    throw new Error(`hairline: ${spec.id}() needs a DOM. Call it in the browser, once the element exists: in an effect, in onMount, or in a script after the element.`);
  }
  if (!el || el.nodeType !== 1) {
    throw new TypeError(`hairline: ${spec.id}() takes an element as its first argument, and got ${el === null ? "null" : typeof el}.`);
  }
  mounted.get(el)?.();

  const opts: HairlineOptions = { ...options };
  const doc = el.ownerDocument;
  const root = el.getRootNode();
  inject(root.nodeType === 9 || "host" in root ? (root as Document | ShadowRoot) : doc);

  /* attributes: the host's own are left alone, ours are remembered */
  const owned = new Set<string>();
  const attr = (name: string, value: string | null) => {
    if (!owned.has(name) && el.hasAttribute(name)) return;
    if (value === null) { el.removeAttribute(name); owned.delete(name); }
    else { el.setAttribute(name, value); owned.add(name); }
  };
  const dress = () => {
    attr("data-hairline-theme", opts.theme === "light" || opts.theme === "dark" ? opts.theme : null);
    attr("aria-label", el.hasAttribute("aria-labelledby") ? null : typeof opts.label === "string" ? opts.label : spec.label);
  };
  attr("data-hairline", spec.id);
  attr("role", spec.focusable ? "group" : "img");
  if (spec.focusable) attr("tabindex", "0");
  dress();

  const svg = doc.createElementNS(NS, "svg");
  svg.setAttribute("viewBox", "0 0 400 320");
  svg.setAttribute("aria-hidden", "true");
  el.appendChild(svg);
  let live: HTMLElement | null = null;
  if (spec.focusable) {
    live = doc.createElement("span");
    live.setAttribute("data-hairline-live", "");
    live.setAttribute("aria-live", "polite");
    el.appendChild(live);
  }

  /* the read-out: engines write it every frame, so only a change goes any further */
  let text: string | null = null;
  let playing: TourHandle | null = null;
  const read: Readout = {
    get textContent() { return text; },
    set textContent(value) {
      const next = value ?? "";
      if (next === text) return;
      text = next;
      /* a playing figure says only what a person did: the tour's stops stay out of the live region, the rest caption always goes in */
      if (live && live.textContent !== next && (!playing || next === spec.rest || el.matches(":hover, :focus-within"))) live.textContent = next;
      const fn = opts.onRead;
      if (typeof fn === "function") try { fn(next); } catch (err) { report(err); }
    },
  };

  let value = parameter(spec.id, opts.intensity);
  /* the tour registers before the engine, so its board ticks first in a frame: the ghost moves, then the engine draws the answer */
  playing = opts.play === true ? tour(el, spec.tour ?? LAP) : null;
  let engine: FigureHandle;
  try { engine = spec.engine({ stage: el, svg, read }, value); } catch (err) { playing?.stop(); throw err; }
  if (text === null) read.textContent = spec.rest;

  let dead = false;
  const destroy = () => {
    if (dead) return;
    dead = true;
    if (mounted.get(el) === destroy) mounted.delete(el);
    playing?.stop();
    playing = null;
    engine.destroy();
    svg.remove();
    live?.remove();
    for (const name of owned) el.removeAttribute(name);
    owned.clear();
  };
  mounted.set(el, destroy);

  return {
    update(next) {
      if (dead || !next) return;
      /* a caller without types may send keys that are not options; they are kept and never read */
      const own = opts as Record<string, unknown>, given = next as Record<string, unknown>;
      for (const k in given) {
        if (given[k] === undefined) delete own[k];
        else own[k] = given[k];
      }
      const v = parameter(spec.id, opts.intensity);
      if (v !== value) { value = v; engine.set(v); }
      const play = opts.play === true;
      if (play !== !!playing) {
        playing?.stop();
        playing = play ? tour(el, spec.tour ?? LAP) : null;
      }
      dress();
    },
    destroy,
  };
}
