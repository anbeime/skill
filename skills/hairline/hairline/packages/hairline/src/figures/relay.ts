import { Cam, facing, fit, lerp, poly, proj, ringAt, rrect, seg, type Ring, type Vec2, type Vec3 } from "../core/iso";
import { tdone, tset, tval, tween, type Tween } from "../core/motion";
import { disposer, mk, pointer, put, register, solid, type FigureMount, type Solid } from "../core/stage";
import { inset, slab } from "../slab";

/**
 * Relay: a hub plate and four branches of thin tiles on a floor, joined by
 * dashed links. The pointer picks the nearest leaf; the path from the hub to it
 * lights hop by hop: each link turns solid as a line that grows along it, and
 * each tile on the path rises a little, a short delay per hop. The leaf takes
 * the bright edge, which cross-fades from one leaf to the next (and to the hub's
 * rim at rest). Moving to another leaf lowers the old path leaf to hub, slower
 * than it rose, then lights the new one. The slider is the delay per hop, in ms.
 *
 * The pattern: discrete items. Tweens, a stagger by hop count, and a hit test
 * on the leaves' resting positions, so a tile that has risen cannot flip the choice.
 */

const T = 3, HT = 7, RISE = 9, TS = 9, HS = 17;
// Each branch leaves the hub along an axis: its first tile at `a`, its second at `b`, then leaves
// beside the second, to either side. Tiles are [along, across] on that axis; the parent is the one before it.
const BRANCHES = [
  { d: [-1, 0], a: 50, b: 84, side: [-1, 1] },
  { d: [0, -1], a: 50, b: 76, side: [1] },
  { d: [1, 0], a: 50, b: 84, side: [-1, 1] },
  { d: [0, 1], a: 50, b: 76, side: [-1] },
];
const FORK = 31;

type Node = {
  c: Vec2; par: number; dep: number; tag?: string;
  a: Vec2; b: Vec2; link: SVGPathElement; l: Tween; z: Tween; h: Tween; ld: number; zd: number; hd: boolean;
  ring: Ring; inner: Ring; el: Solid;
};

/** The tiles of the tree: world centre, parent index (-1 is the hub), depth, and its leaf's read-out. */
function tree(): Node[] {
  const nodes: Node[] = [];
  BRANCHES.forEach((br, k) => {
    const at = (s: number, o: number): Vec2 => [br.d[0] * s - br.d[1] * o, br.d[1] * s + br.d[0] * o];
    const i = nodes.length;
    nodes.push({ c: at(br.a, 0), par: -1, dep: 1 } as Node);
    nodes.push({ c: at(br.b, 0), par: i, dep: 2 } as Node);
    br.side.forEach((s, j) => nodes.push({ c: at(br.b, s * FORK), par: i + 1, dep: 3, tag: "leaf " + (k + 1) + "·" + (j + 1) } as Node));
  });
  return nodes;
}

export const mount: FigureMount = ({ stage, svg, read }, value) => {
  const bag = disposer();
  let step = value;
  const nodes = tree(), leaves = nodes.filter((n) => n.tag);

  const C = Cam(45, 0.5, 1.9);
  const pts: Vec3[] = [[-HS, -HS, 0], [HS, HS, 0], [-HS, HS, 0], [HS, -HS, 0]];
  for (const n of nodes) for (const [sx, sy] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) pts.push([n.c[0] + sx * TS, n.c[1] + sy * TS, T + RISE]);
  fit(C, pts, 200, 166);
  const P = proj(C), front = facing(C);
  const g = mk("g", {}, svg);

  // Links, painted before the plates they join: a dashed run, and over it the solid line that grows.
  for (const n of nodes) {
    const from = n.par < 0 ? [0, 0] : nodes[n.par].c;
    const dx = n.c[0] - from[0], dy = n.c[1] - from[1], len = Math.hypot(dx, dy), o0 = n.par < 0 ? HS : 0, o1 = 0;
    n.a = P(from[0] + (dx / len) * o0, from[1] + (dy / len) * o0, 0); n.b = P(n.c[0] - (dx / len) * o1, n.c[1] - (dy / len) * o1, 0);
    let dd = "";
    const L = Math.hypot(n.b[0] - n.a[0], n.b[1] - n.a[1]), k = Math.max(2, Math.round(L / 9));
    for (let j = 0; j < k; j++) dd += seg([lerp(n.a[0], n.b[0], (j + 0.1) / k), lerp(n.a[1], n.b[1], (j + 0.1) / k)], [lerp(n.a[0], n.b[0], (j + 0.6) / k), lerp(n.a[1], n.b[1], (j + 0.6) / k)]);
    mk("path", { d: dd, class: "nf" }, g);
  }
  for (const n of nodes) {
    n.link = mk("path", { class: "nf sil" }, g);
    n.l = tween(0); n.z = tween(0); n.h = tween(0); n.ld = NaN; n.zd = NaN; n.hd = false;
  }

  // The hub: a thick plate with a recessed square set in its top.
  const hub = solid(g);
  const hr = rrect(-HS, -HS, HS, HS, 7, 8);
  put(hub, slab(P, front, hr, inset(C, hr, 1.3), 0, HT));
  const rim = mk("path", { d: poly(ringAt(P, inset(C, hr, 2.8), HT)), class: "nf hi" }, g);
  const rimW = tween(1); let rimD = true;
  mk("path", { d: poly(ringAt(P, inset(C, hr, 3.8), HT)), class: "nf lo" }, g);

  // The tiles, back to front by x + y.
  for (const n of nodes.slice().sort((p, q) => p.c[0] + p.c[1] - q.c[0] - q.c[1])) {
    n.ring = rrect(n.c[0] - TS, n.c[1] - TS, n.c[0] + TS, n.c[1] + TS, 3.6, 8);
    n.inner = inset(C, n.ring, 1);
    n.el = solid(g);
  }

  const B = register(stage, (_dt, now) => {
    let moving = false;
    for (const n of nodes) {
      const l = tval(n.l, now), z = tval(n.z, now);
      if (l !== n.ld) {
        n.ld = l;
        n.link.setAttribute("d", l > 0.002 ? seg(n.a, [lerp(n.a[0], n.b[0], l), lerp(n.a[1], n.b[1], l)]) : "");
      }
      if (z !== n.zd) {
        n.zd = z;
        put(n.el, slab(P, front, n.ring, n.inner, z * RISE, z * RISE + T));
      }
      // The bright edge is a class on the silhouette; the kernel eases the stroke between the two (260ms),
      // so the hand-off is a cross-fade. Its weight tween only says when to flip.
      if (n.tag) { const h = tval(n.h, now) > 0.5; if (h !== n.hd) { n.hd = h; n.el.sil.classList.toggle("hi", h); } }
      if (!tdone(n.l, now) || !tdone(n.z, now) || !tdone(n.h, now)) moving = true;
    }
    const rw = tval(rimW, now) > 0.5;
    if (rw !== rimD) { rimD = rw; rim.classList.toggle("hi", rw); }
    if (!tdone(rimW, now)) moving = true;
    return moving;
  });
  bag.add(B.unregister);

  // Hit test on the leaves' rest positions, in screen space: they never move. It is sticky: the leaf
  // in hand is kept until another is clearly nearer, so a pointer passing by does not flash it.
  const spot = leaves.map((n) => P(n.c[0], n.c[1], T));
  const CAP = 78, STICK = 18;
  const dist = (i: number, [x, y]: Vec2) => Math.hypot(spot[i][0] - x, spot[i][1] - y);
  function hit(p: Vec2) {
    let best = -1, bd = CAP;
    spot.forEach((_, i) => { const d = dist(i, p); if (d < bd) { bd = d; best = i; } });
    if (act >= 0 && best !== act && dist(act, p) < CAP && dist(act, p) - bd < STICK) return act;
    return best;
  }

  // Tweens with their own length: what rises is quick, what falls back is longer and softer.
  const UP = 700, DOWN = 1500;
  const go = (tw: Tween, to: number, now: number, delay: number, dur: number) => { if (tw.to === to) return; tset(tw, to, now, delay); tw.dur = dur; };
  const lit = new Set<Node>(), parentOf = (n: Node): Node | null => (n.par < 0 ? null : nodes[n.par]);
  let act = -1;
  /** Lights the path to leaf a (-1: none). What leaves the path goes first, leaf to hub, slower than it rose; what joins it follows, hub to leaf. */
  function setActive(a: number) {
    if (a === act) return;
    const now = performance.now(), want = new Set<Node>(), out = step * 1.5;
    for (let n: Node | null = a < 0 ? null : leaves[a]; n; n = parentOf(n)) want.add(n);
    const off = [...lit].filter((n) => !want.has(n)), top = off.reduce((m, n) => Math.max(m, n.dep), 0);
    const wait = off.length ? (off.length - 1) * out * 0.65 + step * 0.5 : 0;
    for (const n of nodes) {
      const on = want.has(n), was = lit.has(n);
      if (on === was) continue;
      if (on) { go(n.l, 1, now, wait + (n.dep - 1) * step, UP); go(n.z, 1, now, wait + n.dep * step, UP); }
      else { go(n.z, 0, now, (top - n.dep) * out, DOWN); go(n.l, 0, now, (top - n.dep) * out + out * 0.5, DOWN); }
      if (n.tag) {
        // the bright edge hands over: the old leaf lets go just as the new one takes hold
        if (on) go(n.h, 1, now, wait + n.dep * step, 40);
        else go(n.h, 0, now, a < 0 ? 0 : Math.max(0, wait + 3 * step - 60), 40);
      }
    }
    lit.clear(); want.forEach((n) => lit.add(n));
    go(rimW, a < 0 ? 1 : 0, now, a < 0 ? (off.length - 1) * out * 0.5 + 120 : 0, 40);
    act = a;
    read.textContent = a < 0 ? "rest" : leaves[a].tag!;
    B.wake();
  }

  bag.add(pointer(stage, { move: (p) => setActive(hit(p)), leave: () => setActive(-1) }));
  bag.add(() => svg.replaceChildren());

  return { set: (v) => { step = v; }, destroy: bag.dispose };
};
