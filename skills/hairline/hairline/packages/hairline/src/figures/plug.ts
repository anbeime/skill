import { Cam, circ, clamp, fit, hull, lerp, open, poly, proj, rad, rrect, run, unproj, type Ring, type Vec2, type Vec3 } from "../core/iso";
import { spring, stepS } from "../core/motion";
import { disposer, mk, pointer, put, register, solid, type FigureMount } from "../core/stage";

/**
 * Plug: a wall plate with a socket, and a plug lying on the floor at the end
 * of a cord that curves away out of the frame. The pointer draws the plug up
 * toward the socket on a spring, and the cord pays out behind it. It never
 * seats: it stops short, and falls back when the pointer leaves. At rest it
 * lies on the floor, its two pins bright, the socket's holes bare. The slider
 * is how much of the way to the socket the plug can come.
 *
 * The pattern: follow a position. One spring on how far along its way the
 * plug is, set from where the pointer falls on the screen line from the
 * plug's rest to the socket, which never moves. Where the plug is and how far
 * it has turned to face the wall are both read from that one number.
 */

const PT = 3, PH = 21, ZC = 30, PR = 7, B = 1.4;           // the plate: thickness, half its side, the socket's height, corner radius, crease inset
const HOLE = 2.6, HS = 8, RECESS = 13;                     // the socket: hole radius, the holes' offset from its centre, the recess round them
const BW = 11, BH = 6.5, BR = 4.5, BL = 18;                // the plug's body: half width, half height, corner radius, length
const PIN = 2, PL = 11, SL = 7, S0 = 4.6, S1 = 3, CR = 1.8; // pin radius, pin length, the sleeve's length and two radii, the cord's radius
const REST: Vec2 = [48, 8], YAW = 100, TURN = 0.7, S = 2.8; // the pins' face on the floor, its heading, the share of the way the turn takes, scale
const EDGE = 398;                                          // where the cord leaves the picture: the viewBox's right edge, less a stroke
const ss = (t: number) => t * t * (3 - 2 * t);

/** Cuts the loops an inner offset makes where the cord bends tighter than its radius on screen. */
function untangle(L: Vec2[]): Vec2[] {
  for (let i = 0; i < L.length - 3; i++) for (let j = L.length - 2; j > i + 1; j--) {
    const p = L[i], q = L[i + 1], r = L[j], s = L[j + 1];
    const e0 = q[0] - p[0], e1 = q[1] - p[1], f0 = s[0] - r[0], f1 = s[1] - r[1], g0 = r[0] - p[0], g1 = r[1] - p[1], d = e0 * f1 - e1 * f0;
    if (!d) continue;
    const t = (g0 * f1 - g1 * f0) / d, u = (g0 * e1 - g1 * e0) / d;
    if (t > 0 && t < 1 && u > 0 && u < 1) { L.splice(i + 1, j - i, [p[0] + t * e0, p[1] + t * e1]); break; }
  }
  return L;
}

/** A screen line up to where it first crosses x = X, ending on it. */
function upTo(L: Vec2[], X: number): Vec2[] {
  const i = L.findIndex((p) => p[0] > X);
  if (i < 1) return i < 0 ? L : [];
  const p = L[i - 1], q = L[i], f = (X - p[0]) / (q[0] - p[0]);
  return [...L.slice(0, i), [X, p[1] + (q[1] - p[1]) * f]];
}

/** The cord's outline: its screen centre line offset by its radius, the plug's end a round cut, the far end cut off at x = X with no line across it, as the frame would. */
function tube(Q: readonly Vec2[], rho: number, X: number): string {
  const n = Q.length, A: Vec2[] = [], Bk: Vec2[] = [];
  for (let i = 0; i < n; i++) {
    const a = Q[Math.max(i - 1, 0)], c = Q[i], b = Q[Math.min(i + 1, n - 1)];
    let tx = b[0] - a[0], ty = b[1] - a[1];
    const l = Math.hypot(tx, ty) || 1; tx /= l; ty /= l;
    A.push([c[0] - ty * rho, c[1] + tx * rho]); Bk.push([c[0] + ty * rho, c[1] - tx * rho]);
  }
  const cap = (c: Vec2) => { const o: Vec2[] = []; for (let k = 7; k >= 1; k--) { const t = (Math.PI * k) / 8; o.push([c[0] + rho * Math.cos(t), c[1] + rho * 0.5 * Math.sin(t)]); } return o; };
  return open([...upTo(untangle(Bk), X).reverse(), ...cap(Q[0]), ...upTo(untangle(A), X)]);
}

/** Where the plug is s of the way to the socket: the centre of its pins' face, its heading (w) and its width (u). Up is up. */
function pose(s: number): { c: Vec3; w: Vec3; u: Vec3 } {
  const th = rad(lerp(YAW, 180, ss(clamp(s / TURN, 0, 1))));
  return {
    c: [lerp(REST[0], PL, s), lerp(REST[1], 0, s), lerp(BH, ZC, Math.sin((s * Math.PI) / 2))],
    w: [Math.cos(th), Math.sin(th), 0],
    u: [-Math.sin(th), Math.cos(th), 0],
  };
}

export const mount: FigureMount = ({ stage, svg, read }, value) => {
  const bag = disposer();
  const C = Cam(45, 0.5, S), zf = Math.sqrt(1 - C.k * C.k);
  /** Toward the camera: a face whose normal has a positive dot with this is seen. */
  const V: Vec3 = [Math.sin(C.az) * zf, Math.cos(C.az) * zf, C.k];
  const dot = (a: Vec3, b: Vec3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  /** A point in the plug's own frame: a across, b up, d along its heading from the pins' face. */
  const at = (o: ReturnType<typeof pose>, a: number, b: number, d: number): Vec3 =>
    [o.c[0] + a * o.u[0] + d * o.w[0], o.c[1] + a * o.u[1] + d * o.w[1], o.c[2] + b];

  // The camera is fitted to the plate and the plug at both ends of its way.
  const ext: Vec3[] = [];
  for (const x of [0, -PT]) for (const y of [-PH, PH]) for (const z of [ZC - PH, ZC + PH]) ext.push([x, y, z]);
  for (const s of [0, 1]) { const o = pose(s); for (const a of [-BW, BW]) for (const b of [-BH, BH]) for (const d of [PL, -BL - SL]) ext.push(at(o, a, b, d)); }
  fit(C, ext, 200, 166);
  const P = proj(C), Pv = (p: Vec3) => P(p[0], p[1], p[2]);

  // The plate: a thin slab on the wall, its face toward +x, the recess and two holes cut into it.
  const g = mk("g", {}, svg);
  const face = rrect(-PH, ZC - PH, PH, ZC + PH, PR, 6), lip = rrect(-PH + B, ZC - PH + B, PH - B, ZC + PH - B, PR - B, 6);
  put(solid(g), {
    sil: poly(hull(face.map((q) => P(0, q.u, q.v)).concat(face.map((q) => P(-PT, q.u, q.v))))),
    crease: open(run(lip, (q) => q.nu * V[1] + q.nv * V[2] > 0).map((q) => P(0, q.u, q.v))),
  });
  mk("path", { class: "nf lo", d: poly(circ(RECESS, 48).map((q) => P(0, q.u, ZC + q.v))) }, g);
  mk("path", { class: "nf", d: [-HS, HS].map((y) => poly(circ(HOLE, 16).map((q) => P(0, y + q.u, ZC + q.v)))).join("") }, g);

  // The plug, back to front as it lies; the order turns over with it.
  const pg = mk("g", {}, svg);
  const cord = mk("path", { class: "sil" }, pg), sleeve = mk("path", { class: "sil" }, pg), body = solid(pg), pins = mk("path", { class: "sil hi" }, pg);
  const s0 = circ(S0, 16), s1 = circ(S1, 16);
  /** An end rounded over rr: the cross-section f(inset) in four steps, from the face at d inward along dir. */
  const rounded = (f: (k: number) => Ring, rr: number, d: number, dir: number) =>
    [0, 30, 60, 90].map((a): [Ring, number] => [f(rr * (1 - Math.sin(rad(a)))), d + dir * rr * (1 - Math.cos(rad(a)))]);
  const box = (k: number) => rrect(-BW + k, -BH + k, BW - k, BH - k, BR - k), rod = (k: number) => circ(PIN - k, 12);
  const inner = box(2), shell = [...rounded(box, 2, 0, -1), ...rounded(box, 2, -BL, 1)], prong = [[rod(0), 0] as [Ring, number], ...rounded(rod, PIN * 0.8, PL, -1)];
  /** The silhouette of a solid swept through cross-sections, each a ring at a distance along the heading, a0 across. */
  const sweep = (o: ReturnType<typeof pose>, parts: Array<[Ring, number]>, a0 = 0) =>
    poly(hull(parts.flatMap(([r, d]) => r.map((q) => Pv(at(o, a0 + q.u, q.v, d))))));

  // The cord's floor end, past the frame's right edge, and the floor point it bends round; neither moves.
  // The cord is drawn only up to just inside that edge, so it runs out of the picture without leaving the viewBox.
  const end: Vec3 = [...unproj(C, 440, 150, CR), CR], bend: Vec3 = [REST[0] + 18, REST[1] - 52, CR];
  let front = true, drawn = NaN;
  const sp = spring(0, { eps: 0.002 });

  function draw() {
    if (sp.x === drawn) return;
    drawn = sp.x;
    const o = pose(sp.x), pinsFace = dot(o.w, V) > 0, vu = dot(o.u, V);
    if (pinsFace !== front) { front = pinsFace; pg.append(...(front ? [cord, sleeve, body.g, pins] : [pins, body.g, cord, sleeve])); }
    const dEnd = front ? 0 : -BL;
    put(body, {
      sil: sweep(o, shell),
      crease: open(run(inner, (q) => q.nu * vu + q.nv * V[2] > 0).map((q) => Pv(at(o, q.u, q.v, dEnd)))),
    });
    pins.setAttribute("d", [-HS, HS].map((a) => sweep(o, prong, a)).join(""));
    sleeve.setAttribute("d", sweep(o, [[s0, -BL], [s1, -BL - SL]]));
    // The cord: a cubic from inside the sleeve's end, leaving along the plug's heading, round the bend to the floor end.
    const t0 = at(o, 0, 0, -BL - SL + 2), t1 = at(o, 0, 0, -BL - SL - 26), Q: Vec2[] = [];
    for (let i = 0; i <= 40; i++) {
      const t = i / 40, a = (1 - t) ** 3, b = 3 * (1 - t) ** 2 * t, c = 3 * (1 - t) * t * t, d = t ** 3;
      Q.push(P(a * t0[0] + b * t1[0] + c * bend[0] + d * end[0], a * t0[1] + b * t1[1] + c * bend[1] + d * end[1], a * t0[2] + b * t1[2] + c * bend[2] + d * end[2]));
    }
    cord.setAttribute("d", tube(Q, CR * S, EDGE));
  }

  const loop = register(stage, (dt) => { const m = stepS(sp, dt); draw(); return m; });
  bag.add(loop.unregister);

  // The line the pointer is read along: from the pins' face at rest to the socket, on screen. Neither moves.
  const A = Pv(pose(0).c), Bs = P(0, 0, ZC), ab: Vec2 = [Bs[0] - A[0], Bs[1] - A[1]], ab2 = ab[0] * ab[0] + ab[1] * ab[1];
  let pull = value, along = -1;
  function retarget() {
    sp.t = along < 0 ? 0 : Math.min(along, pull);
    // the gap from the pins' tips to the socket, read from the target, never the pose on screen
    const o = pose(sp.t), tip = at(o, 0, 0, PL);
    read.textContent = along < 0 ? "rest" : `gap ${Math.round(Math.hypot(tip[0], tip[1], tip[2] - ZC))} · 0 V`;
    loop.wake();
  }
  retarget();
  draw();

  bag.add(pointer(stage, {
    move: (p) => { along = clamp(((p[0] - A[0]) * ab[0] + (p[1] - A[1]) * ab[1]) / ab2, 0, 1); retarget(); },
    leave: () => { along = -1; retarget(); },
  }));
  bag.add(() => svg.replaceChildren());

  return { set: (v) => { pull = v; retarget(); }, destroy: bag.dispose };
};
