import { Cam, clamp, facing, fit, hull, open, poly, proj, ringAt, rrect, seg, type Ring, type Vec2, type Vec3 } from "../core/iso";
import { reducedMotion, spring, stepS, tdone, tset, tval, tween, type Spring, type Tween } from "../core/motion";
import { disposer, mk, pointer, put, register, solid, type FigureMount, type Solid } from "../core/stage";
import { inset, slab } from "../slab";

/**
 * Hub: a thick plate in the middle of a faint floor grid, eight thin tiles
 * around it, a little off their cells, each joined to the hub by a dashed
 * link. The tile nearest the pointer rises on a spring and its link turns
 * solid, drawn out from the hub; the tiles beside it rise less, by how far
 * round the ring they sit. The risen tile is the bright mark; at rest it is
 * the hub's inset square. The slider is the rise, in world units.
 *
 * The pattern: one of many, on springs. A hit test on the tiles' resting
 * positions, a falloff by angle, a stagger by hops round the ring.
 */

const D = 52, HS = 10, T = 3, HUB = 18, HT = 8, FALL = [1, 0.5, 0.2, 0.06, 0], STEP = 70, HIT = 40;
// The rise arrives on a lightly underdamped spring; the return is slower and near-critical.
const UP = { k: 70, c: 14 }, DOWN = { k: 40, c: 12.4 }, DRAW = { k: 120, c: 21, eps: 0.002 }, RETRACT = { k: 36, c: 11.6, eps: 0.002 };
// Each tile's cell, and how far it sits off it.
const JIT = [[2, -2], [-2, 1.5], [1.5, 2.5], [-2.5, -1], [2, 1.5], [-1.5, 2], [2.5, -1.5], [-2, -2.5]];
const CELLS = [[-1, -1], [0, -1], [1, -1], [1, 0], [1, 1], [0, 1], [-1, 1], [-1, 0]];

type Tile = {
  k: number; x: number; y: number; n: number; a: number; b: number;
  sp: Spring; lk: Spring; hw: Tween; drawn: number; due: number; tgt: number; pend: boolean; on: boolean;
  ring: Ring; inner: Ring; el: Solid; slot: SVGPathElement; line: SVGPathElement;
};

export const mount: FigureMount = ({ stage, svg, read }, value) => {
  const bag = disposer();
  let lift = value;

  const C = Cam(45, 0.5, 1.76);
  const E = 3 * D / 2 - 4;
  const pts: Vec3[] = [[-E, -E, 0], [E, -E, 0], [E, E, 0], [-E, E, 0]];
  CELLS.forEach(([i, j], k) => pts.push([i * D + JIT[k][0] - HS, j * D + JIT[k][1] - HS, 24 * 1.15 + T], [i * D + JIT[k][0] + HS, j * D + JIT[k][1] + HS, 24 * 1.15 + T]));
  fit(C, pts, 200, 166);
  const P = proj(C), front = facing(C);

  const g = mk("g", {}, svg);
  // the floor: a faint grid on the tile pitch
  let d = "";
  for (let v = -E; v <= E + 1; v += D / 2) d += seg(P(v, -E, 0), P(v, E, 0)) + seg(P(-E, v, 0), P(E, v, 0));
  mk("path", { d, class: "nf lo" }, g);

  const tiles = CELLS.map(([i, j], k) => {
    const x = i * D + JIT[k][0], y = j * D + JIT[k][1];
    return { k, x, y, sp: spring(0, { ...UP }), lk: spring(0, { ...DRAW, eps: 0.002 }), hw: tween(0, 220), drawn: NaN, due: 0, tgt: 0, pend: false, on: false } as Tile;
  });
  // ring order, by angle: the neighbours of a tile are the ones beside it on the ring
  const ring = tiles.slice().sort((a, b) => Math.atan2(a.y, a.x) - Math.atan2(b.y, b.x));
  ring.forEach((t, n) => { t.n = n; });

  // links go down first: dashed to every tile, and a solid one over it that is drawn out from the hub
  // each link is a floor segment from the hub's rim to the tile's footprint edge
  tiles.forEach((t) => {
    const m = Math.max(Math.abs(t.x), Math.abs(t.y));
    t.a = HUB / m; t.b = 1 - HS / m;
    // the visible rim: where the floor segment comes out from behind the hub's silhouette
    const H = hull([[-HUB, -HUB], [HUB, -HUB], [HUB, HUB], [-HUB, HUB]].flatMap(([x, y]) => [P(x, y, 0), P(x, y, HT)]));
    const inside = (q: Vec2) => { let s0 = 0; for (let i = 0; i < H.length; i++) { const a = H[i], b = H[(i + 1) % H.length], c = (b[0] - a[0]) * (q[1] - a[1]) - (b[1] - a[1]) * (q[0] - a[0]); if (c * s0 < 0) return false; if (c) s0 = c; } return true; };
    let u = t.a; while (u < t.b - 0.05 && inside(P(t.x * u, t.y * u, 0))) u += 0.005;
    t.a = Math.min(u + 0.01, t.b - 0.1);
    // short real dashes in the plain stroke, so the link reads at 240px
    const len = Math.hypot(t.x, t.y) * (t.b - t.a), n = Math.max(2, Math.round(len / 6));
    let dd = "";
    for (let i = 0; i < n; i++) {
      const u0 = t.a + ((t.b - t.a) * (i + 0.15)) / n, u1 = t.a + ((t.b - t.a) * (i + 0.65)) / n;
      dd += seg(P(t.x * u0, t.y * u0, 0), P(t.x * u1, t.y * u1, 0));
    }
    mk("path", { d: dd, class: "nf" }, g);
  });
  tiles.forEach((t) => { t.slot = mk("path", { class: "nf lo" }, g); t.line = mk("path", { class: "nf hi" }, g); });

  // plates, back to front by x + y; the hub sits among them
  let mark!: SVGPathElement;
  const order: (Tile | null)[] = [...tiles, null].sort((a, b) => (a ? a.x + a.y : 0) - (b ? b.x + b.y : 0));
  for (const t of order) {
    if (!t) {
      // the lip and the frame keep an even gap to the plate's edge as drawn; the mark stands free
      const r = rrect(-HUB, -HUB, HUB, HUB, 7, 8), ri = inset(C, r, 1.3), fr = inset(C, r, 2.8), mr = rrect(-7, -7, 7, 7, 2, 8);
      put(solid(g), slab(P, front, r, ri, 0, HT));
      mk("path", { d: open(ringAt(P, fr.concat(fr.slice(0, 1)), HT)), class: "nf lo" }, g);
      const md = open(ringAt(P, mr.concat(mr.slice(0, 1)), HT));
      mark = mk("path", { d: md, class: "nf hi" }, g);
      continue;
    }
    t.ring = rrect(t.x - HS, t.y - HS, t.x + HS, t.y + HS, 4, 8);
    t.inner = inset(C, t.ring, 1.1);
    t.el = solid(g);
  }

  const hubW = tween(1, 240);
  let hubOn = true;
  function draw(t: Tile, now: number) {
    const z = Math.max(0, t.sp.x), l = clamp(t.lk.x, 0, 1), w = tval(t.hw, now);
    if (z !== t.drawn) {
      t.drawn = z; put(t.el, slab(P, front, t.ring, t.inner, z, z + T));
      t.slot.setAttribute("d", z > 0.4 ? poly(ringAt(P, t.ring, 0)) : "");
    }
    // the bright mark is the stroke's own colour transition, switched when its weight crosses half
    if ((w > 0.5) !== t.on) { t.on = w > 0.5; t.el.sil.classList.toggle("hi", t.on); }
    const e = t.a + (t.b - t.a) * l;
    t.line.setAttribute("d", l > 0.002 ? seg(P(t.x * t.a, t.y * t.a, 0), P(t.x * e, t.y * e, 0)) : "");
  }

  const B = register(stage, (dt, now) => {
    let moving = false;
    for (const t of tiles) {
      if (t.pend) { if (now >= t.due) { t.pend = false; Object.assign(t.sp, t.tgt > t.sp.t ? UP : DOWN); t.sp.t = t.tgt; } else moving = true; }
      if (stepS(t.sp, dt)) moving = true;
      if (stepS(t.lk, dt)) moving = true;
      if (!tdone(t.hw, now)) moving = true;
      draw(t, now);
    }
    const hw = tval(hubW, now) > 0.5;
    if (hw !== hubOn) { hubOn = hw; mark.setAttribute("class", hw ? "nf hi" : "nf lo"); }
    if (!tdone(hubW, now)) moving = true;
    return moving;
  });
  bag.add(B.unregister);

  // hit: the tile whose RESTING top is nearest the pointer on screen; the hub's own ground is rest
  const top = tiles.map((t) => P(t.x, t.y, T)), hubAt = P(0, 0, HT);
  let act = -1;
  function hit([sx, sy]: Vec2) {
    if (Math.hypot(sx - hubAt[0], sy - hubAt[1]) < 30) return -1;
    let a = -1, best = HIT;
    top.forEach((q, k) => { const m = Math.hypot(sx - q[0], sy - q[1]); if (m < best) { best = m; a = k; } });
    // a little hysteresis: the tile already under the pointer is kept until another is clearly nearer
    if (a !== act && act >= 0) {
      const held = Math.hypot(sx - top[act][0], sy - top[act][1]);
      if (held < HIT && best > 0.8 * held) return act;
    }
    return a;
  }

  /** Hops round the ring from tile `from`. */
  const hops = (t: Tile, from: number) => Math.min((t.n - from + 8) % 8, (from - t.n + 8) % 8);
  function setActive(a: number) {
    if (a === act) return;
    const now = performance.now(), from = a >= 0 ? tiles[a].n : tiles[act].n;
    act = a;
    tiles.forEach((t) => {
      const hop = hops(t, from), tgt = a < 0 ? 0 : lift * FALL[hop], rising = tgt > t.tgt;
      // up: the touched tile first, the others a beat behind by hops; down: the outer ones first, the one just left last
      const delay = reducedMotion() ? 0 : rising ? hop * STEP : a < 0 ? (4 - hop) * 25 : hop === 0 ? 60 : 0;
      t.tgt = tgt; t.due = now + delay; t.pend = true;
      const on = t.k === a;
      Object.assign(t.lk, on ? DRAW : RETRACT); t.lk.t = on ? 1 : 0;
      t.hw.dur = on ? 220 : 260; tset(t.hw, on ? 1 : 0, now, on ? 60 : 0);
    });
    hubW.dur = a < 0 ? 280 : 200; tset(hubW, a < 0 ? 1 : 0, now, a < 0 ? 180 : 0);
    read.textContent = a < 0 ? "rest" : "tile " + (a + 1);
    B.wake();
  }

  bag.add(pointer(stage, { move: (p) => setActive(hit(p)), leave: () => setActive(-1) }));
  bag.add(() => svg.replaceChildren());

  return {
    set: (v) => {
      lift = v;
      if (act >= 0) { const from = tiles[act].n; tiles.forEach((t) => { t.tgt = t.sp.t = lift * FALL[hops(t, from)]; t.pend = false; }); B.wake(); }
    },
    destroy: bag.dispose,
  };
};
