import { Cam, circ, fit, hull, open, poly, proj, unproj, type Vec2, type Vec3 } from "../core/iso";
import { tdone, tset, tval, tween } from "../core/motion";
import { disposer, mk, pointer, put, register, solid, type FigureMount } from "../core/stage";
import { TABLE } from "../intensity";

/**
 * Sieve: three test sieves stacked over a pan, standing a little apart. The
 * pointer's height picks a sieve; it rises clear of the one below, the ones
 * above it ride up with it, and each mesh is bare. At rest the stack is parted
 * under the middle sieve, whose rim is bright. The slider is the gap.
 *
 * The pattern: one of many. A tween for the gap under each sieve, staggered
 * outwards from the one picked. The pick is read from the sieves' rest
 * heights, which move only with the slider, never from the stack on screen.
 */

const N = 3, R = 36, H = 11, PAN = 8, WALL = 2.6, SEAT = 2, FLOOR = 1.6; // sieves, radius, a sieve's height, the pan's, wall, closed gap, the mesh above a sieve's foot
const CHORDS = [-22, -11, 0, 11, 22], STEP = 40, S = 2.35, REST = 0.8, RIDE = 0.6; // mesh chords, stagger ms, scale, the rest gap and the gap above a pick, as shares of the gap

/** The gap under sieve i when sieve f is picked (-1 for rest: the stack parted under the middle one). */
const under = (f: number, i: number, gap: number) => {
  const a = f < 0 ? 1 : f;
  return i === a ? (f < 0 ? gap * REST : gap) : f >= 0 && i === a + 1 ? gap * RIDE : SEAT;
};

export const mount: FigureMount = ({ stage, svg, read }, value) => {
  const bag = disposer();
  const [, MID, MAX] = TABLE.sieve;
  const C = Cam(45, 0.5, S);
  // The tallest pose (a lower sieve picked at the widest gap) and the rest stack at the default gap. The box
  // runs as far below the rest stack's middle as the tallest top is above it: rest sits in the middle, and the tallest still fits.
  const tall = PAN + N * H + SEAT + MAX * (1 + RIDE), rest = PAN + N * H + 2 * SEAT + MID * REST;
  const ext: Vec3[] = [];
  for (const [x, y] of [[-R, 0], [R, 0], [0, -R], [0, R]]) ext.push([x, y, rest - tall], [x, y, tall]);
  fit(C, ext, 200, 166);
  const P = proj(C), y0 = P(0, 0, 0)[1];
  const rise = (z: number) => P(0, 0, z)[1] - y0;
  const outer = circ(R, 72), inner = circ(R - WALL, 72);
  const g = mk("g", {}, svg);

  // The pan, then the sieves bottom to top: each a drum, its mouth, and its mesh seen through the mouth.
  const drum = (z0: number, z1: number): Vec2[] => hull(outer.map((q) => P(q.u, q.v, z0)).concat(outer.map((q) => P(q.u, q.v, z1))));
  put(solid(g), { sil: poly(drum(0, PAN)), crease: poly(inner.map((q) => P(q.u, q.v, PAN))) });
  const parts = Array.from({ length: N }, () => ({ s: solid(g), mesh: mk("path", { class: "nf lo" }, g) }));

  /** The runs of a line on the floor at zf that show through the mouth at zm. */
  const through = (pts: readonly Vec2[], zf: number, zm: number): Vec2[][] => {
    const runs: Vec2[][] = [[]];
    for (const [u, v] of pts) {
      const s = P(u, v, zf), m = unproj(C, s[0], s[1], zm);
      if (Math.hypot(u, v) < R - WALL && Math.hypot(m[0], m[1]) < R - WALL) runs[runs.length - 1].push(s);
      else if (runs[runs.length - 1].length) runs.push([]);
    }
    return runs.filter((r) => r.length > 1);
  };
  // The mesh: chords both ways, and the floor's edge, begun at the front so its far run is one piece.
  const chord = (a: Vec2, b: Vec2): Vec2[] => Array.from({ length: 29 }, (_, k) => [a[0] + ((b[0] - a[0]) * k) / 28, a[1] + ((b[1] - a[1]) * k) / 28]);
  const lines = CHORDS.flatMap((c) => [chord([c, -R], [c, R]), chord([-R, c], [R, c])]);
  lines.push(Array.from({ length: 73 }, (_, k) => { const t = Math.PI / 4 + (k / 72) * Math.PI * 2, r = R - WALL - 0.05; return [r * Math.cos(t), r * Math.sin(t)]; }));

  // A sieve standing on the ground, drawn once. What shows through the mouth depends only on the mouth's
  // height over the mesh, so a sieve at any height is this, moved up the screen.
  const body = drum(0, H), mouth = inner.map((q) => P(q.u, q.v, H)), mesh = lines.flatMap((l) => through(l, FLOOR, H));
  const up = (pts: readonly Vec2[], dy: number) => pts.map((p): Vec2 => [p[0], p[1] + dy]);

  const gaps = Array.from({ length: N }, () => tween(SEAT));
  const drawn = gaps.map(() => NaN);
  let picked = -2, gap = value;
  function draw(now: number) {
    let z = PAN;
    gaps.forEach((t, i) => {
      z += tval(t, now);
      if (z !== drawn[i]) {
        drawn[i] = z;
        const dy = rise(z);
        put(parts[i].s, { sil: poly(up(body, dy)), crease: poly(up(mouth, dy)) });
        parts[i].mesh.setAttribute("d", mesh.map((r) => open(up(r, dy))).join(""));
      }
      z += H;
    });
  }

  const loop = register(stage, (_dt, now) => { draw(now); return gaps.some((t) => !tdone(t, now)); });
  bag.add(loop.unregister);

  /** Sets every gap for a pick, f being the sieve picked, or -1 for rest. */
  function choose(f: number, now: number) {
    if (f === picked) return;
    picked = f;
    const a = f < 0 ? 1 : f;
    gaps.forEach((t, i) => tset(t, under(f, i, gap), now, Math.abs(i - a) * STEP));
    parts.forEach((p, i) => p.s.sil.classList.toggle("hi", i === a));
    read.textContent = f < 0 ? "rest" : `sieve ${N - f} · 0`;
    loop.wake();
  }
  choose(-1, -1e9);
  draw(0);

  /** The rest stack's middles on screen, bottom to top: what the pointer's height is read against. */
  const bands = () => { let z = PAN; return gaps.map((_, i) => { z += under(-1, i, gap); const y = P(0, 0, z + H / 2)[1]; z += H; return y; }); };
  let mids = bands();
  const pick = (p: Vec2) => mids.reduce((best, y, i) => (Math.abs(p[1] - y) < Math.abs(p[1] - mids[best]) ? i : best), 0);

  bag.add(pointer(stage, { move: (p) => choose(pick(p), performance.now()), leave: () => choose(-1, performance.now()) }));
  bag.add(() => svg.replaceChildren());

  return {
    set: (v) => { gap = v; mids = bands(); const f = picked; picked = -2; choose(f, performance.now()); },
    destroy: bag.dispose,
  };
};
