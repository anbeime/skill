import { hull, open, poly, ringAt, rrect, run, type Camera, type PrismPaths, type Projector, type Ring, type Sample } from "./core/iso";

/**
 * Slabs: the tiles, plates and frames of the graph figures, drawn whole. Not
 * in src/core, so the skill's kernel and the pages it wrote stay as they are.
 */

/**
 * A prism whose lid is drawn whole. The silhouette carries the lid's front
 * edge, so the lid reads as a face on its band, and the crease is the inset
 * ring all round, a lip.
 */
export function slab(
  P: Projector,
  front: (q: Sample) => boolean,
  ring: readonly Sample[],
  inner: readonly Sample[] | null | undefined,
  z0: number,
  z1: number,
): PrismPaths {
  return {
    sil: poly(hull(ringAt(P, ring, z1).concat(ringAt(P, ring, z0)))) + open(ringAt(P, run(ring, front), z1)),
    crease: inner ? poly(ringAt(P, inner, z1)) : "",
  };
}

/**
 * A ring set d inside another, the gap measured on the screen, so it reads even all the way round, corners
 * included. Concentric in plan is not enough: the 2:1 view squeezes the top and bottom corners, which pinches
 * the gap there, and stretches the side corners, which opens it. So each sample goes to the view plane with
 * its normal, moves d + m in, and stays only if it is that far inside every tangent; then it grows back m, and
 * where the cut took a corner out the ring turns round it at radius m. Then back to plan, to ride any height.
 */
export function inset(C: Camera, ring: readonly Sample[], d: number, m = 1): Ring {
  const c = Math.cos(C.az), s = Math.sin(C.az), k = C.k, e = d + m, out: Ring = [];
  const put = (x: number, y: number, a: number, b: number) => {
    const nu = c * a + k * s * b, nv = k * c * b - s * a, l = Math.hypot(nu, nv);
    out.push({ u: x * c + (y / k) * s, v: (y / k) * c - x * s, nu: nu / l, nv: nv / l });
  };
  // the view plane: the normal goes by the inverse transpose, so it stays square to the edge as drawn
  const v = ring.map((q) => {
    const a = q.nu * c - q.nv * s, b = (q.nu * s + q.nv * c) / k, l = Math.hypot(a, b);
    return [q.u * c - q.v * s, (q.u * s + q.v * c) * k, a / l, b / l];
  });
  const w = v
    .map(([x, y, a, b]) => [x - e * a, y - e * b, a, b])
    .filter(([x, y]) => v.every(([X, Y, a, b]) => (x - X) * a + (y - Y) * b < 1e-6 - e));
  w.forEach(([x, y, a, b], i) => {
    const [X, Y, A, B] = w[(i + 1) % w.length], t = Math.atan2(a * B - b * A, a * A + b * B);
    put(x + m * a, y + m * b, a, b);
    if (Math.abs(t) < 0.1) return;
    // the two edges meet at (px, py): round it
    const h = x * a + y * b, H = X * A + Y * B, D = a * B - b * A, px = (h * B - H * b) / D, py = (a * H - A * h) / D;
    for (let j = 0, n = Math.ceil(Math.abs(t) / 0.2); j <= n; j++) {
      const r = Math.atan2(b, a) + (t * j) / n, ca = Math.cos(r), sa = Math.sin(r);
      put(px + m * ca, py + m * sa, ca, sa);
    }
  });
  return out;
}

/** A rounded footprint and its lip, inset by b, sampled finely enough for a large tile: eight samples per corner. */
export const lid = (x0: number, y0: number, x1: number, y1: number, r: number, b: number): [Ring, Ring] => [
  rrect(x0, y0, x1, y1, r, 8),
  rrect(x0 + b, y0 + b, x1 - b, y1 - b, Math.max(0.3, r - b), 8),
];
