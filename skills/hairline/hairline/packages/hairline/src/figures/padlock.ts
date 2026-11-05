import { Cam, circ, clamp, fillet, fit, hull, open, poly, proj, rad, run, type Ring, type Vec2, type Vec3 } from "../core/iso";
import { spring, stepS } from "../core/motion";
import { disposer, mk, pointer, put, register, solid, type FigureMount } from "../core/stage";

/**
 * Padlock: a solid body with a keyway in its face, and a U-shaped shackle, a
 * round bar drawn as one tube. As the pointer comes near the lock, the
 * shackle rises out of the body on a spring; once its short leg has cleared
 * its hole, it swings about its long leg, which never leaves the body. Going
 * away drops it back and locks it. At rest it is caught just unlatched: up,
 * a little turned, bright. The slider is how far it swings, in degrees.
 *
 * The pattern: a continuous field with one part, as Terrain's falloff: one
 * spring on how open the lock is, set by the pointer's distance to the body,
 * which never moves. Lift and turn are both read from that one number, the
 * turn only once the lift is done, so the short leg can never cut the body.
 */

const W = 56, D = 20, H = 44, B = 1.6;                        // body: width, depth, height, crease inset
const T = 4.2, S2 = 30, XL = 13, YC = D / 2, ARM = 13, SINK = 7, LIFT = 11; // shackle: bar radius, leg spacing, long leg's x, legs' y, straight above the body, short leg's depth when shut, lift
const O1 = 0.42, REST_TURN = 26, R0 = 56, R1 = 200, SC = 2.75, TMAX = 100;
const VX = Math.SQRT1_2 * Math.sqrt(3);                      // the view's x (and y) for a z of 1, at Cam(45, .5)
const ss = (t: number) => t * t * (3 - 2 * t);

/** A closed outline in the face's own (x, z), as ring samples with outward normals. */
function samples(pts: readonly Vec2[]): Ring {
  return pts.map((p, i) => {
    const a = pts[(i + pts.length - 1) % pts.length], b = pts[(i + 1) % pts.length];
    const tx = b[0] - a[0], tz = b[1] - a[1], l = Math.hypot(tx, tz) || 1;
    return { u: p[0], v: p[1], nu: tz / l, nv: -tx / l };
  });
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

/** The bar's outline: its screen centre line offset by its radius, each end a flat round cut seen from above. */
function tube(Q: readonly Vec2[], rho: number): string {
  const n = Q.length, A: Vec2[] = [], Bk: Vec2[] = [];
  for (let i = 0; i < n; i++) {
    const a = Q[Math.max(i - 1, 0)], c = Q[i], b = Q[Math.min(i + 1, n - 1)];
    const u0 = [c[0] - a[0], c[1] - a[1]], u1 = [b[0] - c[0], b[1] - c[1]];
    const l0 = Math.hypot(u0[0], u0[1]) || 1, l1 = Math.hypot(u1[0], u1[1]) || 1;
    let tx = u0[0] / l0 + u1[0] / l1, ty = u0[1] / l0 + u1[1] / l1;
    const l = Math.hypot(tx, ty) || 1; tx /= l; ty /= l;
    A.push([c[0] - ty * rho, c[1] + tx * rho]); Bk.push([c[0] + ty * rho, c[1] - tx * rho]);
  }
  const cap = (c: Vec2) => { const o: Vec2[] = []; for (let k = 7; k >= 1; k--) { const t = (Math.PI * k) / 8; o.push([c[0] + rho * Math.cos(t), c[1] + rho * 0.5 * Math.sin(t)]); } return o; };
  return poly([...untangle(A), ...cap(Q[n - 1]), ...untangle(Bk).reverse(), ...cap(Q[0])]);
}

export const mount: FigureMount = ({ stage, svg, read }, value) => {
  const bag = disposer();
  const tm = spring(value);
  let over = false;

  // The shackle's centre line, from the short leg's end, over the bow, down the long leg into its hole.
  const line = <R>(P: (x: number, y: number, z: number) => R, lift: number, th: number): R[] => {
    const u = [Math.cos(rad(th)), -Math.sin(rad(th))], za = H + ARM + lift, r = S2 / 2;
    const at = (s: number, z: number) => P(XL + u[0] * s, YC + u[1] * s, z);
    const pts = [at(S2, Math.max(H - SINK + lift, H)), at(S2, za)];
    for (let i = 1; i < 28; i++) { const f = (Math.PI * i) / 28; pts.push(at(r + r * Math.cos(f), za + r * Math.sin(f))); }
    pts.push(at(0, za), at(0, H));
    return pts;
  };

  // The camera is fitted to the body and the shackle at its highest and furthest swing.
  const C = Cam(45, 0.5, SC);
  const id = (x: number, y: number, z: number): Vec3 => [x, y, z];
  const ext: Vec3[] = [[0, 0, 0], [W, 0, 0], [0, D, 0], [W, D, 0], [0, 0, H]];
  for (const th of [0, 40, 80, TMAX]) for (const p of line(id, LIFT, th)) ext.push([p[0], p[1], p[2] + T]);
  fit(C, ext, 200, 170);
  const P = proj(C), rho = T * SC;

  // The body: its face a rounded block, fuller at the foot, stood out along y.
  const face = fillet([[0, 0], [W, 0], [W, H], [0, H]], [14, 14, 7, 7], 12);
  const inner = samples(fillet([[B, B], [W - B, B], [W - B, H - B], [B, H - B]], [14 - B, 14 - B, 7 - B, 7 - B], 12));
  const g = mk("g", {}, svg);
  put(solid(g), {
    sil: poly(hull(face.map((p) => P(p[0], 0, p[1])).concat(face.map((p) => P(p[0], D, p[1]))))),
    crease: open(run(inner, (q) => q.nu * VX + q.nv > 0).map((q) => P(q.u, D, q.v))),
  });

  // The keyway: a round hole and the slot under it, one closed cut in the face.
  const kx = W / 2, kz = H * 0.56, kr = 4.4, kw = 1.8, kb = kz - 12, a0 = Math.asin(kw / kr), key: Vec2[] = [];
  for (let i = 0; i <= 20; i++) { const t = -Math.PI / 2 + a0 + ((2 * Math.PI - 2 * a0) * i) / 20; key.push([kx + kr * Math.cos(t), kz + kr * Math.sin(t)]); }
  for (let i = 0; i <= 6; i++) { const t = Math.PI + (Math.PI * i) / 6; key.push([kx + kw * Math.cos(t), kb + kw * Math.sin(t)]); }
  mk("path", { d: poly(key.map((p) => P(p[0], D, p[1]))), class: "nf" }, g);

  // The two holes in the top the legs stand in.
  const hole = circ(T + 1.3, 20);
  for (const x of [XL, XL + S2]) mk("path", { d: poly(hole.map((q) => P(x + q.u, YC + q.v, H))), class: "nf lo" }, g);

  const bar = mk("path", { class: "sil" }, g);

  /** Lift and turn from how open the lock is: the lift first, then, with the short leg clear, the turn. */
  const pose = (o: number, max: number): [number, number] => [LIFT * ss(clamp(o / O1, 0, 1)), max * ss(clamp((o - O1) / (1 - O1), 0, 1))];
  /** How open the rest pose is: just unlatched, turned REST_TURN degrees, whatever the slider. */
  const restO = () => O1 + (1 - O1) * (0.5 - Math.sin(Math.asin(1 - (2 * REST_TURN) / tm.t) / 3));

  const sp = spring(restO(), { eps: 0.002 });
  let dO = NaN, dT = NaN;
  function draw() {
    if (sp.x === dO && tm.x === dT) return;
    dO = sp.x; dT = tm.x;
    const [lift, th] = pose(sp.x, tm.x);
    bar.setAttribute("d", tube(line(P, lift, th), rho));
  }

  const loop = register(stage, (dt) => { const a = stepS(sp, dt), b = stepS(tm, dt); draw(); return a || b; });
  bag.add(loop.unregister);

  const c0 = P(W / 2, D / 2, H / 2);
  function retarget() {
    const [lift, th] = pose(sp.t, tm.t), shut = over && lift < SINK;   // read from the targets, never the pose on screen
    read.textContent = !over ? "rest" : shut ? "locked" : th < 1 ? "open" : Math.round(th) + "°";
    bar.classList.toggle("hi", !shut);
    loop.wake();
  }
  retarget();

  bag.add(pointer(stage, {
    move: (p) => { over = true; sp.t = clamp((R1 - Math.hypot(p[0] - c0[0], p[1] - c0[1])) / (R1 - R0), 0, 1); retarget(); },
    leave: () => { over = false; sp.t = restO(); retarget(); },
  }));
  bag.add(() => svg.replaceChildren());

  return {
    set: (v) => { tm.t = v; if (!over) sp.t = restO(); retarget(); },
    destroy: bag.dispose,
  };
};
