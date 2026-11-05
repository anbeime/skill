import { Cam, facing, fit, hull, lerp, poly, proj, ringAt, rrect, seg, unproj, type Ring, type Vec2, type Vec3 } from "../core/iso";
import { EASE_LIFT, reducedMotion, tdone, tset, tval, tween, type Tween } from "../core/motion";
import { disposer, mk, pointer, put, register, solid, type FigureMount, type Solid } from "../core/stage";
import { inset, slab } from "../slab";

/**
 * Rebuild: a monorepo as a tree of package tiles on a rounded plinth, a thick
 * root at the back, two packages under it, five more under those, joined by
 * dashed links on the floor. The tile under the pointer rises, and every
 * package that depends on it (its subtree) rises after it, hop by hop along
 * the links, each a little less; a pulse of ink runs down each link just ahead
 * of the tile it feeds. The rest stay down. Letting go is slower and softer than the
 * rise, deepest tile first. The touched tile takes the bright edge as the
 * last one lets it go (the stage's stroke transition is the cross-fade); at
 * rest that is the root. The slider is the rise, in world units.
 *
 * The pattern: discrete items. Tweens, a stagger by hop (forward on the rise,
 * reversed on the return), and a hit test on the target pose of each tile, so
 * a tile rising under the pointer cannot flip it.
 */
const T = 3, TH = 5, HALF = 12, HUBH = 18, FALL = 0.7, REACH = 24;
// ms: a hop of the rise, a hop of the return (deepest first), the two durations, the pulse, the mark's hand-over
const HOP = 125, RHOP = 90, UP = 700, DOWN = 1350, PULSE = 420, LATE = 70;
const TAIL = 0.45, GRACE = 400;
// Depth runs down the screen (x + y), spread across it (x - y); parents sit between their children.
type Dash = { u: number; d: string; full: string; lit: number; el: SVGPathElement };
type Link = { n: Node; pt: Tween; on: boolean; dashes: Dash[] };
type Node = {
  p: number; l: number; d: number; s: number;
  i: number; x: number; y: number; h: number; tw: Tween; drawn: number; want: boolean; at: number | undefined;
  ring: Ring; inner: Ring; el: Solid; rec?: Ring; recEl?: SVGPathElement;
};
/** The tree's shape; each mount draws its own copy, so two of the figure on a page never share a tile. */
const TREE: ReadonlyArray<Pick<Node, "p" | "l" | "d" | "s">> = [
  { p: -1, l: 0, d: 0, s: -9 },
  { p: 0, l: 1, d: 60, s: -54 }, { p: 0, l: 1, d: 60, s: 36 },
  { p: 1, l: 2, d: 120, s: -72 }, { p: 1, l: 2, d: 120, s: -36 },
  { p: 2, l: 2, d: 120, s: 0 }, { p: 2, l: 2, d: 120, s: 36 }, { p: 2, l: 2, d: 120, s: 72 },
];
/** Hops from a to b along the links. */
const dist = (a: number, b: number) => {
  const up = (i: number) => { const c: number[] = []; for (; i >= 0; i = TREE[i].p) c.push(i); return c; };
  const ca = up(a), cb = up(b), m = ca.find((i) => cb.includes(i))!;
  return ca.indexOf(m) + cb.indexOf(m);
};
const under = (a: number, b: number) => { for (let i = b; i >= 0; i = TREE[i].p) if (i === a) return true; return false; };

export const mount: FigureMount = ({ stage, svg, read }, value) => {
  const bag = disposer();
  let rise = value, act = -1, grace: number | null = null;
  const NODES = TREE.map((t) => ({ ...t }) as Node);
  const half = (n: Node) => (n.l ? HALF : HUBH), thick = (n: Node) => (n.l ? T : TH), round = (n: Node) => (n.l ? 4.6 : 7);
  NODES.forEach((n, i) => { n.i = i; n.x = n.d + n.s; n.y = n.d - n.s; n.h = half(n); n.tw = tween(0); n.drawn = NaN; n.want = !n.i; n.at = undefined; });

  const C = Cam(45, 0.5, 1.5);
  const ext: Vec3[] = [];
  for (const n of NODES) ext.push([n.x - n.h, n.y - n.h, 0], [n.x + n.h, n.y + n.h, 0], [n.x, n.y, 20 + TH]);
  fit(C, ext, 200, 166);
  const P = proj(C), front = facing(C);

  const g = mk("g", {}, svg);

  // Links and footprints lie on the floor, so they go down before any tile.
  const links: Link[] = [];
  for (const n of NODES) {
    if (n.p < 0) continue;
    const q = NODES[n.p], dx = n.x - q.x, dy = n.y - q.y, L = Math.hypot(dx, dy);
    // a straight run on the floor from one slab's edge to the other's, along the line between their centres
    const cut = (h: number) => h / Math.max(Math.abs(dx), Math.abs(dy)) * L + 2.5;
    const a = cut(q.h) / L, e = 1 - cut(n.h) / L;
    // short real dashes along the run, in screen space
    const A = P(q.x + dx * a, q.y + dy * a, 0), Z = P(q.x + dx * e, q.y + dy * e, 0);
    const k = Math.max(2, Math.round(Math.hypot(Z[0] - A[0], Z[1] - A[1]) / 9));
    const lk: Link = { n, pt: tween(0, PULSE), on: false, dashes: [] }; links.push(lk);
    for (let j = 0; j < k; j++) lk.dashes.push({ u: (j + 0.35) / k, d: seg([lerp(A[0], Z[0], (j + 0.1) / k), lerp(A[1], Z[1], (j + 0.1) / k)], [lerp(A[0], Z[0], (j + 0.6) / k), lerp(A[1], Z[1], (j + 0.6) / k)]), full: seg([lerp(A[0], Z[0], j / k), lerp(A[1], Z[1], j / k)], [lerp(A[0], Z[0], (j + 1) / k), lerp(A[1], Z[1], (j + 1) / k)]), lit: 0 } as Dash);
  }
  // each dash is its own path, so the pulse can take them one by one (the stage eases the ink)
  for (const L of links) for (const e of L.dashes) e.el = mk("path", { d: e.d, class: "nf" }, g);
  for (const n of NODES) {
    const r = rrect(n.x - n.h, n.y - n.h, n.x + n.h, n.y + n.h, round(n), 8);
    n.ring = r;
    mk("path", { d: poly(ringAt(P, r, 0)), class: "nf lo" }, g);
  }
  // Back to front by x + y of the centre.
  const order = NODES.slice().sort((a, b) => a.x + a.y - (b.x + b.y));
  for (const n of order) {
    const r = rrect(n.x - n.h, n.y - n.h, n.x + n.h, n.y + n.h, round(n), 8);
    n.ring = r; n.inner = inset(C, r, n.l ? 1.1 : 1.3); n.el = solid(g);
    // the root carries a recessed square in its lid
    if (!n.l) {
      n.rec = inset(C, r, 2.8); n.recEl = mk("path", { class: "nf lo" }, n.el.g);
    }
  }
  const draw = (n: Node, h: number) => {
    put(n.el, slab(P, front, n.ring, n.inner, h, h + thick(n)));
    if (n.rec) n.recEl!.setAttribute("d", poly(ringAt(P, n.rec, h + thick(n))));
  };

  const B = register(stage, (_dt, now) => {
    let moving = false;
    for (const n of NODES) {
      const h = tval(n.tw, now);
      if (!tdone(n.tw, now)) moving = true;
      if (h !== n.drawn) { n.drawn = h; draw(n, h); }
    }
    // on open floor the last tile is held a moment before it lets go
    if (grace !== null) { if (now >= grace) { grace = null; set(-1); } else moving = true; }
    // the bright mark changes hands a beat after the old one lets go
    for (const n of NODES) {
      if (n.at === undefined) continue;
      if (now >= n.at) { n.el.sil.classList.toggle("hi", n.want); n.at = undefined; } else moving = true;
    }
    for (const L of links) {
      if (!L.on) continue;
      const fin = tdone(L.pt, now);
      moving = true;
      // the head travels the run, mostly steadily, the tail of lit dashes behind it
      const s = tval(L.pt, now);
      let lo = 0, hi = 1;
      for (let i = 0; i < 14; i++) { const m = (lo + hi) / 2; if (EASE_LIFT(m) < s) lo = m; else hi = m; }
      const hd = fin ? 9 : lerp(lo, s, 0.3) * (1 + TAIL);
      for (const e of L.dashes) {
        // under the head a dash closes up into a solid run; behind it, it stays inked and lets go
        const x = hd - e.u, lit = x < 0 || x >= TAIL ? 0 : x < TAIL * 0.4 ? 2 : 1;
        if (lit !== e.lit) { e.lit = lit; e.el.classList.toggle("sil", lit > 0); e.el.setAttribute("d", lit === 2 ? e.full : e.d); }
      }
      if (fin) { L.on = false; L.pt.from = L.pt.to = 0; L.pt.t0 = -1e9; }
    }
    return moving;
  });
  bag.add(B.unregister);

  /** The rise tile n takes when a is touched: it falls off a little with each hop down the links. */
  const target = (a: number, n: Node) => (a >= 0 && under(a, n.i) ? rise * FALL ** dist(a, n.i) : 0);

  const within = (q: Vec2, pg: Vec2[]) => {
    const s = pg.map((a, i) => { const b = pg[(i + 1) % pg.length]; return (b[0] - a[0]) * (q[1] - a[1]) - (b[1] - a[1]) * (q[0] - a[0]); });
    return s.every((v) => v >= 0) || s.every((v) => v <= 0);
  };
  /** The tile under the point on its target pose, the nearest in front first; else keep, near the tree, or -1 away from it. */
  function hit(p: Vec2): number {
    for (let k = order.length - 1; k >= 0; k--) {
      const n = order[k], z = target(act, n);
      if (within(p, hull(ringAt(P, n.ring, 0).concat(ringAt(P, n.ring, z + thick(n)))))) return n.i;
    }
    const [x, y] = unproj(C, p[0], p[1], 0);
    return NODES.some((n) => Math.hypot(x - n.x, y - n.y) < n.h + REACH - HALF) ? act : -1;
  }

  const name = (a: number) => (a < 0 ? "rest" : a === 0 ? "root" : `pkg ${NODES[a].l}·${NODES.filter((n) => n.l === NODES[a].l && n.i <= a).length}`);
  /** Moves tile n to y after delay: a rise keeps the arrival's life, a fall is slower. */
  const go = (n: Node, y: number, now: number, delay: number) => {
    if (n.tw.to === y) return;
    const up = y > n.tw.to;
    tset(n.tw, y, now, delay);
    n.tw.dur = up ? UP : DOWN;
  };
  /** Touches a (-1 lets go): tiles that rise follow the hops from a; tiles that fall go deepest first from the one left. */
  function set(a: number) {
    if (a === act) return;
    const now = performance.now(), o = act, now_t = NODES.map((n) => target(a, n));
    act = a;
    let deep = 0;
    NODES.forEach((n, i) => { if (now_t[i] < n.tw.to && o >= 0) deep = Math.max(deep, dist(o, n.i)); });
    NODES.forEach((n, i) => go(n, now_t[i], now, now_t[i] < n.tw.to ? (deep - dist(o, n.i)) * RHOP : a >= 0 ? dist(a, n.i) * HOP : 0));
    for (const L of links) {
      L.pt.from = L.pt.to = 0; L.pt.t0 = -1e9; L.on = false; for (const e of L.dashes) { e.lit = 0; e.el.classList.remove("sil"); e.el.setAttribute("d", e.d); }
      if (a >= 0 && under(a, L.n.i) && L.n.i !== a) { L.on = true; tset(L.pt, 1, now, dist(a, L.n.p) * HOP + 20); }
    }
    for (const n of NODES) {
      const on = n.i === (a < 0 ? 0 : a);
      if (on !== n.want) { n.want = on; n.at = on ? now + LATE : now; }
    }
    read.textContent = name(a);
    B.wake();
  }
  NODES[0].el.sil.classList.add("hi");
  read.textContent = "rest";
  for (const n of NODES) draw(n, 0);

  bag.add(pointer(stage, {
    move: (p) => {
      const h = hit(p);
      if (h < 0 && act >= 0 && !reducedMotion()) { if (grace === null) { grace = performance.now() + GRACE; B.wake(); } return; }
      grace = null; set(h);
    },
    leave: () => { grace = null; set(-1); },
  }));
  bag.add(() => svg.replaceChildren());

  return {
    set: (v) => { rise = v; const now = performance.now(); for (const n of NODES) { if (n.tw.to !== target(act, n)) { tset(n.tw, target(act, n), now, 0); n.tw.dur = UP; } } B.wake(); },
    destroy: bag.dispose,
  };
};
