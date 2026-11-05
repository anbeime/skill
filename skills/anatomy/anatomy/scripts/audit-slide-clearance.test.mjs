import assert from "node:assert/strict";
import test from "node:test";
import * as A from "../kit/audit.mjs";
import * as G from "../kit/lathe.mjs";
const P = { origin: [0, 0], scale: 1, azimuth: 45, elevation: 30 };
const F = G.frameAlong([0, 0, 0], [0, 0, 1]);
function scene(axis = [0, 0, 1]) {
  const frame = G.frameAlong([0, 0, 0], axis);
  const move = G.mul3(axis, 8);
  const rod = A.slide(frame, 0, 2, 1, { name: "piston", move, piece: "piston" });
  const obstacle = A.disc(frame, 6, 8, 2, { name: "obstacle" });
  const drawn = G.rodOut(frame, 0, 2, 1, P, { stroke: 8 });
  assert.equal(drawn.reach, 10);
  assert.ok(drawn.paths.fill.length > 0 && drawn.clip.length > 0);
  return { rod, obstacle, frame };
}
for (const axis of [[0, 0, 1], [1, 0, 0]]) test(`native solid clearance checks an extending rod along ${axis}`, () => {
  const { rod, obstacle, frame } = scene(axis);
  const state = { label: "stroke", shares: { piston: 1 } };
  const posed = A.moved(rod, A.offsetOf(rod, state));
  const inside = G.add3(frame.o, G.mul3(frame.a, 7));
  assert.equal(posed.slide.to, 10);
  assert.ok(A.sdf(posed, inside) < -0.9 && A.sdf(obstacle, inside) < -0.9);
  const result = A.solidClearances([rod, obstacle], { state, spacing: 0.2, sunk: 0.2 });
  assert.equal(result.length, 1);
  assert.equal(result[0].tube, "piston");
  assert.equal(result[0].other, "obstacle");
  assert.equal(result[0].state, "stroke");
  assert.ok(result[0].clearance < -0.9);
});
test("native recorder audit reports an extending rod with a stationary obstacle in either input order", () => {
  const { rod, obstacle } = scene();
  for (const shapes of [[rod, obstacle], [obstacle, rod]]) {
    const R = A.recorder(P, { order: ["piston"] });
    for (const shape of shapes) R.solid(shape);
    const result = A.audit(R, P, { frames: [], apart: true });
    assert.equal(result.apart.length, 1);
    assert.ok(result.apart[0].clearance <= -0.5);
    assert.ok(A.failures(result) > 0);
  }
});
test("native solid clearance preserves rest, intermediate and retracted rod controls", () => {
  const { rod, obstacle } = scene();
  for (const state of [0, 0.4, -0.1]) assert.deepEqual(A.solidClearances([rod, obstacle], { state, spacing: 0.2, sunk: 0.2 }), []);
});
test("native solid clearance preserves translated solid penetration detection", () => {
  const { obstacle } = scene();
  const moving = A.ball([0, 0, 1], 1, { name: "moving", move: [0, 0, 6] });
  const result = A.solidClearances([moving, obstacle], { state: 1, spacing: 0.2, sunk: 0.2 });
  assert.equal(result.length, 1);
  assert.ok(result[0].clearance < -0.9);
});
test("native sliding clearance preserves a seated host exemption", () => {
  const { rod, obstacle } = scene();
  rod.seated = true;
  rod.cut = obstacle;
  assert.deepEqual(A.solidClearances([rod, obstacle], { state: 1, spacing: 0.2, sunk: 0.2 }), []);
});
