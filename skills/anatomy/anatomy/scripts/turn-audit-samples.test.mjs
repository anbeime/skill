import assert from "node:assert/strict";
import test from "node:test";
import { samplesOf } from "../kit/turn-audit.mjs";
const clip = (from, to) => ({ from, to, periodic: false });
test("a clip is sampled through its final instant and never past it", () => {
  for (const [from, to, frame] of [[0, 1, 0.4], [0, 1, 0.3], [0, 0.42, 1 / 60], [0.5, 1.01, 1 / 60], [0, 2.5, 4 / 60]]) {
    const xs = samplesOf(clip(from, to), frame);
    assert.equal(xs[0], from);
    assert.equal(xs[xs.length - 1], to);
    assert.ok(xs.every((x, i) => x >= from && x <= to && (i === 0 || x > xs[i - 1])), `${from}..${to} by ${frame}: ${xs}`);
    assert.ok(xs.every((x, i) => i === 0 || x - xs[i - 1] <= frame + 1e-9));
  }
});
test("a clip whose length is a whole number of frames keeps its frames", () => {
  assert.deepEqual(samplesOf(clip(0, 1), 0.25), [0, 0.25, 0.5, 0.75, 1]);
  assert.equal(samplesOf(clip(0, 1), 1 / 60).length, 61);
  assert.equal(samplesOf(clip(0, 1.5), 1 / 60).length, 91);
});
test("an empty clip has a single sample", () => {
  assert.deepEqual(samplesOf(clip(2, 2), 1 / 60), [2]);
});
test("a periodic sweep still stops one frame short of the repeat", () => {
  const xs = samplesOf({ from: 0, to: 360, periodic: true }, 90);
  assert.deepEqual(xs, [0, 90, 180, 270]);
  assert.equal(samplesOf({ from: 0, to: 360, periodic: true }, 0.3).length, 1200);
});
