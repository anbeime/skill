import { Cam, circ, clamp, facing, fit, open, poly, prism, proj, rad, type Vec2, type Vec3 } from "../core/iso";
import { spring, stepS } from "../core/motion";
import { disposer, mk, pointer, put, register, solid, type FigureMount } from "../core/stage";
import { TABLE } from "../intensity";

/**
 * Query: a question mark built as a solid on a small round plinth. The hook
 * is one bent bar, swept along a centre line of an arc, a neck and a stem, as
 * Padlock's shackle is; the dot is a ball lying loose on the plinth under it.
 * The pointer turns the hook about its stem toward it, and the ball rolls
 * round after it, later and softer, and comes back to lie under the stem. At
 * rest the hook stands well off square and the ball lies on its axis,
 * under the stem's foot, bright: the dot of the mark. The slider is how far
 * the hook turns, in degrees.
 *
 * The pattern: follow a position. One spring on the hook's turn, set by the
 * pointer's screen x against the stem's, which never moves. The ball follows
 * that turn on a softer spring, because a loose ball lags what it rolls after;
 * it is pushed off the axis only by how far it lags, a few units at most, so
 * it always reads as the dot and settles back under the stem.
 */

const PR = 27, PH = 6, B = 1.6;                         // the plinth: radius, height, crease inset
const T = 4.3, R = 16, ZC = 66, A0 = 200, A1 = -35;     // the bar: radius, the hook's radius, its centre's height, where the arc starts and ends
const ZK = 38, ZS = 29, BR = 6, SWAY = 0.2, TRAVEL = 4; // the neck's foot, the stem's end, the ball's radius, how far off the axis a degree of lag pushes it, and the most it goes
const FACE = -45, REST = 36, REACH = 150, S = 2.6;        // the plane that faces the camera, the rest turn, the pointer's reach in viewBox units, scale
const LIGHT: Vec2 = [-Math.SQRT1_2, -Math.SQRT1_2], GLEAM = 0.4; // where the light comes from on screen (the ball's glint too), and how far the bar's crease leans to it, in radii

/** The centre line in the hook's own plane (s across, z up): over the arc, down the neck, down the stem. */
const LINE: Vec2[] = /* @__PURE__ */ (() => {
  const pts: Vec2[] = [];
  for (let i = 0; i <= 30; i++) { const a = rad(A0 + ((A1 - A0) * i) / 30); pts.push([R * Math.cos(a), ZC + R * Math.sin(a)]); }
  const e = pts[pts.length - 1], a = rad(A1), t: Vec2 = [Math.sin(a), -Math.cos(a)];
  const c1: Vec2 = [e[0] + t[0] * 10, e[1] + t[1] * 10], c2: Vec2 = [0, ZK + 10];   // long handles: the neck bends no tighter than 2.5 bar radii
  for (let i = 1; i <= 20; i++) {
    const u = i / 20, w = 1 - u;
    pts.push([w * w * w * e[0] + 3 * w * w * u * c1[0] + 3 * w * u * u * c2[0], w * w * w * e[1] + 3 * w * w * u * c1[1] + 3 * w * u * u * c2[1] + u * u * u * ZK]);
  }
  pts.push([0, ZS]);
  return pts;
})();

/** The run of LINE the bar's crease follows: the arc, short of its tip and of the neck. */
const ARC = [2, 28];

/** Point i of a screen centre line, moved d toward the light across the bar: the line a round section catches its light on. */
function lean(Q: readonly Vec2[], i: number, d: number): Vec2 {
  const a = Q[Math.max(i - 1, 0)], b = Q[Math.min(i + 1, Q.length - 1)], l = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
  const nx = -(b[1] - a[1]) / l, ny = (b[0] - a[0]) / l, k = d * (nx * LIGHT[0] + ny * LIGHT[1]);
  return [Q[i][0] + nx * k, Q[i][1] + ny * k];
}

/** Where two screen segments cross, or null. */
function cross(p: Vec2, q: Vec2, r: Vec2, s: Vec2): Vec2 | null {
  const e0 = q[0] - p[0], e1 = q[1] - p[1], f0 = s[0] - r[0], f1 = s[1] - r[1], g0 = r[0] - p[0], g1 = r[1] - p[1];
  const d = e0 * f1 - e1 * f0;
  if (!d) return null;
  const t = (g0 * f1 - g1 * f0) / d, u = (g0 * e1 - g1 * e0) / d;
  return t > 0 && t < 1 && u > 0 && u < 1 ? [p[0] + t * e0, p[1] + t * e1] : null;
}
/** Cuts the loops an inner offset makes where the bar bends tighter than its radius on screen. */
function untangle(L: Vec2[]): Vec2[] {
  for (let i = 0; i < L.length - 3; i++) for (let j = L.length - 2; j > i + 1; j--) {
    const x = cross(L[i], L[i + 1], L[j], L[j + 1]);
    if (x) { L.splice(i + 1, j - i, x); break; }
  }
  return L;
}

/** The bar's outline: its screen centre line offset by its radius. The curl's tip is a dome, round from anywhere; the stem's foot is cut flat, seen from above. */
function tube(Q: readonly Vec2[], rho: number): string {
  const n = Q.length, A: Vec2[] = [], Bk: Vec2[] = [], tan: Vec2[] = [];
  for (let i = 0; i < n; i++) {
    const a = Q[Math.max(i - 1, 0)], c = Q[i], b = Q[Math.min(i + 1, n - 1)];
    const l0 = Math.hypot(c[0] - a[0], c[1] - a[1]) || 1, l1 = Math.hypot(b[0] - c[0], b[1] - c[1]) || 1;
    let tx = (c[0] - a[0]) / l0 + (b[0] - c[0]) / l1, ty = (c[1] - a[1]) / l0 + (b[1] - c[1]) / l1;
    const l = Math.hypot(tx, ty) || 1; tx /= l; ty /= l;
    tan.push([tx, ty]);
    A.push([c[0] - ty * rho, c[1] + tx * rho]); Bk.push([c[0] + ty * rho, c[1] - tx * rho]);
  }
  /** The dome: half a round from the near side to the far, through the point the tip faces. */
  const dome = (c: Vec2, t: Vec2) => Array.from({ length: 9 }, (_, k): Vec2 => {
    const a = (Math.PI * (k + 1)) / 10, cs = -Math.cos(a), sn = -Math.sin(a);
    return [c[0] + rho * (-t[1] * cs + t[0] * sn), c[1] + rho * (t[0] * cs + t[1] * sn)];
  });
  /** The flat cut: the near half of a level round, as Padlock's ends are. The stem stands plumb, so it runs left to right. */
  const cut = (c: Vec2) => Array.from({ length: 7 }, (_, k): Vec2 => { const a = (Math.PI * (7 - k)) / 8; return [c[0] + rho * Math.cos(a), c[1] + rho * 0.5 * Math.sin(a)]; });
  return poly([...untangle(A), ...cut(Q[n - 1]), ...untangle(Bk).reverse(), ...dome(Q[0], tan[0])]);
}

export const mount: FigureMount = ({ stage, svg, read }, value) => {
  const bag = disposer();
  const TMAX = TABLE.query[2];
  let max = value, over = false;

  /** The hook's plane, turned th degrees from facing the camera: a point (s, z) of it in the world. */
  const at = (th: number) => { const a = rad(FACE - th), c = Math.cos(a), n = Math.sin(a); return (s: number, z: number): Vec3 => [s * c, s * n, z]; };
  /** The ball's centre: on the axis under the stem, pushed across the hook's plane by how far it lags the turn. */
  const ball = (lag: number, th: number): Vec3 => at(th)(clamp(lag * SWAY, -TRAVEL, TRAVEL), PH + BR);

  // The camera is fitted to the plinth and the hook at both ends of its widest turn.
  const C = Cam(45, 0.5, S);
  const ext: Vec3[] = [[-PR, 0, 0], [PR, 0, 0], [0, -PR, 0], [0, PR, 0]];
  for (const th of [-TMAX, -TMAX / 2, 0, TMAX / 2, TMAX]) for (const p of LINE) { const q = at(th)(p[0], p[1]); ext.push([q[0], q[1], q[2] + T], [q[0], q[1], q[2] - T]); }
  fit(C, ext, 200, 166);
  C.ox += 200 - proj(C)(0, 0, 0)[0];   // the stem stands on the frame's middle, however unevenly the turns reach
  const P = proj(C), front = facing(C), rho = T * S;
  const g = mk("g", {}, svg);

  // Back to front: the plinth, the ball lying on it, the hook over it.
  put(solid(g), prism(P, front, circ(PR, 72), circ(PR - B, 72), 0, PH));
  const dot = solid(g);
  const disc = circ(BR * S, 40), shine = circ(BR * S * 0.62, 40).slice(23, 31);
  const bar = mk("path", { class: "sil" }, g);
  const gleam = mk("path", { class: "nf lo" }, g);

  /** The rest turn: off square, the other way from where it opens, and always inside the slider's reach. */
  const rest = () => -Math.min(REST, 0.9 * max);
  const sp = spring(rest()), roll = spring(rest(), { k: 36, c: 7 });
  let dH = NaN, dB = NaN;
  function draw() {
    if (sp.x !== dH) {
      dH = sp.x;
      const w = at(sp.x);
      const Q = LINE.map((p) => P(...w(p[0], p[1])));
      bar.setAttribute("d", tube(Q, rho));
      gleam.setAttribute("d", open(Q.slice(ARC[0], ARC[1]).map((c, i) => lean(Q, ARC[0] + i, GLEAM * rho))));
    }
    const lag = sp.x - roll.x;
    if (lag !== dB) {
      dB = lag;
      const c = P(...ball(lag, roll.x));
      put(dot, { sil: poly(disc.map((q) => [c[0] + q.u, c[1] + q.v])), crease: open(shine.map((q): Vec2 => [c[0] + q.u, c[1] + q.v])) });
    }
  }

  const loop = register(stage, (dt) => {
    roll.t = sp.x;   // the ball rolls after where the hook is, not where it is going
    const a = stepS(sp, dt), b = stepS(roll, dt);
    draw();
    return a || b;
  });
  bag.add(loop.unregister);

  const cx = P(0, 0, 0)[0];
  let px = cx;
  function retarget() {
    sp.t = over ? max * clamp((px - cx) / REACH, -1, 1) : rest();   // read from the target, never the turn on screen
    read.textContent = over ? `turn ${Math.abs(Math.round(sp.t))}° · 0` : "rest";
    dot.sil.classList.toggle("hi", !over);
    bar.classList.toggle("hi", over);
    loop.wake();
  }
  retarget();

  bag.add(pointer(stage, {
    move: (p) => { over = true; px = p[0]; retarget(); },
    leave: () => { over = false; retarget(); },
  }));
  bag.add(() => svg.replaceChildren());

  return { set: (v) => { max = v; retarget(); }, destroy: bag.dispose };
};
