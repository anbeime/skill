import { Cam, clamp, facing, fit, lerp, poly, proj, rad, ringAt, rrect, seg, unproj, type Ring, type Vec2, type Vec3 } from "../core/iso";
import { reducedMotion, spring, stepS, tdone, tset, tval, tween, type Spring, type Tween } from "../core/motion";
import { disposer, mk, pointer, put, register, solid, type FigureMount, type Solid } from "../core/stage";
import { inset, slab } from "../slab";

/**
 * Settle: a hub plate on a faint floor grid and twelve thin tiles lying
 * scattered and crooked around it, no links. The nearer the pointer comes to
 * the hub, the more the map resolves: each tile slides and turns into its
 * place in a pinwheel tree on its own spring, the inner ones first, and a
 * dashed link draws in from the hub once both its ends are seated. Pointer far
 * away: they drift back to the heap. The hub takes the bright stroke. The
 * slider is the reach, in world units: how far from the hub the map starts to
 * resolve.
 *
 * The pattern: a field, read as a count. The pointer sets a distance on the
 * ground plane (which never moves); each tile has its own threshold on it.
 */

const TH = 3.2, HALF = 9, HUB = 17, HUBT = 6.5, GRID = 22, GN = 0, GR = 86;
// [settled x, y, parent (-1 hub), scattered x, y, angle, z]
const T: number[][] = [
  [50, 0, -1, 51, -19, 14, 0], [88, 0, 0, 93, 23, -22, 0], [50, 34, 0, 58, 50, 26, 0],
  [0, 50, -1, -21, 59, -16, 0], [0, 88, 3, 20, 84, 28, 0], [-34, 50, 3, -59, 64, -20, 0],
  [-50, 0, -1, -67, -20, -12, 0], [-88, 0, 6, -91, 26, 20, 0], [-50, -34, 6, -47, -57, -28, 0],
  [0, -50, -1, 22, -46, 18, 0], [0, -88, 9, -15, -95, -14, 0], [34, -50, 9, 62, -60, 22, 0],
];

type Link = { i: number; from: Vec2; to: Vec2; tw: Tween; p: number; el: SVGPathElement; drawn: number };
type Tile = {
  i: number; t: number[]; el: Solid; th: number; sp: Spring; key: string; ord: number; k: number;
  rise: { k: number; c: number }; fall: { k: number; c: number }; lag: number; want: number; wait: number; falling: boolean;
};

/** A rounded square of half-side h about (cx, cy), turned by a degrees: a ring whose samples carry their normals round with it. */
function turned(cx: number, cy: number, h: number, r: number, a: number): Ring {
  const c = Math.cos(rad(a)), s = Math.sin(rad(a));
  return rrect(-h, -h, h, h, r, 8).map((q) => ({
    u: cx + q.u * c - q.v * s, v: cy + q.u * s + q.v * c, nu: q.nu * c - q.nv * s, nv: q.nu * s + q.nv * c,
  }));
}

export const mount: FigureMount = ({ stage, svg, read }, value) => {
  const bag = disposer();
  let reach = value, q = 0;

  const C = Cam(45, 0.5, 1.9);
  const pts: Vec3[] = [[0, 0, HUBT], [GR, 0, 0], [-GR, 0, 0], [0, GR, 0], [0, -GR, 0]];
  for (const t of T) for (const [x, y] of [[t[0], t[1]], [t[3], t[4]]] as Vec2[]) pts.push([x - 11, y - 11, 0], [x + 11, y + 11, 0], [x + 11, y - 11, 0], [x - 11, y + 11, 0]);
  fit(C, pts, 200, 166);
  const P = proj(C), front = facing(C);

  const g = mk("g", {}, svg);
  // the floor: a faint grid, lying flat, under everything
  let d = "";
  for (let k = -GN; k <= GN; k++) {
    const e = Math.sqrt(GR * GR - (k * GRID) ** 2);
    d += seg(P(k * GRID, -e, 0), P(k * GRID, e, 0)) + seg(P(-e, k * GRID, 0), P(e, k * GRID, 0));
  }
  if (GN > 0) mk("path", { d, class: "nf lo" }, g);

  // links are guides on the floor: painted before every plate they join
  const links: Link[] = T.map((t, i) => {
    const a: Vec2 = t[2] < 0 ? [0, 0] : [T[t[2]][0], T[t[2]][1]], b: Vec2 = [t[0], t[1]];
    const L = Math.hypot(b[0] - a[0], b[1] - a[1]), u = [(b[0] - a[0]) / L, (b[1] - a[1]) / L];
    const ha = t[2] < 0 ? HUB : HALF, from: Vec2 = [a[0] + u[0] * (ha + 2), a[1] + u[1] * (ha + 2)], to: Vec2 = [b[0] - u[0] * (HALF + 2), b[1] - u[1] * (HALF + 2)];
    return { i, from, to, tw: tween(0), p: parent(i), el: mk("path", { class: "nf" }, g), drawn: NaN };
  });
  function parent(i: number) { return T[i][2]; }

  // the hub: a thick slab with a recessed square set into its lid
  const hub = mk("g", {}, g);
  const hr = rrect(-HUB, -HUB, HUB, HUB, 7, 8);
  const hs = solid(hub);
  put(hs, slab(P, front, hr, inset(C, hr, 1.3), 0, HUBT));
  hs.sil.classList.add("hi");
  mk("path", { d: poly(ringAt(P, inset(C, hr, 2.8), HUBT)), class: "nf lo" }, hub);

  const tiles: Tile[] = T.map((t, i) => ({
    i, t, el: solid(mk("g", {}, g)),
    // the inner tiles seat first and a little more briskly; the outer ones follow, out of step
    th: [0.05, 0.3, 0.4][i % 3],
    sp: spring(0, { k: i % 3 === 0 ? 120 : 90 - (i % 3) * 8, c: i % 3 === 0 ? 14 : 12, eps: 0.002 }),
    key: "", ord: 0, k: 0,
    // arrival and return keep their own springs: the return is softer, near-critical, no bounce
    rise: { k: i % 3 === 0 ? 120 : 90 - (i % 3) * 8, c: i % 3 === 0 ? 14 : 12 },
    fall: { k: [38, 44, 50][i % 3], c: 2 * Math.sqrt([38, 44, 50][i % 3]) },
    // outermost let go first: the leaves, then the middles, then the stems
    lag: [0.3, 0.2, 0.12][i % 3] * 1000,
    want: 0, wait: 0, falling: false,
  }));

    function pose(tl: Tile) {
    const s = tl.sp.x, [sx, sy, , x0, y0, a0, z0] = tl.t;
    const w = clamp(s, 0, 1), hop = 6.5 * w * (1 - w) * 4 / 4;
    const x = lerp(x0, sx, s), y = lerp(y0, sy, s), a = lerp(a0, 0, s), z = Math.max(0, lerp(z0, 0, w) + hop);
    return { x, y, a, z };
  }
  function drawTile(tl: Tile) {
    const p = pose(tl), key = [p.x, p.y, p.a, p.z].map((v) => v.toFixed(2)).join();
    tl.k = p.x + p.y + 6 * p.z;
    if (key === tl.key) return;
    tl.key = key;
    const r = turned(p.x, p.y, HALF, 3.6, p.a);
    put(tl.el, slab(P, front, r, inset(C, r, 1), p.z, p.z + TH));
  }

  let order = "";
  function paintOrder() {
    const list = tiles.slice().sort((a, b) => a.k - b.k);
    const hubAt = list.findIndex((t) => t.k > 0), arr = list.slice();
    // the hub sits at x + y = 0; tiles are painted around it
    const seq: (SVGGElement | SVGGElement)[] = hubAt < 0 ? arr.map((t) => t.el.g).concat(hub) : arr.slice(0, hubAt).map((t) => t.el.g).concat(hub, arr.slice(hubAt).map((t) => t.el.g));
    const id = seq.map((e) => (e === hub ? "h" : tiles.findIndex((t) => t.el.g === e))).join();
    if (id === order) return;
    order = id;
    for (const e of seq) g.appendChild(e);
  }

  function drawLink(l: Link, now: number) {
    const A = l.p < 0 ? null : tiles[l.p], B2 = tiles[l.i];
    const a = A ? A.sp.x : 1, b = B2.sp.x;
    // it draws in only once both ends are seated, and draws back out as soon as either is asked to leave
    const want = Math.min(a, b) > 0.96 && B2.want >= 1 && (!A || A.want >= 1) ? 1 : 0;
    if (l.tw.to !== want) { tset(l.tw, want, now, 0); l.tw.dur = want ? 700 : 900; }
    const u = tval(l.tw, now);
    if (u === l.drawn) return;
    l.drawn = u;
    // real dashes along the link in screen space, as many as the draw-in has reached
    const pa = P(l.from[0], l.from[1], 0), pb = P(l.to[0], l.to[1], 0), k = Math.max(2, Math.round(Math.hypot(pb[0] - pa[0], pb[1] - pa[1]) / 9));
    let dd = "";
    for (let j = 0; j < k; j++) {
      const f0 = (j + 0.1) / k, f1 = Math.min((j + 0.6) / k, u);
      if (f1 > f0) dd += seg([lerp(pa[0], pb[0], f0), lerp(pa[1], pb[1], f0)], [lerp(pa[0], pb[0], f1), lerp(pa[1], pb[1], f1)]);
    }
    l.el.setAttribute("d", dd);
  }

  const B = register(stage, (dt, now) => {
    let m = false;
    for (const tl of tiles) {
      if (tl.wait > 0) { tl.wait -= dt * 1000; m = true; if (tl.wait <= 0) tl.sp.t = tl.want; }
      if (stepS(tl.sp, dt)) m = true;
      drawTile(tl);
    }
    for (const l of links) { drawLink(l, now); if (!tdone(l.tw, now)) m = true; }
    paintOrder();
    return m;
  });
  bag.add(B.unregister);

  function retarget() {
    let n = 0;
    for (const tl of tiles) {
      const s = clamp((q - tl.th) / 0.22, 0, 1);
      if (s > tl.want) {
        tl.falling = false; tl.wait = 0; tl.want = s; Object.assign(tl.sp, tl.rise); tl.sp.t = s;
      } else if (s < tl.want) {
        if (!tl.falling) { tl.falling = true; tl.wait = reducedMotion() ? 0 : tl.lag; Object.assign(tl.sp, tl.fall); }
        tl.want = s;
        if (tl.wait <= 0) tl.sp.t = s;
      }
      if (s > 0.5) n++;
    }
    read.textContent = q <= 0 ? "rest" : `map ${n}·${tiles.length}`;
    B.wake();
  }

  /** How resolved the map is, 0 at the reach and beyond, 1 at the hub. */
  const resolve = (dd: number) => { const u = clamp((reach - dd) / (reach - 18), 0, 1); return u * u * (3 - 2 * u); };
  bag.add(pointer(stage, {
    move: (p) => { const [x, y] = unproj(C, p[0], p[1], 0); q = resolve(Math.hypot(x, y)); retarget(); },
    leave: () => { q = 0; retarget(); },
  }));
  bag.add(() => svg.replaceChildren());
  for (const tl of tiles) drawTile(tl);
  paintOrder();
  read.textContent = "rest";

  return { set: (v) => { reach = v; }, destroy: bag.dispose };
};
