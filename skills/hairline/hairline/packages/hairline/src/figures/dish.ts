import { Cam, circ, facing, fit, hull, open, poly, prism, proj, rad, ringAt, rings, rrect, run, seg, type Ring, type Vec2, type Vec3 } from "../core/iso";
import { spring, stepS } from "../core/motion";
import { disposer, flatDot, mk, place, pointer, put, register, solid, type FigureMount, type Solid } from "../core/stage";

/**
 * Dish: a parabolic dish on a two-axis gimbal. A base plate engraved with an
 * azimuth scale, a turntable with an index dot, and a yoke whose two arms hold
 * the elevation axis; the dish hangs on it by two trunnions at its rim, with a
 * feed horn on three struts at its focus. The pointer aims the dish, as if it
 * stood in front of the screen: azimuth and elevation each ride a spring. The
 * bowl's outline is computed at every pose: the rim circle projected, and the
 * hull of the rim and the back. The reach is clamped so the dish always shows
 * its inside. At rest it looks off to the right, rim bright. The slider is the
 * azimuth reach, in degrees; elevation reaches half of it.
 *
 * The pattern: a continuous aim. Two springs, a clamped reach, a hit test that
 * reads only the pointer, and a paint order fixed by separating planes.
 */

const R = 26, FOC = 17, SK = 1.4, DEP = (R * R) / (4 * FOC), ZE = 46, W = 31, T = 5, ZB = 10, ZY = 16;
const AZ0 = 45, EL0 = 40, REST = [-20, 30], PIV: Vec3 = [0, 0, ZE];
const ax = (p: Vec3, q: Vec3, s: number): Vec3 => [p[0] + q[0] * s, p[1] + q[1] * s, p[2] + q[2] * s];
const dot3 = (p: Vec3, q: Vec3) => p[0] * q[0] + p[1] * q[1] + p[2] * q[2];

type Frame = { th: number; h: Vec3; e: Vec3; a: Vec3; u: Vec3 };
/** An aim's frame: h and e on the ground (e is the elevation axis), a the dish's axis, u the rim's up. */
function frame(th: number, ph: number): Frame {
  const t = rad(th), f = rad(ph), c = Math.cos(f), s = Math.sin(f);
  const h: Vec3 = [Math.cos(t), Math.sin(t), 0], e: Vec3 = [-Math.sin(t), Math.cos(t), 0];
  return { th, h, e, a: [h[0] * c, h[1] * c, s], u: [-h[0] * s, -h[1] * s, c] };
}
/** A point of the dish: `along` its axis from the rim's centre, rho out from it at angle psi. */
const onDish = (F: Frame, along: number, rho: number, psi: number) => ax(ax(ax(PIV, F.a, along), F.e, rho * Math.cos(psi)), F.u, rho * Math.sin(psi));
/** A circle of n points about centre c, in the plane of x and y. */
const disc = (c: Vec3, x: Vec3, y: Vec3, r: number, n: number) => Array.from({ length: n }, (_, i) => ax(ax(c, x, r * Math.cos((2 * Math.PI * i) / n)), y, r * Math.sin((2 * Math.PI * i) / n)));
/** A ring drawn in the (h, e) frame turned onto the ground. */
const turn = (ring: Ring, F: Frame): Ring => ring.map((q) => ({
  u: q.u * F.h[0] + q.v * F.e[0], v: q.u * F.h[1] + q.v * F.e[1], nu: q.nu * F.h[0] + q.nv * F.e[0], nv: q.nu * F.h[1] + q.nv * F.e[1],
}));

type Side = {
  s: number; g: SVGGElement; near: boolean | null;
  ring: SVGPathElement; arm: Solid; trun: SVGPathElement;
  foot: Ring; top: Ring; inner: Ring;
};

export const mount: FigureMount = ({ stage, svg, read }, value) => {
  const bag = disposer();
  let reach = value, over: Vec2 | null = null;

  // Fitted to the four corners of the widest reach, and rest, so nothing leaves the frame.
  const C = Cam(45, 0.5, 2.5), pts: Vec3[] = [[-30, -30, 0], [30, 30, 0], [30, -30, 0], [-30, 30, 0]];
  for (const [th, ph] of [[-25, 5], [-25, 75], [115, 5], [115, 75], REST]) {
    const F = frame(th, ph);
    pts.push(...disc(PIV, F.e, F.u, R, 16), onDish(F, FOC - DEP + 3, 0, 0));
    for (const s of [-1, 1]) pts.push(ax(ax(PIV, F.e, s * (W + T / 2)), [0, 0, 1], 6));
  }
  fit(C, pts, 200, 166);
  const P = proj(C), front = facing(C), Pv = (q: Vec3) => P(q[0], q[1], q[2]);
  // the direction toward the camera, from the projection itself
  const o = P(0, 0, 0), cx = P(1, 0, 0), cy = P(0, 1, 0), cz = P(0, 0, 1);
  const r1 = [cx[0] - o[0], cy[0] - o[0], cz[0] - o[0]], r2 = [cx[1] - o[1], cy[1] - o[1], cz[1] - o[1]];
  const cross: Vec3 = [r1[1] * r2[2] - r1[2] * r2[1], r1[2] * r2[0] - r1[0] * r2[2], r1[0] * r2[1] - r1[1] * r2[0]];
  const vl = Math.hypot(...cross) * Math.sign(cross[2]);
  const VD = cross.map((x) => x / vl) as Vec3;

  // Static, back to front: the base, its azimuth scale, the turntable.
  const g = mk("g", {}, svg);
  const [br, bi] = rings(-30, -30, 30, 30, 9, 2);
  put(solid(g), prism(P, front, br, bi, 0, 5));
  for (let i = 0; i < 36; i++) {
    const t = (i / 36) * 2 * Math.PI, r = i % 9 === 0 ? 26.5 : 25.5;
    place(flatDot(g, C, i % 9 === 0 ? 0.75 : 0.5, "dot off"), P(r * Math.cos(t), r * Math.sin(t), 5));
  }
  put(solid(g), prism(P, front, circ(20, 48), circ(18.8, 48), 5, ZB));
  const index = flatDot(g, C, 0.8, "dot m");

  // Turning with the azimuth: the yoke's beam, then each side's arm, bearing and trunnion, in an order set per frame.
  const beam = solid(g);
  const yb = W + T / 2 + 1, [bmr, bmi] = rings(-9, -yb, 9, yb, 4, 1.4);
  const dishG = mk("g", {}, g);
  const sides: Side[] = [-1, 1].map((s) => {
    const sg = mk("g", {}, g);
    return {
      s, g: sg, near: null,
      ring: mk("path", { class: "nf" }, sg), arm: solid(sg), trun: mk("path", { class: "sil" }, sg),
      foot: rrect(-8, s * W - T / 2, 8, s * W + T / 2, 2.5, 4),
      top: rrect(-5.5, s * W - T / 2, 5.5, s * W + T / 2, 2.5, 4),
      inner: rrect(-4.5, s * W - T / 2 + 1, 4.5, s * W + T / 2 - 1, 1.5, 4),
    };
  });

  // The dish: its outline, a panel seam and the hub at its vertex seen through the aperture, the rim, the struts, the feed.
  const outline = mk("path", { class: "sil" }, dishG), seam = mk("path", { class: "nf lo" }, dishG), hubR = mk("path", { class: "nf lo" }, dishG);
  const rim = mk("path", { class: "nf hi" }, dishG), struts = mk("path", { class: "nf" }, dishG);
  const feed = solid(dishG);
  const BACK = [0, 0.35, 0.6, 0.78, 0.9, 0.97, 1];

  /** The seam at rho: the run of it seen through the aperture, its ends cut where the sight line meets the rim. */
  function seen(F: Frame, rho: number, n: number) {
    const along = (rho * rho) / (4 * FOC) - DEP, t = -along / dot3(F.a, VD), q: Vec3[] = [], s: number[] = [];
    for (let i = 0; i < n; i++) {
      q.push(onDish(F, along, rho, (2 * Math.PI * i) / n));
      const hit = ax(q[i], VD, t);
      s.push(R - Math.hypot(hit[0] - PIV[0], hit[1] - PIV[1], hit[2] - PIV[2]));
    }
    if (s.every((x) => x > 0)) return poly(q.map(Pv));
    const i0 = s.findIndex((x, i) => x > 0 && s[(i + n - 1) % n] <= 0);
    if (i0 < 0) return "";
    const cut = (i: number, j: number) => Pv(ax(q[i], [q[j][0] - q[i][0], q[j][1] - q[i][1], q[j][2] - q[i][2]], s[i] / (s[i] - s[j])));
    const out = [cut((i0 + n - 1) % n, i0)];
    let i = i0;
    while (s[i] > 0) { out.push(Pv(q[i])); i = (i + 1) % n; }
    out.push(cut((i + n - 1) % n, i));
    return open(out);
  }

  let drawn = "";
  function draw(th: number, ph: number) {
    const key = th.toFixed(3) + "," + ph.toFixed(3);
    if (key === drawn) return;
    drawn = key;
    const F = frame(th, ph);
    place(index, P(18 * F.h[0], 18 * F.h[1], ZB));
    put(beam, prism(P, front, turn(bmr, F), turn(bmi, F), ZB, ZY));
    // a side whose outer face looks at the camera paints after the dish, inside out; the other before it, outside in
    for (const sd of sides) {
      const near = sd.s * dot3(F.e, VD) > 0;
      if (near !== sd.near) {
        sd.near = near;
        if (near) { sd.g.append(sd.trun, sd.arm.g, sd.ring); dishG.after(sd.g); }
        else { sd.g.append(sd.ring, sd.arm.g, sd.trun); dishG.before(sd.g); }
      }
      put(sd.arm, {
        sil: poly(hull(ringAt(P, turn(sd.foot, F), ZY).concat(ringAt(P, turn(sd.top, F), ZE + 6)))),
        crease: open(ringAt(P, run(turn(sd.inner, F), front), ZE + 6)),
      });
      const zz: Vec3 = [0, 0, 1], out = ax(PIV, F.e, sd.s * (W + T / 2));
      sd.ring.setAttribute("d", poly(disc(out, F.h, zz, 3.4, 24).map(Pv)));
      sd.trun.setAttribute("d", poly(hull(disc(ax(PIV, F.e, sd.s * R), F.h, zz, 2.2, 16).concat(disc(ax(PIV, F.e, sd.s * (W - T / 2)), F.h, zz, 2.2, 16)).map(Pv))));
    }
    // the bowl: its outline is the hull of the rim and the back, a skin SK thick; the rim is all seen, as the reach keeps the inside to the camera
    const lip = disc(PIV, F.e, F.u, R, 72), back: Vec3[] = [];
    for (const f of BACK) for (let i = 0; i < 40; i++) back.push(onDish(F, (f * f * R * R) / (4 * FOC) - DEP - SK, f * R, (2 * Math.PI * i) / 40));
    outline.setAttribute("d", poly(hull(lip.concat(back).map(Pv))));
    seam.setAttribute("d", seen(F, 0.62 * R, 48));
    hubR.setAttribute("d", seen(F, 3.2, 20));
    rim.setAttribute("d", poly(lip.map(Pv)));
    const mouth = onDish(F, FOC - DEP - 3, 0, 0), tail = onDish(F, FOC - DEP + 3, 0, 0);
    struts.setAttribute("d", [90, 210, 330].map((d) => seg(Pv(onDish(F, 0, R, rad(d))), Pv(mouth))).join(""));
    put(feed, {
      sil: poly(hull(disc(mouth, F.e, F.u, 3.6, 16).concat(disc(tail, F.e, F.u, 2.4, 16)).map(Pv))),
      crease: poly(disc(tail, F.e, F.u, 1.3, 16).map(Pv)),
    });
  }

  const az = spring(REST[0], { eps: 0.01 }), el = spring(REST[1], { eps: 0.01 });
  const B = register(stage, (dt) => {
    const a = stepS(az, dt), b = stepS(el, dt);
    draw(az.x, el.x);
    return a || b;
  });
  bag.add(B.unregister);

  // The aim reads only the pointer's offset from the axis on screen, never what is drawn: nothing can flicker.
  const hub = P(0, 0, ZE);
  function retarget() {
    if (over) {
      az.t = AZ0 - reach * Math.tanh((over[0] - hub[0]) / 120);
      el.t = EL0 + (reach / 2) * Math.tanh((hub[1] - over[1]) / 90);
      read.textContent = `az ${Math.round((az.t + 360) % 360)} · el ${Math.round(el.t)}`;
    } else { az.t = REST[0]; el.t = REST[1]; read.textContent = "rest"; }
    B.wake();
  }

  bag.add(pointer(stage, {
    move: (p) => { over = p; retarget(); },
    leave: () => { over = null; retarget(); },
  }));
  bag.add(() => svg.replaceChildren());

  return {
    set: (v) => { reach = v; if (over) retarget(); },
    destroy: bag.dispose,
  };
};
