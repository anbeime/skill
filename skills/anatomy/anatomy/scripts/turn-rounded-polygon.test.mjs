import assert from "node:assert/strict";
import test from "node:test";
import * as G from "../kit/lathe.mjs";
import { roundedPolygon, turning } from "../kit/turn-build.mjs";
const square = [[0, 0], [10, 0], [10, 10], [0, 10]];
const extent = (ring, axis) => [Math.min(...ring.map((p) => p[axis])), Math.max(...ring.map((p) => p[axis]))];
test("a repeated vertex does not change the rounded outline", () => {
  const expected = roundedPolygon(square, 1, 2);
  assert.equal(expected.length, 12);
  assert.deepEqual(roundedPolygon([[0, 0], [10, 0], [10, 0], [10, 10], [0, 10]], 1, 2), expected);
  assert.deepEqual(roundedPolygon([[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]], 1, 2), expected);
  assert.deepEqual(roundedPolygon([[0, 0], [0, 0], [0, 0], [10, 0], [10, 10], [0, 10]], 1, 2), expected);
});
test("a repeated vertex keeps the rounded outline inside the polygon", () => {
  const ring = roundedPolygon([[0, 0], [10, 0], [10, 0], [10, 10], [0, 10]], 1, 2);
  assert.deepEqual(extent(ring, 0), [0, 10]);
  assert.deepEqual(extent(ring, 1), [0, 10]);
});
test("a prism with a repeated vertex and a corner radius stays inside its polygon", () => {
  const T = turning({ origin: [0, 0], scale: 1, azimuth: 45, elevation: 30 }); T.layer("all");
  const F = G.frameAlong([0, 0, 0], [0, 0, 1]);
  const part = T.prism({ name: "block", F, s0: 0, s1: 2, polygon: [[0, 0], [4, 0], [4, 0], [4, 4], [0, 4]], round: 1 });
  assert.deepEqual(extent(part.world.ring, 0), [0, 4]);
  assert.deepEqual(extent(part.world.ring, 1), [0, 4]);
});
