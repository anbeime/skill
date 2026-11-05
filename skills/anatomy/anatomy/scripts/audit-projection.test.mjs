import assert from "node:assert/strict";
import test from "node:test";
import * as A from "../kit/audit.mjs";
const projection = (azimuth, elevation, scale = 1) => ({ origin: [0, 0], scale, azimuth, elevation });
const options = { step: 0.5, tolerance: 0.1, least: 0.25 };
const fixture = () => [{ name: "body", key: 0, shapes: [A.cylinder(0, 0, 2, 0, 10)] }, { name: "probe", key: 0, shapes: [A.ball([1.5, 0, 5], 1)] }];
for (const [name, before, after] of [
  ["azimuth reversal", projection(45, 30), projection(180, 30)],
  ["elevation change", projection(45, 30), projection(45, 60)],
  ["side view to oblique", projection(0, 0), projection(45, 30)],
]) test(`reused body ray geometry matches a fresh build after ${name}`, () => {
  const items = fixture();
  A.overlapsOf(items, before, options);
  const reused = A.overlapsOf(items, after, options);
  const fresh = A.overlapsOf(fixture(), after, options);
  assert.equal(fresh.pairs.length, 1);
  assert.deepEqual(reused, fresh);
});
test("azimuth reversal retains the physically nearer body in the key solver", () => {
  const items = fixture();
  A.overlapsOf(items, projection(45, 30), options);
  const solved = A.orderKeys(items, A.overlapsOf(items, projection(180, 30), options));
  assert.equal(solved.cycles.length, 0);
  assert.ok(solved.keys[0] > solved.keys[1]);
});
test("repeated identical projections keep identical depth results", () => {
  const items = fixture(); const P = projection(45, 30);
  const first = A.overlapsOf(items, P, options);
  assert.equal(first.pairs.length, 1);
  assert.deepEqual(A.overlapsOf(items, P, options), first);
});
test("scale and origin changes keep the unchanged camera direction valid", () => {
  const items = fixture(); A.overlapsOf(items, projection(45, 30), options);
  const P = { ...projection(45, 30, 2), origin: [20, 30] };
  assert.deepEqual(A.overlapsOf(items, P, options), A.overlapsOf(fixture(), P, options));
});
