import { Cam, circ, clamp, facing, fit, hull, lerp, open, poly, prism, proj, rad, ringAt, rrect, run, seg, type Ring, type Vec2, type Vec3 } from "../core/iso";
import { spring, stepS, type Spring } from "../core/motion";
import { disposer, flatDot, mk, place, pointer, put, register, solid, type FigureMount, type Solid } from "../core/stage";

/**
 * Router: a low wifi router with a row of status lights along its front edge
 * and four antennas standing on swivel bosses along its back. Each antenna is a
 * tapered rod that leans in its own upright plane, square to the line of sight,
 * so the four never touch and always paint in the same order. The pointer pulls
 * each one toward itself on its own spring: the nearest reaches all the way
 * for it, the others less the further away they are. At rest they stand as they
 * were left, the last one tilted out and bright. The slider is the spread, in
 * antennas.
 *
 * The pattern: a continuous aim over a row of parts. A spring per antenna, a
 * falloff by distance with a floor, a clamped lean, and a hit test on the
 * antennas' fixed pivots.
 */

const X1 = 124, Y1 = 58, H = 14, T = 3, BR = 13;
const XS = [18, 48, 78, 108], YB = 11, KH = 5, KR = 4.6, L = 56, R0 = 3.3, R1 = 2.1, ELBOW = 0.21;
const STOP = R1 + 1, MAX = 44, REST = [-9, 3, -4, 32], LIT0 = 3;
const D = [Math.SQRT1_2, -Math.SQRT1_2];

/** The share of its reach an antenna takes, u pivots further from the pointer than the nearest one: all of it, down to a floor R pivots on. */
const falloff = (u: number, R: number) => clamp(1 - u / R, 0.1, 1);

/** Antenna i's axis, `l` along it, leaning th degrees in its plane (positive leans right on screen). */
const along = (i: number, th: number, l: number): Vec3 => {
  const s = Math.sin(rad(th)), c = Math.cos(rad(th));
  return [XS[i] + D[0] * s * l, YB + D[1] * s * l, H + KH - 1 + c * l];
};

type Ant = { i: number; el: Solid; sp: Spring; drawn: number; piv: Vec2 };

export const mount: FigureMount = ({ stage, svg, read }, value) => {
  const bag = disposer();
  let R = value, over: Vec2 | null = null, lit: Ant | null = null;

  // Fitted to the body and to every antenna at both ends of its lean, so nothing leaves the frame.
  const C = Cam(45, 0.5, 1.78), pts: Vec3[] = [[0, 0, 0], [X1, Y1, 0], [X1, 0, 0], [0, Y1, 0]];
  XS.forEach((_, i) => { for (const th of [-MAX, 0, MAX]) pts.push(along(i, th, L + R1)); });
  fit(C, pts, 200, 166);
  const P = proj(C), front = facing(C), Pv = (q: Vec3) => P(q[0], q[1], q[2]);
  const o = P(0, 0, 0), dd = P(D[0], D[1], 0), zz = P(0, 0, 1);
  const SH = Math.hypot(dd[0] - o[0], dd[1] - o[1]), SZ = o[1] - zz[1];

  // The body: a low shell, narrower at its top than at its foot, and the status lights along its front.
  const g = mk("g", {}, svg);
  const foot = rrect(0, 0, X1, Y1, BR, 6), top = rrect(T, T, X1 - T, Y1 - T, BR - T, 6);
  const inner = rrect(T + 1.6, T + 1.6, X1 - T - 1.6, Y1 - T - 1.6, BR - T - 1.6, 6);
  put(solid(g), { sil: poly(hull(ringAt(P, foot, 0).concat(ringAt(P, top, H)))), crease: open(ringAt(P, run(inner, front), H)) });
  for (let k = 0; k < 6; k++) {
    const z = H * 0.56, y = Y1 - T * (z / H) + 0.1;
    place(mk("circle", { r: 1.05, class: k === 0 ? "dot m" : "dot off" }, g), P(34 + k * 9, y, z));
  }
  // a vent grille across the front of the lid, in staggered rows
  for (let j = 0; j < 3; j++) for (let k = 0; k < 13 - (j % 2); k++) place(flatDot(g, C, 0.5, "dot off"), P(26 + (j % 2) * 3 + k * 6, 29 + j * 5.5, H));

  // Back to front: each antenna's boss, then the antenna. Every antenna leans in a plane x + y = const, so the order never changes.
  const ants: Ant[] = XS.map((x, i) => {
    const boss = solid(g);
    const shift = (ring: Ring): Ring => ring.map((q) => ({ ...q, u: q.u + x, v: q.v + YB }));
    put(boss, prism(P, front, shift(circ(KR, 16)), shift(circ(KR - 1.1, 16)), H, H + KH));
    return { i, el: solid(g), sp: spring(REST[i], { eps: 0.05 }), drawn: NaN, piv: Pv(along(i, 0, 0)) };
  });
  const gap = Math.abs(ants[1].piv[0] - ants[0].piv[0]) / SH;

  /** A disc of screen points about p, r world units across. */
  const disc = (p: Vec2, r: number): Vec2[] => Array.from({ length: 20 }, (_, k): Vec2 => [p[0] + r * SH * Math.cos((k * Math.PI) / 10), p[1] + r * SH * Math.sin((k * Math.PI) / 10)]);
  function drawAnt(a: Ant) {
    const th = a.sp.x;
    if (th === a.drawn) return;
    a.drawn = th;
    const b = Pv(along(a.i, th, 0)), t = Pv(along(a.i, th, L)), e = Pv(along(a.i, th, L * ELBOW));
    const len = Math.hypot(t[0] - b[0], t[1] - b[1]), n = [-(t[1] - b[1]) / len, (t[0] - b[0]) / len];
    const w = lerp(R0, R1, ELBOW) * SH - 1.1;
    put(a.el, {
      sil: poly(hull(disc(b, R0).concat(disc(t, R1)))),
      crease: seg([e[0] + n[0] * w, e[1] + n[1] * w], [e[0] - n[0] * w, e[1] - n[1] * w]),
    });
  }
  function light(a: Ant) {
    if (a === lit) return;
    lit?.el.sil.classList.remove("hi");
    lit = a;
    a.el.sil.classList.add("hi");
  }

  const B = register(stage, (dt) => {
    let m = false;
    for (const a of ants) { if (stepS(a.sp, dt)) m = true; drawAnt(a); }
    return m;
  });
  bag.add(B.unregister);

  /**
   * Each antenna aims at the pointer from its fixed pivot, in its own plane. A
   * pointer within reach is raised onto the circle the tip sweeps, so a tip
   * stops just short of it and never passes it: two antennas either side of
   * the pointer meet over it, and never cross.
   */
  function retarget() {
    if (!over) {
      ants.forEach((a, i) => { a.sp.t = REST[i]; });
      light(ants[LIT0]); read.textContent = "rest";
    } else {
      const at = over;
      const dxs = ants.map((a) => (at[0] - a.piv[0]) / SH), d0 = Math.min(...dxs.map(Math.abs));
      const near = ants[dxs.findIndex((d) => Math.abs(d) === d0)];
      ants.forEach((a, i) => {
        const dx = Math.sign(dxs[i]) * Math.max(Math.abs(dxs[i]) - STOP, 0), hz = Math.max((a.piv[1] - at[1]) / SZ, Math.sqrt(Math.max(L * L - dx * dx, 0)), 0);
        const aim = (Math.atan2(dx, hz) * 180) / Math.PI;
        a.sp.t = clamp(aim, -MAX, MAX) * falloff((Math.abs(dxs[i]) - d0) / gap, R);
      });
      light(near);
      read.textContent = `antenna ${near.i + 1} · ${Math.round(Math.abs(near.sp.t))}°`;
    }
    B.wake();
  }
  light(ants[LIT0]);

  bag.add(pointer(stage, {
    move: (p) => { over = p; retarget(); },
    leave: () => { over = null; retarget(); },
  }));
  bag.add(() => svg.replaceChildren());

  return {
    set: (v) => { R = v; if (over) retarget(); },
    destroy: bag.dispose,
  };
};
