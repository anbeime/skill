import { Cam, clamp, fillet, fit, poly, prism, proj, rings, rrect, type Ring, type Sample, type Vec2 } from "../core/iso";
import { spring, stepS, type Spring } from "../core/motion";
import { disposer, mk, pointer, put, register, solid, type FigureMount, type Solid } from "../core/stage";

/**
 * Terminal: a terminal window floating upright as a thin rounded slab. A title
 * bar with its three round buttons across the top, a prompt bar across the
 * foot with a chevron and a block cursor, and between them the output: rows
 * of rounded bars, indented and of different lengths, as code and logs are.
 * The pointer's height scrolls back through twenty-four lines of history on a
 * spring; lines leaving the top pass in behind the title bar, and new ones
 * come up from behind the prompt bar, cut where they meet it. The line under the
 * pointer lifts off the slab, and its neighbours less, each on its own spring.
 * At rest the window is scrolled back half a line and one long line is caught
 * lifted, bright. The slider is how far the lift spreads, in lines.
 *
 * The slab stands in the x–z plane and faces +y, so the figure draws in its
 * own frame: u across, v up, w out of the face, P2(u, v, w) = P(u, w, v).
 * The pattern: scrub and pick. One spring for the scroll, a spring per line
 * for its lift, a falloff by distance, and a hit test on the rest planes.
 */

const N = 24, V = 7, G = 11, T = 2.1, LH = 1.8, CH = 3.9, LIFT = 5.5, HB = 3.4, SLAB = 3;
const W = 150, TB = 17, PB = 17, PAD = 11, IN = 2.5, FIRST = 37;
const VB = PB, VA = PB + V * G, H = VA + TB, E = 4;
/** The history, oldest first: an indent in cells, then each token's length in cells. */
const HIST = [
  "0 5 12", "2 7 3 9", "2 14", "4 6 10", "4 18", "2 3", "0 2", "0 2 6 8",
  "0 26", "0 20", "0 11 4", "2 9 12", "2 5 3 7", "4 16", "4 8 8", "2 4",
  "0 3 14", "0 24", "0 30", "0 17", "2 6 11", "2 13", "0 9 5", "0 4 7",
];
/** Rest: scrolled back part way into a line, with line 18 lifted and its neighbours following. */
const REST_TOP = N - V - 2.6, REST_LINE = 18, REST_R = 2;

/** The share of the full lift a line takes, d lines from the one under the pointer: all of it there, none past R. */
const falloff = (d: number, R: number) => clamp(1 - d / R, 0, 1);
const smooth = (t: number) => t * t * (3 - 2 * t);
/** A ring sample faces the camera: its normal, in the slab's u–v plane, against the view direction (x .612, z .5). */
const front = (q: Sample) => 0.612 * q.nu + 0.5 * q.nv > 0;
/** A ring cut to the window between the bars: whatever lies past a bar is pressed flat against it. */
const cut = (ring: Ring): Ring => ring.map((q) => ({ ...q, v: clamp(q.v, VB, VA) }));

type Seg = { x0: number; x1: number; el: Solid };
type Row = { j: number; segs: Seg[]; sp: Spring; drawn: string };
type Over = "prompt" | number | null;

export const mount: FigureMount = ({ stage, svg, read }, value) => {
  const bag = disposer();
  const C = Cam(45, 0.5, 1.62);
  const W3 = (u: number, v: number, w: number): [number, number, number] => [u, w, v];
  fit(C, [W3(0, 0, -SLAB), W3(W, 0, -SLAB), W3(0, H, -SLAB), W3(W, H, -SLAB), W3(W, 0, HB + 2.8), W3(0, H, HB + 1.3), W3(PAD, VA - 4, LIFT + LH)], 200, 166);
  const P = proj(C), P2 = (u: number, v: number, w: number) => P(u, w, v);
  let R = value, over: Over = null, lit: Element[] = [];

  const g = mk("g", {}, svg);
  const [sr, si] = rings(0, 0, W, H, 9, 2);
  put(solid(g), prism(P2, front, sr, si, -SLAB, 0));

  // The history, oldest (highest) first. Each token is a pill, cut to the window as it is drawn.
  const rows: Row[] = HIST.map((s, j) => {
    const [ind, ...tok] = s.split(" ").map(Number), segs: Seg[] = [];
    let at = ind;
    for (const n of tok) {
      const x0 = PAD + at * CH;
      segs.push({ x0, x1: x0 + n * CH - 1.4, el: solid(g) });
      at += n + 1;
    }
    return { j, segs, sp: spring(0, { eps: 0.01 }), drawn: "" };
  });

  // The prompt bar, its chevron (two strokes joined into one shape) and the block cursor, painted after the
  // lines as the title bar is: a line coming up out of it rises from behind it, cut flat inside it.
  const [pr, pi] = rings(IN, IN, W - IN, VB, 6, 1.4);
  put(solid(g), prism(P2, front, pr, pi, 0, HB));
  const cy = (IN + VB) / 2;
  const chev = fillet([[0, 6.2], [8.5, 0], [0, -6.2], [0, -3.1], [4.25, 0], [0, 3.1]], [0.9, 1.1, 0.9, 0.5, 0.6, 0.5]);
  const chevEl = mk("path", { d: poly(chev.map(([x, y]) => P2(PAD + x, cy + y, HB))), class: "nf" }, g);
  const [kr, ki] = rings(PAD + 13, cy - 5.2, PAD + 13 + CH * 1.5, cy + 5.2, 1.2, 0.8);
  const cursor = solid(g);
  put(cursor, prism(P2, front, kr, ki, HB, HB + 2.8));

  // The title bar and its buttons, painted after the lines: a line going up passes in behind it.
  const [tr, ti] = rings(IN, VA, W - IN, H - IN, 6, 1.4);
  put(solid(g), prism(P2, front, tr, ti, 0, HB));
  for (let i = 0; i < 3; i++) {
    const cx = PAD + i * 8.5, cv = (VA + H - IN) / 2;
    const [r, ri] = rings(cx - 2.8, cv - 2.8, cx + 2.8, cv + 2.8, 2.8, 0.8);
    put(solid(g), prism(P2, front, r, ri, HB, HB + 1.3));
  }

  /** Row j with the window scrolled to `top` lines: cut to the window, and lifted less as it nears either bar. */
  function drawRow(rw: Row, top: number) {
    const key = top + "|" + rw.sp.x;
    if (key === rw.drawn) return;
    rw.drawn = key;
    const vc = VA - (rw.j - top + 0.5) * G, v0 = Math.max(vc - T, VB), v1 = Math.min(vc + T, VA);
    const env = smooth(clamp((VA - vc - T) / E, 0, 1)) * smooth(clamp((vc - T - VB) / E, 0, 1));
    const w0 = rw.sp.x * env;
    for (const s of rw.segs) {
      if (v1 - v0 < 0.05) { put(s.el, { sil: "", crease: "" }); continue; }
      const ring = cut(rrect(s.x0, vc - T, s.x1, vc + T, T, 4)), inner = cut(rrect(s.x0 + 0.7, vc - T + 0.7, s.x1 - 0.7, vc + T - 0.7, T - 0.7, 4));
      put(s.el, prism(P2, front, ring, inner, w0, w0 + LH));
    }
  }

  function light(els: Element[]) {
    for (const el of lit) el.classList.remove("hi");
    lit = els;
    for (const el of lit) el.classList.add("hi");
  }

  const top = spring(REST_TOP, { eps: 0.002 });
  const B = register(stage, (dt) => {
    let m = stepS(top, dt);
    for (const rw of rows) { if (stepS(rw.sp, dt)) m = true; drawRow(rw, top.x); }
    return m;
  });
  bag.add(B.unregister);

  /** The slab-frame point [u, v] under a screen point, on the plane w. */
  function onFace([sx, sy]: Vec2, w: number): Vec2 {
    const o = P2(0, 0, w), a = P2(1, 0, w), b = P2(0, 1, w);
    const ax = a[0] - o[0], ay = a[1] - o[1], bx = b[0] - o[0], by = b[1] - o[1], det = ax * by - ay * bx;
    return [((sx - o[0]) * by - (sy - o[1]) * bx) / det, (ax * (sy - o[1]) - ay * (sx - o[0])) / det];
  }
  /** Where the pointer is, on the rest planes, nearest first: "prompt", a depth down the rows from 0 to 1, or null off the window. */
  function hit(p: Vec2): Over {
    const qb = onFace(p, HB), inU = (q: Vec2) => q[0] > IN && q[0] < W - IN;
    if (inU(qb) && qb[1] > IN && qb[1] < VB) return "prompt";
    if (inU(qb) && qb[1] > VA && qb[1] < H - IN) return 0;
    const q = onFace(p, 0);
    if (q[0] < 0 || q[0] > W || q[1] < 0 || q[1] > H) return null;
    return q[1] <= VB ? "prompt" : clamp((VA - G / 2 - q[1]) / ((V - 1) * G), 0, 1);
  }

  function retarget() {
    let t: number, c: number, r = R;
    if (over === null) { t = REST_TOP; c = REST_LINE; r = REST_R; read.textContent = "rest"; }
    else if (over === "prompt") { t = N - V; c = -1; read.textContent = "prompt"; }
    else {
      // The pointer runs over the row centres; the column scrolls with it, and the line nearest it is taken, kept clear of both bars.
      t = over * (N - V);
      c = clamp(Math.round(over * (N - 1)), Math.ceil(t), Math.floor(t + V - 1));
      read.textContent = "line " + (FIRST + c);
    }
    top.t = t;
    for (const rw of rows) rw.sp.t = c < 0 ? 0 : LIFT * falloff(Math.abs(rw.j - c), r);
    light(c < 0 ? [cursor.sil, chevEl] : rows[c].segs.map((s) => s.el.sil));
    B.wake();
  }
  retarget();
  for (const rw of rows) rw.sp.x = rw.sp.t;

  bag.add(pointer(stage, {
    move: (p) => { over = hit(p); retarget(); },
    leave: () => { over = null; retarget(); },
  }));
  bag.add(() => svg.replaceChildren());

  return {
    set: (v) => { R = v; if (over !== null) retarget(); },
    destroy: bag.dispose,
  };
};
