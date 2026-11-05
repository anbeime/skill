import assert from "node:assert/strict";
import test from "node:test";
import * as A from "../kit/audit.mjs";

const taper = () => A.tube([[0, 0, 0], [10, 0, 0]], t => 1 + 2 * t);
const close = (actual, expected) => assert.ok(Math.abs(actual - expected) < 1e-12, `${actual} differs from ${expected}`);
test("the narrow portion of a taper does not invent a collision", () => {
  close(A.sdf(taper(), [1, 2, 0]), 0.8 / Math.sqrt(1.04));
});
test("the wide portion of a taper does not hide a collision", () => {
  close(A.sdf(taper(), [9, 2.5, 0]), -0.3 / Math.sqrt(1.04));
});
test("the actual conical surface has zero signed distance", () => {
  close(A.sdf(taper(), [1, 1.2, 0]), 0);
});
test("taper distance follows a rotated and translated tube frame", () => {
  const shape = A.tube([[5, 3, 2], [5, 13, 2]], [1, 3]);
  close(A.sdf(shape, [7, 4, 2]), 0.8 / Math.sqrt(1.04));
});
test("constant-radius cylinders retain their sides, caps and interior", () => {
  const shape = A.tube([[0, 0, 0], [10, 0, 0]], 2);
  close(A.sdf(shape, [5, 3, 0]), 1);
  close(A.sdf(shape, [-1, 0, 0]), 1);
  close(A.sdf(shape, [5, 0, 0]), -2);
});
test("taper end caps keep their true radii", () => {
  close(A.sdf(taper(), [-1, 0, 0]), 1);
  close(A.sdf(taper(), [11, 0, 0]), 1);
});
