import {
  Cam, clamp, extremes, facing, fit, poly, prism, proj, ringAt, rings, rrect, seg,
  type Ring, type Sample, type Vec2,
} from "../core/iso";
import { spring, stepS } from "../core/motion";
import { disposer, flatDot, mk, place, pointer, put, register, solid, type FigureMount, type Solid } from "../core/stage";

/**
 * Exploded — an app window taken apart into surface, sidebar, card and
 * popover. The pointer's x scrubs the gap through a spring; its y picks a
 * layer, which gets the bright edge, and its name and lift go to the
 * read-out. The bright edge is the whole callout. From the study's third
 * figure (design/lab-hairline/cartilha-v2.html).
 *
 * Picking is tested against the target gap, not the gap on screen, so the
 * layer under the pointer is the one it will be under once the spring lands.
 * Each layer's dashed drops (from its outermost points down to the layer
 * below) are painted before its plate, so a plate hides the guides behind it.
 */

type Rect = [number, number, number, number];
type Layer = {
  name: string;
  /** Footprint, window units: x0, y0, x1, y1. */
  r: Rect;
  rad: number;
  /** Content marks drawn on the top face. */
  segs: [Vec2, Vec2][];
  /** Traffic-light dots (surface only). */
  dots?: Vec2[];
  /** A selected row outlined in the silhouette's stroke (popover only). */
  sel?: Rect;
};

const LAY: Layer[] = [
  { name: "surface", r: [0, 0, 132, 96], rad: 7, segs: [[[1.5, 12], [130.5, 12]]], dots: [[7, 6], [13, 6], [19, 6]] },
  { name: "sidebar", r: [5, 17, 38, 91], rad: 4, segs: [[[10, 25], [28, 25]], [[10, 33], [32, 33]], [[10, 41], [24, 41]], [[10, 49], [30, 49]], [[10, 83], [22, 83]]] },
  { name: "card", r: [48, 22, 120, 62], rad: 5, segs: [[[54, 30], [92, 30]], [[54, 38], [112, 38]], [[54, 46], [104, 46]], [[54, 54], [80, 54]]] },
  { name: "popover", r: [80, 50, 126, 86], rad: 4, segs: [[[86, 58], [118, 58]], [[86, 74], [116, 74]], [[86, 80], [108, 80]]], sel: [83, 62, 123, 70] },
];

/** The gap's share of the max at rest (pointer away), and each slab's thickness. */
const REST = 0.18, TK = 2.4;

/** Even-odd point-in-polygon. */
function inside(pt: Vec2, pg: readonly Vec2[]) {
  let c = false;
  for (let i = 0, j = pg.length - 1; i < pg.length; j = i++) {
    const [xi, yi] = pg[i], [xj, yj] = pg[j];
    if ((yi > pt[1]) !== (yj > pt[1]) && pt[0] < ((xj - xi) * (pt[1] - yi)) / (yj - yi) + xi) c = !c;
  }
  return c;
}

export const mount: FigureMount = ({ stage, svg, read }, value) => {
  const bag = disposer();
  let GAP = value, act = -1, lastP: Vec2 | null = null;
  const e = spring(REST, { eps: 0.002 });
  const C = Cam(45, 0.5, 1.42);
  fit(C, [[0, 0, 0], [132, 96, 0], [132, 0, 0], [0, 96, 0], [0, 0, 3 * 34 + TK], [132, 0, 3 * 34 + TK]], 180, 166);
  const P = proj(C), front = facing(C);
  const g = mk("g", {}, svg);

  const els = LAY.map((L, i) => {
    const [ring, inner] = rings(...L.r, L.rad, 1.3);
    const ext: Sample[] = extremes(P, ring);
    // The guide goes in before the plate: paint order is what hides it.
    const guide = i > 0 ? mk("path", { class: "nf dash" }, g) : null;
    const el: Solid = solid(g);
    const marks = mk("path", { class: "nf" }, el.g);
    const selRing: Ring | null = L.sel ? rrect(...L.sel, 2) : null;
    const selEl = L.sel ? mk("path", { class: "nf sil" }, el.g) : null;
    const dotEls = L.dots ? L.dots.map(() => flatDot(el.g, C, 1.6, "nf")) : null;
    return { ring, inner, ext, guide, el, marks, selRing, selEl, dotEls };
  });

  const corners = ([x0, y0, x1, y1]: Rect, z: number): Vec2[] => [P(x0, y0, z), P(x1, y0, z), P(x1, y1, z), P(x0, y1, z)];
  /** The topmost layer under the pointer, tested where the layers are going (target gap), not where they are. */
  function pick(p: Vec2 | null) {
    if (!p) return -1;
    for (let i = LAY.length - 1; i >= 0; i--) if (inside(p, corners(LAY[i].r, i * GAP * e.t + TK))) return i;
    return -1;
  }
  function setAct(a: number) {
    if (a === act) return;
    act = a;
    els.forEach((E, i) => E.el.sil.classList.toggle("hi", i === a));
    B.wake();
  }

  const B = register(stage, (dt) => {
    const m = stepS(e, dt), z = (i: number) => i * GAP * e.x;
    LAY.forEach((L, i) => {
      const E = els[i], zi = z(i), zt = zi + TK;
      put(E.el, prism(P, front, E.ring, E.inner, zi, zt));
      E.marks.setAttribute("d", L.segs.map(([a, b]) => seg(P(a[0], a[1], zt), P(b[0], b[1], zt))).join(""));
      if (E.selEl && E.selRing) E.selEl.setAttribute("d", poly(ringAt(P, E.selRing, zt)));
      if (E.dotEls && L.dots) L.dots.forEach(([dx, dy], k) => place(E.dotEls![k], P(dx, dy, zt)));
      if (E.guide) {
        const zp = z(i - 1) + TK;
        E.guide.setAttribute("d", E.ext.map((q) => seg(P(q.u, q.v, zi), P(q.u, q.v, zp))).join(""));
      }
    });
    read.textContent = act >= 0 ? `0${act + 1} · ${LAY[act].name} · z ${z(act).toFixed(1)}` : `gap ${(GAP * e.x).toFixed(1)}`;
    return m;
  });
  bag.add(B.unregister);

  bag.add(pointer(stage, {
    move: (p) => { lastP = p; e.t = REST + (1 - REST) * clamp((p[0] - 60) / 280, 0, 1); setAct(pick(p)); B.wake(); },
    leave: () => { lastP = null; e.t = REST; setAct(-1); B.wake(); },
  }));
  bag.add(() => svg.replaceChildren());

  return {
    set: (v) => { GAP = v; if (lastP) setAct(pick(lastP)); B.wake(); },
    destroy: bag.dispose,
  };
};
