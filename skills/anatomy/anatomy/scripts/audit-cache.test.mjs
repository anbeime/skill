import assert from "node:assert/strict";
import test from "node:test";
import * as A from "../kit/audit.mjs";

function fixture(move = [1, 0, 0]) {
  return [
    A.box([0, 0, 0], [2, 2, 2], { name: "moving", move, piece: "moving" }),
    A.box([1.7, 0.6, 0.6], [2.2, 1.4, 1.4], { name: "fixed" }),
  ];
}
const inspect = (shapes, options = {}) => A.solidClearances(shapes, { state: 1, sunk: 0.05, ...options });
test("rebuilds the surface grid when the opted-in cell size changes", () => {
  const shapes = fixture();
  assert.equal(inspect(shapes, { cell: 0.1 }).length, 1);
  const cached = inspect(shapes);
  const fresh = inspect(fixture());
  assert.equal(cached.length, 1);
  assert.deepEqual(cached, fresh);
  assert.ok(Math.abs(cached[0].clearance + 0.8) < 1e-12);
});
test("refines surface samples when the opted-in spacing changes", () => {
  const shapes = fixture(); inspect(shapes, { spacing: 2 });
  const refined = inspect(shapes, { spacing: 0.1 });
  const fresh = inspect(fixture(), { spacing: 0.1 });
  assert.deepEqual(refined, fresh);
  assert.ok(Math.abs(refined[0].clearance + 0.8) < 1e-12);
});
test("preserves repeated default audits of the same moving overlap", () => {
  const shapes = fixture(); const first = inspect(shapes);
  assert.equal(first.length, 1); assert.deepEqual(inspect(shapes), first);
});
test("keeps a separated motion clear across sampling options", () => {
  const shapes = fixture([-1, 0, 0]);
  assert.deepEqual(inspect(shapes, { cell: 0.1 }), []);
  assert.deepEqual(inspect(shapes), []);
  assert.deepEqual(inspect(shapes, { spacing: 0.1 }), []);
});
