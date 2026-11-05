import assert from "node:assert/strict";
import test from "node:test";
import * as A from "../kit/audit.mjs";

test("horizontal stiff tube resting on a grounded horizontal tube supports itself and mounted solids", () => {
  const base = A.tube([[0, 0, 0], [10, 0, 0]], 2, { name: "stand.base", ground: true });
  const upper = A.tube([[0, 0, 4], [10, 0, 4]], 2, { name: "upper" });
  const cross = A.tube([[5, -5, 8], [5, 5, 8]], 2, { name: "cross" });
  const cap = A.box([3, -1, 10], [7, 1, 12], { name: "cap" });
  assert.deepEqual(A.supports([cap], [base, upper, cross]), { loose: [], hanging: [], sunk: [] });
});

test("horizontal stiff tube separated from a wall beyond its flat end cap is reported hanging", () => {
  const wall = A.box([-4, -2, -2], [-1.8, 2, 2], { name: "stand.wall", ground: true });
  const pipe = A.tube([[0, 0, 0], [10, 0, 0]], 2, { name: "pipe" });
  const collar = A.box([4, -3, -3], [6, 3, 3], { name: "collar" });
  assert.ok(Math.abs(A.sdf(pipe, [-1.8, 0, 0]) - 1.8) < 1e-9);
  assert.deepEqual(A.supports([wall, collar], [pipe]), { loose: ["collar"], hanging: ["pipe"], sunk: [] });
});

test("horizontal stiff tube whose flat end cap touches a grounded wall is supported", () => {
  const wall = A.box([-4, -2, -2], [-0.05, 2, 2], { name: "stand.wall", ground: true });
  const pipe = A.tube([[0, 0, 0], [10, 0, 0]], 2, { name: "pipe" });
  const collar = A.box([4, -3, -3], [6, 3, 3], { name: "collar" });
  assert.deepEqual(A.supports([wall, collar], [pipe]), { loose: [], hanging: [], sunk: [] });
});

test("inclined stiff tubes detect perpendicular contact and reject perpendicular gaps", () => {
  const lower = A.tube([[0, 0, 0], [6, 0, 8]], 2, { name: "stand.lower", ground: true });
  const touching = A.tube([[-3.2, 0, 2.4], [2.8, 0, 10.4]], 2, { name: "touching" });
  const floating = A.tube([[-3.6, 0, 2.7], [2.4, 0, 10.7]], 2, { name: "floating" });
  assert.deepEqual(A.supports([], [lower, touching]), { loose: [], hanging: [], sunk: [] });
  assert.deepEqual(A.supports([], [lower, floating]), { loose: [], hanging: ["floating"], sunk: [] });
});

test("vertical stiff tubes and limp tubes preserve their support semantics", () => {
  const floor = A.box([-4, -4, -2], [4, 4, 0], { name: "stand.floor", ground: true });
  const column = A.tube([[0, 0, 0], [0, 0, 8]], 1.5, { name: "column" });
  const detached = A.tube([[0, 0, 10], [0, 0, 16]], 1.5, { name: "detached" });
  const cable = A.tube([[0, 0, 20], [10, 0, 20]], 1.5, { name: "cable", limp: true });
  assert.deepEqual(A.supports([floor], [column, detached, cable]), { loose: [], hanging: ["detached"], sunk: [] });
});
