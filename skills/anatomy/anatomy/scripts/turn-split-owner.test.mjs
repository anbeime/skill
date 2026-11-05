import assert from "node:assert/strict";
import test from "node:test";
import * as A from "../kit/audit.mjs";
import * as G from "../kit/lathe.mjs";
import { turning } from "../kit/turn-build.mjs";
import { TURN } from "../kit/turn.mjs";
import { posed } from "../kit/turn-audit.mjs";
function fixture(kind, owner = "pipe") {
  const T = turning({ origin: [0, 0], scale: 1, azimuth: 45, elevation: 30 }); T.layer("all");
  const group = T.group("assembly", { turn: { pivot: [5, 2] } });
  const F = G.frameAlong([0, 0, 0], [0, 0, 1]);
  const base = { name: "ferrule", owner, group, F, s0: 0, s1: 10 };
  const part = kind === "prism" ? T.prism({ ...base, polygon: [[-2, -2], [2, -2], [2, 2], [-2, 2]] }) : T.round({ ...base, r: 2, ...(kind === "default round" ? {} : { fixed: false }) });
  const tube = A.tube([[0, 0, -2], [0, 0, 12]], 0.5, { name: "pipe", owner: "pipe" });
  return { T, part, tube };
}
for (const kind of ["prism", "round", "default round"]) test(`split ${kind} preserves explicit ownership and its pipe clearance`, () => {
  const { T, part, tube } = fixture(kind);
  assert.deepEqual(A.clearances([tube], part.shapes), []);
  const halves = T.split(part, { n: [0, 0, 1], d: 5 });
  assert.equal(halves.length, 2);
  assert.ok(halves.every((half) => half.owner === "pipe" && half.shapes.every((shape) => shape.owner === "pipe")));
  assert.deepEqual(A.clearances([tube], halves.flatMap((half) => half.shapes)), []);
  T.build();
  const scene = TURN.prepare(T.data, { unit: 1 });
  for (const angle of [0, 45, 90, 180]) {
    const cams = TURN.cams(scene, { assembly: angle });
    const group = T.groups[0];
    const pose = { R: cams[group.index].R, t: cams[group.index].t, origin: group.origin };
    const shapes = halves.flatMap((half) => half.shapes.map((shape) => posed(shape, pose)));
    const original = posed(part.shapes[0], pose);
    assert.deepEqual(A.clearances([posed(tube, pose)], shapes), []);
    for (const z of [2.5, 7.5]) {
      const a = angle * Math.PI / 180;
      const point = [5 - 4 * Math.cos(a) + 2 * Math.sin(a), 2 - 4 * Math.sin(a) - 2 * Math.cos(a), z];
      const distance = Math.min(...shapes.map((shape) => A.sdf(shape, point)));
      assert.ok(distance < 0);
      assert.ok(Math.abs(distance - A.sdf(original, point)) < 1e-8);
    }
    for (const run of scene.runs) {
      const frame = TURN.emit(run, cams[run.group], TURN.frame(run));
      assert.ok(frame.d.some((path) => typeof path === "string" && path.length));
    }
  }
});
test("an unrelated pipe still reports real penetration of split fittings", () => {
  for (const kind of ["prism", "round", "default round"]) {
    const { T, part, tube } = fixture(kind, "other");
    const halves = T.split(part, { n: [0, 0, 1], d: 5 });
    const failures = A.clearances([tube], halves.flatMap((half) => half.shapes));
    assert.equal(failures.length, 2);
    assert.ok(failures.every((failure) => failure.kind === "through" && failure.clearance < 0));
  }
});
test("unowned split parts retain normal collision checking", () => {
  for (const kind of ["prism", "round", "default round"]) {
    const { T, part, tube } = fixture(kind, null);
    const halves = T.split(part, { n: [0, 0, 1], d: 5 });
    assert.ok(halves.every((half) => !half.owner && half.shapes.every((shape) => !shape.owner)));
    assert.equal(A.clearances([tube], halves.flatMap((half) => half.shapes)).length, 2);
  }
});
