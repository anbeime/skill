import { Cam, clamp, facing, fit, hull, open, poly, prism, proj, rings, rrect, run, seg, type Projector, type Ring, type Sample, type Vec2, type Vec3 } from "../core/iso";
import { spring, stepS, type Spring } from "../core/motion";
import { disposer, mk, place, pointer, put, register, solid, type FigureMount, type Solid } from "../core/stage";

/**
 * Cabinet: a server rack of twelve 1U blades between two drilled rails, on a
 * plinth. Each blade is a chassis behind a faceplate: ears with pull handles
 * on the rails, four drive bays, a vent and a status lamp. The pointer's
 * height is read on the rack's closed front, and the blades near it slide out
 * along their rails, the farther the less, each on its own spring; the one
 * under it comes all the way and its lamp lights. At rest the last update has
 * stopped part-way: blade 7 half out and lit, a few others caught on the way.
 * The slider is the reach, in blades.
 *
 * The pattern: a continuous field, as Keyboard's, over a stack: a spring per
 * blade, a falloff by distance, a hit test on the rest pose's planes.
 */

const N = 12, U = 10.4, BH = 9.6, W = 84, EAR = 4, FT = 2, D = 44, OUT = 26;
const X0 = -10, X1 = W + 10, Z0 = 6, ZB = 11, ZT = ZB + (N - 1) * U + BH, H = ZT + 6;
/** Where the last update stopped: blade 7 half out, its neighbours and two others caught on their way. */
const REST = [0, 0, 0.2, 0, 0, 0.3, 0.58, 0.26, 0, 0, 0.13, 0];
const LIT = 6;

/** The share of full travel a blade comes out, u reaches from the pointer: all of it under the pointer, none past the reach. */
const falloff = (u: number) => (u >= 1 ? 0 : (1 - u) * (1 - u));
/** On a plate's front face, the samples whose edge meets its top or its right side: they lie inside the silhouette. */
const inner = (q: Sample) => 0.375 * q.nu + 0.307 * q.nv > 0;

/** A plate standing in the x-z plane, from y0 back to y1 front: its silhouette, and the crease of its front face. */
function slab(P: Projector, ring: Ring, inset: Ring | null, y0: number, y1: number) {
  const at = (r: Ring, y: number) => r.map((q): Vec2 => P(q.u, y, q.v));
  return { sil: poly(hull(at(ring, y0).concat(at(ring, y1)))), crease: inset ? open(at(run(inset, inner), y1)) : "" };
}

type Blade = {
  i: number; z: number;
  body: Ring; face: Ring; faceIn: Ring;
  chassis: Solid; plate: Solid; marks: SVGPathElement; lamp: SVGCircleElement;
  sp: Spring; drawn: number;
};

export const mount: FigureMount = ({ stage, svg, read }, value) => {
  const bag = disposer();
  const C = Cam(45, 0.5, 1.5);
  const yo = D + FT + OUT;
  fit(C, [[X0, 0, 0], [X1, 0, H], [X1, D, 0], [X0, 0, H], [-EAR, yo, ZB], [-EAR, yo, ZT], [W + EAR, yo, ZB]], 200, 166);
  const P = proj(C), front = facing(C);
  let R = value, over: number | null = null, lit: Blade | null = null;

  const g = mk("g", {}, svg);
  // the plinth, set back under the cabinet, then the cabinet itself
  const [pr, pi] = rings(X0 + 3, 3, X1 - 3, D - 3, 3, 1.2);
  put(solid(g), prism(P, front, pr, pi, 0, Z0));
  const [br, bi] = rings(X0, 0, X1, D, 3.5, 1.6);
  put(solid(g), prism(P, front, br, bi, Z0, H));
  // its front: the opening's edge round the rails, a hole in each rail for every U; and the side panel's inset
  const onFront = (r: Ring) => r.map((q): Vec2 => P(q.u, D, q.v)), onSide = (r: Ring) => r.map((q): Vec2 => P(X1, q.u, q.v));
  mk("path", { d: poly(onFront(rrect(-7.6, ZB - 2.2, W + 7.6, ZT + 2.2, 2, 4))) + poly(onSide(rrect(5, Z0 + 7, D - 5, H - 7, 3, 4))), class: "lo nf" }, g);
  for (let i = 0; i < N; i++) for (const x of [-5.8, W + 5.8]) {
    place(mk("circle", { r: 0.75, class: "dot off" }, g), P(x, D, ZB + i * U + BH / 2));
  }

  // Bottom to top: the camera looks down, so a lower blade can never cover a higher one.
  const blades: Blade[] = [];
  for (let i = 0; i < N; i++) {
    const z = ZB + i * U, gi = mk("g", {}, g);
    blades.push({
      i, z,
      body: rrect(0, z + 0.4, W, z + BH - 0.4, 1.6, 4),
      face: rrect(-EAR, z, W + EAR, z + BH, 2, 4),
      faceIn: rrect(-EAR + 0.8, z + 0.8, W + EAR - 0.8, z + BH - 0.8, 1.2, 4),
      chassis: solid(gi), plate: solid(gi),
      marks: mk("path", { class: "lo nf" }, gi),
      lamp: mk("circle", { r: 1.1, class: "dot off" }, gi),
      sp: spring(OUT * REST[i], { eps: 0.02 }), drawn: NaN,
    });
  }

  /** Blade b's faceplate marks, drawn on its front at y: two handles, four bays, a vent. */
  function marks(b: Blade, y: number) {
    const z = b.z, F = (r: Ring) => poly(r.map((q): Vec2 => P(q.u, y, q.v)));
    let d = F(rrect(-3.4, z + 2, -1.2, z + BH - 2, 1, 3)) + F(rrect(W + 1.2, z + 2, W + 3.4, z + BH - 2, 1, 3));
    for (let k = 0; k < 4; k++) d += F(rrect(4 + k * 10.6, z + 2, 13.8 + k * 10.6, z + BH - 2, 1, 3));
    for (let k = 0; k < 8; k++) d += seg(P(50 + k * 2.6, y, z + 2.5), P(50 + k * 2.6, y, z + BH - 2.5));
    return d;
  }

  function drawBlade(b: Blade) {
    const o = b.sp.x;
    if (o === b.drawn) return;
    b.drawn = o;
    const yf = D + o + FT, zm = b.z + BH / 2;
    const ch = slab(P, b.body, null, D, D + o + 0.5);
    // the slide: where the chassis's side rides out along its rail
    put(b.chassis, { sil: ch.sil, crease: seg(P(W, D, zm), P(W, D + o, zm)) });
    put(b.plate, slab(P, b.face, b.faceIn, D + o, yf));
    b.marks.setAttribute("d", marks(b, yf));
    place(b.lamp, P(W - 5, yf, zm));
  }

  function light(b: Blade) {
    if (b === lit) return;
    if (lit) { lit.plate.sil.classList.remove("hi"); lit.lamp.setAttribute("class", "dot off"); }
    lit = b;
    lit.plate.sil.classList.add("hi");
    lit.lamp.setAttribute("class", "dot");
  }

  const B = register(stage, (dt) => {
    let m = false;
    for (const b of blades) { if (stepS(b.sp, dt)) m = true; drawBlade(b); }
    return m;
  });
  bag.add(B.unregister);

  // The hit test: the pointer is put on the rack's planes with every blade home, which never move.
  const o0 = P(0, 0, 0), E = [P(1, 0, 0), P(0, 1, 0), P(0, 0, 1)].map((p) => [p[0] - o0[0], p[1] - o0[1]]);
  /** The world point under screen point p on the plane where coordinate `axis` is c. */
  function onPlane(p: Vec2, axis: number, c: number): Vec3 {
    const [a, k] = [0, 1, 2].filter((n) => n !== axis), ea = E[a], ek = E[k];
    const rx = p[0] - o0[0] - c * E[axis][0], ry = p[1] - o0[1] - c * E[axis][1], det = ea[0] * ek[1] - ea[1] * ek[0];
    const w: Vec3 = [0, 0, 0];
    w[axis] = c; w[a] = (rx * ek[1] - ry * ek[0]) / det; w[k] = (ea[0] * ry - ea[1] * rx) / det;
    return w;
  }
  /** The pointer's height, in blades from the bottom one, or null off the rack: first on each faceplate where it
   * stands at rest, top down as a higher blade covers a lower one; then on the closed front, and the side panel. */
  function hit(p: Vec2): number | null {
    for (let i = N - 1; i >= 0; i--) {
      const q = onPlane(p, 1, D + FT + OUT * REST[i]), z = (q[2] - ZB - BH / 2) / U;
      if (q[0] >= -EAR && q[0] <= W + EAR && Math.abs(z - i) <= 0.5) return z;
    }
    const f = onPlane(p, 1, D + FT), s = onPlane(p, 0, X1);
    let z: number | null = null;
    if (f[0] >= X0 - OUT - 4 && f[0] <= X1 && f[2] >= -OUT * 0.8 && f[2] <= H) z = f[2];
    else if (s[1] >= 0 && s[1] <= D && s[2] >= 0 && s[2] <= H + 4) z = s[2];
    return z === null ? null : clamp((z - ZB - BH / 2) / U, 0, N - 1);
  }

  function retarget() {
    if (over === null) {
      for (const b of blades) b.sp.t = OUT * REST[b.i];
      light(blades[LIT]); read.textContent = "rest";
    } else {
      for (const b of blades) b.sp.t = OUT * falloff(Math.max(0, Math.abs(b.i - over) - 0.5) / R);
      const a = Math.round(over);
      light(blades[a]); read.textContent = "blade " + (a + 1);
    }
    B.wake();
  }
  light(blades[LIT]);

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
