import assert from "node:assert/strict";
import test from "node:test";
import * as A from "../kit/audit.mjs";
import * as G from "../kit/lathe.mjs";
const P = { origin: [0, 0], scale: 1, azimuth: 0, elevation: 0 };
const cam = A.cameraBasis(P);
const at = (screen, depth) => G.add3(G.mul3(cam.R, screen), G.mul3(cam.V, depth));
const inspect = (items) => A.overlapsOf(items, P, { step: 0.25, tolerance: 0.01, least: 0.01 });
const chain = (count) => Array.from({ length: count }, (_, i) => ({ name: `ball${i}`, key: 0, shapes: [A.ball(at(i * 1.5, -i * 0.5), 1)] }));
const assertRules = (overlaps, solved) => {
  for (const pair of overlaps.pairs) {
    const front = pair.front[0].area >= overlaps.least ? pair.a : pair.b;
    const back = front === pair.a ? pair.b : pair.a;
    assert.ok(solved.keys[front] - solved.keys[back] >= 0.02 - 1e-9);
  }
};
test("a 410-part acyclic drawn overlap chain converges without losing constraints", () => {
  const items = chain(410); const overlaps = inspect(items);
  assert.equal(overlaps.pairs.length, 409);
  assert.ok(overlaps.pairs.every((p) => p.front[0].area >= overlaps.least && p.front[1].area < overlaps.least));
  const solved = A.orderKeys(items, overlaps);
  assert.deepEqual(solved.dropped, []);
  assert.deepEqual(solved.cycles, []);
  assertRules(overlaps, solved);
});
test("an explicit final-round budget does not invent a victim once all rules are satisfied", () => {
  const items = chain(10); const overlaps = inspect(items);
  const solved = A.orderKeys(items, overlaps, { rounds: 9 });
  assert.deepEqual(solved.dropped, []);
  assertRules(overlaps, solved);
});
test("small acyclic figures preserve the existing zero-drop solution", () => {
  const items = chain(10); const overlaps = inspect(items); const solved = A.orderKeys(items, overlaps);
  assert.deepEqual(solved.dropped, []);
  assertRules(overlaps, solved);
  assert.ok(Math.abs(solved.keys[0] - 0.18) < 1e-12);
});
test("an actual three-item geometric cycle still drops its weakest conflicting rule", () => {
  const items = [
    { name: "a", key: 0, shapes: [A.ball(at(0, 3), 1), A.ball(at(20, 0), 1)] },
    { name: "b", key: 0, shapes: [A.ball(at(0, 0), 1), A.ball(at(10, 3), 1)] },
    { name: "c", key: 0, shapes: [A.ball(at(10, 0), 1), A.ball(at(20, 3), 1)] },
  ];
  const overlaps = inspect(items); assert.equal(overlaps.pairs.length, 3);
  const solved = A.orderKeys(items, overlaps);
  assert.equal(solved.rules, 3);
  assert.equal(solved.dropped.length, 1);
  assert.equal(solved.cycles.length, 0);
  for (const pair of overlaps.pairs) {
    const front = pair.front[0].area >= overlaps.least ? pair.a : pair.b;
    const back = front === pair.a ? pair.b : pair.a;
    if (solved.dropped.some((rule) => rule.front === front && rule.back === back)) continue;
    assert.ok(solved.keys[front] - solved.keys[back] >= 0.02 - 1e-9);
  }
});
