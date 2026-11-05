import { Cam, clamp, facing, fit, hull, poly, prism, proj, rad, rings, rrect, seg, type Ring, type Vec2, type Vec3 } from "../core/iso";
import { tdone, tset, tval, tween, type Tween } from "../core/motion";
import { disposer, mk, pointer, put, register, solid, type FigureMount } from "../core/stage";

/**
 * Lockers: a bank of twelve, six across and two high, standing on a plinth.
 * Each door is a thin steel plate with louvred vents, a blank number plate and
 * a latch cup on its free edge, hung on a hinge down its left side. The pointer
 * is put on the closed door faces; the locker under it swings its door open on
 * the 700ms curve, and the one open before it swings shut on the same clock.
 * An opening shows the locker's inside: its floor and shelf running back along
 * the inner wall. At rest, one door stands ajar, bright. The slider is how far
 * a door opens, in degrees.
 *
 * The pattern: one of many. A tween per door, a hit test on the plane of the
 * closed doors, and each door drawn every frame as a plate turned on its hinge.
 */

const COLS = 6, ROWS = 2, W = 24, HR = 38, GAP = 1.2, FM = 3, ZP = 6, D = 26, T = 1.4, DEP = 23;
const BW = COLS * W + 2 * FM, BH = ROWS * HR + 2 * FM, DW = W - 2 * GAP, DH = HR - 2 * GAP;
const REST_I = 5, REST_A = 22, FAR = 120;

/** The door's local outline and marks, in (u, v): u from the hinge, v up from its foot. */
const OUTLINE = rrect(0, 0, DW, DH, 1.8, 4);
const VENTS = [0, 1, 2].map((k) => rrect(4, DH - 6.6 - k * 3.2, DW - 4, DH - 5.2 - k * 3.2, 0.7, 2));
const PLATE = rrect(DW / 2 - 4.5, DH - 19, DW / 2 + 4.5, DH - 15, 1, 3);
const CUP = rrect(DW - 5.6, DH / 2 - 7, DW - 2.8, DH / 2 + 2, 1.2, 3);
const FRAME = rrect(2.6, 2.6, DW - 2.6, DH - 2.6, 1.4, 3);

/** Twice the signed area of a screen polygon: its sign says which way round it is seen. */
const area = (pts: readonly Vec2[]) => pts.reduce((s, p, i) => { const q = pts[(i + 1) % pts.length]; return s + p[0] * q[1] - q[0] * p[1]; }, 0);

type Locker = {
  c: number; r: number; n: number; x0: number; z0: number; drawn: number; sign0: number; tw: Tween;
  plate: SVGPathElement; face: SVGPathElement; marks: SVGPathElement; cup: SVGPathElement;
};

export const mount: FigureMount = ({ stage, svg, read }, value) => {
  const bag = disposer();
  const C = Cam(45, 0.5, 1.6);
  // fitted with the corner doors swung to the slider's far end, so no pose leaves the frame
  const sw = [Math.cos(rad(FAR)) * DW, Math.sin(rad(FAR)) * DW];
  fit(C, [[-4, -4, 0], [BW + 4, D + 4, 0], [BW + 4, -4, 0], [-4, D + 4, 0], [0, 0, ZP + BH], [BW, 0, ZP + BH],
    [FM + sw[0], D + sw[1], ZP + FM], [FM + sw[0], D + sw[1], ZP + BH - FM]], 200, 166);
  const P = proj(C), front = facing(C);
  let MAX = value, act = -1;

  /** The world point (x, z) on the vertical plane y = y0 that lies under a screen point. */
  function onFace(p: Vec2, y0: number): Vec2 {
    const o = P(0, y0, 0), a = P(1, y0, 0), b = P(0, y0, 1);
    const ex = [a[0] - o[0], a[1] - o[1]], ez = [b[0] - o[0], b[1] - o[1]], det = ex[0] * ez[1] - ex[1] * ez[0];
    const qx = p[0] - o[0], qy = p[1] - o[1];
    return [(qx * ez[1] - qy * ez[0]) / det, (ex[0] * qy - ex[1] * qx) / det];
  }
  /** A world segment, cut to what shows through a locker's opening: clipped on the face plane, as a screen path. */
  function through(A: Vec3, B: Vec3, L: Locker) {
    const pa = P(...A), pb = P(...B), a = onFace(pa, D), b = onFace(pb, D), m = 0.9;
    let t0 = 0, t1 = 1;
    const lim = [[a[0] - b[0], a[0] - (L.x0 + m)], [b[0] - a[0], L.x0 + DW - m - a[0]], [a[1] - b[1], a[1] - (L.z0 + m)], [b[1] - a[1], L.z0 + DH - m - a[1]]];
    for (const [p, q] of lim) {
      if (p === 0) { if (q < 0) return ""; continue; }
      const r = q / p;
      if (p < 0) t0 = Math.max(t0, r); else t1 = Math.min(t1, r);
    }
    if (t1 - t0 < 0.01) return "";
    const at = (t: number): Vec2 => [pa[0] + (pb[0] - pa[0]) * t, pa[1] + (pb[1] - pa[1]) * t];
    return seg(at(t0), at(t1));
  }

  const g = mk("g", {}, svg);
  const [pr, pi] = rings(-4, -4, BW + 4, D + 4, 5, 1.6);
  put(solid(g), prism(P, front, pr, pi, 0, ZP));
  const [br, bi] = rings(0, 0, BW, D, 3, 1.4);
  put(solid(g), prism(P, front, br, bi, ZP, ZP + BH));

  // Column by column from the left, bottom row before top: a door swings left and
  // out, over the column before it and the row below it, so this is back to front.
  const lockers: Locker[] = [];
  for (let c = 0; c < COLS; c++) for (let r = 0; r < ROWS; r++) {
    const x0 = FM + c * W + GAP, z0 = ZP + FM + r * HR + GAP;
    const lg = mk("g", {}, g);
    mk("path", { d: poly(OUTLINE.map((q) => P(x0 + q.u, D, z0 + q.v))), class: "" }, lg);
    const L = { c, r, n: (ROWS - 1 - r) * COLS + c + 1, x0, z0, drawn: NaN, sign0: 0, tw: tween(0) } as Locker;
    const zs = L.z0 + DH - 9.5, x1 = L.x0 + DW;
    const inside = [
      through([L.x0, D, L.z0], [L.x0, D - DEP, L.z0], L),
      through([L.x0, D - 1.6, zs], [x1, D - 1.6, zs], L),
      through([L.x0, D - 1.6, zs], [L.x0, D - DEP, zs], L),
    ].join("");
    mk("path", { d: inside, class: "nf lo" }, lg);
    L.plate = mk("path", { class: "lo" }, lg);
    L.face = mk("path", { class: "sil" }, lg);
    L.marks = mk("path", { class: "nf lo" }, lg);
    L.cup = mk("path", { class: "nf" }, lg);
    lockers.push(L);
  }
  const byN = (n: number) => lockers.find((L) => L.n === n)!;

  /** Door L turned th degrees on its hinge: a point on it at (u, v), s off its middle plane toward the front. */
  function drawDoor(L: Locker, th: number) {
    if (th === L.drawn) return;
    L.drawn = th;
    const cs = Math.cos(rad(th)), sn = Math.sin(rad(th));
    const at = (s: number) => (q: { u: number; v: number }) => P(L.x0 + q.u * cs - s * sn, D + T / 2 + q.u * sn + s * cs, L.z0 + q.v);
    const fr = OUTLINE.map(at(T / 2)), bk = OUTLINE.map(at(-T / 2));
    const outward = area(fr) * L.sign0 > 0, s = outward ? T / 2 : -T / 2;
    L.plate.setAttribute("d", poly(hull(fr.concat(bk))));
    L.face.setAttribute("d", poly(outward ? fr : bk));
    const marks: Ring[] = outward ? [...VENTS, PLATE] : [...VENTS, FRAME];
    L.marks.setAttribute("d", marks.map((m) => poly(m.map(at(s)))).join(""));
    L.cup.setAttribute("d", outward ? poly(CUP.map(at(s))) : "");
  }
  for (const L of lockers) L.sign0 = Math.sign(area(OUTLINE.map((q) => P(L.x0 + q.u, D + T, L.z0 + q.v))));

  const B = register(stage, (_dt, now) => {
    let m = false;
    for (const L of lockers) { drawDoor(L, tval(L.tw, now)); if (!tdone(L.tw, now)) m = true; }
    return m;
  });
  bag.add(B.unregister);

  /** The locker under a screen point, read on the plane of the closed door faces, which never moves. */
  function hit(p: Vec2) {
    const [x, z] = onFace(p, D + T);
    if (x < 0 || x > BW || z < ZP || z > ZP + BH) return -1;
    const c = clamp(Math.floor((x - FM) / W), 0, COLS - 1), r = clamp(Math.floor((z - ZP - FM) / HR), 0, ROWS - 1);
    return (ROWS - 1 - r) * COLS + c + 1;
  }

  /** Opens locker n and shuts the one open before it; 0 puts the bank back to rest. */
  function choose(n: number, force?: boolean) {
    if (n === act && !force) return;
    act = n;
    const now = performance.now(), lit = n > 0 ? n : REST_I;
    for (const L of lockers) {
      tset(L.tw, L.n === n ? MAX : n <= 0 && L.n === REST_I ? REST_A : 0, now, 0);
      L.face.classList.toggle("hi", L.n === lit);
      L.cup.classList.toggle("hi", L.n === lit);
    }
    read.textContent = n > 0 ? "locker " + String(n).padStart(2, "0") : "rest";
    B.wake();
  }
  byN(REST_I).tw = tween(REST_A);
  choose(0, true);

  bag.add(pointer(stage, { move: (p) => choose(Math.max(0, hit(p))), leave: () => choose(0) }));
  bag.add(() => svg.replaceChildren());

  return {
    set: (v) => { MAX = v; if (act > 0) choose(act, true); },
    destroy: bag.dispose,
  };
};
