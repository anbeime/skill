import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { mkdtemp, rm, writeFile, access } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import test from "node:test";

const execute = promisify(execFile);
async function run(actions, script = "") {
  const directory = await mkdtemp(join(tmpdir(), "anatomy-driver-regression-"));
  try {
    const page = join(directory, "figure.html");
    const file = join(directory, "actions.json");
    const output = join(directory, "orbit.png");
    await writeFile(page, `<!doctype html><div class="iso-plate" style="width:240px;height:120px"><span data-readout>rest</span></div><script>${script}</script>`);
    await writeFile(file, JSON.stringify(typeof actions === "function" ? actions(output) : actions));
    let result;
    try { result = { code: 0, ...await execute(process.execPath, ["scripts/drive.mjs", page, "--actions", file], { timeout: 15000 }) }; }
    catch (error) { result = { code: error.code, stdout: error.stdout, stderr: error.stderr }; }
    result.hasImage = await access(output).then(() => true, () => false);
    console.log(JSON.stringify(result));
    return result;
  } finally { await rm(directory, { recursive: true, force: true }); }
}

for (const expression of ["false", "Promise.resolve(false)", "new Promise(()=>{})"])
  test(`until times out and stops after ${expression}`, async () => {
    const result = await run([["until", expression, 100], ["eval", "'AFTER_FAILED_WAIT'"]]);
    assert.equal(result.code, 1);
    assert.match(result.stderr, /until: timed out/);
    assert.doesNotMatch(result.stdout, /AFTER_FAILED_WAIT/);
  });

test("until awaits a delayed asynchronous condition", async () => {
  const result = await run([["until", "new Promise(resolve=>setTimeout(()=>{window.ready=true;resolve(true)},100))", 1000], ["eval", "window.ready"]]);
  assert.equal(result.code, 0);
  assert.match(result.stdout, /eval: true/);
});

test("until propagates a rejected asynchronous condition", async () => {
  const result = await run([["until", "Promise.reject(new Error('async condition failed'))", 1000], ["eval", "'AFTER_REJECTION'"]]);
  assert.equal(result.code, 1);
  assert.match(result.stderr, /async condition failed/);
  assert.doesNotMatch(result.stdout, /AFTER_REJECTION/);
});

for (const expression of ["true", "({ready:true})", "(()=>{})", "Promise.resolve({ready:true})"])
  test(`until preserves truthiness of ${expression}`, async () => {
    const result = await run([["until", expression, 1000], ["eval", "'AFTER_SUCCESS'"]]);
    assert.equal(result.code, 0);
    assert.match(result.stdout, /AFTER_SUCCESS/);
  });
