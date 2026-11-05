import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import { fileURLToPath } from "node:url";
import test from "node:test";

const execute = promisify(execFile);
const drive = fileURLToPath(new URL("drive.mjs", import.meta.url));

async function run(actions) {
  const directory = await mkdtemp(join(tmpdir(), "anatomy-drive-actions-"));
  try {
    const page = join(directory, "figure.html");
    const file = join(directory, "actions.json");
    await writeFile(page, '<!doctype html><div class="iso-plate">Figure</div>');
    await writeFile(file, JSON.stringify(actions));
    try {
      return { code: 0, ...await execute(process.execPath, [drive, page, "--actions", file], { timeout: 30000 }) };
    } catch (error) {
      return { code: error.code, stdout: error.stdout, stderr: error.stderr };
    }
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
}

test("unknown actions fail instead of silently skipping verification", async () => {
  const result = await run([["unti", "false", 1]]);
  assert.equal(result.code, 1);
  assert.match(result.stderr, /unknown action unti/);
});

test("valid actions still execute after validation", async () => {
  const result = await run([["wait", 1], ["eval", "({checked:true})"]]);
  assert.equal(result.code, 0);
  assert.match(result.stdout, /eval: \{"checked":true\}/);
});

test("an invalid later action fails before earlier actions execute", async () => {
  const result = await run([["eval", "({shouldNotRun:true})"], ["screenshot", "out.png"]]);
  assert.equal(result.code, 1);
  assert.doesNotMatch(result.stdout, /shouldNotRun/);
});

test("orbit rejects a step that never reaches its end angle", async () => {
  for (const action of [["orbit", "out.png", 90, 0, 0], ["orbit", "out.png", 0, 90, -10], ["orbit", "out.png", 0, 90, "10"]]) {
    const result = await run([action]);
    assert.equal(result.code, 1, JSON.stringify(action));
    assert.match(result.stderr, /orbit needs numeric from, to and a nonzero step/);
  }
});

test("sheet rejects a count that yields no frames", async () => {
  for (const action of [["sheet", "out.png", 50, 0], ["sheet", "out.png", 50, 2.5], ["sheet", "out.png", -1, 3]]) {
    const result = await run([action]);
    assert.equal(result.code, 1, JSON.stringify(action));
    assert.match(result.stderr, /sheet needs a non-negative every/);
  }
});

test("a valid orbit and sheet still pass validation", async () => {
  const orbit = join(tmpdir(), `anatomy-orbit-${process.pid}.png`);
  const sheet = join(tmpdir(), `anatomy-sheet-${process.pid}.png`);
  try {
    const result = await run([["eval", "window.__isoTurn={set(){}}"], ["orbit", orbit, 0, 20, 10], ["sheet", sheet, 10, 2]]);
    assert.equal(result.code, 0, result.stderr);
  } finally {
    await rm(orbit, { force: true });
    await rm(sheet, { force: true });
  }
});
