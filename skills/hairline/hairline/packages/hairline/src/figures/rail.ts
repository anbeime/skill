import { Cam, clamp, facing, fillet, fit, hull, open, poly, prism, proj, rad, rings, type Vec2, type Vec3 } from "../core/iso";
import { spring, stepS } from "../core/motion";
import { disposer, mk, pointer, put, register, solid, type FigureMount } from "../core/stage";

/**
 * Rail: a garment rail on two uprights, with seven bare hangers. The pointer
 * brushes the hangers: each rocks on its hook away from it, the nearest most,
 * and settles. At rest they hang at uneven angles and one is bright. The
 * slider is how many hangers the brush reaches.
 *
 * The pattern: a field, as Terrain's. One spring per hanger on its rock, the
 * target falling off with its distance, in hangers, from the one picked. The
 * pick is the hanger whose rest centre is nearest the pointer's screen x. The
 * springs are softer than the default because a hanger is a pendulum.
 */

const L = 132, TOP = 92, POST = 4.4, FOOT = 34, BAR = 2;  // rail length, its height, upright side, foot depth, rail radius
const N = 7, X0 = 21, DX = 15, TH = 1.8, ROCK = 22;       // hangers, the first one's x, their pitch, thickness, furthest rock in degrees
const REST = [4, -7, 2, 13, -3, 6, -9], MARK = 3, S = 1.9;
/** A hanger in its own plane: s along its shoulders, d down from the rail's centre. */
const BODY = /* @__PURE__ */ fillet([[0, 9], [25, 21], [25, 25], [-25, 25], [-25, 21]], [4, 2, 2, 2, 2], 5);
const HOLE = /* @__PURE__ */ fillet([[0, 14], [15, 21.5], [-15, 21.5]], [2, 1.2, 1.2], 4);
/** Its hook: the stem, then up the rail's near side and over; the tip that drops behind the rail is hidden, so not drawn. */
const HOOK: Vec2[] = /* @__PURE__ */ (() => [[0, 9], [0, 5], ...Array.from({ length: 10 }, (_, k): Vec2 => { const t = rad(120 - k * 20); return [Math.sin(t) * 3.4, -Math.cos(t) * 3.4]; })])();

export const mount: FigureMount = ({ stage, svg, read }, value) => {
  const bag = disposer();
  const C = Cam(45, 0.5, S);
  const ext: Vec3[] = [[0, -FOOT / 2, 0], [L, -FOOT / 2, 0], [0, FOOT / 2, 0], [L, FOOT / 2, 0], [0, 0, TOP + 6], [L, 0, TOP + 6], [0, -30, TOP - 30], [L, 30, TOP - 30]];
  fit(C, ext, 200, 166);
  const P = proj(C), front = facing(C);
  const g = mk("g", {}, svg);
  const block = (x0: number, y0: number, x1: number, y1: number, r: number, z0: number, z1: number) => { const [o, i] = rings(x0, y0, x1, y1, r, 0.7); put(solid(g), prism(P, front, o, i, z0, z1)); };

  // Back to front: the far foot and upright, the hangers from the far end, the rail, their hooks, the near foot and upright.
  // The hangers go under the rail: all of one the rail crosses on screen is its far shoulder, which is behind it.
  block(-POST / 2 - 1, -FOOT / 2, POST / 2 + 1, FOOT / 2, 2.2, 0, 3);
  block(-POST / 2, -POST / 2, POST / 2, POST / 2, 1.4, 3, TOP + 4);
  const bodies = Array.from({ length: N }, () => solid(g));
  block(0, -BAR, L, BAR, BAR, TOP - BAR, TOP + BAR);
  const hooks = bodies.map(() => mk("path", { class: "nf" }, g));
  block(L - POST / 2 - 1, -FOOT / 2, L + POST / 2 + 1, FOOT / 2, 2.2, 0, 3);
  block(L - POST / 2, -POST / 2, L + POST / 2, POST / 2, 1.4, 3, TOP + 4);

  const sp = REST.map((a) => spring(a, { k: 60, c: 6, eps: 0.02 }));
  const drawn = REST.map(() => NaN);
  function draw() {
    sp.forEach((s, i) => {
      if (s.x === drawn[i]) return;
      drawn[i] = s.x;
      const c = Math.cos(rad(s.x)), n = Math.sin(rad(s.x)), x = X0 + i * DX;
      // a point of the hanger's plane, rocked about the rail
      const at = (p: Vec2, dx: number) => P(x + dx, p[0] * c + p[1] * n, TOP - (p[1] * c - p[0] * n));
      put(bodies[i], { sil: poly(hull(BODY.map((p) => at(p, 0)).concat(BODY.map((p) => at(p, TH))))), crease: poly(HOLE.map((p) => at(p, TH))) });
      hooks[i].setAttribute("d", open(HOOK.map((p) => at(p, TH / 2))));
    });
  }

  const loop = register(stage, (dt) => { let m = false; for (const s of sp) m = stepS(s, dt) || m; draw(); return m; });
  bag.add(loop.unregister);

  // Each hanger's rest centre on screen: what the pointer's x is read against.
  const cx = REST.map((_, i) => P(X0 + i * DX, 0, TOP - 17)[0]);
  let reach = value, picked = -2, side = 1;
  function choose(a: number) {
    picked = a;
    sp.forEach((s, i) => {
      const f = a < 0 ? 0 : clamp(1 - Math.abs(i - a) / (reach + 0.5), 0, 1);
      s.t = REST[i] - ROCK * f * f * (i === a ? side : Math.sign(i - a));   // a lower rock swings the bottom right: away from a pointer on the left
    });
    bodies.forEach((b, i) => b.sil.classList.toggle("hi", i === (a < 0 ? MARK : a)));
    read.textContent = a < 0 ? "rest" : `hanger ${a + 1} · 0`;
    loop.wake();
  }
  choose(-1);
  draw();

  bag.add(pointer(stage, {
    move: (p) => {
      const a = cx.reduce((best, x, i) => (Math.abs(p[0] - x) < Math.abs(p[0] - cx[best]) ? i : best), 0);
      side = p[0] < cx[a] ? 1 : -1;
      choose(a);
    },
    leave: () => choose(-1),
  }));
  bag.add(() => svg.replaceChildren());

  return { set: (v) => { reach = v; choose(picked < 0 ? -1 : picked); }, destroy: bag.dispose };
};
