import {
  Cam, facing, fillet, fit, hull, open, poly, proj, rad, ringAt, rrect, run, seg,
  type Camera, type Projector, type Ring, type Sample, type Vec2,
} from "../core/iso";

/**
 * Riffle's drawing, with no DOM: the camera, the tray and a card in any pose,
 * as path strings. The engine (riffle.ts) writes these into its svg on every
 * frame.
 */

export const N = 8, W = 84, H = 54, G = 13, TW = 22, TH = 7, TABS = [6, 31, 56], TK = 1.4;
export const REST = -12, BACK = -24, FWD = 20, LIFT = 16;
export const X0 = -5, X1 = W + 5, Y0 = -9, Y1 = (N - 1) * G + 9, WH = 20, WR = 6, WT = 2.4;

/** The camera, fitted to the tray with a card lifted, so nothing leaves the frame in any pose. */
export function camera(): Camera {
  const C = Cam(45, 0.5, 1.62);
  fit(C, [[X0, Y0, 0], [X1, Y1, -8], [X1, Y0, 0], [X0, Y1, 0], [X0, Y0, H + TH], [X1, Y0, H + TH + LIFT]], 200, 166);
  return C;
}

/** The tray's outline and the rim's inner edge. */
export const trayRings = (): { outer: Ring; inner: Ring } => ({
  outer: rrect(X0, Y0, X1, Y1, WR, 6),
  inner: rrect(X0 + WT, Y0 + WT, X1 - WT, Y1 - WT, WR - WT, 6),
});

/** A run of points ordered left to right on screen. */
const LR = (pts: Vec2[]) => (pts[0][0] <= pts[pts.length - 1][0] ? pts : pts.slice().reverse());

/**
 * The tray's paths, which never move. `far` is painted before the cards, `near`
 * after them; each entry is [d, class].
 */
export function tray(P: Projector, front: (q: Sample) => boolean, outer: Ring, inner: Ring) {
  // far half: body, the rim's inner edge, and the floor seam along the far walls
  const far: [string, string][] = [
    [poly(hull(ringAt(P, outer, 0).concat(ringAt(P, outer, WH)))), "sil"],
    [poly(ringAt(P, inner, WH)), "nf"],
    [open(ringAt(P, run(inner, (q) => !front(q)), 2.5)), "nf lo"],
  ];
  // near half: one opaque piece from the rim's inner edge down to the floor
  const iF = LR(ringAt(P, run(inner, front), WH)), oT = LR(ringAt(P, run(outer, front), WH)), oB = LR(ringAt(P, run(outer, front), 0));
  // a finger pull, set into the front
  const hx = (X0 + X1) / 2, onFront = (ring: Ring) => ring.map((q) => P(q.u, Y1, q.v));
  const near: [string, string][] = [
    [poly([...iF, oT[oT.length - 1], ...oB.slice().reverse(), oT[0]]), "fo"],
    [open(oT), "nf lo"],
    [open(iF), "nf"],
    [open([oT[0], ...oB, oT[oT.length - 1]]), "nf sil"],
    [poly(onFront(rrect(hx - 11, 6.5, hx + 11, 12.5, 3, 5))), "nf"],
    [poly(onFront(rrect(hx - 9.4, 8, hx + 9.4, 11, 1.5, 5))), "nf lo"],
  ];
  return { far, near };
}

/**
 * Card i, back to front: its number (8 at the back), which of the three tab
 * positions it takes, and its filleted outline, drawn upright in its own plane.
 */
export function card(i: number) {
  const n = N - i, t0 = TABS[(N - 1 - i) % 3];
  const shape = fillet(
    [[0, 0], [W, 0], [W, H], [t0 + TW, H], [t0 + TW, H + TH], [t0, H + TH], [t0, H], [0, H]],
    [1, 1, 3.2, 1.8, 2.4, 2.4, 1.8, 3.2],
  );
  return { n, t0, shape };
}

export type CardPose = { back: string; face: string; head: string; rules: string; punch: Vec2[] };

/**
 * Card i leaning th degrees (negative leans back) and lifted by `lift`: its
 * back edge, face, heading and rules as paths, and where each of the eight
 * punches of its number sits, in a 4 × 2 grid on the tab.
 */
export function pose(P: Projector, i: number, t0: number, shape: readonly Vec2[], th: number, lift: number): CardPose {
  const yb = i * G, s = Math.sin(rad(th)), c = Math.cos(rad(th));
  const w = (u: number, v: number) => P(u, yb + v * s, v * c + lift);
  const wb = (u: number, v: number) => P(u, yb + v * s - TK * c, v * c + TK * s + lift);
  const punch: Vec2[] = [];
  for (let k = 0; k < 8; k++) punch.push(w(t0 + TW / 2 + ((k % 4) - 1.5) * 3.6, H + TH / 2 + (0.5 - Math.floor(k / 4)) * 2.8));
  return {
    back: poly(shape.map((p) => wb(p[0], p[1]))),
    face: poly(shape.map((p) => w(p[0], p[1]))),
    head: seg(w(6, H - 11), w(W - 6, H - 11)),
    rules: [H - 18, H - 25, H - 32, H - 39].map((v) => seg(w(6, v), w(W - 6, v))).join(""),
    punch,
  };
}

/** The fitted camera, its projector and facing test, and the tray's rings: what both the engine and the still start from. */
export function scene() {
  const C = camera();
  return { C, P: proj(C), front: facing(C), ...trayRings() };
}
