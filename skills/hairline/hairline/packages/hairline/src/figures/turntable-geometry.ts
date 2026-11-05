/**
 * Turntable — the blocks on the platter and the order they are painted in,
 * with no DOM, so the one part of the figure that can go wrong all the way
 * round (tests/hairline-geometry.spec.ts sweeps it) is checked without a
 * browser. From the study's sixth figure (design/lab-hairline/cartilha-v2.html).
 *
 * The camera turns and the blocks stand still, so which block is in front
 * changes with the azimuth and is worked out again every frame. `s` and `c`
 * are sin and cos of the azimuth, `k` is sin(elevation).
 */

/** One axis-aligned block: [x0, y0, z0, x1, y1, z1, column]. A column is blocks stacked on one footprint. */
export type Blk = readonly [number, number, number, number, number, number, number];

export const BLK: readonly Blk[] = [
  [-42, -42, 0, -12, -12, 14, 0], [-36, -36, 14, -18, -18, 34, 0],
  [0, -46, 0, 16, -6, 10, 1],
  [24, -32, 0, 40, -16, 44, 2],
  [-44, 4, 0, -4, 18, 22, 3],
  [8, 6, 0, 40, 38, 8, 4], [16, 14, 8, 28, 26, 20, 4],
  [-30, 28, 0, -16, 42, 12, 5],
];

/** The azimuth the figure is drawn at, and the quarter turn between its detents. */
export const HOME = 45;
export const DETENT = 90;

/** The nearest quarter-turn detent to an angle, in degrees: every stop is 2:1 again. */
export const detent = (a: number) => HOME + DETENT * Math.round((a - HOME) / DETENT);

/** A sort key for blocks no plane separates: farther is smaller. */
export const depth = (b: Blk, s: number, c: number) => (b[0] + b[3]) * s + (b[1] + b[4]) * c + (b[2] + b[5]) * 0.01;

/**
 * Whether A is painted before B. Two blocks in one column stack, lower first;
 * otherwise any axis plane between their footprints says which one is behind.
 */
export function behind(A: Blk, B: Blk, s: number, c: number): boolean {
  if (A[6] === B[6]) return A[2] < B[2];
  if (A[3] <= B[0]) return s > 0;
  if (B[3] <= A[0]) return s < 0;
  if (A[4] <= B[1]) return c > 0;
  if (B[4] <= A[1]) return c < 0;
  return depth(A, s, c) < depth(B, s, c);
}

/** A block's screen box at unit scale and no offset: [x0, y0, x1, y1]. */
export function scr(b: Blk, s: number, c: number, k: number): [number, number, number, number] {
  const zf = Math.sqrt(1 - k * k);
  let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
  for (const x of [b[0], b[3]]) for (const y of [b[1], b[4]]) for (const z of [b[2], b[5]]) {
    const X = x * c - y * s, Y = (x * s + y * c) * k - z * zf;
    x0 = Math.min(x0, X); x1 = Math.max(x1, X); y0 = Math.min(y0, Y); y1 = Math.max(y1, Y);
  }
  return [x0, y0, x1, y1];
}

/**
 * The painter's order and how many picks had to break a cycle. Only pairs
 * whose screen boxes overlap are constrained (far pairs could otherwise chain
 * into a cycle), then a topological sort draws the farthest free block first.
 * If no block is free, the farthest waiting one is forced; `forced` counts
 * those, and for BLK it should stay 0 at every angle.
 */
export function paintOrder(bs: readonly Blk[], s: number, c: number, k: number): { order: number[]; forced: number } {
  const n = bs.length, bx = bs.map((b) => scr(b, s, c, k));
  const next: number[][] = bs.map(() => []), wait = bs.map(() => 0);
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
    const a = bx[i], b = bx[j];
    if (i === j || a[2] <= b[0] || b[2] <= a[0] || a[3] <= b[1] || b[3] <= a[1]) continue;
    if (behind(bs[i], bs[j], s, c)) { next[i].push(j); wait[j]++; }
  }
  const out: number[] = [], done = bs.map(() => false);
  let forced = 0;
  while (out.length < n) {
    let pick = -1, pass = 0;
    for (; pass < 2 && pick < 0; pass++)
      for (let i = 0; i < n; i++)
        if (!done[i] && (pass || !wait[i]) && (pick < 0 || depth(bs[i], s, c) < depth(bs[pick], s, c))) pick = i;
    if (pass === 2) forced++;
    done[pick] = true; out.push(pick);
    for (const j of next[pick]) wait[j]--;
  }
  return { order: out, forced };
}

/** Indices into `bs`, back to front. */
export const order = (bs: readonly Blk[], s: number, c: number, k: number) => paintOrder(bs, s, c, k).order;
