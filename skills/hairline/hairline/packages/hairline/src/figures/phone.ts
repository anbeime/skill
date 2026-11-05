import {
  Cam, circ, clamp, extremes, facing, fillet, fit, hull, lerp, poly, prism, proj, ringAt, rings, rrect, seg,
  type Ring, type Vec2,
} from "../core/iso";
import { spring, stepS } from "../core/motion";
import { disposer, mk, pointer, put, register, solid, type FigureMount } from "../core/stage";

/**
 * Phone: a phone lying face down, taken apart in four layers, from the bottom:
 * the glass with its notch, an L-shaped board with its chips, the battery with
 * the connector tab that runs to the board, and the back shell with its camera
 * bump and side buttons. The pointer's x scrubs the gaps (a spring per gap);
 * its y picks a layer, which takes the bright edge and goes to the read-out.
 * The gaps open in turn outwards from the layer picked: the two beside it
 * chase the target, and each further gap chases its inner neighbour. At rest
 * the board is caught lifting off the glass, bright. The slider is the
 * largest gap, in world units.
 *
 * The pattern: scrub and pick, as Exploded. Picking is tested against the
 * target gaps, never the gaps on screen, and the stack is centred on its own
 * middle so it opens both ways and stays in the frame.
 */

const W = 68, L = 140, R = 11, GMAX = 40;
/** Thicknesses: glass, board, the tallest chip, battery, shell, the camera bump and a lens. */
const TG = 2, TB = 1.6, TC = 1.8, TBAT = 7, TS = 6, TBUMP = 2.2, TL = 0.9;
const STACK = TG + TB + TC + TBAT + TS + TBUMP + TL;
const NAMES = ["glass", "board", "battery", "shell"];
/** The gaps at rest, as shares of the largest: the board caught lifting off the glass. */
const REST = [0.36, 0.3, 1.2], MIN = 0.08, PIVOT = 1;
const BOARD: Vec2[] = [[4, L - 44], [W - 4, L - 44], [W - 4, L - 5], [36, L - 5], [36, L - 30], [4, L - 30]];
const BAT: [number, number, number, number] = [9, 12, W - 9, L - 48];
/** Chips on the board, [x0, y0, x1, y1, height], back to front: a modem, a socket, a regulator, the processor. */
const CHIPS: Array<[number, number, number, number, number]> = [
  [10, L - 41, 26, L - 34, 1.4], [45, L - 40, 54, L - 35, 1.2], [57, L - 42, 62, L - 36, 1.2], [42, L - 27, 56, L - 13, 1.8],
];
const RECT: Vec2[] = [[0, 0], [W, 0], [W, L], [0, L]];
const FOOT: Vec2[][] = [RECT, BOARD, [[BAT[0], BAT[1]], [BAT[2], BAT[1]], [BAT[2], BAT[3]], [BAT[0], BAT[3]]], RECT];
const THICK = [TG, TB, TBAT, TS];

/** Each layer's base height, from the three gaps, centred so the stack opens both ways about its middle. */
function bases(g: readonly number[]): number[] {
  const b = [0], t = [TG, TB + TC, TBAT];
  for (let j = 0; j < 3; j++) b.push(b[j] + t[j] + g[j]);
  const mid = (b[3] + TS + TBUMP + TL) / 2;
  return b.map((z) => z - mid);
}

/** Even-odd point-in-polygon, on screen. */
function inside(pt: Vec2, pg: readonly Vec2[]) {
  let c = false;
  for (let i = 0, j = pg.length - 1; i < pg.length; j = i++) {
    const [xi, yi] = pg[i], [xj, yj] = pg[j];
    if ((yi > pt[1]) !== (yj > pt[1]) && pt[0] < ((xj - xi) * (pt[1] - yi)) / (yj - yi) + xi) c = !c;
  }
  return c;
}

/** A ring moved by (cx, cy) on the ground. */
const at = (ring: Ring, cx: number, cy: number): Ring => ring.map((q) => ({ ...q, u: q.u + cx, v: q.v + cy }));

export const mount: FigureMount = ({ stage, svg, read }, value) => {
  const bag = disposer();
  let GAP = value, share: number | null = null, act = -1, origin = PIVOT, lastP: Vec2 | null = null;

  const C = Cam(45, 0.5, 1.5), H = (STACK + 3 * GMAX) / 2;
  fit(C, [[0, 0, -H], [W + 2.2, L, -H], [W + 2.2, 0, -H], [0, L, -H], [0, 0, H], [W + 2.2, 0, H], [0, L, H]], 200, 166);
  const P = proj(C), front = facing(C);
  const flat = (pts: readonly Vec2[], z: number) => poly(pts.map(([x, y]) => P(x, y, z)));
  const g = mk("g", {}, svg);

  // the guides, from the shell's outermost points down to the glass: painted first, so every plate hides them
  const outer = rrect(0, 0, W, L, R, 8);
  const ext = extremes(P, outer).slice(0, 2), guide = mk("path", { class: "nf dash" }, g);

  // glass: a rounded slab, its display edge cut by the notch, a camera and a speaker slit in the notch
  const gg = mk("g", {}, g), glass = solid(gg), gIn = rrect(1.2, 1.2, W - 1.2, L - 1.2, R - 1.2, 8);
  const DISP = fillet([[4, 4], [W - 4, 4], [W - 4, L - 4], [W / 2 + 12, L - 4], [W / 2 + 12, L - 10], [W / 2 - 12, L - 10], [W / 2 - 12, L - 4], [4, L - 4]], [7.5, 7.5, 7.5, 2, 3.5, 3.5, 2, 7.5]);
  const disp = mk("path", { class: "nf" }, gg), lensF = mk("path", { class: "nf" }, gg), slit = mk("path", { class: "nf lo" }, gg);
  const camF = at(circ(1.5, 16), W / 2 + 6, L - 7);

  // board: an L-shaped plate, its edge as a second outline, and its chips
  const bg = mk("g", {}, g), BF = fillet(BOARD, [4, 4, 4, 4, 3, 4]);
  const bBack = mk("path", { class: "lo" }, bg), bFace = mk("path", { class: "sil" }, bg);
  const chips = CHIPS.map(([x0, y0, x1, y1, h]) => { const [ring, inner] = rings(x0, y0, x1, y1, 1.5, 0.7); return { ring, inner, h, el: solid(bg) }; });

  // battery: a rounded block, and the flex tab that leaves its near end with the connector on it
  const tg = mk("g", {}, g), battery = solid(tg), [batR, batI] = rings(...BAT, 6, 1.6);
  const TAB = fillet([[41, L - 48], [52, L - 48], [52, L - 31], [41, L - 31]], [0.5, 0.5, 2, 2]);
  const tBack = mk("path", { class: "lo" }, tg), tFace = mk("path", {}, tg), conn = solid(tg);
  const [conR, conI] = rings(42, L - 38, 51, L - 32, 1.5, 0.7);

  // shell: the back, two volume buttons standing off its near side, the camera bump and its lenses
  const sg = mk("g", {}, g), shell = solid(sg), sIn = rrect(1.8, 1.8, W - 1.8, L - 1.8, R - 1.8, 8);
  const buttons = [[L - 68, L - 58], [L - 54, L - 44]].map(([y0, y1]) => { const [ring, inner] = rings(W - 0.5, y0, W + 2.2, y1, 1.2, 0.5); return { ring, inner, el: solid(sg) }; });
  const bump = solid(sg), bumpR = rrect(7, L - 33, 33, L - 7, 7, 6), bumpI = rrect(8, L - 32, 32, L - 8, 6, 6);
  const lenses = [[14.5, L - 25.5], [25.5, L - 14.5]].map(([x, y]) => {
    const el = solid(sg);
    return { ring: at(circ(4.6, 24), x, y), inner: at(circ(3.6, 24), x, y), eye: at(circ(1.9, 16), x, y), el, glass: mk("path", { class: "nf lo" }, el.g) };
  });
  const flash = mk("path", { class: "nf" }, sg), FL = at(circ(1.7, 16), 25.5, L - 25.5);

  const draw: Array<(z: number) => void> = [
    (z) => {
      put(glass, prism(P, front, outer, gIn, z, z + TG));
      const t = z + TG;
      disp.setAttribute("d", flat(DISP, t));
      lensF.setAttribute("d", poly(ringAt(P, camF, t)));
      slit.setAttribute("d", seg(P(W / 2 - 6, L - 7, t), P(W / 2 + 1.5, L - 7, t)));
    },
    (z) => {
      bBack.setAttribute("d", flat(BF, z));
      bFace.setAttribute("d", flat(BF, z + TB));
      for (const c of chips) put(c.el, prism(P, front, c.ring, c.inner, z + TB, z + TB + c.h));
    },
    (z) => {
      put(battery, prism(P, front, batR, batI, z, z + TBAT));
      tBack.setAttribute("d", flat(TAB, z + 0.8));
      tFace.setAttribute("d", flat(TAB, z + 1.4));
      put(conn, prism(P, front, conR, conI, z + 1.4, z + 2.6));
    },
    (z) => {
      put(shell, prism(P, front, outer, sIn, z, z + TS));
      for (const b of buttons) put(b.el, prism(P, front, b.ring, b.inner, z + 1.6, z + 4.4));
      const t = z + TS, u = t + TBUMP;
      put(bump, prism(P, front, bumpR, bumpI, t, u));
      for (const l of lenses) { put(l.el, prism(P, front, l.ring, l.inner, u, u + TL)); l.glass.setAttribute("d", poly(ringAt(P, l.eye, u + TL))); }
      flash.setAttribute("d", poly(ringAt(P, FL, u)));
    },
  ];
  const sils = [glass.sil, bFace, battery.sil, shell.sil];

  /** The gaps the pointer asks for: one share of the largest across, or the rest pose. */
  const targets = () => [0, 1, 2].map((j) => GAP * (share === null ? REST[j] : share));
  const gs = targets().map((t) => spring(t, { eps: 0.01 }));
  const drawn = [NaN, NaN, NaN, NaN];

  const B = register(stage, (dt) => {
    // the gaps beside the origin chase the target; each further gap chases its inner neighbour's lag
    const T = targets(), order = [0, 1, 2].sort((a, b) => Math.abs(a + 0.5 - origin) - Math.abs(b + 0.5 - origin));
    let m = false;
    for (const j of order) {
      const d = j + 0.5 - origin, k = d > 0 ? j - 1 : j + 1;
      gs[j].t = Math.abs(d) < 1 ? T[j] : T[j] + gs[k].x - T[k];
      if (stepS(gs[j], dt)) m = true;
    }
    const b = bases(gs.map((s) => s.x));
    let changed = false;
    b.forEach((z, i) => { if (z !== drawn[i]) { drawn[i] = z; draw[i](z); changed = true; } });
    if (changed) guide.setAttribute("d", ext.map((q) => seg(P(q.u, q.v, b[3]), P(q.u, q.v, b[0] + TG))).join(""));
    return m;
  });
  bag.add(B.unregister);

  /** The layer under a screen point, tested where the layers are going (the target gaps), topmost first; else the nearest in height. */
  function pick(p: Vec2) {
    const b = bases(targets());
    for (let i = 3; i >= 0; i--) {
      const f = FOOT[i], top = f.map(([x, y]) => P(x, y, b[i] + THICK[i]));
      const shape = i === 1 ? top : hull(top.concat(f.map(([x, y]) => P(x, y, b[i]))));
      if (inside(p, shape)) return i;
    }
    let best = 0, bd = Infinity;
    b.forEach((z, i) => { const dy = Math.abs(P(W / 2, L / 2, z + THICK[i])[1] - p[1]); if (dy < bd) { bd = dy; best = i; } });
    return best;
  }
  function setAct(a: number) {
    if (a >= 0) origin = a;
    act = a;
    const lit = a >= 0 ? a : PIVOT;
    sils.forEach((s, i) => s.classList.toggle("hi", i === lit));
    read.textContent = a >= 0 ? NAMES[a] : "rest";
    B.wake();
  }
  setAct(-1);

  bag.add(pointer(stage, {
    move: (p) => { lastP = p; share = lerp(MIN, 1, clamp((p[0] - 60) / 280, 0, 1)); setAct(pick(p)); },
    leave: () => { lastP = null; share = null; setAct(-1); },
  }));
  bag.add(() => svg.replaceChildren());

  return {
    set: (v) => { GAP = v; if (lastP) setAct(pick(lastP)); B.wake(); },
    destroy: bag.dispose,
  };
};
