/**
 * Hairline — the drawing maths every figure shares, with no DOM. Ported from
 * the study (design/lab-hairline/cartilha-v2.html) arithmetic-for-arithmetic,
 * so a figure here can be diffed against its IIFE there by eye.
 *
 * Everything is in viewBox units: every figure is drawn in a 400 × 320 box and
 * scaled to its column by the svg, so no number here depends on the viewport.
 * World space is x/y on the ground and z up; the camera turns the ground by an
 * azimuth, then squashes y by sin(el) and lifts z by cos(el). There is no
 * perspective and no hidden-line removal: plates are filled with the ground
 * colour and painted back to front, so a nearer one simply covers.
 */

export type Vec2 = [number, number];
export type Vec3 = [number, number, number];

/** A sample on a rounded outline, with its outward normal on the ground plane. */
export type Sample = { u: number; v: number; nu: number; nv: number };
export type Ring = Sample[];

/**
 * An orthographic camera. `az` is in radians, `k` is sin(elevation) (.5 is
 * the 2:1 view every figure rests at), `S` is the scale, and `ox`/`oy` the
 * screen offset `fit` computes. Mutable on purpose: the turntable turns it.
 */
export type Camera = { az: number; k: number; S: number; ox: number; oy: number };
export type Projector = (x: number, y: number, z: number) => Vec2;

/** Two lines of a solid: its bright silhouette and the one dim crease inside it. */
export type PrismPaths = { sil: string; crease: string };

export const clamp = (v: number, a: number, b: number) => Math.max(a, Math.min(b, v));
export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
export const rad = (d: number) => (d * Math.PI) / 180;
/** Two decimals: enough for a hairline at any zoom, and path strings stay short. */
export const r2 = (n: number) => Math.round(n * 100) / 100;

/** A closed path through the points. */
export const poly = (pts: readonly Vec2[]) =>
  "M" + pts.map((p) => r2(p[0]) + " " + r2(p[1])).join("L") + "Z";
/** One straight segment, as its own subpath, so several can be joined into one `d`. */
export const seg = (a: Vec2, b: Vec2) => `M${r2(a[0])} ${r2(a[1])}L${r2(b[0])} ${r2(b[1])}`;
/** An open polyline; empty for fewer than two points. */
export const open = (pts: readonly Vec2[]) =>
  pts.length < 2 ? "" : "M" + pts.map((p) => r2(p[0]) + " " + r2(p[1])).join("L");

/* ---------- projection ---------- */

export const Cam = (azDeg: number, k: number, S: number): Camera => ({ az: rad(azDeg), k, S, ox: 0, oy: 0 });

/**
 * The projector for the camera as it is now. Figures that move the camera
 * (the turntable) call this again each frame; the rest call it once.
 */
export function proj(C: Camera): Projector {
  const c = Math.cos(C.az), s = Math.sin(C.az), zf = Math.sqrt(1 - C.k * C.k);
  return (x, y, z) => {
    const X = x * c - y * s, Y = x * s + y * c;
    return [C.ox + C.S * X, C.oy + C.S * (Y * C.k - z * zf)];
  };
}

/**
 * The ground-plane inverse: the world x/y under a screen point, on the plane
 * at height z. This is how the pointer reaches the drawing — every hover in
 * the figures is tested in world units, never in pixels.
 */
export function unproj(C: Camera, sx: number, sy: number, z: number): [number, number] {
  const c = Math.cos(C.az), s = Math.sin(C.az), zf = Math.sqrt(1 - C.k * C.k);
  const X = (sx - C.ox) / C.S, Y = ((sy - C.oy) / C.S + z * zf) / C.k;
  return [X * c + Y * s, -X * s + Y * c];
}

/** Sets the camera's offset so the bounding box of `pts` is centred on (cx, cy). */
export function fit(C: Camera, pts: readonly Vec3[], cx: number, cy: number) {
  C.ox = 0; C.oy = 0;
  const P = proj(C);
  let a = 1e9, b = -1e9, c = 1e9, d = -1e9;
  for (const p of pts) {
    const q = P(p[0], p[1], p[2]);
    a = Math.min(a, q[0]); b = Math.max(b, q[0]); c = Math.min(c, q[1]); d = Math.max(d, q[1]);
  }
  C.ox = cx - (a + b) / 2; C.oy = cy - (c + d) / 2;
}

/* ---------- rounded solids ---------- */

/**
 * A rounded rectangle, sampled. Each sample carries its outward normal, so a
 * caller can keep just the run that faces the camera. `n` samples per corner.
 */
export function rrect(u0: number, v0: number, u1: number, v1: number, r: number, n = 4): Ring {
  r = Math.max(0, Math.min(r, (u1 - u0) / 2, (v1 - v0) / 2));
  const out: Ring = [];
  for (const [cu, cv, a0] of [[u1 - r, v1 - r, 0], [u0 + r, v1 - r, 90], [u0 + r, v0 + r, 180], [u1 - r, v0 + r, 270]])
    for (let k = 0; k <= n; k++) {
      const a = rad(a0 + (90 * k) / n), ca = Math.cos(a), sa = Math.sin(a);
      out.push({ u: cu + r * ca, v: cv + r * sa, nu: ca, nv: sa });
    }
  return out;
}

/** A circle of radius R about the origin, sampled the same way. */
export function circ(R: number, n = 96): Ring {
  const out: Ring = [];
  for (let k = 0; k < n; k++) {
    const a = (k / n) * Math.PI * 2, ca = Math.cos(a), sa = Math.sin(a);
    out.push({ u: R * ca, v: R * sa, nu: ca, nv: sa });
  }
  return out;
}

/** Convex hull (monotone chain), counter-clockwise in screen space. */
export function hull(input: readonly Vec2[]): Vec2[] {
  const pts = input.slice().sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const x = (o: Vec2, a: Vec2, b: Vec2) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const lo: Vec2[] = [], up: Vec2[] = [];
  for (const p of pts) { while (lo.length > 1 && x(lo[lo.length - 2], lo[lo.length - 1], p) <= 0) lo.pop(); lo.push(p); }
  for (let i = pts.length - 1; i >= 0; i--) { const p = pts[i]; while (up.length > 1 && x(up[up.length - 2], up[up.length - 1], p) <= 0) up.pop(); up.push(p); }
  lo.pop(); up.pop();
  return lo.concat(up);
}

/** A ring laid flat at height z, projected. */
export const ringAt = (P: Projector, ring: readonly Sample[], z: number): Vec2[] => ring.map((q) => P(q.u, q.v, z));

/**
 * The samples whose normal faces the camera. The world direction of
 * screen-down is (sin az, cos az), so facing is a dot product with it.
 */
export const facing = (C: Camera) => {
  const s = Math.sin(C.az), c = Math.cos(C.az);
  return (q: Sample) => q.nu * s + q.nv * c >= -1e-6;
};

/** The one cyclic run of samples that pass `keep`, in ring order. */
export function run(ring: readonly Sample[], keep: (q: Sample) => boolean): Ring {
  const n = ring.length;
  let s = -1;
  for (let i = 0; i < n; i++) if (keep(ring[i]) && !keep(ring[(i + n - 1) % n])) { s = i; break; }
  if (s < 0) return keep(ring[0]) ? ring.slice() : [];
  const out: Ring = [];
  for (let k = 0; k < n && keep(ring[(s + k) % n]); k++) out.push(ring[(s + k) % n]);
  return out;
}

/**
 * A prism standing from z0 to z1. Its silhouette is the hull of the two rings,
 * so the vertical corners are never drawn; its only inner line is the crease,
 * the front run of an inset ring on the lid, which reads as a bevel.
 */
export function prism(
  P: Projector,
  front: (q: Sample) => boolean,
  ring: readonly Sample[],
  inner: readonly Sample[] | null | undefined,
  z0: number,
  z1: number,
): PrismPaths {
  return {
    sil: poly(hull(ringAt(P, ring, z1).concat(ringAt(P, ring, z0)))),
    crease: inner ? open(ringAt(P, run(inner, front), z1)) : "",
  };
}

/** A rounded footprint and its crease ring, inset by b. */
export const rings = (x0: number, y0: number, x1: number, y1: number, r: number, b: number): [Ring, Ring] => [
  rrect(x0, y0, x1, y1, r),
  rrect(x0 + b, y0 + b, x1 - b, y1 - b, Math.max(0.3, r - b)),
];

/** The leftmost, rightmost and nearest samples of a ring: where construction lines drop from. */
export function extremes(P: Projector, ring: readonly Sample[]): [Sample, Sample, Sample] {
  const pr = ring.map((q) => P(q.u, q.v, 0));
  let a = 0, b = 0, c = 0;
  pr.forEach((p, k) => { if (p[0] < pr[a][0]) a = k; if (p[0] > pr[b][0]) b = k; if (p[1] > pr[c][1]) c = k; });
  return [ring[a], ring[b], ring[c]];
}

/** Rounds every vertex of a closed polygon with a quadratic through the vertex; r per vertex. */
export function fillet(pts: readonly Vec2[], rs: readonly number[], n = 4): Vec2[] {
  const m = pts.length, out: Vec2[] = [];
  for (let i = 0; i < m; i++) {
    const a = pts[(i + m - 1) % m], p = pts[i], b = pts[(i + 1) % m];
    const la = Math.hypot(a[0] - p[0], a[1] - p[1]), lb = Math.hypot(b[0] - p[0], b[1] - p[1]);
    const t = Math.min(rs[i], la / 2, lb / 2);
    const p1 = [p[0] + ((a[0] - p[0]) / la) * t, p[1] + ((a[1] - p[1]) / la) * t];
    const p2 = [p[0] + ((b[0] - p[0]) / lb) * t, p[1] + ((b[1] - p[1]) / lb) * t];
    for (let k = 0; k <= n; k++) {
      const s = k / n, w = 1 - s;
      out.push([w * w * p1[0] + 2 * w * s * p[0] + s * s * p2[0], w * w * p1[1] + 2 * w * s * p[1] + s * s * p2[1]]);
    }
  }
  return out;
}

/**
 * A prism's mirror under its floor, as a path: the far edge of the reflection
 * and its two sides. `y0`/`y1` are where its fade starts (the floor's top) and
 * ends (just past the reflection's lowest point).
 */
export function ghost(
  P: Projector, front: (q: Sample) => boolean, ring: readonly Sample[], z0: number, depth: number,
): { d: string; y0: number; y1: number } {
  const f = run(ring, front), lowP = ringAt(P, f, z0 - depth);
  return {
    d: open(lowP) + [f[0], f[f.length - 1]].map((q) => seg(P(q.u, q.v, z0), P(q.u, q.v, z0 - depth))).join(""),
    y0: Math.min(...ringAt(P, f, z0).map((p) => p[1])),
    y1: Math.max(...lowP.map((p) => p[1])) + 2,
  };
}
