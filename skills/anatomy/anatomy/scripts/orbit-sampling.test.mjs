import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import test from "node:test";

const execute = promisify(execFile);
const page = "examples/turning-dial/turning-dial-verify-light.html";
async function run(args) {
  try { return { code: 0, ...await execute(process.execPath, ["scripts/turn-check.mjs", page, ...args], { timeout: 60000 }) }; }
  catch (error) { return { code: error.code, stdout: error.stdout, stderr: error.stderr }; }
}
for (const step of ["NaN", "Infinity", "-1", "721"])
  test(`rejects orbit step ${step} instead of passing an empty sweep`, async () => {
    const result = await run(["--order", "--step", step]);
    assert.equal(result.code, 1);
    assert.match(result.stderr, /--step must be a finite number/);
    assert.doesNotMatch(result.stdout, /turn check passed/);
  });
test("rejects an empty explicit pose list instead of auditing zero states", async () => {
  const directory = await mkdtemp(join(tmpdir(), "anatomy-orbit-states-"));
  try {
    const file = join(directory, "states.json"); await writeFile(file, "[]");
    const result = await run(["--order", "--states", file]);
    assert.equal(result.code, 1); assert.match(result.stderr, /nonempty JSON list/);
    assert.doesNotMatch(result.stdout, /turn check passed/);
  } finally { await rm(directory, { recursive: true, force: true }); }
});
test("rejects a nonfinite fine step instead of silently skipping the second difference", async () => {
  const result = await run(["--pops", "--step", "360", "--fine", "NaN"]);
  assert.equal(result.code, 1); assert.match(result.stderr, /--fine must be a finite number/);
  assert.doesNotMatch(result.stdout, /turn check passed/);
});
test("preserves a valid native orbit sweep and its planted control", async () => {
  const result = await run(["--order", "--step", "360"]);
  assert.equal(result.code, 0); assert.match(result.stdout, /order: 1 states/);
  assert.match(result.stdout, /order control.*fails as it should/); assert.match(result.stdout, /turn check passed/);
});

test("preserves a nonempty explicit pose list and its planted control", async () => {
  const directory = await mkdtemp(join(tmpdir(), "anatomy-orbit-states-"));
  try {
    const file = join(directory, "states.json"); await writeFile(file, "[0,90]");
    const result = await run(["--order", "--states", file]);
    assert.equal(result.code, 0); assert.match(result.stdout, /order: 2 states/);
    assert.match(result.stdout, /order control.*fails as it should/); assert.match(result.stdout, /turn check passed/);
  } finally { await rm(directory, { recursive: true, force: true }); }
});
