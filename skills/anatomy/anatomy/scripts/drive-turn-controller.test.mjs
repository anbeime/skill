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

for (const script of ["", "window.__isoTurn={}"])
  for (const action of ["turn", "orbit"])
    test(`${action} rejects a missing callable turn controller (${script || "absent"})`, async () => {
      const result = await run(out => [action === "turn" ? ["turn", 90] : ["orbit", out, 0, 90, 90], ["eval", "'AFTER_FAILED_TURN'"]], script);
      assert.equal(result.code, 1);
      assert.match(result.stderr, /requires window\.__isoTurn\.set/);
      assert.doesNotMatch(result.stdout, /AFTER_FAILED_TURN/);
      assert.equal(result.hasImage, false);
    });

const controller = "window.turns=[];window.__isoTurn={set(value){window.turns.push(value);document.querySelector('[data-readout]').textContent=JSON.stringify(value)}}";
test("turn preserves numeric, named-group and object poses", async () => {
  const result = await run([["turn", 90], ["turn", 0.5, "lift"], ["turn", {dial:45,lift:1}], ["eval", "window.turns"]], controller);
  assert.equal(result.code, 0);
  assert.match(result.stdout, /eval: \[90,\{"lift":0.5\},\{"dial":45,"lift":1\}\]/);
});

test("orbit still visits its requested poses and writes an image", async () => {
  const result = await run(out => [["orbit", out, 0, 90, 90], ["eval", "window.turns"]], controller);
  assert.equal(result.code, 0);
  assert.match(result.stdout, /eval: \[0,90\]/);
  assert.equal(result.hasImage, true);
});
