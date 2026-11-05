import { Cam, circ, clamp, facing, fillet, fit, hull, open, poly, prism, proj, rings, rrect, seg, type Vec2, type Vec3 } from "../core/iso";
import { spring, stepS } from "../core/motion";
import { disposer, flatDot, mk, place, pointer, put, register, solid, type FigureMount } from "../core/stage";

/**
 * Elevator: an open shaft, two walls at its back, the car inside it on two
 * guide rails, and four floors running off to the right of it, one landing
 * in front of the car's door on each. A rope runs from the car's crosshead
 * up through the head slab, over the traction sheave and down to a
 * counterweight that falls as the car rises. The pointer's height on the stage
 * picks a floor; the car travels there on a spring, through every floor in
 * between, and the floor it is bound for takes the bright stroke. At rest the
 * car is caught between the first and the second floor, bright. The slider is
 * the car's spring stiffness: stiffer travels faster.
 *
 * The pattern: scrub and pick. A spring for where the car is, a choice read
 * from the fixed floors, never from the car on screen.
 */

type Box = [number, number, number, number];

const SX = 32, SY = 34, FH = 36, CH = 25, T = 2.5, NF = 4, TOP = 3 * FH + CH + 7;
const CAR: Box = [5, 7, 28, 27], RX = 16.5, CW: Box = [-8, 11, -2, 23], CWH = 17;
const WALL = 2;
/** The plinth: under the shaft, and under the floors where they run back past the shaft's wall, no further. */
const BASE = fillet([[-16, -2], [33, -2], [33, -56], [76, -56], [76, 38], [-16, 38]], [3, 2, 4, 6, 6, 6]);
/** A floor's outline: the plate to the right of the shaft and the landing in front of the car's door, as one L. */
const FLOOR = fillet([[33, -56], [72, -56], [72, -6], [43, -6], [43, 34], [33, 34]], [4, 4, 4, 3, 3, 3]);
const CWX = (CW[0] + CW[2]) / 2, SR = (RX - CWX) / 2;
/** The sheave's centre. */
const SC: Vec3 = [CWX + SR, SY / 2, TOP + 3 + SR + 2];
const REST_Z = 1.5 * FH - 4;
const NAMES = ["ground", "floor 1", "floor 2", "floor 3"];

export const mount: FigureMount = ({ stage, svg, read }, value) => {
  const bag = disposer();
  const C = Cam(45, 0.5, 1.3);
  fit(C, [[-16, -56, -8], [76, 38, -8], [76, -56, -8], [-16, 38, -8], [SC[0], SC[1], SC[2] + SR]], 200, 166);
  const P = proj(C), front = facing(C);
  const g = mk("g", {}, svg);
  const block = (box: Box, r: number, b: number, z0: number, z1: number) => { const [o, i] = rings(...box, r, b); put(solid(g), prism(P, front, o, i, z0, z1)); };
  const line = (cls: string) => mk("path", { class: cls }, g);
  // A slab on any outline, convex or not: its silhouette is the far run of the
  // top joined to the near run of the underside; the top's near run is the crease.
  const slab = (pts: Vec2[], z0: number, z1: number) => {
    const n = pts.length, near = pts.map((p, i) => { const q = pts[(i + 1) % n]; return q[1] - p[1] - (q[0] - p[0]) > 0; });
    const runOf = (want: boolean) => {
      const s = near.findIndex((f, i) => f === want && near[(i + n - 1) % n] !== want), out: Vec2[] = [];
      for (let i = s; near[i % n] === want; i++) out.push(pts[i % n]);
      return out.concat([pts[(s + out.length) % n]]);
    };
    const at = (r: Vec2[], z: number) => r.map((p) => P(p[0], p[1], z)), back = runOf(false), fore = runOf(true);
    const sil = mk("path", { class: "sil", d: poly(at(back, z1).concat(at(fore, z0))) }, g);
    mk("path", { class: "nf lo", d: open(at(fore, z1)) }, g);
    return sil;
  };

  // The plinth, the shaft's two back walls, then back to front: the far rail,
  // the counterweight and its rope, the car, the near rail.
  slab(BASE, -8, -T);
  block([-14 - WALL, -WALL, -14, SY], 1, 0.5, -T, TOP);
  block([-14, -WALL, SX, 0], 1, 0.5, -T, TOP);
  block([RX - 1.3, 3, RX + 1.3, 5.4], 0.8, 0.5, -T, TOP);
  const [cwo, cwi] = rings(...CW, 1.6, 0.8);
  const cw = solid(g), cwBands = line("nf lo"), cwRope = line("nf");
  const [co, ci] = rings(...CAR, 2.4, 1.1);
  const car = solid(g), door = line("nf"), split = line("nf lo");
  const [ho, hi] = rings(RX - 1.7, 5.4, RX + 1.7, 28.6, 0.8, 0.5);
  const head = solid(g), rope = line("nf");
  block([RX - 1.3, 28.6, RX + 1.3, 31], 0.8, 0.5, -T, TOP);

  // The head slab, the machine behind the sheave, the ropes up to it, the sheave.
  block([-14 - WALL, -WALL, SX + 1, SY + 1], 4, 1.4, TOP, TOP + 3);
  block([CWX + 2, 4, RX - 2, SY / 2 - 3], 2, 1, TOP + 3, SC[2] + 4);
  mk("path", { class: "nf", d: seg(P(RX, SY / 2, TOP + 3), P(RX, SY / 2, SC[2])) + seg(P(CWX, SY / 2, TOP + 3), P(CWX, SY / 2, SC[2])) }, g);
  const disc = (y: number, r: number) => circ(r, 28).map((q) => P(SC[0] + q.u, y, SC[2] + q.v));
  put(solid(g), { sil: poly(hull(disc(SY / 2 - 1.8, SR).concat(disc(SY / 2 + 1.8, SR)))), crease: poly(disc(SY / 2 + 1.8, SR - 1.4)) });
  const spokes = line("nf lo");
  mk("path", { class: "nf lo", d: poly(disc(SY / 2 + 1.8, 2.6)) }, g);

  // The floors, bottom to top: each an L-shaped slab, two columns at its
  // right holding up the next, and its number in dots on the landing by the door.
  const lands: Array<{ sil: SVGPathElement; dots: SVGEllipseElement[] }> = [];
  for (let f = 0; f < NF; f++) {
    const z = f * FH, sil = slab(FLOOR, z - T, z);
    if (f < NF - 1) for (const y of [-53, -15]) block([62, y, 68, y + 6], 1.5, 0.8, z, z + FH - T);
    const dots: SVGEllipseElement[] = [];
    for (let k = 0; k <= f; k++) { const d = flatDot(g, C, 0.8, "dot off"); place(d, P(37, CAR[1] - 3 - k * 3, z)); dots.push(d); }
    lands.push({ sil, dots });
  }

  const sp = spring(REST_Z, { k: value, c: 1.8 * Math.sqrt(value) });
  let drawn = NaN, chosen: number | null = null;

  function draw(z: number) {
    const zc = 3 * FH - z + 6, mid = (CAR[1] + CAR[3]) / 2;
    put(cw, prism(P, front, cwo, cwi, zc, zc + CWH));
    cwBands.setAttribute("d", [5, 9, 13].map((v) => seg(P(CW[0] + 0.6, CW[3], zc + v), P(CW[2] - 0.6, CW[3], zc + v))).join(""));
    cwRope.setAttribute("d", seg(P(CWX, SY / 2, zc + CWH), P(CWX, SY / 2, TOP)));
    put(car, prism(P, front, co, ci, z, z + CH));
    door.setAttribute("d", poly(rrect(CAR[1] + 3.5, z + 1.2, CAR[3] - 3.5, z + CH - 4, 1.2, 4).map((q) => P(CAR[2], q.u, q.v))));
    split.setAttribute("d", seg(P(CAR[2], mid, z + 1.2), P(CAR[2], mid, z + CH - 4)));
    put(head, prism(P, front, ho, hi, z + CH, z + CH + 2.4));
    rope.setAttribute("d", seg(P(RX, SY / 2, z + CH + 2.4), P(RX, SY / 2, TOP)));
    // the sheave turns as the rope runs over it
    const a = z / SR, y = SY / 2 + 1.8, at = (t: number, r: number) => P(SC[0] + Math.cos(t) * r, y, SC[2] + Math.sin(t) * r);
    spokes.setAttribute("d", [0, 1, 2, 3, 4, 5].map((k) => seg(at(a + k * Math.PI / 3, 2.6), at(a + k * Math.PI / 3, SR - 1.4))).join(""));
  }

  const B = register(stage, (dt) => {
    const m = stepS(sp, dt);
    if (sp.x !== drawn) { drawn = sp.x; draw(sp.x); }
    return m;
  });
  bag.add(B.unregister);

  // The floor under the pointer: its height read on the fixed column of the car's door, against the floors, which never move.
  const base = P(CAR[2], SY / 2, 0)[1], perZ = base - P(CAR[2], SY / 2, 1)[1];
  const pick = (p: Vec2) => clamp(Math.floor(((base - p[1]) / perZ + 8) / FH), 0, NF - 1);

  function choose(f: number) {
    if (f === chosen) return;
    chosen = f;
    sp.t = f < 0 ? REST_Z : f * FH;
    car.sil.classList.toggle("hi", f < 0);
    lands.forEach((l, i) => {
      l.sil.classList.toggle("hi", i === f);
      l.dots.forEach((d) => d.setAttribute("class", i === f ? "dot m" : "dot off"));
    });
    read.textContent = f < 0 ? "rest" : NAMES[f];
    B.wake();
  }
  choose(-1);

  bag.add(pointer(stage, { move: (p) => choose(pick(p)), leave: () => choose(-1) }));
  bag.add(() => svg.replaceChildren());

  return {
    set: (v) => { sp.k = v; sp.c = 1.8 * Math.sqrt(v); B.wake(); },
    destroy: bag.dispose,
  };
};
