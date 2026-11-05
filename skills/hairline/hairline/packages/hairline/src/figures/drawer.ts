import { Cam, facing, fit, hull, open, poly, prism, proj, rings, rrect, run, type Projector, type Ring, type Sample, type Vec2, type Vec3 } from "../core/iso";
import { tdone, tset, tval, tween } from "../core/motion";
import { disposer, mk, pointer, put, register, solid, type FigureMount, type Solid } from "../core/stage";
import { TABLE } from "../intensity";

/**
 * Drawer: a filing cabinet of three deep drawers on a plinth, each front with
 * a bar pull. The pointer's height picks a drawer; it slides out on its
 * runners and shows its inside, two dim dividers running back and nothing
 * between them. The others close. At rest the middle drawer stands a quarter
 * out, its front bright. The slider is how far a drawer comes out.
 *
 * The pattern: one of many, as Sieve's. A tween per drawer on how far it is
 * out. The pick puts the pointer on each front's plane where it stands at
 * rest, which moves only with the slider, never with the drawer on screen.
 * Only a drawer whose tween moved is drawn again.
 */

const N = 3, W = 54, D = 60, Z0 = 5, M = 3, PITCH = 26, G = 1.6, FT = 2.4; // drawers, carcass width and depth, plinth, margin round the fronts, a drawer's pitch, the gap between fronts, a front's thickness
const T = 1.3, IN = 3.2, LOW = 2.2, HIGH = 3.6, DIV = 2.6, S = 2.1;       // a wall's thickness, the box's inset from its front's sides, below its front's foot and its top, how far the dividers sit under the walls, scale
const ZB = Z0 + M, H = ZB + N * PITCH + M, REST = 0.7;                     // the lowest front's foot, the carcass's top, the rest pull as a share of the slider's

/** On a front's face, the samples whose edge meets its top or its right side: they lie inside the silhouette. */
const inner = (q: Sample) => 0.375 * q.nu + 0.307 * q.nv > 0;

/** A plate standing in the x-z plane, from y0 back to y1 front: its silhouette, and the crease of its front face. */
function slab(P: Projector, ring: Ring, inset: Ring, y0: number, y1: number) {
  const at = (r: Ring, y: number) => r.map((q): Vec2 => P(q.u, y, q.v));
  return { sil: poly(hull(at(ring, y0).concat(at(ring, y1)))), crease: open(at(run(inset, inner), y1)) };
}

type Drawer = { z0: number; z1: number; parts: SVGPathElement[]; front: Solid; pull: Solid; drawn: number };

export const mount: FigureMount = ({ stage, svg, read }, value) => {
  const bag = disposer();
  const MAX = TABLE.drawer[2];
  const C = Cam(45, 0.5, S);
  // The carcass, and the top and bottom drawers out as far as the slider goes, each mirrored through the
  // carcass's middle: the cabinet stands in the middle of the frame, and the farthest pull still fits.
  const out = D + MAX + FT, ext: Vec3[] = [[0, 0, 0], [W, 0, 0], [0, 0, H], [W, 0, H], [W, D, 0], [0, out, ZB], [0, out, H - M], [W, out, ZB]];
  fit(C, ext.concat(ext.map(([x, y, z]): Vec3 => [W - x, D - y, H - z])), 200, 166);
  const P = proj(C), front = facing(C);
  const g = mk("g", {}, svg);

  // The plinth, set back under the carcass, then the carcass.
  const [pr, pi] = rings(3, 3, W - 3, D - 3, 2.4, 1);
  put(solid(g), prism(P, front, pr, pi, 0, Z0));
  const [cr, ci] = rings(0, 0, W, D, 3, 1.4);
  put(solid(g), prism(P, front, cr, ci, Z0, H));

  const x0 = M + IN, x1 = W - M - IN, xs = [x0 + (x1 - x0) / 3, x0 + (2 * (x1 - x0)) / 3];
  const onFace = (r: Ring, y: number) => poly(r.map((q): Vec2 => P(q.u, y, q.v)));
  // Each drawer's opening on the carcass's face: hidden by its front, seen above its box when it is out.
  mk("path", { class: "nf lo", d: Array.from({ length: N }, (_, k) => {
    const z = ZB + k * PITCH + G / 2;
    return onFace(rrect(x0 - 0.8, z + LOW - 0.8, x1 + 0.8, z + PITCH - G - HIGH + 1.4, 0.8, 2), D);
  }).join("") }, g);

  // Bottom to top: the camera looks down, so a lower drawer never covers a higher one.
  // In a drawer, back to front: its floor, left wall, dividers, right wall, the box's outline, its front, its pull.
  const drawers: Drawer[] = Array.from({ length: N }, (_, k) => {
    const z0 = ZB + k * PITCH + G / 2, z1 = z0 + PITCH - G, dg = mk("g", {}, g);
    const parts = [0, 1, 2, 3].map(() => mk("path", { class: "lo" }, dg));
    parts.push(mk("path", { class: "nf sil" }, dg));
    return { z0, z1, parts, front: solid(dg), pull: solid(dg), drawn: NaN };
  });
  const face = (d: Drawer) => rrect(M, d.z0, W - M, d.z1, 1.6, 4), faceIn = (d: Drawer) => rrect(M + 1, d.z0 + 1, W - M - 1, d.z1 - 1, 1, 4);

  /** A box from y0 to y1 with a rounded footprint, standing from z0 to z1: its silhouette. */
  const box = (a: number, b: number, y0: number, y1: number, z0: number, z1: number, r: number) =>
    y1 - y0 < 0.05 ? "" : prism(P, front, rrect(a, y0, b, y1, r, 3), null, z0, z1).sil;

  function draw(d: Drawer, o: number) {
    if (o === d.drawn) return;
    d.drawn = o;
    const zb = d.z0 + LOW, zt = d.z1 - HIGH, yb = D + o, yf = yb + FT;
    const [floor, left, divs, right, outline] = d.parts;
    floor.setAttribute("d", box(x0, x1, D, yb, zb, zb + T, 0.6));
    left.setAttribute("d", box(x0, x0 + T, D, yb, zb + T, zt, 0.5));
    divs.setAttribute("d", xs.map((x) => box(x - 0.5, x + 0.5, D, yb, zb + T, zt - DIV, 0.4)).join(""));
    right.setAttribute("d", box(x1 - T, x1, D, yb, zb + T, zt, 0.5));
    outline.setAttribute("d", box(x0, x1, D, yb, zb, zt, 0.8));
    put(d.front, slab(P, face(d), faceIn(d), yb, yf));
    const zp = (d.z0 + d.z1) / 2, xm = W / 2;
    const [br, bi] = rings(xm - 9, yf, xm + 9, yf + 2.6, 1.3, 0.6);
    put(d.pull, prism(P, front, br, bi, zp - 1.3, zp + 1.3));
  }

  const tw = drawers.map(() => tween(0));
  const B = register(stage, (_dt, now) => {
    let m = false;
    drawers.forEach((d, k) => { draw(d, tval(tw[k], now)); if (!tdone(tw[k], now)) m = true; });
    return m;
  });
  bag.add(B.unregister);

  let pull = value, picked = -2;
  /** Opens drawer f, counted from the bottom, and closes the rest; -1 puts the cabinet back to rest. */
  function choose(f: number, now: number) {
    if (f === picked) return;
    picked = f;
    const a = f < 0 ? 1 : f;
    tw.forEach((t, k) => tset(t, k === a ? (f < 0 ? pull * REST : pull) : 0, now, 0));
    drawers.forEach((d, k) => d.front.sil.classList.toggle("hi", k === a));
    read.textContent = f < 0 ? "rest" : `drawer ${N - f} · 0`;
    B.wake();
  }
  tw[1] = tween(pull * REST);
  choose(-1, -1e9);
  drawers.forEach((d, k) => draw(d, tval(tw[k], 0)));

  /** The world x and z under screen point p on the upright plane y = yf: the projection, inverted. */
  const c = Math.cos(C.az), s = Math.sin(C.az), zf = Math.sqrt(1 - C.k * C.k);
  const onFront = (p: Vec2, yf: number): Vec2 => { const x = (p[0] - C.ox) / (C.S * c) + (yf * s) / c; return [x, ((x * s + yf * c) * C.k - (p[1] - C.oy) / C.S) / zf]; };
  /** The drawer under p: first on each front where it stands at rest, top down as a higher drawer covers a lower one;
   * off every front, the nearest middle in z on the closed front. */
  function pick(p: Vec2) {
    for (let k = N - 1; k >= 0; k--) {
      const [x, z] = onFront(p, D + FT + (k === 1 ? pull * REST : 0)), d = drawers[k];
      if (x >= M && x <= W - M && z >= d.z0 && z <= d.z1) return k;
    }
    const z = onFront(p, D + FT)[1];
    return drawers.reduce((best, d, k) => (Math.abs(z - (d.z0 + d.z1) / 2) < Math.abs(z - (drawers[best].z0 + drawers[best].z1) / 2) ? k : best), 0);
  }

  bag.add(pointer(stage, { move: (p) => choose(pick(p), performance.now()), leave: () => choose(-1, performance.now()) }));
  bag.add(() => svg.replaceChildren());

  return {
    set: (v) => { pull = v; const f = picked; picked = -2; choose(f, performance.now()); },
    destroy: bag.dispose,
  };
};
