import { Cam, clamp, facing, fit, hull, open, poly, prism, proj, ringAt, rings, rrect, run, seg, unproj, type Ring, type Vec2 } from "../core/iso";
import { spring, stepS, type Spring } from "../core/motion";
import { disposer, mk, pointer, put, register, solid, type FigureMount, type Solid } from "../core/stage";

/**
 * Keyboard: a sixty-key board, rows staggered as a real one's are, with the
 * long keys a hand finds without looking: backspace, enter, the two shifts,
 * the space bar. Each cap is narrower at its top than at its foot, and each row
 * stands at its own height, the sculpted profile. The pointer is put on the
 * tops of the rows at rest, front row first; the key under it sinks all the
 * way and its neighbours follow it down, less the further away, each on its own
 * spring. At rest, enter is caught half-way down, bright. The slider is the
 * radius, in keys.
 *
 * The pattern: a continuous field, as Terrain's, over discrete parts: a spring
 * per key, a falloff by distance, a hit test on each row's rest top.
 */

const U = 14, PAD = 0.8, TAPER = 1.8, Z0 = 1, TRAVEL = 8, BZ = 6, CASE = 8, W = 15;
/** Each row's rest height, back to front: the sculpted profile, lowest on the home row. */
const ROW_H = [12.6, 11.3, 10.4, 11, 11.8];
/** Each row's keys, as [width in keys, read-out]. Fifteen keys wide; sixty keys in all. */
const L = (s: string) => s.split(" ").map((c): [number, string] => [1, "key " + c]);
const ROWS: Array<Array<[number, string]>> = [
  [[1, "esc"], ...L("1 2 3 4 5 6 7 8 9 0 - ="), [2, "bksp"]],
  [[1.5, "tab"], ...L("q w e r t y u i o p [ ]"), [1.5, "key \\"]],
  [[1.75, "caps"], ...L("a s d f g h j k l ; '"), [2.25, "enter"]],
  [[2.25, "shift l"], ...L("z x c v b n m , . /"), [2.75, "shift r"]],
  [[1.5, "ctrl l"], [1, "super"], [1.5, "alt l"], [7, "space"], [1.5, "alt r"], [1, "fn"], [1.5, "ctrl r"]],
];
const HOMING = ["key f", "key j"];

/** The share of full travel a neighbour sinks, u radii from the pointer: all of it at the pressed key's edge, nothing past one radius. */
const falloff = (u: number) => clamp(1 - u, 0, 1);

type Key = {
  r: number; name: string; x0: number; x1: number; y0: number; y1: number; h: number;
  foot: Ring; top: Ring; inner: Ring; el: Solid; sp: Spring; drawn: number; bump: SVGPathElement | null;
};
type Over = { at: Vec2; key: Key };

export const mount: FigureMount = ({ stage, svg, read }, value) => {
  const bag = disposer();
  const C = Cam(45, 0.5, 1.42);
  fit(C, [[-BZ, -BZ, -CASE], [W * U + BZ, 5 * U + BZ, -CASE], [W * U + BZ, -BZ, -CASE], [-BZ, 5 * U + BZ, -CASE], [0, 0, ROW_H[0]]], 200, 166);
  const P = proj(C), front = facing(C);
  let R = value, over: Over | null = null, lit: Key | null = null;

  const g = mk("g", {}, svg);
  const [cr, ci] = rings(-BZ, -BZ, W * U + BZ, 5 * U + BZ, 9, 2.2);
  put(solid(g), prism(P, front, cr, ci, -CASE, 0));

  // Row by row from the back, and left to right in a row: each key is cut from
  // the ones behind it and to its left by a vertical plane, so this is back to front.
  const keys: Key[] = [];
  ROWS.forEach((row, r) => {
    let x = 0;
    for (const [w, name] of row) {
      const x0 = x * U, x1 = (x + w) * U, y0 = r * U, y1 = (r + 1) * U, t = PAD + TAPER;
      const el = solid(g);
      keys.push({
        r, name, x0, x1, y0, y1, h: ROW_H[r],
        foot: rrect(x0 + PAD, y0 + PAD, x1 - PAD, y1 - PAD, 2.6, 4),
        top: rrect(x0 + t, y0 + t, x1 - t, y1 - t, 2, 4),
        inner: rrect(x0 + t + 0.9, y0 + t + 0.9, x1 - t - 0.9, y1 - t - 0.9, 1.2, 4),
        el, sp: spring(ROW_H[r], { eps: 0.02 }), drawn: NaN,
        bump: HOMING.includes(name) ? mk("path", { class: "lo nf" }, el.g) : null,
      });
      x += w;
    }
  });
  const enter = keys.find((k) => k.name === "enter")!;

  /** Each key's target depth, from a point on the board, the key pressed, a radius in keys and a share of full travel. */
  function sink(at: Vec2, pressed: Key, radius: number, depth: number) {
    for (const k of keys) {
      const dx = Math.max(k.x0 - at[0], 0, at[0] - k.x1), dy = Math.max(k.y0 - at[1], 0, at[1] - k.y1);
      const f = k === pressed ? 1 : falloff(Math.hypot(dx, dy) / (radius * U));
      k.sp.t = k.h - TRAVEL * depth * f;
    }
  }
  const restAt: Vec2 = [(enter.x0 + enter.x1) / 2, (enter.y0 + enter.y1) / 2];
  sink(restAt, enter, 1.6, 0.6);
  for (const k of keys) k.sp.x = k.sp.t;

  function drawKey(k: Key) {
    const h = k.sp.x;
    if (h === k.drawn) return;
    k.drawn = h;
    put(k.el, { sil: poly(hull(ringAt(P, k.foot, Z0).concat(ringAt(P, k.top, h)))), crease: open(ringAt(P, run(k.inner, front), h)) });
    if (k.bump) {
      const cx = (k.x0 + k.x1) / 2, cy = k.y1 - PAD - TAPER - 2.4;
      k.bump.setAttribute("d", seg(P(cx - 2.2, cy, h), P(cx + 2.2, cy, h)));
    }
  }
  function light(k: Key) {
    if (k === lit) return;
    lit?.el.sil.classList.remove("hi");
    lit = k;
    k.el.sil.classList.add("hi");
  }

  const B = register(stage, (dt) => {
    let m = false;
    for (const k of keys) { if (stepS(k.sp, dt)) m = true; drawKey(k); }
    return m;
  });
  bag.add(B.unregister);

  const keyAt = (r: number, x: number) => keys.find((k) => k.r === r && x >= k.x0 && x < k.x1)!;
  /** The key under a screen point, tested against each row's rest top, front row first, as a nearer row covers a farther one. */
  function hit(p: Vec2): Over | null {
    for (let r = ROWS.length - 1; r >= 0; r--) {
      const q = unproj(C, p[0], p[1], ROW_H[r]);
      if (q[1] < r * U || q[1] >= (r + 1) * U || q[0] < 0 || q[0] >= W * U) continue;
      return { at: q, key: keyAt(r, q[0]) };
    }
    // in a gap between two rows' tops, or over the bezel: the nearest key on the board
    const q = unproj(C, p[0], p[1], ROW_H[2]);
    if (q[0] < -BZ || q[0] > W * U + BZ || q[1] < -BZ || q[1] > 5 * U + BZ) return null;
    const at: Vec2 = [clamp(q[0], 0, W * U - 0.01), clamp(q[1], 0, 5 * U - 0.01)];
    return { at, key: keyAt(Math.floor(at[1] / U), at[0]) };
  }

  function retarget() {
    if (over) { sink(over.at, over.key, R, 1); light(over.key); read.textContent = over.key.name; }
    else { sink(restAt, enter, 1.6, 0.6); light(enter); read.textContent = "rest"; }
    B.wake();
  }
  light(enter);

  bag.add(pointer(stage, {
    move: (p) => { over = hit(p); retarget(); },
    leave: () => { over = null; retarget(); },
  }));
  bag.add(() => svg.replaceChildren());

  return {
    set: (v) => { R = v; if (over) retarget(); },
    destroy: bag.dispose,
  };
};
