import assert from "node:assert/strict";
import test from "node:test";
import * as A from "../kit/audit.mjs";
import * as G from "../kit/lathe.mjs";
const F = G.frameAlong([0, 0, 0], [0, 0, 1]);
const radius = (s) => 2 + Math.sin(2 * Math.PI * s / 10);
const slope = (s) => Math.cos(2 * Math.PI * s / 10) * 2 * Math.PI / 10;
const profile = [[0, 2], [10, 2]];
const radialAt = (points, s) => {
  const index = points.findIndex((p) => p[0] >= s);
  if (!index) return points[0][1];
  const [a, ra] = points[index - 1]; const [b, rb] = points[index];
  return ra + (rb - ra) * (s - a) / (b - a);
};
test("inflected analytic recording follows the actual band side geometry", () => {
  const bands = G.bandsOf(profile, [], F, { origin: [0, 0], scale: 10 }, { radius, slope });
  const recorded = A.traced(profile, { radius });
  const actual = bands.sidesOf().points.flat();
  const bulge = actual.filter((p) => Math.abs(p[2] - 2.5) < 1e-8);
  assert.equal(bulge.length, 2);
  for (const p of bulge) assert.ok(Math.abs(radialAt(recorded, p[2]) - Math.hypot(p[0], p[1])) <= 0.02);
});
test("analytic tracing keeps bulge points inside the recorded solid", () => {
  assert.ok(A.sdf(A.solid(F, profile, { radius }), [0, 2.5, 2.5]) < 0);
});
test("analytic tracing keeps neck points outside the recorded solid", () => {
  assert.ok(A.sdf(A.solid(F, profile, { radius }), [0, 1.5, 7.5]) > 0);
});
test("smooth Hermite inflection retains its quarter-span curvature", () => {
  const knots = [[0, 2, 1], [1, 2, 1], [2, 3, 1], [3, 3, 1]];
  const curve = G.profileCurve(knots);
  assert.ok(Math.abs(radialAt(A.traced(knots), 1.25) - curve.radius(1.25)) <= 0.02);
  assert.ok(Math.abs(radialAt(A.traced(knots), 1.75) - curve.radius(1.75)) <= 0.02);
});
test("constant and linear radius controls keep their exact two endpoints", () => {
  assert.deepEqual(A.traced([[0, 2], [10, 2]], { radius: () => 2 }), [[0, 2], [10, 2]]);
  assert.deepEqual(A.traced([[0, 1], [10, 3]], { radius: (s) => 1 + s / 5 }), [[0, 1], [10, 3]]);
});
test("explicit zero recursion depth retains the requested coarse profile", () => {
  assert.deepEqual(A.traced(profile, { radius, depth: 0 }), profile);
});
