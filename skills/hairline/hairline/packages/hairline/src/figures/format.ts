import { Cam, clamp, facing, fit, proj, rad, rrect, unproj, type Ring, type Vec2 } from "../core/iso";
import { reducedMotion, spring, stepS, type Spring } from "../core/motion";
import { disposer, mk, pointer, put, register, solid, type FigureMount, type Solid } from "../core/stage";
import { lid, slab } from "../slab";

/**
 * Format: a file as a stack of ten thin slabs on a rounded board, one to a
 * line, indented like code. At rest it is unformatted: every line pivoted
 * about its own start, its indent wrong, none touching another. The pointer
 * runs the formatter down the file: every line above the pointer swings square
 * to its indent on a spring, staggered line by line; lines below stay as they
 * were. The line at the formatter's front takes the bright edge (none at
 * rest), which the kernel's stroke transition fades from line to line.
 * Leaving un-formats the file slowly, bottom-up, with no bounce.
 * The slider is the disorder, in degrees of the worst skew.
 *
 * The pattern: discrete items on springs. A stagger by distance, a hit test on
 * the ground plane (which never moves), and a rest that is a composition.
 */

const G = 12, WD = 5.5, T = 2.4, X0 = 8, IND = 13, PB = 5, STEP = 55, STEP_OUT = 80, MAXV = 14;
const BX0 = -9, BX1 = 118, BY0 = -8, BY1 = 9 * G + WD + 8, GUT = 1;
// Each line: indent level, length, and how it sits crooked at rest, as fractions of the slider's far end:
// yaw (about its own start, the indent point), dx (the indent error), dy (a small shift along the page), dz (unused: a raised line would cross its neighbour on screen).
// Picked by search so that no two lines touch at any slider value or any mix of their springs (lines further down are never less crooked than the ones above while the formatter runs).
const LINES: [number, number, number, number, number, number][] = [
  [0, 56, 0.3, -8, -2, 0],
  [1, 40, 0.75, 8, -1.9, 0],
  [1, 58, 0.3, -8, -0.8, 0],
  [2, 74, 1, -8, -1.9, 0],
  [2, 48, 1, 8, 1.3, 0],
  [1, 34, 0.3, 8, 2, 0],
  [1, 66, 1, -8, -2, 0],
  [2, 52, 1, -8, -0.8, 0],
  [1, 30, 0.45, 8, 2, 0],
  [0, 22, 1, -8, 1.6, 0],
];
const N = LINES.length;

type Row = {
  r: number; yaw: number; dx: number; dy: number; dz: number; px: number; py: number; drawn: number;
  ring: Ring; sp: Spring; tgt: number; due: number; el: Solid;
  lit: boolean; wantLit: boolean; litDue: number;
};

/** A ring turned by th degrees about (cx, cy) and moved by (dx, dy): normals turn with it. */
function turn(ring: Ring, cx: number, cy: number, th: number, dx: number, dy: number): Ring {
  const s = Math.sin(rad(th)), c = Math.cos(rad(th));
  return ring.map((q) => ({
    u: cx + (q.u - cx) * c - (q.v - cy) * s + dx, v: cy + (q.u - cx) * s + (q.v - cy) * c + dy,
    nu: q.nu * c - q.nv * s, nv: q.nu * s + q.nv * c,
  }));
}

export const mount: FigureMount = ({ stage, svg, read }, value) => {
  const bag = disposer();
  let mess = value / MAXV;

  // The camera is fitted to the board and to the most crooked, most raised line at the slider's far end.
  const C = Cam(45, 0.5, 1.9);
  fit(C, [[BX0, BY0, -PB], [BX1, BY0, -PB], [BX0, BY1, -PB], [BX1, BY1, -PB], [BX1, BY1, 9]], 200, 168);
  const P = proj(C), front = facing(C);

  const g = mk("g", {}, svg);
  const [br, bi] = lid(BX0, BY0, BX1, BY1, 8, 2.2);
  put(solid(g), slab(P, front, br, bi, -PB, 0));
  // the gutter: a dashed guide on the board, before any line lies on it
  mk("path", { d: `M${P(X0 - 4, BY0 + 5, 0).join(" ")}L${P(X0 - 4, BY1 - 5, 0).join(" ")}`, class: "dash" }, g);

  const rows = LINES.map(([lv, len, yaw, dx, dy, dz], r) => {
    const x0 = X0 + lv * IND, y0 = r * G;
    const e = solid(g);
    return {
      r, yaw, dx, dy, dz, px: x0, py: y0 + WD / 2, drawn: NaN,
      ring: rrect(x0, y0, x0 + len, y0 + WD, 2.2, 6),
      sp: spring(1, { k: 100, c: 14, eps: 0.003 }), tgt: 1, due: -1, el: e,
      // the bright edge: the kernel's stroke transition fades it in and out; this only says when
      lit: false, wantLit: false, litDue: -1,
    } as Row;
  });

  function draw(w: Row) {
    const m = w.sp.x;
    if (m !== w.drawn) {
      w.drawn = m;
      const k = m * mess, th = w.yaw * MAXV * k, z = Math.max(0, m) * w.dz * mess;
      put(w.el, slab(P, front, turn(w.ring, w.px, w.py, th, w.dx * k, w.dy * k), null, z, z + T));
    }
  }

  let fr = -1;
  const B = register(stage, (dt, now) => {
    let moving = false;
    for (const w of rows) {
      if (w.due >= 0) { if (now >= w.due) { w.sp.t = w.tgt; w.due = -1; } else moving = true; }
      if (stepS(w.sp, dt)) moving = true;
      if (w.litDue >= 0) {
        if (now >= w.litDue) { w.litDue = -1; if (w.lit !== w.wantLit) { w.lit = w.wantLit; w.el.sil.classList.toggle("hi", w.lit); } } else moving = true;
      }
      draw(w);
    }
    return moving;
  });
  bag.add(B.unregister);

  /** Lines 0..a are formatted. New ones snap in a ripple down from the old front; un-formatting is slow and goes bottom-up: the last to be fixed is the first to go. */
  function setFront(a: number) {
    if (a === fr) return;
    const now = performance.now(), prev = fr, rm = reducedMotion();
    fr = a;
    for (const w of rows) {
      const tgt = w.r <= a ? 0 : 1;
      if (tgt !== w.tgt) {
        w.tgt = tgt;
        const slow = tgt === 1;
        w.sp.k = slow ? 22 : 100; w.sp.c = slow ? 9.4 : 14;
        w.due = now + (rm ? 0 : slow ? (N - 1 - w.r) * STEP_OUT : (w.r - (prev + 1)) * STEP);
      }
      // the bright edge belongs to the line at the front, and to nothing at rest; it arrives with that line's snap
      const on = w.r === a ? 1 : 0;
      w.wantLit = !!on;
      w.litDue = now + (on && !rm ? Math.max(0, w.r - (prev + 1)) * STEP : 0);
    }
    read.textContent = a < 0 ? "rest" : `ln ${a + 1}`;
    B.wake();
  }

  // The pointer is read on the ground plane, which never moves: the line is the band of rows it is over.
  const rowAt = (p: Vec2) => {
    const [x, y] = unproj(C, p[0], p[1], 0);
    return x < BX0 || x > BX1 || y < BY0 || y > BY1 ? -1 : clamp(Math.floor(y / G), -1, N - 1);
  };
  bag.add(pointer(stage, { move: (p) => setFront(rowAt(p)), leave: () => setFront(-1) }));
  bag.add(() => svg.replaceChildren());

  rows.forEach((w) => draw(w));
  return {
    set: (v) => { mess = v / MAXV; rows.forEach((w) => { w.drawn = NaN; }); B.wake(); },
    destroy: bag.dispose,
  };
};
