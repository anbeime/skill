import { expect, test } from "vitest";
import { Cam, fit, proj, rad, unproj } from "../src/core/iso";
import { BLK, DETENT, HOME, detent, paintOrder } from "../src/figures/turntable-geometry";

/**
 * The parts of Hairline that can be checked without a browser. The painter's
 * order is the one that can go wrong somewhere in a full turn and look right
 * everywhere else, so it is swept all the way round at the three elevations
 * the turntable reaches (20° to 40°, resting at 30°).
 */
const close = (a: number, b: number, eps = 1e-6) => expect(Math.abs(a - b)).toBeLessThan(eps);

test("turntable order is a full permutation with no forced pick, all the way round", () => {
  for (const el of [20, 30, 40]) {
    const k = Math.sin(rad(el));
    for (let az = 0; az <= 360; az += 0.5) {
      const { order, forced } = paintOrder(BLK, Math.sin(rad(az)), Math.cos(rad(az)), k);
      expect(forced, `cycle at az ${az} el ${el}`).toBe(0);
      expect(order.slice().sort((a, b) => a - b)).toEqual(BLK.map((_, i) => i));
    }
  }
});

test("a stacked column paints bottom first", () => {
  // blocks 0 and 1 are column 0, and 5 and 6 are column 4; lower first at every angle
  for (let az = 0; az < 360; az += 7.5) {
    const o = paintOrder(BLK, Math.sin(rad(az)), Math.cos(rad(az)), 0.5).order;
    expect(o.indexOf(0)).toBeLessThan(o.indexOf(1));
    expect(o.indexOf(5)).toBeLessThan(o.indexOf(6));
  }
});

test("detent seats on the nearest quarter turn from HOME", () => {
  expect(HOME).toBe(45);
  expect(DETENT).toBe(90);
  expect(detent(45)).toBe(45);
  expect(detent(89)).toBe(45);
  expect(detent(91)).toBe(135);
  expect(detent(200)).toBe(225);
  expect(detent(-44)).toBe(-45);
  expect(detent(400)).toBe(405);
  for (let a = -720; a <= 720; a += 3.7) {
    const d = detent(a);
    expect(Math.abs(d - a)).toBeLessThanOrEqual(45);
    expect((((d - HOME) % 90) + 90) % 90).toBe(0);
  }
});

test("unproj inverts proj on the plane it is given", () => {
  for (const [az, k, S] of [[45, 0.5, 1.62], [0, 0.34, 2], [123, 0.64, 1.3], [-80, 0.5, 1.85]]) {
    const C = Cam(az, k, S);
    fit(C, [[0, 0, 0], [100, 80, 0], [0, 0, 40]], 200, 160);
    const P = proj(C);
    for (const [x, y, z] of [[0, 0, 0], [12.5, -40, 0], [80, 33, 17], [-20, 60, -9]]) {
      const [sx, sy] = P(x, y, z);
      const [ux, uy] = unproj(C, sx, sy, z);
      close(ux, x); close(uy, y);
    }
  }
});

test("fit centres the box it is given", () => {
  const C = Cam(45, 0.5, 1.58);
  const pts: [number, number, number][] = [[-6, -6, -5], [132, 132, -5], [132, -6, -5], [-6, 132, -5], [0, 0, 43.5]];
  fit(C, pts, 200, 166);
  const P = proj(C), xs = pts.map((p) => P(...p)[0]), ys = pts.map((p) => P(...p)[1]);
  close((Math.min(...xs) + Math.max(...xs)) / 2, 200);
  close((Math.min(...ys) + Math.max(...ys)) / 2, 166);
});
